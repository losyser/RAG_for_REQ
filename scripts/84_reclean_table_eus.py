"""
从 v1 备份恢复原始文本，用改进 prompt 重新清理 171 条表格噪声 EU。

改进点：新 prompt 明确要求
  - 每个表格行转换为独立工程陈述句，保留所有数值和单位
  - 不压缩成叙述摘要
  - 不能因"整理"而丢失任何数字、操作符、量纲

输出写回 evidence_units_v2.jsonl；
日志写入 data/search_results/exp_v4/kb_reclean_log.json（断点续跑）。
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT     = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

V1_JSONL = ROOT / "data/processed/evidence_units.jsonl"
V2_JSONL = ROOT / "data/processed/evidence_units_v2.jsonl"
LOG_FILE = ROOT / "data/search_results/exp_v4/kb_reclean_log.json"

_TABLE_PAT    = re.compile(r"(\s{3,}|\t){3,}")
_NUM_DENSE    = re.compile(r"(\d[\d\s./]{0,5}){5,}")
_TABLE_HEADER = re.compile(r"(bar\s+kgf|psi\s+[°C℃]|mm\s+in\.|TABLE\s+\d|Tier\s+Rule\s+Ref)", re.IGNORECASE)
_MULTI_NUM    = re.compile(r"(\d+\.?\d*\s+){4,}")

_RECLEAN_PROMPT = """\
你是船舶工程知识库整理专家。下面是一条证据单元的原始文本，来自船舶主机冷却水系统相关文档。
原文可能包含从 PDF 表格提取的数据，列标题和数据行混在一起。

整理规则（严格遵守）：
1. 如果原文包含表格数据，**必须将每一行数据转换为独立的工程陈述句**，格式：
   "[适用对象/类别]：[参数名] [运算符] [数值] [单位]；[参数名2] [运算符] [数值] [单位]。适用条件：[...]"
2. **保留原文中的所有数字、运算符（≤ ≥ < > =）和计量单位**，一个都不能丢
3. 同一列标题对应多个数值（如 bar 和 kgf/cm²）均保留，用斜杠或括号说明
4. 保留适用范围、条件分组（如 Group I/II、a/b/c 类）
5. 去除纯格式垃圾（重复空格、换行、页码、文档修订号）
6. 如果原文已经是干净的工程陈述，直接保留，不要改写
7. 如果原文有"可支撑"/"不能支撑"等已有标注，在整理后的数值内容之后另起段落保留
8. 若原文确实没有任何有效工程内容，仅输出：[NO_CONTENT]

原始文本：
{text}

整理后输出（仅输出整理结果，不加任何解释或前缀）：
"""


def load_v1_map() -> dict[str, str]:
    m: dict[str, str] = {}
    with open(V1_JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                eu = json.loads(line)
                m[eu["id"]] = eu.get("text", "")
    return m


def is_noisy(text: str) -> bool:
    return bool(
        _TABLE_PAT.search(text)
        or _NUM_DENSE.search(text[:200])
        or _TABLE_HEADER.search(text)
        or _MULTI_NUM.search(text)
    )


def load_v2() -> list[dict]:
    eus = []
    with open(V2_JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                eus.append(json.loads(line))
    return eus


def write_back(eus: list[dict]):
    with open(V2_JSONL, "w", encoding="utf-8") as f:
        for eu in eus:
            f.write(json.dumps(eu, ensure_ascii=False) + "\n")


def reclean(text: str, client, model: str) -> str:
    prompt = _RECLEAN_PROMPT.format(text=text[:2000])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1200,
    )
    return resp.choices[0].message.content.strip()


def main():
    from cooling_rag_mg.config import DeepSeekConfig
    cfg    = DeepSeekConfig()
    client = cfg.make_client()
    model  = cfg.model

    v1_map = load_v1_map()
    eus    = load_v2()
    eu_map = {eu["id"]: eu for eu in eus}

    # 171 条噪声EU（以v1原始文本为判定标准）
    noisy_ids = [eid for eid, text in v1_map.items() if is_noisy(text)]
    print(f"需重新清理: {len(noisy_ids)} 条")

    # 断点续跑
    log: dict[str, str] = {}
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    if log:
        print(f"已有 {len(log)} 条记录，跳过")

    changed = 0
    for i, eu_id in enumerate(noisy_ids):
        # 应用已有日志
        if eu_id in log:
            new_text = log[eu_id]
            if new_text == "[NO_CONTENT]":
                eu_map[eu_id]["text"] = ""
                if "search_text" in eu_map[eu_id]:
                    eu_map[eu_id]["search_text"] = ""
            else:
                eu_map[eu_id]["text"] = new_text
                if "search_text" in eu_map[eu_id]:
                    eu_map[eu_id]["search_text"] = new_text
            continue

        orig_text = v1_map.get(eu_id, "")
        tier = eu_map[eu_id].get("kb_tier", "?")
        src  = eu_map[eu_id].get("source_document", "?")[:50]
        print(f"[{i+1:03d}/{len(noisy_ids)}] {eu_id} ({tier}) {src}", end=" ... ", flush=True)

        try:
            new_text = reclean(orig_text, client, model)
        except Exception as exc:
            print(f"FAILED: {exc}")
            time.sleep(2)
            continue

        log[eu_id] = new_text

        if new_text == "[NO_CONTENT]":
            eu_map[eu_id]["text"] = ""
            if "search_text" in eu_map[eu_id]:
                eu_map[eu_id]["search_text"] = ""
            print("→ [NO_CONTENT]")
        else:
            eu_map[eu_id]["text"] = new_text
            if "search_text" in eu_map[eu_id]:
                eu_map[eu_id]["search_text"] = new_text
            print(f"→ {new_text[:80].replace(chr(10), ' ')}...")

        changed += 1

        if changed % 10 == 0:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            write_back(list(eu_map.values()))
            print(f"  [checkpoint: {changed} 条已写回]")

        time.sleep(0.3)

    # 最终写回
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    write_back(list(eu_map.values()))

    no_content = sum(1 for v in log.values() if v == "[NO_CONTENT]")
    print(f"\n完成！共处理 {len(log)} 条，其中 {no_content} 条标记为 NO_CONTENT")
    print(f"已写回: {V2_JSONL}")


if __name__ == "__main__":
    main()
