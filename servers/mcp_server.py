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
            "description": "画师，必须以 @ 开头。支持多画师混合（如 '@fkey, @jima'），但稳定性下降，AI 自动生成时建议只用 1 位。画师名遵循特定格式：1. 名字中间无下划线（如 @kawakami rokkaku, 而非 @kawakami_rokkaku）；2. 以 @ 开头（如 @fkey）。如果画师名里本身有括号，如 @yd (orange maru), 则需要用转移符号转义括号，记作 @yd \\(orange maru\\), 以避免被解析器误认为是附加信息。"
        },
        "style": {"type": "string", "description": "画风"},
        "tags": {
            "type": "string",
            "description": "Danbooru 标签（逗号分隔）"
        },
        "nltags": {"type": "string", "description": "自然语言补充"},
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
        "repeat": {
            "type": "integer",
            "description": "提交几次独立生成任务（queue 模式，每次独立随机 seed）。默认 1。总生成张数 = repeat × batch_size",
            "default": 1, "minimum": 1, "maximum": 16,
        },
        "batch_size": {
            "type": "integer",
            "description": "单次任务内生成几张（latent batch 模式，共享参数，更吃显存）。默认 1",
            "default": 1, "minimum": 1, "maximum": 4,
        },
        "loras": {
            "type": "array",
            "description": (
                "可选：多 LoRA（仅 UNET）。会在 UNETLoader 与 KSampler 之间按顺序链式注入 LoraLoaderModelOnly。"
                "重要：ComfyUI 会对 lora_name 做枚举校验，必须与 GET /models/loras 返回的字符串完全一致（含子目录分隔符）。"
                "可使用 list_anima_models(model_type=loras) 工具查询当前可用的 LoRA 模型列表，并确保使用的 LoRA 存在同名 .json sidecar 元数据文件（强制要求）。"
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


LIST_HISTORY_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "返回最近几条历史记录（默认 5）",
            "default": 5, "minimum": 1, "maximum": 50,
        },
    },
}


# reroll schema：source 必填 + generate 的所有可选参数可作为覆盖项
_REROLL_OVERRIDE_PROPS = {
    k: v for k, v in TOOL_SCHEMA["properties"].items()
}
REROLL_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {
            "type": "string",
            "description": "要 reroll 的历史记录。'last' 表示最近一条，或使用历史 ID（如 '12' 或 '#12'）",
        },
        **_REROLL_OVERRIDE_PROPS,
    },
    "required": ["source"],
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="generate_anima_image",
            description=(
                "使用 Anima 模型生成二次元/插画图片。画师必须以 @ 开头（如 @fkey）。"
                "必须明确安全标签（safe/sensitive/nsfw/explicit）。"
                "支持 repeat 参数一次提交多个独立生成任务（默认方式），"
                "也支持 batch_size 参数在单任务内生成多张。"
            ),
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
        Tool(
            name="list_anima_history",
            description=(
                "查看最近的图片生成历史记录。"
                "返回每条记录的 ID、时间、画师、标签、种子等摘要信息。"
                "用于在 reroll 之前确认要引用哪条历史。"
            ),
            inputSchema=LIST_HISTORY_SCHEMA,
        ),
        Tool(
            name="reroll_anima_image",
            description=(
                "基于历史记录重新生成图片。引用一条历史记录作为基础参数，"
                "可选覆盖部分参数（如换画师、加 LoRA 等）。"
                "seed 默认自动随机（出不同画面），也可手动指定保持一致。"
                "支持 repeat 参数一次提交多个独立任务。"
            ),
            inputSchema=REROLL_SCHEMA,
        ),
    ]


async def _generate_with_repeat(
    executor: "AnimaExecutor",
    prompt_json: Dict[str, Any],
) -> list[TextContent | ImageContent]:
    """执行生成（支持 repeat 多次独立 queue 提交），返回 MCP 内容列表。"""
    from copy import deepcopy

    repeat = max(1, int(prompt_json.pop("repeat", 1) or 1))
    # batch_size 留在 prompt_json 中，由 executor._inject() 处理

    all_contents: list[TextContent | ImageContent] = []
    history_ids: list[int] = []

    for i in range(repeat):
        run_params = deepcopy(prompt_json)
        # 每次 repeat 都使用新随机 seed（除非用户显式指定了 seed）
        if "seed" not in prompt_json or prompt_json.get("seed") is None:
            run_params.pop("seed", None)

        result = await asyncio.to_thread(executor.generate, run_params)

        if not result.get("success"):
            all_contents.append(TextContent(type="text", text=f"第 {i+1}/{repeat} 次生成失败: {result}"))
            continue

        if result.get("history_id"):
            history_ids.append(result["history_id"])

        for img in result.get("images", []):
            if img.get("base64") and img.get("mime_type"):
                all_contents.append(
                    ImageContent(
                        type="image",
                        data=img["base64"],
                        mimeType=img["mime_type"],
                    )
                )

    if not all_contents:
        all_contents.append(TextContent(type="text", text="生成完成，但没有产出图片。"))

    # 追加历史 ID 提示，让 AI 自然知道可以 reroll
    if history_ids:
        ids_str = ", ".join(f"#{hid}" for hid in history_ids)
        hint = f"已保存为历史记录 {ids_str}。可用 reroll_anima_image(source=\"{history_ids[-1]}\") 或 reroll_anima_image(source=\"last\") 重新生成。"
        all_contents.append(TextContent(type="text", text=hint))

    return all_contents


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent]:
    """调用工具"""
    try:
        executor = get_executor()
        args = dict(arguments or {})

        # ---- list_anima_models ----
        if name == "list_anima_models":
            model_type = str(args.get("model_type") or "").strip()
            if not model_type:
                return [TextContent(type="text", text="参数错误：model_type 不能为空")]
            result = await asyncio.to_thread(executor.list_models, model_type)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        # ---- list_anima_history ----
        if name == "list_anima_history":
            limit = int(args.get("limit") or 5)
            records = executor.history.list_recent(limit)
            if not records:
                return [TextContent(type="text", text="暂无生成历史。")]
            lines = [r.summary() for r in records]
            return [TextContent(type="text", text="\n".join(lines))]

        # ---- reroll_anima_image ----
        if name == "reroll_anima_image":
            source = str(args.pop("source", "")).strip()
            if not source:
                return [TextContent(type="text", text="参数错误：source 不能为空（使用 'last' 或历史 ID）")]

            record = executor.history.get(source)
            if record is None:
                return [TextContent(type="text", text=f"未找到历史记录：{source}。请先使用 list_anima_history 查看可用记录。")]

            # 深拷贝原始参数，用覆盖项更新
            from copy import deepcopy
            merged = deepcopy(record.params)
            overrides = {k: v for k, v in args.items() if v is not None}
            merged.update(overrides)

            # seed 默认行为：未显式指定则自动随机（删掉原 seed）
            if "seed" not in args or args.get("seed") is None:
                merged.pop("seed", None)

            return await _generate_with_repeat(executor, merged)

        # ---- generate_anima_image ----
        if name == "generate_anima_image":
            return await _generate_with_repeat(executor, args)

        return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def main():
    """启动 MCP Server（stdio 模式）"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
