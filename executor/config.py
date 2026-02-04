from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple


def _get_env_bool(key: str, default: bool) -> bool:
    """从环境变量获取布尔值"""
    val = os.environ.get(key, "").lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _get_env_float(key: str, default: float) -> float:
    """从环境变量获取浮点数"""
    val = os.environ.get(key)
    if val:
        try:
            return float(val)
        except ValueError:
            pass
    return default


def _get_env_int(key: str, default: int) -> int:
    """从环境变量获取整数"""
    val = os.environ.get(key)
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    return default


# 默认模型文件名
DEFAULT_UNET_NAME = "anima-preview.safetensors"
DEFAULT_CLIP_NAME = "qwen_3_06b_base.safetensors"
DEFAULT_VAE_NAME = "qwen_image_vae.safetensors"


@dataclass
class AnimaToolConfig:
    """
    Anima 工具配置。

    所有配置项都支持通过环境变量覆盖：
    - COMFYUI_URL: ComfyUI Web 服务地址（默认 http://127.0.0.1:8188）
    - ANIMATOOL_DOWNLOAD_IMAGES: 是否下载图片到本地（默认 true）
    - ANIMATOOL_OUTPUT_DIR: 图片输出目录
    - ANIMATOOL_TIMEOUT: 生成超时时间（秒，默认 600）
    - ANIMATOOL_POLL_INTERVAL: 轮询间隔（秒，默认 1）
    - ANIMATOOL_TARGET_MP: 目标像素数（MP，默认 1.0）
    - ANIMATOOL_ROUND_TO: 分辨率对齐倍数（默认 16）

    示例：
        # Windows PowerShell
        $env:COMFYUI_URL = "http://192.168.1.100:8188"

        # Linux/macOS
        export COMFYUI_URL=http://192.168.1.100:8188

        # Cursor MCP 配置中
        {
          "mcpServers": {
            "anima-tool": {
              "command": "python",
              "args": ["mcp_server.py"],
              "env": {
                "COMFYUI_URL": "http://192.168.1.100:8188"
              }
            }
          }
        }
    """

    # ComfyUI 服务地址
    # 支持：本地 (127.0.0.1)、局域网 (192.168.x.x)、Docker (host.docker.internal)
    comfyui_url: str = field(
        default_factory=lambda: os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
    )

    # 下载模式：把 /view 拿到的图片保存到本地
    download_images: bool = field(
        default_factory=lambda: _get_env_bool("ANIMATOOL_DOWNLOAD_IMAGES", True)
    )
    output_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("ANIMATOOL_OUTPUT_DIR", "")
        ) if os.environ.get("ANIMATOOL_OUTPUT_DIR") else Path(__file__).resolve().parent.parent / "outputs"
    )

    # 轮询历史接口等待执行完成
    timeout_s: float = field(
        default_factory=lambda: _get_env_float("ANIMATOOL_TIMEOUT", 600.0)
    )
    poll_interval_s: float = field(
        default_factory=lambda: _get_env_float("ANIMATOOL_POLL_INTERVAL", 1.0)
    )

    # 分辨率生成：当只给 aspect_ratio 时，按目标像素数估算宽高
    target_megapixels: float = field(
        default_factory=lambda: _get_env_float("ANIMATOOL_TARGET_MP", 1.0)
    )
    # 宽高向上取整到 round_to 的倍数
    # 注意：Anima 基于 Cosmos 架构，VAE 缩放 8 倍后还需被 spatial_patch_size=2 整除
    # 所以必须是 8×2=16 的倍数，否则会报错 "should be divisible by spatial_patch_size"
    round_to: int = field(
        default_factory=lambda: _get_env_int("ANIMATOOL_ROUND_TO", 16)
    )

    # -------------------------
    # 模型配置
    # -------------------------
    # ComfyUI models 根目录（用于模型预检查）
    # 如果不设置，则尝试自动探测，探测失败则跳过预检查（远程 ComfyUI 场景）
    comfyui_models_dir: Optional[Path] = field(
        default_factory=lambda: (
            Path(os.environ["COMFYUI_MODELS_DIR"]) if os.environ.get("COMFYUI_MODELS_DIR") else 
            (Path.cwd() / "models" if (Path.cwd() / "models").exists() else 
             (Path(__file__).resolve().parent.parent.parent.parent / "models" if (Path(__file__).resolve().parent.parent.parent.parent / "models").exists() else None))
        )
    )

    # 模型文件名（可通过环境变量或参数覆盖）
    unet_name: str = field(
        default_factory=lambda: os.environ.get("ANIMATOOL_UNET_NAME", DEFAULT_UNET_NAME)
    )
    clip_name: str = field(
        default_factory=lambda: os.environ.get("ANIMATOOL_CLIP_NAME", DEFAULT_CLIP_NAME)
    )
    vae_name: str = field(
        default_factory=lambda: os.environ.get("ANIMATOOL_VAE_NAME", DEFAULT_VAE_NAME)
    )

    # 是否启用模型预检查（默认启用，但需要设置 COMFYUI_MODELS_DIR）
    check_models: bool = field(
        default_factory=lambda: _get_env_bool("ANIMATOOL_CHECK_MODELS", True)
    )

    def get_model_paths(self) -> dict:
        """
        返回模型文件的预期路径（相对于 ComfyUI models 目录）。
        """
        return {
            "unet": ("diffusion_models", self.unet_name),
            "clip": ("text_encoders", self.clip_name),
            "vae": ("vae", self.vae_name),
        }

    def check_models_exist(self) -> Tuple[bool, List[str]]:
        """
        检查模型文件是否存在。
        
        Returns:
            (all_exist, missing_files): 是否全部存在，缺失的文件列表
        """
        if not self.comfyui_models_dir:
            # 未配置 models 目录，跳过检查
            return True, []
        
        models_dir = Path(self.comfyui_models_dir)
        if not models_dir.exists():
            return False, [f"ComfyUI models 目录不存在: {models_dir}"]
        
        missing = []
        for model_type, (subdir, filename) in self.get_model_paths().items():
            model_path = models_dir / subdir / filename
            if not model_path.exists():
                missing.append(f"{model_type}: {subdir}/{filename}")
        
        return len(missing) == 0, missing
