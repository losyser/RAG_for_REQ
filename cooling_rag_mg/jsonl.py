from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    records: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p} 第 {line_no} 行不是合法 JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{p} 第 {line_no} 行不是 JSON 对象")
            records.append(obj)
    return records
