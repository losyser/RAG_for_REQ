"""
Phase 1: 从 CCS/DNV/IACS 规范 PDF 提取 L1 监管层约束单元。

每个编号条款 → 一个结构化证据单元（L1，kb_tier=1）：
  - unit_id: 来源文档编号（如 CCS-M3-5.3.2.1）
  - 强制级别: 强制/推荐/指导
  - 约束类型: redundancy/temperature/pressure/flow/alarm等
  - 核心要求: 原文或精简翻译
  - 可接受标准: 具体指标（如有）
  - 验证方式: design_review/inspection/test

前置条件:
  1. 将 CCS/DNV PDF 放入 data/raw/ccs_rules/ 目录
     推荐文件:
       CCS《海船入级规范》第4册（机电设备）→ volume4_mechanical.pdf
       IACS UR M28 (Internal Combustion Engines) → iacs_ur_m28.pdf
       IACS UR M47 (Monitoring & Automation) → iacs_ur_m47.pdf
  2. 安装 PDF 解析库: pip install pdfplumber 或 pymupdf

用法:
  python scripts/63_extract_ccs_units.py                    # 处理所有PDF
  python scripts/63_extract_ccs_units.py --file volume4.pdf # 处理单个文件
  python scripts/63_extract_ccs_units.py --dry-run 10       # 预览前10个段落

输出:
  data/processed/ccs_draft_units.jsonl  ← L1草稿（需人工审核）
  data/processed/ccs_draft_review.csv  ← 人工审核表格
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

DATA      = PROJECT_ROOT / "data" / "processed"
RAW_DIR   = PROJECT_ROOT / "data" / "raw" / "ccs_rules"
OUT_JSONL = DATA / "ccs_draft_units.jsonl"
OUT_CSV   = DATA / "ccs_draft_review.csv"

# 冷却水系统相关关键词过滤：只提取相关章节
RELEVANT_KEYWORDS = [
    "cooling", "冷却", "pump", "泵", "heat exchanger", "热交换器",
    "thermostat", "温控", "temperature", "温度", "pressure", "压力",
    "flow", "流量", "coolant", "冷却液", "jacket water", "缸套水",
    "fresh water", "淡水", "sea water", "海水", "expansion tank", "膨胀水箱",
    "alarm", "报警", "redundan", "冗余", "备用", "standby",
]

# 强制性条文识别模式
MANDATORY_PATTERNS = [
    r'\bshall\b', r'\bmust\b', r'\bshall not\b', r'\brequired\b',
    r'应不少于', r'不得低于', r'不得超过', r'应设置', r'应配备',
    r'应具备', r'不允许', r'必须', r'严禁',
]

SYSTEM_PROMPT = """\
你是船舶工程规范解析专家。从规范条文中提取结构化约束单元，供RAG知识库使用。

对于给定的规范段落，识别其中的工程约束，输出JSON格式：
{
  "units": [
    {
      "title": "简短标题（15字内，中文）",
      "constraint_type": "redundancy|temperature|pressure|flow|alarm|material|inspection|calculation之一",
      "primary_component": "cooling_water_pump|cooler|expansion_tank|pipe|valve|alarm_system|filter|cooling_system之一",
      "primary_intent": "redundancy|alarm_setpoint|specification|installation|inspection|water_quality之一",
      "mandatory_level": "mandatory|recommended|guidance",
      "core_requirement": "核心要求原文或精简翻译（中英均可，100字内）",
      "acceptance_criteria": "具体接受标准/数值（如有，否则写null）",
      "verification_method": "design_review|inspection|calculation|test之一",
      "evidence_strength": "direct",
      "source_clause": "条款编号（如 5.3.2.1 或 Article 47.2）"
    }
  ]
}

若段落不包含冷却水系统的工程约束，输出 {"units": []}。
只提取有实际约束力的条款，不提取纯描述性或解释性内容。"""


def _is_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in RELEVANT_KEYWORDS)


def _has_mandatory_language(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in MANDATORY_PATTERNS)


def _extract_pdf_paragraphs(pdf_path: Path) -> list[dict]:
    """从PDF提取段落，返回 [{page, text, section}]"""
    try:
        import pdfplumber
        paras = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            current_section = ""
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                # 按双换行分段
                for para in text.split("\n\n"):
                    para = para.strip()
                    if not para or len(para) < 30:
                        continue
                    # 检测章节标题
                    if re.match(r'^[\d\.]+\s+\w', para) and len(para) < 100:
                        current_section = para[:80]
                    if _is_relevant(para):
                        paras.append({
                            "page": page_num,
                            "section": current_section,
                            "text": para[:1000],
                        })
        return paras
    except ImportError:
        try:
            import fitz  # pymupdf
            paras = []
            doc = fitz.open(str(pdf_path))
            for page_num, page in enumerate(doc, 1):
                text = page.get_text("text")
                for para in text.split("\n\n"):
                    para = para.strip()
                    if not para or len(para) < 30:
                        continue
                    if _is_relevant(para):
                        paras.append({
                            "page": page_num,
                            "section": "",
                            "text": para[:1000],
                        })
            return paras
        except ImportError:
            print("⚠ 需要安装 pdfplumber 或 pymupdf:")
            print("  pip install pdfplumber")
            print("  或: pip install pymupdf")
            return []


def _llm_extract(para: dict, source_doc: str, client, model: str) -> list[dict]:
    """调用LLM从段落提取约束单元"""
    user_msg = (
        f"规范文档: {source_doc}\n"
        f"章节: {para.get('section', '')}\n"
        f"第{para['page']}页段落:\n{para['text']}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        obj = loads_lenient(raw) or {}
        return obj.get("units", [])
    except Exception as ex:
        print(f"  ⚠ LLM error: {ex}")
        return []


def _make_unit(extracted: dict, source_doc: str, source_file: str, page: int, counter: int) -> dict:
    """将提取结果转换为 evidence_unit 格式"""
    clause = extracted.get("source_clause", f"p{page}")
    safe_clause = re.sub(r'[^\w\-.]', '', clause)[:20]
    src_short = re.sub(r'[^\w]', '', Path(source_file).stem.upper())[:12]
    uid = f"L1-{src_short}-{safe_clause}-{counter:03d}"

    comp  = extracted.get("primary_component", "cooling_system")
    intent = extracted.get("primary_intent", "specification")
    title  = extracted.get("title", "规范要求")

    core_req = extracted.get("core_requirement", "")
    accept   = extracted.get("acceptance_criteria") or ""
    text_parts = [title, core_req]
    if accept:
        text_parts.append(f"Acceptance: {accept}")
    text = "\n".join(p for p in text_parts if p)

    search_parts = [title, comp, intent, core_req]
    search_text = " ".join(p for p in search_parts if p)

    return {
        "id": uid,
        "parent_chunk_id": f"CH-{src_short}-{safe_clause}",
        "text": text,
        "search_text": search_text,
        "metadata": {
            "topic": title,
            "source_document": source_doc,
            "source_type": "ship_rule",
            "source_link": "",
            "location": f"p{page}",
            "section_title": extracted.get("source_clause", ""),
            "component_objects": [comp],
            "requirement_intents": [intent],
            "evidence_strength": "direct",
            "is_generalizable": True,
            "applicability_level": "general",
            "mandatory_level": extracted.get("mandatory_level", "mandatory"),
            "acceptance_criteria": accept,
            "verification_method": extracted.get("verification_method", "design_review"),
            "constraint_type": extracted.get("constraint_type", ""),
            "is_noise": False,
            "need_human_review": True,
            "kb_tier": 1,
            "tier_reason": f"来自规范文档: {source_doc[:40]}",
        },
        "primary_component": comp,
        "primary_intent": intent,
        "kb_tier": 1,
        "tier_reason": f"来自规范文档: {source_doc[:40]}",
        "_draft_status": "pending",
        "_draft_note": "",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=str, default="", help="处理单个PDF文件名")
    ap.add_argument("--dry-run", type=int, default=0, metavar="N", help="只处理前N个段落")
    args = ap.parse_args()

    # 检查 PDF 目录
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"已创建目录: {RAW_DIR}")
        print("\n请将以下文件放入该目录:")
        print("  - CCS《海船入级规范》第4册: volume4_mechanical.pdf")
        print("  - IACS UR M28: iacs_ur_m28.pdf")
        print("  - IACS UR M47: iacs_ur_m47.pdf")
        print("\n下载地址:")
        print("  CCS: pbc.ccs.org.cn → 规范标准 → 入级规范")
        print("  IACS UR: iacs.org.uk → Publications → Unified Requirements (M series)")
        return

    # 确定要处理的PDF
    if args.file:
        pdf_files = [RAW_DIR / args.file]
    else:
        pdf_files = list(RAW_DIR.glob("*.pdf")) + list(RAW_DIR.glob("*.PDF"))

    if not pdf_files:
        print(f"未找到PDF文件，请将PDF放入: {RAW_DIR}")
        return

    print(f"找到 {len(pdf_files)} 个PDF文件")

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # 加载已有草稿
    existing_units: list[dict] = []
    if OUT_JSONL.exists():
        with open(OUT_JSONL, encoding="utf-8") as f:
            existing_units = [json.loads(l) for l in f]
        print(f"已有草稿: {len(existing_units)} 条")

    all_units: list[dict] = list(existing_units)
    n_extracted = 0
    counter = len(existing_units)

    for pdf_path in pdf_files:
        source_doc = pdf_path.stem.replace("_", " ")
        print(f"\n处理: {pdf_path.name}")

        paras = _extract_pdf_paragraphs(pdf_path)
        if not paras:
            print(f"  ⚠ 无法提取段落（缺少PDF解析库或文件为扫描版）")
            continue

        # 过滤：优先处理含强制语言的段落
        mandatory_paras = [p for p in paras if _has_mandatory_language(p["text"])]
        other_paras     = [p for p in paras if not _has_mandatory_language(p["text"])]
        ordered_paras   = mandatory_paras + other_paras
        print(f"  相关段落: {len(paras)} 个（含强制语言: {len(mandatory_paras)} 个）")

        if args.dry_run:
            ordered_paras = ordered_paras[:args.dry_run]

        for i, para in enumerate(ordered_paras, 1):
            extracted_list = _llm_extract(para, source_doc, client, model)
            for ex in extracted_list:
                counter += 1
                unit = _make_unit(ex, source_doc, pdf_path.name, para["page"], counter)
                all_units.append(unit)
                n_extracted += 1
                print(f"  [{i}/{len(ordered_paras)}] +1 单元: {ex.get('title','?')[:50]}")

            if i % 20 == 0:
                _flush(all_units, OUT_JSONL)
            time.sleep(0.1)

    _flush(all_units, OUT_JSONL)
    _write_review_csv([u for u in all_units if u.get("_draft_status") == "pending"], OUT_CSV)

    print(f"\n=== 提取完成 ===")
    print(f"本次新提取: {n_extracted} 个 L1 约束单元")
    print(f"总草稿数:   {len(all_units)} 条")
    print(f"\n草稿文件: {OUT_JSONL}")
    print(f"审核表格: {OUT_CSV}")
    print("\n下一步:")
    print("  1. 检查 ccs_draft_review.csv，将 _draft_status 改为 approved 或 rejected")
    print("  2. 运行 python scripts/57_append_kb_content.py  (追加到 evidence_units.jsonl)")
    print("     注：需先修改 57 脚本的 DRAFT_PATH 指向 ccs_draft_units.jsonl")


def _flush(units: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")


def _write_review_csv(units: list[dict], path: Path) -> None:
    fields = [
        "id", "kb_tier", "primary_component", "primary_intent",
        "source_document", "source_clause", "mandatory_level",
        "acceptance_criteria", "verification_method",
        "_draft_status", "_draft_note", "text_snippet",
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for u in units:
            meta = u.get("metadata", {})
            row = {
                "id": u.get("id", ""),
                "kb_tier": u.get("kb_tier", 1),
                "primary_component": u.get("primary_component", ""),
                "primary_intent": u.get("primary_intent", ""),
                "source_document": meta.get("source_document", "")[:60],
                "source_clause": meta.get("section_title", ""),
                "mandatory_level": meta.get("mandatory_level", ""),
                "acceptance_criteria": meta.get("acceptance_criteria", ""),
                "verification_method": meta.get("verification_method", ""),
                "_draft_status": u.get("_draft_status", "pending"),
                "_draft_note": u.get("_draft_note", ""),
                "text_snippet": u.get("text", "")[:200].replace("\n", " "),
            }
            w.writerow(row)


if __name__ == "__main__":
    main()
