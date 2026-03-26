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
from executor import QwenExecutor


# 创建 MCP Server
server = Server("anima-tool")

# 全局 executor（懒加载）
_executor: AnimaExecutor | None = None


def get_executor() -> AnimaExecutor:
    global _executor
    if _executor is None:
        _executor = AnimaExecutor(config=AnimaToolConfig())
    return _executor

_qwen_executor: QwenExecutor | None = None

def get_qwen_executor() -> QwenExecutor:
    global _qwen_executor
    if _qwen_executor is None:
        _qwen_executor = QwenExecutor(config=AnimaToolConfig())
    return _qwen_executor

QWEN_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "edit_actions": {
            "type": "array",
            "description": "局部修改指令数组。文生图时留空",
            "items": {"type": "string"}
        },
        "character_and_action": {
            "type": "string",
            "description": "角色与动作描述"
        },
        "appearance_details": {
            "type": "string",
            "description": "外貌与服装细节"
        },
        "environment_and_lighting": {
            "type": "string",
            "description": "背景环境与光影"
        },
        "style_and_quality": {
            "type": "string",
            "description": "画质词与画风"
        },
        "preserve_constraints": {
            "type": "string",
            "description": "防崩坏约束，修图时建议填写"
        },
        "render_text": {
            "type": "string",
            "description": "画面中生成的文字"
        },
        "base_image": {
            "type": "string",
            "description": "底图绝对路径，传入后切换为图生图模式，映射为 Picture 1"
        },
        "reference_images": {
            "type": "array",
            "description": "参考图绝对路径数组（最多2张），映射为 Picture 2/3",
            "items": {"type": "string"}
        },
        "aspect_ratio": {
            "type": "string",
            "description": "仅文生图或扩图时使用，有 base_image 时跟随原图"
        },
        "seed": {"type": "integer"},
        "repeat": {
            "type": "integer",
            "description": "重复生成次数，默认 1",
            "default": 1, "minimum": 1, "maximum": 16,
        },
    },
    "required": []
}


# Tool Schema（从 tool_schema_universal.json 简化）
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt_hint": {
            "type": "string",
            "description": "日志回显用摘要"
        },
        "aspect_ratio": {
            "type": "string",
            "description": "长宽比，默认 1:1",
            "enum": ["21:9", "2:1", "16:9", "16:10", "5:3", "3:2", "4:3", "1:1", "3:4", "2:3", "3:5", "10:16", "9:16", "1:2", "9:21"]
        },
        "width": {"type": "integer", "description": "宽度，须为16倍数"},
        "height": {"type": "integer", "description": "高度，须为16倍数"},
        "quality_meta_year_safe": {
            "type": "string",
            "description": "质量/年份/安全标签，须含 safe/sensitive/nsfw/explicit 之一"
        },
        "count": {
            "type": "string",
            "description": "人数标签，如 '1girl'"
        },
        "character": {"type": "string", "description": "角色名"},
        "series": {"type": "string", "description": "作品/系列名"},
        "appearance": {"type": "string", "description": "角色外观描述"},
        "artist": {
            "type": "string",
            "description": "画师标签，@ 开头，如 @fkey。多画师逗号分隔"
        },
        "style": {"type": "string", "description": "画风倾向"},
        "tags": {
            "type": "string",
            "description": "Danbooru 标签，逗号分隔"
        },
        "nltags": {"type": "string", "description": "自然语言补充"},
        "environment": {"type": "string", "description": "环境与背景光影描述"},
        "neg": {
            "type": "string",
            "description": "负面提示词",
            "default": "worst quality, low quality, score_1, score_2, score_3, blurry, bad hands, bad anatomy, text, watermark"
        },
        "steps": {"type": "integer", "description": "步数，默认 25", "default": 25},
        "cfg": {"type": "number", "description": "CFG，默认 4.5", "default": 4.5},
        "sampler_name": {"type": "string", "description": "采样器，默认 er_sde", "default": "er_sde"},
        "seed": {"type": "integer", "description": "随机种子"},
        "repeat": {
            "type": "integer",
            "description": "独立重复次数，默认 1",
            "default": 1, "minimum": 1, "maximum": 16,
        },
        "batch_size": {
            "type": "integer",
            "description": "单任务 batch size，默认 1",
            "default": 1, "minimum": 1, "maximum": 4,
        },
        "loras": {
            "type": "array",
            "description": "LoRA 列表",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "LoRA 文件名"},
                    "weight": {"type": "number", "default": 1.0}
                },
                "required": ["name"]
            }
        },
        "unet_name": {
            "type": "string",
            "description": "UNET 模型文件名，默认 Anima",
        },
        "clip_name": {
            "type": "string",
            "description": "文本编码器文件名，默认 Qwen3",
        },
        "vae_name": {
            "type": "string",
            "description": "VAE 文件名，默认 Anima VAE",
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
            "description": "模型类型。loras 仅返回有 .json sidecar 的",
        }
    },
    "required": ["model_type"],
}


LIST_HISTORY_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "返回最近记录数，默认 5",
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
        if "必选：" in desc:
            _v["description"] = desc.replace("必选：", "可选覆盖：")
    return props


_REROLL_OVERRIDE_PROPS = _build_reroll_override_props()
REROLL_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {
            "type": "string",
            "description": "基础记录。'last' 或历史 ID",
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
            description="Anima 二次元图片生成。画师 @ 开头，须含安全标签。支持 repeat/batch_size 多张生成。",
            inputSchema=TOOL_SCHEMA,
        ),
        Tool(
            name="list_anima_models",
            description="查询可用模型文件（loras/diffusion_models/vae/text_encoders）。loras 仅返回有 .json sidecar 的。",
            inputSchema=LIST_MODELS_SCHEMA,
        ),
        Tool(
            name="list_anima_history",
            description="查看最近生成历史，返回 ID/时间/画师/标签/种子摘要。",
            inputSchema=LIST_HISTORY_SCHEMA,
        ),
        Tool(
            name="reroll_anima_image",
            description="基于历史记录覆盖重生成。source 外均为可选覆盖项，seed 默认随机。",
            inputSchema=REROLL_SCHEMA,
        ),
        Tool(
            name="generate_qwen_image",
            description="QwenEdit 自然语言图片生成/编辑。base_image 映射 Picture 1，reference_images 映射 Picture 2/3。纯生图填 character/appearance/environment；局部修图用 edit_actions + preserve_constraints。",
            inputSchema=QWEN_TOOL_SCHEMA,
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
            saved_path = img.get("saved_path") or img.get("file_path")
            if saved_path:
                all_contents.append(TextContent(type="text", text=f"图片已保存到本地：{saved_path}"))

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


async def _generate_qwen_with_repeat(
    executor: "QwenExecutor",
    prompt_json: Dict[str, Any],
) -> list[TextContent | ImageContent]:
    from copy import deepcopy

    repeat = max(1, int(prompt_json.pop("repeat", 1) or 1))

    all_contents: list[TextContent | ImageContent] = []
    history_ids: list[int] = []

    for i in range(repeat):
        run_params = deepcopy(prompt_json)
        if "seed" not in prompt_json or prompt_json.get("seed") is None:
            run_params.pop("seed", None)

        result = await asyncio.to_thread(executor.generate, run_params)

        if not result.get("success"):
            all_contents.append(TextContent(type="text", text=f"第 {i+1}/{repeat} 次 Qwen 生成失败: {result}"))
            continue

        if result.get("history_id"):
            history_ids.append(result["history_id"])

        instruction_sent = result.get("instruction_sent", "")
        all_contents.append(TextContent(type="text", text=f"**Qwen 最终指令 ({result.get('width', 0)}x{result.get('height', 0)})**：\n> {instruction_sent}"))

        for img in result.get("images", []):
            saved_path = img.get("saved_path") or img.get("file_path")
            if saved_path:
                all_contents.append(TextContent(type="text", text=f"图片已保存到本地：{saved_path}"))

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

    if history_ids:
        ids_str = ", ".join(f"#{hid}" for hid in history_ids)
        hint = f"已保存为 Qwen 历史记录 {ids_str}。"
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
            executor = get_executor()
            limit = int(args.get("limit") or 5)
            records = executor.history.list_recent(limit)
            if not records:
                return [TextContent(type="text", text="暂无生成历史。")]
            lines = [r.summary() for r in records]
            return [TextContent(type="text", text="\n".join(lines))]

        # ---- reroll_anima_image ----
        if name == "reroll_anima_image":
            executor = get_executor()
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
            executor = get_executor()
            return await _generate_with_repeat(executor, args)

        # ---- generate_qwen_image ----
        if name == "generate_qwen_image":
            qwen_executor = get_qwen_executor()
            return await _generate_qwen_with_repeat(qwen_executor, args)

        return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def main():
    """启动 MCP Server（stdio 模式）"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
