"""
命令行工具。

用法（在 ComfyUI-AnimaTool 目录下）：
    python -m servers.cli --json-file example.json
    python -m servers.cli --json '{"aspect_ratio":"9:16", ...}'
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# 确保能 import 上层 executor
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from executor import AnimaExecutor, AnimaToolConfig


def _load_json_arg(s: str) -> Dict[str, Any]:
    try:
        obj = json.loads(s)
    except Exception as e:
        raise SystemExit(f"--json 解析失败：{e}") from e
    if not isinstance(obj, dict):
        raise SystemExit("--json 必须是一个 JSON object")
    return obj


def _load_json_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"找不到文件：{p}")
    obj = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise SystemExit("--json-file 内容必须是一个 JSON object")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description="Anima Tool CLI (ComfyUI)")
    parser.add_argument("--comfyui-url", default="http://127.0.0.1:8188", help="ComfyUI 地址")
    parser.add_argument("--json", default=None, help="直接传入 JSON object 字符串")
    parser.add_argument("--json-file", default=None, help="从文件读取 JSON object")
    args = parser.parse_args()

    if not args.json and not args.json_file:
        raise SystemExit("必须提供 --json 或 --json-file")
    if args.json and args.json_file:
        raise SystemExit("只能二选一：--json 或 --json-file")

    payload = _load_json_arg(args.json) if args.json else _load_json_file(args.json_file)

    cfg = AnimaToolConfig(comfyui_url=str(args.comfyui_url))
    ex = AnimaExecutor(config=cfg)
    result = ex.generate(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
