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
        "width": {"type": "integer", "description": "宽度（可选，会覆盖 aspect_ratio）"},
        "height": {"type": "integer", "description": "高度（可选，会覆盖 aspect_ratio）"},
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
    },
    "required": ["quality_meta_year_safe", "count", "artist", "tags", "neg"]
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="generate_anima_image",
            description="使用 Anima 模型生成二次元/插画图片。画师必须以 @ 开头（如 @fkey, @jima）。必须明确安全标签（safe/sensitive/nsfw/explicit）。",
            inputSchema=TOOL_SCHEMA,
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent]:
    """调用工具"""
    if name != "generate_anima_image":
        return [TextContent(type="text", text=f"未知工具: {name}")]

    try:
        executor = get_executor()
        
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
