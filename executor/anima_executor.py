from __future__ import annotations

import base64
import json
import math
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urljoin

from .config import AnimaToolConfig


def _round_up(x: int, base: int) -> int:
    if base <= 1:
        return x
    return int(math.ceil(x / base) * base)


def _parse_aspect_ratio(ratio: str) -> float:
    """
    解析 "16:9" -> 16/9。
    """
    s = (ratio or "").strip()
    if ":" not in s:
        raise ValueError(f"aspect_ratio 必须形如 '16:9'，收到：{ratio!r}")
    a_str, b_str = s.split(":", 1)
    a = float(a_str.strip())
    b = float(b_str.strip())
    if a <= 0 or b <= 0:
        raise ValueError(f"aspect_ratio 两边必须 > 0，收到：{ratio!r}")
    return a / b


def estimate_size_from_ratio(
    *,
    aspect_ratio: str,
    target_megapixels: float = 1.0,
    round_to: int = 16,
) -> Tuple[int, int]:
    """
    只给定长宽比时，估算 width/height，使像素数接近 target_megapixels。
    宽高会向上取整到 round_to 的倍数。
    
    注意：Anima 基于 Cosmos 架构，VAE 缩放 8 倍后还需被 spatial_patch_size=2 整除，
    所以 round_to 必须至少是 16（8×2），否则会报错 "should be divisible by spatial_patch_size"。
    """
    r = _parse_aspect_ratio(aspect_ratio)
    target_px = max(1.0, float(target_megapixels)) * 1_000_000.0
    w = int(math.sqrt(target_px * r))
    h = int(math.sqrt(target_px / r))
    w = _round_up(max(64, w), round_to)
    h = _round_up(max(64, h), round_to)
    return w, h


def align_dimension(value: int, round_to: int = 16) -> int:
    """
    将尺寸对齐到 round_to 的倍数（向上取整）。
    用于处理用户直接传入的 width/height。
    """
    return _round_up(max(64, int(value)), round_to)


def _join_csv(*parts: str) -> str:
    cleaned: List[str] = []
    for p in parts:
        if p is None:
            continue
        s = str(p).strip()
        if not s:
            continue
        cleaned.append(s)
    return ", ".join(cleaned)


def build_anima_positive_text(prompt_json: Dict[str, Any]) -> str:
    """
    按 Anima 推荐顺序拼接正面提示词（全部逗号连接，不分行）。
    顺序：[质量/安全/年份] [人数] [角色] [作品] [画师] [风格] [外观] [标签] [自然语言] [环境]
    """
    return _join_csv(
        prompt_json.get("quality_meta_year_safe", ""),
        prompt_json.get("count", ""),
        prompt_json.get("character", ""),
        prompt_json.get("series", ""),
        prompt_json.get("artist", ""),
        prompt_json.get("style", ""),
        prompt_json.get("appearance", ""),
        prompt_json.get("tags", ""),
        prompt_json.get("nltags", ""),
        prompt_json.get("environment", ""),
    )


@dataclass(frozen=True)
class GeneratedImage:
    filename: str
    subfolder: str
    folder_type: str
    view_url: str
    saved_path: Optional[str] = None
    content: Optional[bytes] = None  # 原始图片数据


class AnimaExecutor:
    """
    将结构化 JSON 注入 ComfyUI prompt 并执行，获取输出图片。
    """

    def __init__(self, config: Optional[AnimaToolConfig] = None):
        self.config = config or AnimaToolConfig()
        self._client_id = str(uuid.uuid4())

        template_path = Path(__file__).resolve().parent / "workflow_template.json"
        with template_path.open("r", encoding="utf-8") as f:
            self._workflow_template: Dict[str, Any] = json.load(f)

    # -------------------------
    # HTTP helpers (requests 优先, 无则 urllib)
    # -------------------------
    def _http_post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import requests  # type: ignore
        except Exception:
            requests = None  # type: ignore

        data = json.dumps(payload).encode("utf-8")
        if requests is not None:
            r = requests.post(url, json=payload, timeout=self.config.timeout_s)
            r.raise_for_status()
            return r.json()

        import urllib.request

        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.config.timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)

    def _http_get_json(self, url: str) -> Dict[str, Any]:
        try:
            import requests  # type: ignore
        except Exception:
            requests = None  # type: ignore

        if requests is not None:
            r = requests.get(url, timeout=self.config.timeout_s)
            r.raise_for_status()
            return r.json()

        import urllib.request

        with urllib.request.urlopen(url, timeout=self.config.timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)

    def _http_get_bytes(self, url: str) -> bytes:
        try:
            import requests  # type: ignore
        except Exception:
            requests = None  # type: ignore

        if requests is not None:
            r = requests.get(url, timeout=self.config.timeout_s)
            r.raise_for_status()
            return r.content

        import urllib.request

        with urllib.request.urlopen(url, timeout=self.config.timeout_s) as resp:
            return resp.read()

    # -------------------------
    # Core workflow injection
    # -------------------------
    def _inject(self, prompt_json: Dict[str, Any]) -> Dict[str, Any]:
        wf = deepcopy(self._workflow_template)

        # 模型文件：优先使用参数指定，其次使用配置，最后使用模板默认值
        clip_name = prompt_json.get("clip_name") or self.config.clip_name
        unet_name = prompt_json.get("unet_name") or self.config.unet_name
        vae_name = prompt_json.get("vae_name") or self.config.vae_name
        
        wf["45"]["inputs"]["clip_name"] = str(clip_name)
        wf["44"]["inputs"]["unet_name"] = str(unet_name)
        wf["15"]["inputs"]["vae_name"] = str(vae_name)

        # 文本
        positive = (prompt_json.get("positive") or "").strip()
        if not positive:
            positive = build_anima_positive_text(prompt_json)
        negative = (prompt_json.get("neg") or prompt_json.get("negative") or "").strip()

        wf["11"]["inputs"]["text"] = positive
        wf["12"]["inputs"]["text"] = negative

        # 分辨率
        width = prompt_json.get("width")
        height = prompt_json.get("height")
        aspect_ratio = (prompt_json.get("aspect_ratio") or "").strip()
        round_to = int(prompt_json.get("round_to") or self.config.round_to)

        if (width is None or height is None) and aspect_ratio:
            # 仅提供 aspect_ratio 时自动计算
            w, h = estimate_size_from_ratio(
                aspect_ratio=aspect_ratio,
                target_megapixels=float(prompt_json.get("target_megapixels") or self.config.target_megapixels),
                round_to=round_to,
            )
            width, height = w, h
        elif width is not None and height is not None:
            # 用户直接指定了 width/height，也需要对齐到 round_to 的倍数
            # 避免 "should be divisible by spatial_patch_size" 错误
            width = align_dimension(width, round_to)
            height = align_dimension(height, round_to)

        if width is None or height is None:
            # 默认方形 1MP（1024 是 16 的倍数）
            width, height = 1024, 1024

        wf["28"]["inputs"]["width"] = int(width)
        wf["28"]["inputs"]["height"] = int(height)
        wf["28"]["inputs"]["batch_size"] = int(prompt_json.get("batch_size") or 1)

        # 采样参数
        seed = prompt_json.get("seed")
        if seed is None:
            seed = int.from_bytes(uuid.uuid4().bytes[:4], "big", signed=False)
        wf["19"]["inputs"]["seed"] = int(seed)

        wf["19"]["inputs"]["steps"] = int(prompt_json.get("steps") or wf["19"]["inputs"]["steps"])
        wf["19"]["inputs"]["cfg"] = float(prompt_json.get("cfg") or wf["19"]["inputs"]["cfg"])
        wf["19"]["inputs"]["sampler_name"] = str(prompt_json.get("sampler_name") or wf["19"]["inputs"]["sampler_name"])
        wf["19"]["inputs"]["scheduler"] = str(prompt_json.get("scheduler") or wf["19"]["inputs"]["scheduler"])
        wf["19"]["inputs"]["denoise"] = float(prompt_json.get("denoise") or wf["19"]["inputs"]["denoise"])

        # 文件名前缀
        wf["52"]["inputs"]["filename_prefix"] = str(prompt_json.get("filename_prefix") or wf["52"]["inputs"]["filename_prefix"])

        return wf

    # -------------------------
    # Health check
    # -------------------------
    def check_comfyui_health(self) -> Tuple[bool, str]:
        """
        检查 ComfyUI 是否可访问。
        返回 (is_healthy, message)
        """
        try:
            url = urljoin(self.config.comfyui_url.rstrip("/") + "/", "system_stats")
            self._http_get_json(url)
            return True, f"ComfyUI 运行正常 ({self.config.comfyui_url})"
        except Exception as e:
            error_msg = str(e)
            # 提供友好的错误提示
            if "Connection refused" in error_msg or "连接" in error_msg:
                return False, (
                    f"无法连接到 ComfyUI ({self.config.comfyui_url})\n"
                    f"请确认：\n"
                    f"  1. ComfyUI 已启动\n"
                    f"  2. 地址和端口正确（可通过 COMFYUI_URL 环境变量修改）\n"
                    f"  3. 防火墙未阻止连接"
                )
            elif "timeout" in error_msg.lower() or "超时" in error_msg:
                return False, (
                    f"连接 ComfyUI 超时 ({self.config.comfyui_url})\n"
                    f"可能原因：网络延迟、ComfyUI 负载过高"
                )
            else:
                return False, f"ComfyUI 连接错误: {error_msg}"

    # -------------------------
    # ComfyUI execution
    # -------------------------
    def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        url = urljoin(self.config.comfyui_url.rstrip("/") + "/", "prompt")
        payload = {"prompt": prompt, "client_id": self._client_id}
        
        try:
            resp = self._http_post_json(url, payload)
        except Exception as e:
            # 先检查 ComfyUI 是否可访问
            is_healthy, health_msg = self.check_comfyui_health()
            if not is_healthy:
                raise RuntimeError(health_msg) from e
            raise
        
        prompt_id = str(resp.get("prompt_id") or "")
        if not prompt_id:
            # 检查是否有错误信息
            error = resp.get("error") or resp.get("node_errors")
            if error:
                raise RuntimeError(f"ComfyUI 执行错误：{error}")
            raise RuntimeError(f"ComfyUI /prompt 返回异常：{resp}")
        return prompt_id

    def wait_history(self, prompt_id: str) -> Dict[str, Any]:
        url = urljoin(self.config.comfyui_url.rstrip("/") + "/", f"history/{prompt_id}")
        deadline = time.time() + float(self.config.timeout_s)
        last = None
        while time.time() < deadline:
            data = self._http_get_json(url)
            last = data
            if isinstance(data, dict) and prompt_id in data:
                return data[prompt_id]
            time.sleep(float(self.config.poll_interval_s))
        raise TimeoutError(f"等待 ComfyUI 生成超时：prompt_id={prompt_id}, last={last}")

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
                qs = urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
                view_url = urljoin(self.config.comfyui_url.rstrip("/") + "/", f"view?{qs}")
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
        """下载图片并保存到本地，同时保留原始 bytes 用于 base64 编码"""
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        downloaded: List[GeneratedImage] = []
        for im in images:
            # 总是下载内容（用于 base64）
            content = self._http_get_bytes(im.view_url)
            
            saved_path = None
            if self.config.download_images:
                # 复刻 ComfyUI 的 subfolder 结构（可选）
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

    def _get_mime_type(self, filename: str) -> str:
        """根据文件名推断 MIME 类型"""
        ext = Path(filename).suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(ext, "image/png")

    def check_models(self) -> Tuple[bool, str]:
        """
        检查模型文件是否存在（如果配置了 COMFYUI_MODELS_DIR）。
        返回 (is_ok, message)
        """
        if not self.config.check_models or not self.config.comfyui_models_dir:
            return True, "模型检查已跳过（未配置 COMFYUI_MODELS_DIR）"
        
        all_exist, missing = self.config.check_models_exist()
        if all_exist:
            return True, "所有模型文件已就绪"
        
        missing_str = "\n".join(f"  - {m}" for m in missing)
        return False, (
            f"缺少以下模型文件：\n{missing_str}\n\n"
            f"请从 HuggingFace 下载：https://huggingface.co/circlestone-labs/Anima\n"
            f"并放置到 ComfyUI/models/ 对应子目录"
        )

    def generate(self, prompt_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入结构化 JSON，执行生成。

        返回：
        - prompt_id
        - positive / negative（最终发送给 ComfyUI 的文本）
        - width / height
        - images: [{filename, url, file_path, base64, mime_type, markdown}]
        """
        # 预检查：模型文件
        models_ok, models_msg = self.check_models()
        if not models_ok:
            raise RuntimeError(models_msg)
        
        prompt = self._inject(prompt_json)
        prompt_id = self.queue_prompt(prompt)
        history_item = self.wait_history(prompt_id)
        images = self._extract_images(prompt_id, history_item)
        images = self._download_images(images)

        # 构建图片信息（包含多种格式）
        images_data = []
        for im in images:
            mime_type = self._get_mime_type(im.filename)
            b64 = base64.b64encode(im.content).decode("ascii") if im.content else None
            
            img_info = {
                "filename": im.filename,
                "subfolder": im.subfolder,
                "type": im.folder_type,
                # URL 格式
                "url": im.view_url,
                "view_url": im.view_url,  # 兼容旧字段
                # 本地路径
                "file_path": im.saved_path,
                "saved_path": im.saved_path,  # 兼容旧字段
                # Base64 格式（用于 MCP / Gemini / 嵌入）
                "base64": b64,
                "mime_type": mime_type,
                # Data URL（可直接用于 <img src> 或 markdown）
                "data_url": f"data:{mime_type};base64,{b64}" if b64 else None,
                # Markdown 格式（AI 可直接输出）
                "markdown": f"![{im.filename}]({im.view_url})",
            }
            images_data.append(img_info)

        # 回显最终参数（便于调试）
        result = {
            "success": True,
            "prompt_id": prompt_id,
            "positive": prompt["11"]["inputs"]["text"],
            "negative": prompt["12"]["inputs"]["text"],
            "width": prompt["28"]["inputs"]["width"],
            "height": prompt["28"]["inputs"]["height"],
            "images": images_data,
        }
        return result
