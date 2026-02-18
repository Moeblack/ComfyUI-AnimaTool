from __future__ import annotations

import base64
import json
import math
import time
import uuid
import os
import io
import urllib.request
import urllib.parse
import urllib.error
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None

from .config import AnimaToolConfig
from .history import HistoryManager
from .anima_executor import GeneratedImage, estimate_size_from_ratio, align_dimension


def build_qwen_instruction(prompt_json: Dict[str, Any]) -> str:
    """
    按照 QwenEdit 的特性，将结构化 JSON 智能组装为连贯的祈使句。
    支持多重编辑连击，以及生图/修图模式下的智能取舍。
    """
    parts = []

    # 1. 动作连击 (修图专属)
    edit_actions = prompt_json.get("edit_actions") or []
    if isinstance(edit_actions, list):
        for action in edit_actions:
            if action and str(action).strip():
                parts.append(str(action).strip())
    elif isinstance(edit_actions, str) and edit_actions.strip():
        parts.append(edit_actions.strip())

    # 2. 角色与外观 (生图核心，修图慎用)
    character = str(prompt_json.get("character_and_action") or "").strip()
    if character:
        parts.append(character)

    appearance = str(prompt_json.get("appearance_details") or "").strip()
    if appearance:
        parts.append(appearance)

    env = str(prompt_json.get("environment_and_lighting") or "").strip()
    if env:
        parts.append(env)

    # 3. 风格与画质 (全局生效)
    style = str(prompt_json.get("style_and_quality") or "").strip()
    if style:
        parts.append(style)

    # 4. 文字生成 (Qwen 独家功能)
    text = str(prompt_json.get("render_text") or "").strip()
    if text:
        # 如果用户本身没有加双引号，就帮他加一下以符合指南
        if '"' not in text and "'" not in text:
            parts.append(f'画面中写着文字"{text}"')
        else:
            parts.append(f'画面中写着文字 {text}')

    # 5. 防崩坏锁 (修图核心)
    constraints = str(prompt_json.get("preserve_constraints") or "").strip()
    if constraints:
        parts.append(constraints)

    # 拼接并确保中文断句自然
    # 如果没有使用中文句号，自动加上
    cleaned = []
    for p in parts:
        if not p.endswith("。") and not p.endswith("."):
            p += "。"
        cleaned.append(p)

    return " ".join(cleaned)


class QwenExecutor:
    """
    专为 Qwen-Rapid-AIO 设计的执行器。
    处理动态拓扑结构（T2I/I2I）和多图上传逻辑。
    """

    def __init__(self, config: Optional[AnimaToolConfig] = None):
        self.config = config or AnimaToolConfig()
        self._client_id = str(uuid.uuid4())

        template_path = Path(__file__).resolve().parent / "qwen_workflow_template.json"
        with template_path.open("r", encoding="utf-8") as f:
            self._workflow_template: Dict[str, Any] = json.load(f)

        self.history = HistoryManager()

    # -------------------------
    # HTTP and Upload Helpers
    # -------------------------
    def _http_post_multipart(self, url: str, file_path: str) -> Dict[str, Any]:
        """将本地图片上传给 ComfyUI /upload/image"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"要上传的文件不存在：{file_path}")

        boundary = uuid.uuid4().hex
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

        with path.open("rb") as f:
            file_data = f.read()

        filename = path.name
        # 简单推断 mime
        mime = "image/png"
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            mime = "image/jpeg"
        elif filename.lower().endswith(".webp"):
            mime = "image/webp"

        # 构造 multipart/form-data body
        body = io.BytesIO()
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode("utf-8"))
        body.write(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        body.write(file_data)
        body.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        body_bytes = body.getvalue()

        req = urllib.request.Request(url, data=body_bytes, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {raw}") from e

    def _http_post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except Exception as e:
            if hasattr(e, "read"):
                raw = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {getattr(e, 'code', 'error')}: {raw}") from e
            raise

    def _http_get_json(self, url: str) -> Any:
        try:
            with urllib.request.urlopen(url, timeout=self.config.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except Exception as e:
            if hasattr(e, "read"):
                raw = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP GET {getattr(e, 'code', 'error')}: {raw}") from e
            raise

    def _http_get_bytes(self, url: str) -> bytes:
        try:
            with urllib.request.urlopen(url, timeout=self.config.timeout_s) as resp:
                return resp.read()
        except Exception as e:
            if hasattr(e, "read"):
                raw = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP GET BYTES {getattr(e, 'code', 'error')}: {raw}") from e
            raise

    def _upload_image(self, file_path: str) -> str:
        """上传图片并返回服务端保存的文件名"""
        url = urllib.parse.urljoin(self.config.comfyui_url.rstrip("/") + "/", "upload/image")
        try:
            resp = self._http_post_multipart(url, file_path)
            # 兼容各种版本的 ComfyUI 返回格式
            return str(resp.get("name") or resp.get("filename") or "")
        except Exception as e:
            raise RuntimeError(f"上传图片到 ComfyUI 失败：{file_path} -> {str(e)}") from e

    # -------------------------
    # Resolution Strategy
    # -------------------------
    def _get_image_size(self, file_path: str) -> Tuple[int, int]:
        if Image is None:
            # 如果没装 Pillow，随便给个兜底
            return 1024, 1024
        try:
            with Image.open(file_path) as img:
                return img.size
        except Exception:
            return 1024, 1024

    def _resolve_dimensions(self, prompt_json: Dict[str, Any], base_image_path: Optional[str]) -> Tuple[int, int]:
        """
        核心分辨率策略：
        - 如果传了明确的 width/height，强制对齐 16 的倍数并使用（无论是否传图，这支持扩图）。
        - 否则如果有底图，读取底图原始比例，缩放到 1 Megapixel。
        - 否则如果有 aspect_ratio，缩放到 1 Megapixel。
        - 兜底 1024x1024。
        """
        w = prompt_json.get("width")
        h = prompt_json.get("height")
        ratio_str = prompt_json.get("aspect_ratio")

        if w is not None and h is not None:
            return align_dimension(int(w)), align_dimension(int(h))

        # 尝试通过比例计算（1 Megapixel 面积）
        target_ratio = None
        if ratio_str:
            target_ratio = str(ratio_str)
        elif base_image_path and Path(base_image_path).exists():
            orig_w, orig_h = self._get_image_size(base_image_path)
            target_ratio = f"{orig_w}:{orig_h}"

        if target_ratio:
            try:
                # 复用 AnimaTool 的算法
                ew, eh = estimate_size_from_ratio(aspect_ratio=target_ratio, target_megapixels=1.0)
                return ew, eh
            except Exception:
                pass

        return 1024, 1024

    # -------------------------
    # Core workflow injection
    # -------------------------
    def _inject(self, prompt_json: Dict[str, Any]) -> Dict[str, Any]:
        wf = deepcopy(self._workflow_template)

        # 1. 解析提示词 (Qwen Edit 需要的是指令式长句)
        instruction = build_qwen_instruction(prompt_json)
        wf["3"]["inputs"]["prompt"] = instruction

        # 2. 图片上传与动态连线处理
        base_img_path = prompt_json.get("base_image")
        ref_img_paths = prompt_json.get("reference_images") or []
        if isinstance(ref_img_paths, str):
            ref_img_paths = [ref_img_paths]

        # 计算应该由 EmptyLatent 提供的尺寸
        final_w, final_h = self._resolve_dimensions(prompt_json, base_img_path)
        wf["9"]["inputs"]["width"] = final_w
        wf["9"]["inputs"]["height"] = final_h
        wf["9"]["inputs"]["batch_size"] = int(prompt_json.get("batch_size") or 1)

        # -----------------------------
        # 处理图片节点 (7, 8, 13)
        # -----------------------------
        # Node 7: base_image (Image1)
        if base_img_path and Path(base_img_path).exists():
            remote_name = self._upload_image(base_img_path)
            wf["7"]["inputs"]["image"] = remote_name
            # 图生图核心连线没有改变（因为 EmptyLatentImage 其实就是作为画布提供给 Qwen 的）
            # base_image 被连入 TextEncodeQwenImageEditPlus 的 image1，由 LLM 处理视觉！
        else:
            # 没有 base_image -> 文生图模式
            del wf["7"]
            del wf["3"]["inputs"]["image1"]

        # Node 8: ref_image_1 (Image2)
        if len(ref_img_paths) > 0 and Path(ref_img_paths[0]).exists():
            remote_name = self._upload_image(ref_img_paths[0])
            wf["8"]["inputs"]["image"] = remote_name
        else:
            del wf["8"]
            del wf["3"]["inputs"]["image2"]

        # Node 13: ref_image_2 (Image3)
        if len(ref_img_paths) > 1 and Path(ref_img_paths[1]).exists():
            remote_name = self._upload_image(ref_img_paths[1])
            wf["13"]["inputs"]["image"] = remote_name
        else:
            del wf["13"]
            del wf["3"]["inputs"]["image3"]

        # 3. KSampler 参数 (复用默认，或用户覆盖)
        seed = prompt_json.get("seed")
        if seed is None:
            seed = int.from_bytes(uuid.uuid4().bytes[:4], "big", signed=False)
        wf["2"]["inputs"]["seed"] = int(seed)

        if "steps" in prompt_json:
            wf["2"]["inputs"]["steps"] = int(prompt_json["steps"])
        if "cfg" in prompt_json:
            wf["2"]["inputs"]["cfg"] = float(prompt_json["cfg"])

        # Qwen-Rapid-AIO 的模型名，如果在配置中有，也可以替换
        ckpt_name = prompt_json.get("ckpt_name") or r"_Qwen\Qwen-Rapid-AIO-NSFW-v23.safetensors"
        wf["1"]["inputs"]["ckpt_name"] = str(ckpt_name)

        return wf

    # -------------------------
    # Execution Flow
    # -------------------------
    def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        url = urllib.parse.urljoin(self.config.comfyui_url.rstrip("/") + "/", "prompt")
        payload = {"prompt": prompt, "client_id": self._client_id}
        resp = self._http_post_json(url, payload)
        
        prompt_id = str(resp.get("prompt_id") or "")
        if not prompt_id:
            error = resp.get("error") or resp.get("node_errors")
            if error:
                raise RuntimeError(f"ComfyUI 执行错误：{error}")
            raise RuntimeError(f"ComfyUI /prompt 返回异常：{resp}")
        return prompt_id

    def wait_history(self, prompt_id: str) -> Dict[str, Any]:
        url = urllib.parse.urljoin(self.config.comfyui_url.rstrip("/") + "/", f"history/{prompt_id}")
        deadline = time.time() + float(self.config.timeout_s)
        while time.time() < deadline:
            data = self._http_get_json(url)
            if isinstance(data, dict) and prompt_id in data:
                return data[prompt_id]
            time.sleep(float(self.config.poll_interval_s))
        raise TimeoutError(f"等待 ComfyUI 生成超时：prompt_id={prompt_id}")

    def _extract_images(self, prompt_id: str, history_item: Dict[str, Any]) -> List[GeneratedImage]:
        outputs = history_item.get("outputs") or {}
        images: List[GeneratedImage] = []
        for node_id, node_out in outputs.items():
            if not isinstance(node_out, dict):
                continue
            for im in node_out.get("images") or []:
                filename = str(im.get("filename") or "")
                subfolder = str(im.get("subfolder") or "")
                folder_type = str(im.get("type") or "output")
                if not filename:
                    continue
                qs = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
                view_url = urllib.parse.urljoin(self.config.comfyui_url.rstrip("/") + "/", f"view?{qs}")
                images.append(
                    GeneratedImage(
                        filename=filename,
                        subfolder=subfolder,
                        folder_type=folder_type,
                        view_url=view_url,
                        saved_path=None,
                    )
                )
        return images

    def _download_images(self, images: List[GeneratedImage]) -> List[GeneratedImage]:
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        downloaded: List[GeneratedImage] = []
        for im in images:
            content = self._http_get_bytes(im.view_url)
            saved_path = None
            if self.config.download_images:
                sub_dir = out_dir / (im.subfolder or "")
                sub_dir.mkdir(parents=True, exist_ok=True)
                dst = sub_dir / im.filename
                dst.write_bytes(content)
                saved_path = str(dst)
            
            downloaded.append(
                GeneratedImage(
                    filename=im.filename,
                    subfolder=im.subfolder,
                    folder_type=im.folder_type,
                    view_url=im.view_url,
                    saved_path=saved_path,
                    content=content,
                )
            )
        return downloaded

    def generate(self, prompt_json: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._inject(prompt_json)
        prompt_id = self.queue_prompt(prompt)
        history_item = self.wait_history(prompt_id)
        images = self._extract_images(prompt_id, history_item)
        images = self._download_images(images)

        images_data = []
        for im in images:
            ext = Path(im.filename).suffix.lower()
            mime_type = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")
            b64 = base64.b64encode(im.content).decode("ascii") if im.content else None
            
            images_data.append({
                "filename": im.filename,
                "subfolder": im.subfolder,
                "type": im.folder_type,
                "url": im.view_url,
                "file_path": im.saved_path,
                "base64": b64,
                "mime_type": mime_type,
                "markdown": f"![{im.filename}]({im.view_url})",
            })

        actual_seed = int(prompt["2"]["inputs"]["seed"])
        actual_width = int(prompt["9"]["inputs"]["width"])
        actual_height = int(prompt["9"]["inputs"]["height"])
        actual_instruction = str(prompt["3"]["inputs"]["prompt"])

        result = {
            "success": True,
            "prompt_id": prompt_id,
            "instruction_sent": actual_instruction,
            "seed": actual_seed,
            "width": actual_width,
            "height": actual_height,
            "images": images_data,
        }

        # 记录到历史（复用原有的格式）
        record = self.history.add(
            params=prompt_json,
            positive_text=actual_instruction,
            negative_text="",
            prompt_id=prompt_id,
            seed=actual_seed,
            width=actual_width,
            height=actual_height,
        )
        result["history_id"] = record.id

        return result
