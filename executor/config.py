from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnimaToolConfig:
    """
    Anima 工具配置。

    说明：
    - comfyui_url: ComfyUI Web 服务地址（默认本机 8188）
    - output_dir: 下载图片到本地的目录（工具侧保存）
    """

    comfyui_url: str = "http://127.0.0.1:8188"

    # 下载模式：把 /view 拿到的图片保存到本地
    download_images: bool = True
    output_dir: Path = Path(__file__).resolve().parent.parent / "outputs"

    # 轮询历史接口等待执行完成
    timeout_s: float = 600.0
    poll_interval_s: float = 1.0

    # 分辨率生成：当只给 aspect_ratio 时，按目标像素数估算宽高
    target_megapixels: float = 1.0
    round_to: int = 8  # 宽高向上取整到 round_to 的倍数（8 兼容性最好）
