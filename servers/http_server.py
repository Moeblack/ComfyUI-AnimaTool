"""
独立 FastAPI 服务（不启动 ComfyUI 时单独用）。

启动方式（在 ComfyUI-AnimaTool 目录下）：
    uvicorn servers.http_server:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

# 确保能 import 上层 executor
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from executor import AnimaExecutor, AnimaToolConfig


class GenerateRequest(BaseModel):
    # 允许任意字段（由 tool schema 约束；服务端只做最小校验）
    payload: Dict[str, Any] = Field(default_factory=dict)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def create_app() -> FastAPI:
    app = FastAPI(title="Anima Tool API", version="0.1.0")

    tool_root = Path(__file__).resolve().parent.parent
    knowledge_dir = tool_root / "knowledge"
    schema_path = tool_root / "schemas" / "tool_schema_universal.json"

    config = AnimaToolConfig()
    executor = AnimaExecutor(config=config)

    @app.get("/health")
    def health() -> Dict[str, Any]:
        # 不做真实连通性探测（避免阻塞），只返回配置
        return {"status": "ok", "comfyui_url": config.comfyui_url}

    @app.get("/schema")
    def schema() -> JSONResponse:
        if not schema_path.exists():
            raise HTTPException(status_code=404, detail="schema not found")
        obj = json.loads(schema_path.read_text(encoding="utf-8"))
        return JSONResponse(content=obj)

    @app.get("/knowledge")
    def knowledge() -> Dict[str, Any]:
        return {
            "anima_expert": _read_text(knowledge_dir / "anima_expert.md"),
            "artist_list": _read_text(knowledge_dir / "artist_list.md"),
            "prompt_examples": _read_text(knowledge_dir / "prompt_examples.md"),
        }

    @app.post("/generate")
    def generate(req: GenerateRequest) -> Dict[str, Any]:
        payload = req.payload or {}
        try:
            result = executor.generate(payload)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return result

    return app


app = create_app()
