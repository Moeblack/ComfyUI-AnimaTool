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
            "description": "可选：人类可读的简短需求摘要，仅用于日志回显。"
        },
        "aspect_ratio": {
            "type": "string",
            "description": "可选：长宽比，如 '16:9'、'9:16'、'1:1'。默认 1:1。",
            "enum": ["21:9", "2:1", "16:9", "16:10", "5:3", "3:2", "4:3", "1:1", "3:4", "2:3", "3:5", "10:16", "9:16", "1:2", "9:21"]
        },
        "width": {"type": "integer", "description": "可选：宽度（像素），须为16倍数。若指定则覆盖 aspect_ratio。"},
        "height": {"type": "integer", "description": "可选：高度（像素），须为16倍数。若指定则覆盖 aspect_ratio。"},
        "quality_meta_year_safe": {
            "type": "string",
            "description": "必选：质量/年份/安全标签。必须包含 safe/sensitive/nsfw/explicit 之一。示例: 'masterpiece, best quality, year 2024, safe'"
        },
        "count": {
            "type": "string",
            "description": "必选：人数标签，如 '1girl'、'2girls'、'1boy'。"
        },
        "character": {"type": "string", "description": "可选：角色名（可含作品名括号），如 'hatsune miku' 或 'yunli (honkai star rail)'。"},
        "series": {"type": "string", "description": "可选：作品/系列名，如 'vocaloid'。"},
        "appearance": {"type": "string", "description": "可选：角色固定外观描述（发色、眼睛、身材等，不含服装）。"},
        "artist": {
            "type": "string",
            "description": "必选：画师标签，必须以 @ 开头（如 @fkey）。多画师逗号分隔。若用户没指定画师，请根据风格推荐一位。"
        },
        "style": {"type": "string", "description": "可选：画风倾向或特定渲染风格。"},
        "tags": {
            "type": "string",
            "description": "必选：核心 Danbooru 标签（逗号分隔）。建议包含动作、构图、服装、表情等。"
        },
        "nltags": {"type": "string", "description": "可选：自然语言补充（仅在 tag 难以描述时使用）。"},
        "environment": {"type": "string", "description": "可选：环境与背景光影描述。"},
        "neg": {
            "type": "string",
            "description": "必选：负面提示词。默认已包含通用反咒。建议加入与安全标签相反的约束。",
            "default": "worst quality, low quality, score_1, score_2, score_3, blurry, bad hands, bad anatomy, text, watermark"
        },
        "steps": {"type": "integer", "description": "可选：步数，默认 25。", "default": 25},
        "cfg": {"type": "number", "description": "可选：CFG，默认 4.5。", "default": 4.5},
        "sampler_name": {"type": "string", "description": "可选：采样器，默认 er_sde。", "default": "er_sde"},
        "seed": {"type": "integer", "description": "可选：随机种子。不填则每次生成都随机。"},
        "repeat": {
            "type": "integer",
            "description": "可选：独立任务重复次数。每次都会有不同随机种子。默认 1。",
            "default": 1, "minimum": 1, "maximum": 16,
        },
        "batch_size": {
            "type": "integer",
            "description": "可选：单任务内的 batch size。默认 1。",
            "default": 1, "minimum": 1, "maximum": 4,
        },
        "loras": {
            "type": "array",
            "description": "可选：LoRA 列表。name 须匹配 list_anima_models(model_type=loras) 返回值。",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "LoRA 文件名（含子目录）"},
                    "weight": {"type": "number", "default": 1.0}
                },
                "required": ["name"]
            }
        },
        "unet_name": {
            "type": "string",
            "description": "高级：UNET 模型文件名，默认 Anima。用 list_anima_models(model_type=diffusion_models) 查询可用模型。",
        },
        "clip_name": {
            "type": "string",
            "description": "高级：文本编码器文件名，默认 Qwen3。用 list_anima_models(model_type=text_encoders) 查询。",
        },
        "vae_name": {
            "type": "string",
            "description": "高级：VAE 文件名，默认 Anima VAE。用 list_anima_models(model_type=vae) 查询。",
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
            "description": "模型类型。loras 仅返回有 .json sidecar 元数据的 LoRA。",
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


# reroll schema：source 必填 + generate 的所有参数可作为【可选覆盖项】
# 关键：需要把原 generate 中"必选"的描述改为"可选覆盖"，否则 AI 会自动填入
def _build_reroll_override_props() -> dict:
    """复制 generate schema 的属性，但将描述中的'必选'改为'可选覆盖'。"""
    import copy
    props = copy.deepcopy(TOOL_SCHEMA["properties"])
    for _k, _v in props.items():
        desc = _v.get("description", "")
        if desc.startswith("必选："):
            _v["description"] = "可选覆盖（不提供则沿用历史记录）：" + desc[3:]
    return props


_REROLL_OVERRIDE_PROPS = _build_reroll_override_props()
REROLL_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {
            "type": "string",
            "description": "必选：要 reroll 的基础记录。'last' 表示最近一条，或使用历史 ID（如 '12'）。",
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
                "基于历史记录【覆盖】重新生成。source 以外的所有参数均为【可选覆盖项】。"
                "如果不提供覆盖参数，则完全沿用历史记录（seed 默认除外）。"
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
