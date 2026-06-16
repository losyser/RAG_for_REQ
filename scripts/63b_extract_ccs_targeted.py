"""
Phase 1 (CCS专项): 从《钢质海船入级规范》2025 提取冷却水相关 L1 约束单元。

针对CCS文档结构的精准提取：
  第7篇 第2-3章 自动化系统 (P1909-1965): 冷却水报警整定值表格  ← 最高价值
  第3篇 第3章 管系 (P1426-1438): 管路布置/材料/泵要求
  第3篇 第9章 泵 (P1513-1535): 泵设计要求

输出: data/processed/ccs_l1_units.jsonl (L1约束单元)
      data/processed/ccs_l1_review.csv  (人工审核表)

用法:
  python scripts/63b_extract_ccs_targeted.py
  python scripts/63b_extract_ccs_targeted.py --sections alarms  # 只提取报警章节
  python scripts/63b_extract_ccs_targeted.py --dry-run          # 预览不写文件
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.json_utils import loads_lenient

DATA     = PROJECT_ROOT / "data" / "processed"
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "ccs_rules"
CCS_PDF  = RAW_DIR / "ccs_2025.pdf"
OUT_JSONL = DATA / "ccs_l1_units.jsonl"
OUT_CSV   = DATA / "ccs_l1_review.csv"

# CCS文档中冷却水相关的目标页面范围 (基于2025版目录分析)
TARGET_SECTIONS = {
    "alarms": {
        "desc": "第7篇 自动化系统 - 冷却水报警整定值",
        "pages": (1909, 1966),      # 第7篇第2-3章
        "primary_intent": "alarm_setpoint",
        "evidence_strength": "direct",
    },
    "piping": {
        "desc": "第3篇第3章 船舶管系 - 冷却水管系布置与材料",
        "pages": (1426, 1439),
        "primary_intent": "installation",
        "evidence_strength": "direct",
    },
    "pumps": {
        "desc": "第3篇第9章 泵 - 泵设计与试验要求",
        "pages": (1513, 1536),
        "primary_intent": "redundancy",
        "evidence_strength": "direct",
    },
    "fuel_cooling": {
        "desc": "第3篇第4章 燃油系统 第5节 - 冷却水系统",
        "pages": (1445, 1451),
        "primary_intent": "specification",
        "evidence_strength": "direct",
    },
}

# 冷却水相关过滤关键词（提高提取精度）
COOLING_KEYWORDS = [
    "冷却水", "cooling water", "冷却系统", "海水冷却", "淡水冷却",
    "冷却泵", "膨胀箱", "热交换器", "温控阀", "缸套水",
    "冷却水泵", "气缸冷却", "主机冷却", "HT冷却", "LT冷却",
    "冷却介质", "冷却液位", "冷却压力", "冷却温度",
]

# 强制性语言模式
MANDATORY_PATTERNS = [
    r'应[一-鿿]{1,3}(?:设|配|装|具|满|符)',
    r'不[得应](?:小|大|少|低|高|超)于',
    r'至少(?:应|须|需)',
    r'\b(?:shall|must|required|not less than|not exceed)\b',
    r'每台|每只|每舷|每缸',
]

SYSTEM_PROMPT = """\
你是船舶工程合规专家。从以下CCS《钢质海船入级规范》原文段落中，提取与主机冷却水系统相关的约束性条款。

对每个约束条款输出JSON单元，格式如下：
{
  "units": [
    {
      "title": "简短中文标题（15字内）",
      "clause_id": "条款编号（如3.3.3.1或7.2.1.5.b）",
      "constraint_type": "alarm|redundancy|material|pressure|temperature|flow|installation|inspection 之一",
      "primary_component": "cooling_water_pump|cooler|expansion_tank|pipe|valve|alarm_system|filter|cooling_system 之一",
      "primary_intent": "alarm_setpoint|redundancy|specification|installation|inspection|water_quality 之一",
      "core_requirement": "原文条款精简（中文，100字内，保留数值和条件）",
      "acceptance_criteria": "具体接受标准或数值（如有，否则null）",
      "applies_to": "所有船舶|柴油机船|特定条件（如适用限制）",
      "mandatory_level": "mandatory|recommended",
      "verification_method": "design_review|inspection|calculation|test 之一"
    }
  ]
}

只提取：
1. 与冷却水系统（主机冷却、海水冷却、淡水冷却、冷却水泵）直接相关的条款
2. 有约束力的要求（含"应/不得/至少/不少于"等）
3. 量化的报警整定值或参数限制

忽略：纯描述性内容、与冷却水无关的条款、仅适用于货船舱底水的条款
若段落无相关约束，输出 {"units": []}"""


def _is_cooling_relevant(text: str) -> bool:
    return any(kw in text for kw in COOLING_KEYWORDS)


def _has_mandatory_language(text: str) -> bool:
    for pat in MANDATORY_PATTERNS:
        if re.search(pat, text):
            return True
    return False


def _extract_text_from_pages(doc, start_page: int, end_page: int) -> list[dict]:
    """提取页面文本，按段落分组，过滤冷却水相关内容"""
    paragraphs = []
    current_section = ""

    for pn in range(start_page - 1, min(end_page - 1, doc.page_count)):
        page = doc[pn]
        text = page.get_text("text")
        if not text.strip():
            continue

        # 检测章节标题
        for line in text.split("\n"):
            line = line.strip()
            if re.match(r'^[\d\.]+\s+\S', line) and len(line) < 80:
                current_section = line

        # 按段落切分（双换行）
        for para in re.split(r'\n{2,}', text):
            para = para.strip()
            if len(para) < 40:
                continue
            if _is_cooling_relevant(para) or _has_mandatory_language(para):
                paragraphs.append({
                    "page": pn + 1,
                    "section": current_section,
                    "text": para[:1200],
                    "has_mandatory": _has_mandatory_language(para),
                    "has_cooling": _is_cooling_relevant(para),
                })

    return paragraphs


def _llm_extract_units(para: dict, section_name: str, client, model: str) -> list[dict]:
    """调用LLM从段落提取约束单元"""
    user_msg = (
        "来源: CCS《钢质海船入级规范》2025\n"
        "章节: %s\n"
        "第%d页 | 小节: %s\n\n"
        "原文:\n%s"
    ) % (section_name, para["page"], para.get("section", ""), para["text"])

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        obj = loads_lenient(raw) or {}
        return [u for u in obj.get("units", []) if isinstance(u, dict) and u.get("core_requirement")]
    except Exception as ex:
        print("  ⚠ LLM错误: %s" % str(ex)[:60])
        return []


def _make_unit(extracted: dict, source_name: str, page: int, counter: int,
               default_intent: str, default_strength: str) -> dict:
    """构建证据单元"""
    clause = extracted.get("clause_id", "p%d" % page)
    safe_clause = re.sub(r'[^\w\-.]', '', clause)[:20]
    uid = "L1-CCS2025-%s-%03d" % (safe_clause, counter)

    comp   = extracted.get("primary_component", "cooling_system")
    intent = extracted.get("primary_intent", default_intent)
    title  = extracted.get("title", "CCS规范要求")
    core   = extracted.get("core_requirement", "")
    accept = extracted.get("acceptance_criteria") or ""

    text_parts = [title]
    if clause and clause not in title:
        text_parts.append("条款 %s" % clause)
    text_parts.append(core)
    if accept:
        text_parts.append("接受标准: %s" % accept)
    text = "\n".join(p for p in text_parts if p)

    return {
        "id": uid,
        "parent_chunk_id": "CH-CCS2025-%s" % safe_clause,
        "text": text,
        "search_text": " ".join([title, comp, intent, core, extracted.get("applies_to",""), "CCS 入级规范 冷却水"]),
        "metadata": {
            "topic": title,
            "source_document": "CCS《钢质海船入级规范》2025",
            "source_type": "ship_rule",
            "source_link": "pbc.ccs.org.cn",
            "location": "P%d" % page,
            "section_title": extracted.get("clause_id", ""),
            "component_objects": [comp],
            "requirement_intents": [intent],
            "evidence_strength": extracted.get("evidence_strength", default_strength),
            "is_generalizable": True,
            "applicability_level": "general",
            "mandatory_level": extracted.get("mandatory_level", "mandatory"),
            "acceptance_criteria": accept,
            "applies_to": extracted.get("applies_to", ""),
            "verification_method": extracted.get("verification_method", "design_review"),
            "constraint_type": extracted.get("constraint_type", ""),
            "is_noise": False,
            "need_human_review": True,
        },
        "primary_component": comp,
        "primary_intent": intent,
        "kb_tier": 1,
        "tier_reason": "CCS入级规范 条款 %s" % clause,
        "_draft_status": "pending",
        "_draft_note": "",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", nargs="+", default=list(TARGET_SECTIONS.keys()),
                    choices=list(TARGET_SECTIONS.keys()), help="提取哪些章节")
    ap.add_argument("--dry-run", action="store_true", help="预览，不写文件")
    args = ap.parse_args()

    if not CCS_PDF.exists():
        print("❌ 未找到CCS PDF: %s" % CCS_PDF)
        print("请将 ccs_2025.pdf 放入: %s" % RAW_DIR)
        return

    try:
        import fitz
    except ImportError:
        print("请安装 pymupdf: pip install pymupdf")
        return

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    doc = fitz.open(str(CCS_PDF))
    print("CCS PDF: %d页" % doc.page_count)

    # 加载已有结果
    existing: list[dict] = []
    if OUT_JSONL.exists() and not args.dry_run:
        with open(OUT_JSONL, encoding="utf-8") as f:
            existing = [json.loads(l) for l in f]
        print("已有%d条草稿，继续追加..." % len(existing))

    all_units: list[dict] = list(existing)
    counter = len(existing)
    total_extracted = 0

    for sec_name in args.sections:
        sec = TARGET_SECTIONS[sec_name]
        start, end = sec["pages"]
        print("\n处理: %s (P%d-P%d)" % (sec["desc"], start, end))

        paras = _extract_text_from_pages(doc, start, end)
        # 优先处理：含冷却关键词且含强制语言的段落
        priority = [p for p in paras if p["has_cooling"] and p["has_mandatory"]]
        secondary = [p for p in paras if not (p["has_cooling"] and p["has_mandatory"])]
        ordered = priority + secondary
        print("  过滤后段落: %d个（高优先: %d, 其余: %d）" % (len(ordered), len(priority), len(secondary)))

        for i, para in enumerate(ordered, 1):
            extracted_list = _llm_extract_units(para, sec["desc"], client, model)
            for ex in extracted_list:
                counter += 1
                unit = _make_unit(ex, sec["desc"], para["page"], counter,
                                  sec["primary_intent"], sec["evidence_strength"])
                all_units.append(unit)
                total_extracted += 1
                print("  [%d/%d P%d] +%s (意图=%s)" % (
                    i, len(ordered), para["page"],
                    ex.get("title","?")[:40], ex.get("primary_intent","?")))

            if i % 10 == 0 and not args.dry_run:
                _flush(all_units, OUT_JSONL)
            time.sleep(0.08)

    if not args.dry_run:
        _flush(all_units, OUT_JSONL)
        _write_review_csv(all_units, OUT_CSV)

    print("\n=== CCS提取完成 ===")
    print("本次提取: %d 个L1约束单元" % total_extracted)
    print("总草稿数: %d 条" % len(all_units))
    if not args.dry_run:
        print("草稿文件: %s" % OUT_JSONL)
        print("审核表格: %s" % OUT_CSV)
        print("\n下一步:")
        print("  1. 检查 ccs_l1_review.csv，确认条款正确")
        print("  2. 将 _draft_status 改为 approved 后运行:")
        print("     python scripts/63c_append_ccs_units.py")


def _flush(units: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")


def _write_review_csv(units: list[dict], path: Path) -> None:
    fields = ["id", "kb_tier", "tier_reason", "primary_component", "primary_intent",
              "source_clause", "mandatory_level", "acceptance_criteria",
              "_draft_status", "_draft_note", "text_snippet"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for u in units:
            meta = u.get("metadata", {})
            row = {
                "id": u.get("id", ""),
                "kb_tier": u.get("kb_tier", 1),
                "tier_reason": u.get("tier_reason", ""),
                "primary_component": u.get("primary_component", ""),
                "primary_intent": u.get("primary_intent", ""),
                "source_clause": meta.get("section_title", ""),
                "mandatory_level": meta.get("mandatory_level", ""),
                "acceptance_criteria": meta.get("acceptance_criteria", ""),
                "_draft_status": u.get("_draft_status", "pending"),
                "_draft_note": u.get("_draft_note", ""),
                "text_snippet": u.get("text", "")[:250].replace("\n", " "),
            }
            w.writerow(row)


if __name__ == "__main__":
    main()
