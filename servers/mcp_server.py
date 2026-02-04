"""
Anima Tool MCP Server

让 Cursor/Claude 等支持 MCP 的客户端可以直接调用图像生成，并原生显示图片。

启动方式：
    python -m servers.mcp_server

或在 Cursor 配置中添加此 MCP Server。
"""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence

# 确保能 import 上层 executor
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    CallToolResult,
)

from executor import AnimaExecutor, AnimaToolConfig


# 创建 MCP Server
server = Server("anima-tool")

# 全局 executor（懒加载）
_executor: AnimaExecutor | None = None


def get_executor() -> AnimaExecutor:
    global _executor
    if _executor is None:
        _executor = AnimaExecutor(config=AnimaToolConfig())
    return _executor


# Tool Schema（从 tool_schema_universal.json 简化）
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt_hint": {
            "type": "string",
            "description": "可选：人类可读的简短需求摘要"
        },
        "aspect_ratio": {
            "type": "string",
            "description": "长宽比，如 '16:9'、'9:16'、'1:1'",
            "enum": ["21:9", "2:1", "16:9", "16:10", "5:3", "3:2", "4:3", "1:1", "3:4", "2:3", "3:5", "10:16", "9:16", "1:2", "9:21"]
        },
        "width": {"type": "integer", "description": "宽度（像素），必须是 16 的倍数如 512/768/1024，否则自动对齐。会覆盖 aspect_ratio"},
        "height": {"type": "integer", "description": "高度（像素），必须是 16 的倍数如 512/768/1024，否则自动对齐。会覆盖 aspect_ratio"},
        "quality_meta_year_safe": {
            "type": "string",
            "description": "质量/年份/安全标签。必须包含 safe/sensitive/nsfw/explicit 之一"
        },
        "count": {
            "type": "string",
            "description": "人数，如 '1girl'、'2girls'、'1boy'"
        },
        "character": {"type": "string", "description": "角色名"},
        "series": {"type": "string", "description": "作品名"},
        "appearance": {"type": "string", "description": "角色外观（发色、眼睛等）"},
        "artist": {
            "type": "string",
            "description": "画师，必须以 @ 开头。支持多画师混合（如 '@fkey, @jima'）但稳定性下降，AI 自动生成时建议只用 1 位"
        },
        "style": {"type": "string", "description": "画风"},
        "tags": {
            "type": "string",
            "description": "Danbooru 标签（逗号分隔）"
        },
        "nltags": {"type": "string", "description": "自然语言补充（最多一句）"},
        "environment": {"type": "string", "description": "环境/光影"},
        "neg": {
            "type": "string",
            "description": "负面提示词",
            "default": "worst quality, low quality, blurry, bad hands, bad anatomy, extra fingers, missing fingers, text, watermark"
        },
        "steps": {"type": "integer", "description": "步数", "default": 25},
        "cfg": {"type": "number", "description": "CFG", "default": 4.5},
        "sampler_name": {"type": "string", "description": "采样器", "default": "er_sde"},
        "seed": {"type": "integer", "description": "种子（不填则随机）"},
        "loras": {
            "type": "array",
            "description": (
                "可选：多 LoRA（仅 UNET）。会在 UNETLoader 与 KSampler 之间按顺序链式注入 LoraLoaderModelOnly。"
                "重要：ComfyUI 会对 lora_name 做枚举校验，必须与 GET /models/loras 返回的字符串完全一致（含子目录分隔符）。"
                "Windows 下通常使用反斜杠 `\\` 作为子目录分隔符；如果在 JSON 字符串里手写，需要写成 `\\\\` 才表示一个 `\\`。"
                "另外：list_anima_models(model_type=loras) 只返回带同名 .json sidecar 元数据的 LoRA（强制要求）。"
            ),
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "LoRA 名称（必须逐字匹配 /models/loras 的返回值；可包含子目录）",
                    },
                    "weight": {"type": "number", "default": 1.0}
                },
                "required": ["name"]
            }
        },
    },
    "required": ["quality_meta_year_safe", "count", "artist", "tags", "neg"]
}


LIST_MODELS_SCHEMA = {
    "type": "object",
    "properties": {
        "model_type": {
            "type": "string",
            "enum": ["loras", "diffusion_models", "vae", "text_encoders"],
            "description": "要查询的模型类型。loras 将只返回存在同名 .json sidecar 元数据文件的 LoRA（强制要求）。提示：生成时 lora_name 必须与 /models/loras 返回值逐字一致（Windows 多为 \\\\ 分隔子目录）。",
        }
    },
    "required": ["model_type"],
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="generate_anima_image",
            description="使用 Anima 模型生成二次元/插画图片。画师必须以 @ 开头（如 @fkey）。必须明确安全标签（safe/sensitive/nsfw/explicit）。支持并行调用：生成多张图时可同时发起多个请求，无需串行等待。",
            inputSchema=TOOL_SCHEMA,
        ),
        Tool(
            name="list_anima_models",
            description=(
                "查询 ComfyUI 当前可用的模型文件列表（loras/diffusion_models/vae/text_encoders）。"
                "注意：当 model_type=loras 时，强制只返回存在同名 .json sidecar 元数据文件的 LoRA。"
            ),
            inputSchema=LIST_MODELS_SCHEMA,
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent]:
    """调用工具"""
    try:
        executor = get_executor()

        if name == "list_anima_models":
            model_type = str((arguments or {}).get("model_type") or "").strip()
            if not model_type:
                return [TextContent(type="text", text="参数错误：model_type 不能为空")]

            result = await asyncio.to_thread(executor.list_models, model_type)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        if name != "generate_anima_image":
            return [TextContent(type="text", text=f"未知工具: {name}")]

        # 在线程池中执行同步操作
        result = await asyncio.to_thread(executor.generate, arguments)

        if not result.get("success"):
            return [TextContent(type="text", text=f"生成失败: {result}")]

        # 构建返回内容
        contents: list[TextContent | ImageContent] = []

        # 添加文本信息
        info_text = f"""生成成功！
- 分辨率: {result['width']} x {result['height']}
- 正面提示词: {result['positive'][:100]}...
- 图片数量: {len(result['images'])}"""
        contents.append(TextContent(type="text", text=info_text))

        # 添加图片（base64 格式，原生显示）
        for img in result.get("images", []):
            if img.get("base64") and img.get("mime_type"):
                contents.append(
                    ImageContent(
                        type="image",
                        data=img["base64"],
                        mimeType=img["mime_type"],
                    )
                )

        return contents

    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def main():
    """启动 MCP Server（stdio 模式）"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
