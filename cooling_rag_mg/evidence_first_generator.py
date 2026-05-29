"""Phase 3：证据优先工程需求生成（Qwen）。

核心单变量设计：B0（no-RAG）与 R（RAG）**共用同一 system base**（同角色、同输出格式、
同安全条款），**唯一差别**是 R 的 user 消息里注入了检索到的证据块、要求据证据生成；
B0 无证据块、据共享子需求生成。R 对无证据子需求**弃权**（不产出 shall），B0 永不弃权。

这样把「上下文有无检索证据」隔离成唯一处理变量，配合 Phase 2 的统一 KB 判法，
公平、非循环地检验「据证据生成是否更低幻觉/过推断」。详见 spec。
"""
from __future__ import annotations

from typing import Any

# 两组共用、逐字一致的 system base —— 任何改动都必须对 B0/R 同时生效，保证单变量。
BASE_SYSTEM = """你是船舶主机冷却水系统的需求工程师。把给定的子需求转化为结构化工程需求(shall)。
规则：
- shall_statement 用清晰工程语言书写，忠实于子需求范围，不要扩大义务。
- **无可靠依据不得编造**具体数字/阈值/标准编号；无法确认的参数写「待按厂家技术数据确认」。
- verification_method 取值之一：review, inspection, calculation, test, commissioning_check,
  operation_check, maintenance_check, class_approval。

只输出 JSON（无 markdown）：
{"engineering_requirements":[{"shall_statement":"...","verification_method":"review",
  "acceptance_criteria":["..."],"evidence_ids":[]}]}"""


def build_generation_messages(
    sub_requirement: dict[str, Any],
    evidence_texts: list[str] | None,
    source_requirement: str,
) -> list[dict[str, str]]:
    """构造生成消息。system 对 B0/R 逐字一致；user 仅在 R（evidence_texts 非空）时含证据块。"""
    sub_text = (sub_requirement.get("text") or "").strip()
    lines = [f"原始需求：{source_requirement}", f"子需求：{sub_text}"]
    if evidence_texts:
        block = "\n".join(f"[E{i+1}] {t}" for i, t in enumerate(evidence_texts))
        lines.append(
            "证据：\n" + block +
            "\n\n请**仅依据上述证据**生成工程需求；证据未覆盖的参数不得编造。"
        )
    else:
        lines.append("（无检索证据，依据子需求生成。）")
    return [
        {"role": "system", "content": BASE_SYSTEM},
        {"role": "user", "content": "\n".join(lines)},
    ]


def should_abstain(arm: str, evidence_texts: list[str] | None) -> bool:
    """R 在无证据时弃权（不产出 shall，记入覆盖率）；B0 永不弃权。"""
    return arm == "R" and not evidence_texts
