"""
自动清理表格噪声 EU，结果写回 evidence_units_v2.jsonl。

优先处理被 v3 检索到的28条，再处理剩余143条。
[NO_CONTENT] 的条目 text 置空字符串（保留条目元数据，不物理删除）。
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows consoles (avoids GBK encoding errors)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EU_JSONL  = ROOT / "data/processed/evidence_units_v2.jsonl"
V3_RESULT = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
LOG_FILE  = ROOT / "data/search_results/exp_v4/kb_cleanup_log.json"

_TABLE_PAT = re.compile(r"(\s{3,}|\t){3,}")
_NUM_DENSE = re.compile(r"(\d[\d\s./]{0,5}){5,}")

_CLEAN_PROMPT = """\
你是船舶工程知识库整理专家。下面是一条证据单元的原始文本，来自船舶主机冷却水系统相关文档。
原文因 PDF 表格提取导致格式混乱，数字和列标题堆叠在一起，难以直接使用。

请将其整理为：
1. 以工程陈述句表达（保持原文语言，中英文均可）
2. 保留所有有意义的参数名称、数值、单位、适用条件和范围
3. 去除页码、文档编号序列、编辑日期等非内容信息
4. 去除无语义的重复空格、换行或字符
5. 如果原文含多个独立参数，每条单独成句，用换行分隔
6. 若原文确实没有任何有效工程内容（纯格式垃圾），仅输出：[NO_CONTENT]

原始文本：
{text}

整理后输出（仅输出整理结果，不加任何解释或前缀）：
"""


def load_eus() -> list[dict]:
    eus = []
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                eus.append(json.loads(line))
    return eus


def get_used_ids() -> set[str]:
    with open(V3_RESULT, encoding="utf-8") as f:
        v3 = json.load(f)
    used = set()
    for rs in v3["result_sets"]:
        for er in rs.get("engineering_requirements", []):
            used.update(er.get("evidence_ids", []))
    return used


def is_noisy(eu: dict) -> bool:
    text = eu.get("text", "")
    return bool(_TABLE_PAT.search(text) or _NUM_DENSE.search(text[:200]))


def clean_text(text: str, client, model: str) -> str:
    prompt = _CLEAN_PROMPT.format(text=text[:1500])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


def write_back(eus: list[dict]):
    with open(EU_JSONL, "w", encoding="utf-8") as f:
        for eu in eus:
            f.write(json.dumps(eu, ensure_ascii=False) + "\n")


def main():
    from cooling_rag_mg.config import DeepSeekConfig
    cfg    = DeepSeekConfig()
    client = cfg.make_client()
    model  = cfg.model

    eus      = load_eus()
    used_ids = get_used_ids()
    eu_map   = {eu["id"]: eu for eu in eus}

    noise = [eu for eu in eus if is_noisy(eu)]
    # 优先：被检索到的
    priority = [eu for eu in noise if eu["id"] in used_ids]
    rest     = [eu for eu in noise if eu["id"] not in used_ids]
    ordered  = priority + rest

    print(f"噪声EU总数: {len(ordered)}  (优先: {len(priority)}, 其余: {len(rest)})")

    # 加载已有日志（支持断点续跑）
    log: dict[str, str] = {}
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    already_done = len(log)
    if already_done:
        print(f"已有 {already_done} 条清理记录，跳过已处理条目")

    changed = 0
    for i, eu in enumerate(ordered):
        eu_id = eu["id"]
        tier  = eu.get("kb_tier", "?")
        src   = eu.get("source_document", "?")[:50]

        if eu_id in log:
            # 应用已有结果（断点续跑）
            new_text = log[eu_id]
            if new_text == "[NO_CONTENT]":
                eu_map[eu_id]["text"] = ""
                eu_map[eu_id]["search_text"] = ""
            else:
                eu_map[eu_id]["text"] = new_text
                if "search_text" in eu_map[eu_id]:
                    eu_map[eu_id]["search_text"] = new_text
            continue

        flag = "[!]" if eu_id in used_ids else "   "
        print(f"{flag} [{i+1:03d}/{len(ordered)}] {eu_id} ({tier}) {src}", end=" ... ", flush=True)

        try:
            new_text = clean_text(eu.get("text", ""), client, model)
        except Exception as exc:
            print(f"FAILED: {exc}")
            time.sleep(2)
            continue

        log[eu_id] = new_text

        if new_text == "[NO_CONTENT]":
            eu_map[eu_id]["text"] = ""
            eu_map[eu_id]["search_text"] = ""
            print("→ [NO_CONTENT]")
        else:
            eu_map[eu_id]["text"] = new_text
            if "search_text" in eu_map[eu_id]:
                eu_map[eu_id]["search_text"] = new_text
            preview = new_text[:60].replace("\n", " ")
            print(f"→ {preview}...")

        changed += 1

        # 每10条保存一次日志和JSONL（防止中途崩溃丢失）
        if changed % 10 == 0:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            write_back(list(eu_map.values()))
            print(f"  [checkpoint: {changed} 条已写回]")

        time.sleep(0.3)  # 避免API限速

    # 最终写回
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    write_back(list(eu_map.values()))

    no_content = sum(1 for v in log.values() if v == "[NO_CONTENT]")
    print(f"\n完成！共处理 {len(log)} 条，其中 {no_content} 条标记为 NO_CONTENT")
    print(f"日志: {LOG_FILE}")
    print(f"已写回: {EU_JSONL}")


if __name__ == "__main__":
    main()
