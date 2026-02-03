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
    # 宽高向上取整到 round_to 的倍数
    # 注意：Anima 基于 Cosmos 架构，VAE 缩放 8 倍后还需被 spatial_patch_size=2 整除
    # 所以必须是 8×2=16 的倍数，否则会报错 "should be divisible by spatial_patch_size"
    round_to: int = 16
