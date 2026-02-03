"""
ComfyUI-AnimaTool：随 ComfyUI 启动的 Anima Tool Use API

路由：
  POST /anima/generate   - 执行生成（接收结构化 JSON）
  GET  /anima/schema     - 返回 Tool Schema
  GET  /anima/knowledge  - 返回专家知识
  GET  /anima/health     - 健康检查
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from aiohttp import web

from .executor import AnimaExecutor, AnimaToolConfig


# ComfyUI 的 PromptServer（延迟导入，避免 import 顺序问题）
def _get_prompt_server():
    try:
        from server import PromptServer
        return PromptServer.instance
    except Exception:
        return None


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


_TOOL_ROOT = Path(__file__).resolve().parent


def _setup_routes():
    server = _get_prompt_server()
    if server is None:
        print("[ComfyUI-AnimaTool] PromptServer not available, skip route registration.")
        return

    routes = server.routes

    # 配置 & 执行器
    config = AnimaToolConfig()
    executor = AnimaExecutor(config=config)

    knowledge_dir = _TOOL_ROOT / "knowledge"
    schema_path = _TOOL_ROOT / "schemas" / "tool_schema_universal.json"

    # -------------------------
    # GET /anima/health
    # -------------------------
    @routes.get("/anima/health")
    async def anima_health(request):
        return web.json_response({
            "status": "ok",
            "comfyui_url": config.comfyui_url,
            "tool_root": str(_TOOL_ROOT),
        })

    # -------------------------
    # GET /anima/schema
    # -------------------------
    @routes.get("/anima/schema")
    async def anima_schema(request):
        if not schema_path.exists():
            return web.json_response({"error": "schema not found"}, status=404)
        obj = json.loads(schema_path.read_text(encoding="utf-8"))
        return web.json_response(obj)

    # -------------------------
    # GET /anima/knowledge
    # -------------------------
    @routes.get("/anima/knowledge")
    async def anima_knowledge(request):
        return web.json_response({
            "anima_expert": _read_text(knowledge_dir / "anima_expert.md"),
            "artist_list": _read_text(knowledge_dir / "artist_list.md"),
            "prompt_examples": _read_text(knowledge_dir / "prompt_examples.md"),
        })

    # -------------------------
    # POST /anima/generate
    # -------------------------
    @routes.post("/anima/generate")
    async def anima_generate(request):
        try:
            body = await request.json()
        except Exception as e:
            return web.json_response({"error": f"JSON parse error: {e}"}, status=400)

        # 兼容两种格式：直接传 JSON，或 {"payload": {...}}
        if "payload" in body and isinstance(body["payload"], dict):
            payload = body["payload"]
        else:
            payload = body

        try:
            # 在线程池中执行同步阻塞操作，避免阻塞 aiohttp 事件循环
            result = await asyncio.to_thread(executor.generate, payload)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

        return web.json_response(result)

    print("[ComfyUI-AnimaTool] Routes registered: /anima/health, /anima/schema, /anima/knowledge, /anima/generate")


# ComfyUI 加载 custom_nodes 时会 import 这个模块
# 我们在模块加载时注册路由
_setup_routes()

# ComfyUI 要求导出 NODE_CLASS_MAPPINGS（即使为空也要有）
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
