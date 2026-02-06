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

from copy import deepcopy

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from executor import AnimaExecutor, AnimaToolConfig


class GenerateRequest(BaseModel):
    # 允许任意字段（由 tool schema 约束；服务端只做最小校验）
    payload: Dict[str, Any] = Field(default_factory=dict)


class RerollRequest(BaseModel):
    source: str = Field(..., description="历史记录引用：'last' 或历史 ID")
    overrides: Dict[str, Any] = Field(default_factory=dict, description="覆盖参数")


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

    def _generate_with_repeat(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
        """执行生成（支持 repeat 多次独立 queue 提交），返回结果列表。"""
        repeat = max(1, int(payload.pop("repeat", 1) or 1))
        results = []
        for _ in range(repeat):
            run_params = deepcopy(payload)
            if "seed" not in payload or payload.get("seed") is None:
                run_params.pop("seed", None)
            results.append(executor.generate(run_params))
        return results

    @app.post("/generate")
    def generate(req: GenerateRequest) -> Dict[str, Any]:
        payload = req.payload or {}
        try:
            results = _generate_with_repeat(payload)
            # 单次兼容旧接口，多次返回数组
            if len(results) == 1:
                return results[0]
            return {"success": True, "results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/history")
    def history(limit: int = Query(default=5, ge=1, le=50)) -> Dict[str, Any]:
        records = executor.history.list_recent(limit)
        return {
            "count": len(records),
            "records": [r.to_dict() for r in records],
        }

    @app.post("/reroll")
    def reroll(req: RerollRequest) -> Dict[str, Any]:
        record = executor.history.get(req.source)
        if record is None:
            raise HTTPException(status_code=404, detail=f"未找到历史记录：{req.source}")

        merged = deepcopy(record.params)
        overrides = {k: v for k, v in (req.overrides or {}).items() if v is not None}
        merged.update(overrides)

        # seed 默认行为：未显式指定则自动随机
        if "seed" not in req.overrides or req.overrides.get("seed") is None:
            merged.pop("seed", None)

        try:
            results = _generate_with_repeat(merged)
            if len(results) == 1:
                return results[0]
            return {"success": True, "results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    return app


app = create_app()
