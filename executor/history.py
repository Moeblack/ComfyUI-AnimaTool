"""
生成历史管理器。

- 内存：deque(maxlen=N) 保持最近 N 条
- 文件：JSONL 追加写入，启动时加载最近 N 条到内存
"""
from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GenerationRecord:
    """单次生成的历史记录"""

    id: int                          # 自增 ID
    timestamp: str                   # ISO 格式时间戳
    params: Dict[str, Any]           # 完整生成参数（generate_anima_image 的入参）
    positive_text: str = ""          # 实际拼接后的正面提示词
    negative_text: str = ""          # 负面提示词
    prompt_id: Optional[str] = None  # ComfyUI 返回的 prompt_id
    seed: Optional[int] = None       # 实际使用的种子
    width: Optional[int] = None
    height: Optional[int] = None

    # -- 序列化 --

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GenerationRecord":
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid_keys})

    # -- 摘要 --

    def summary(self) -> str:
        """生成供 AI 阅读的单行摘要"""
        artist = self.params.get("artist", "?")
        tags = self.params.get("tags", "")
        if len(tags) > 60:
            tags = tags[:57] + "..."
        count = self.params.get("count", "")
        size = f"{self.width}x{self.height}" if self.width and self.height else "?"
        return f"#{self.id} [{self.timestamp[:19]}] {artist} | {count}, {tags} | seed:{self.seed} | {size}"


class HistoryManager:
    """线程安全的生成历史管理器（内存 + JSONL 持久化）"""

    def __init__(self, history_file: Optional[Path] = None, maxlen: int = 50):
        self._maxlen = maxlen
        self._lock = threading.Lock()
        self._records: deque[GenerationRecord] = deque(maxlen=maxlen)
        self._next_id = 1

        if history_file is None:
            history_file = Path(__file__).resolve().parent.parent / "outputs" / "history.jsonl"
        self._history_file = history_file

        self._load_from_file()

    # -- 持久化 --

    def _load_from_file(self) -> None:
        """启动时从 JSONL 文件加载历史"""
        if not self._history_file.exists():
            return
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            all_records: List[GenerationRecord] = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    all_records.append(GenerationRecord.from_dict(json.loads(line)))
                except Exception:
                    continue

            for r in all_records[-self._maxlen :]:
                self._records.append(r)

            # 扫描所有记录以确保 next_id 是全局最大的
            max_id = 0
            for r in all_records:
                if r.id > max_id:
                    max_id = r.id
            
            self._next_id = max_id + 1
        except Exception:
            pass  # 文件损坏时静默跳过

    def _append_to_file(self, record: GenerationRecord) -> None:
        """追加一条记录到 JSONL 文件"""
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with self._history_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass  # 写入失败不影响主流程

    # -- 公开 API --

    def add(
        self,
        params: Dict[str, Any],
        positive_text: str = "",
        negative_text: str = "",
        prompt_id: Optional[str] = None,
        seed: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> GenerationRecord:
        """记录一次生成"""
        with self._lock:
            record = GenerationRecord(
                id=self._next_id,
                timestamp=datetime.now().isoformat(),
                params=params,
                positive_text=positive_text,
                negative_text=negative_text,
                prompt_id=prompt_id,
                seed=seed,
                width=width,
                height=height,
            )
            self._next_id += 1
            self._records.append(record)
            self._append_to_file(record)
            return record

    def get(self, source: str) -> Optional[GenerationRecord]:
        """
        获取历史记录。
        - "last"：最后一条
        - 数字 / "#数字"：按 ID 查找
        """
        target_id = None
        with self._lock:
            if not self._records:
                return None

            s = str(source).strip().lstrip("#")

            if s.lower() == "last":
                return self._records[-1]

            try:
                target_id = int(s)
            except ValueError:
                return None

            for r in self._records:
                if r.id == target_id:
                    return r

        # 内存找不到，尝试回退到文件搜索 (在锁外进行，避免长时间持有锁)
        if target_id is not None:
            return self._search_in_file(target_id)
            
        return None

    def _search_in_file(self, target_id: int) -> Optional[GenerationRecord]:
        """在历史文件中搜索指定 ID 的记录"""
        if not self._history_file.exists():
            return None
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            for line in reversed(lines):  # 从新到旧搜索
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("id") == target_id:
                        return GenerationRecord.from_dict(data)
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def list_recent(self, limit: int = 5) -> List[GenerationRecord]:
        """返回最近 N 条记录（从新到旧）"""
        with self._lock:
            items = list(self._records)
            items.reverse()
            return items[:max(1, limit)]
