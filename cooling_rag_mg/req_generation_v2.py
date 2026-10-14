"""两条产线的工程需求生成（v2，原始需求级，不做共享拆分）。

- no-RAG：DeepSeek **强基线**——充分运用领域知识产出完整具体可指导工程的需求，
  明确不是语言润色；不阉割（允许给出工程合理参数），暴露真实能力与幻觉。
- RAG：DeepSeek 据检索证据生成——先判证据相关性、未覆盖不臆造。
两组终端生成均 DeepSeek，差别只在"有无 RAG 证据"。
"""
from __future__ import annotations

from typing import Any

from cooling_rag_mg.json_utils import loads_lenient

_NORAG_SYSTEM = """你是资深船舶主机冷却水系统工程师。把用户给的原始需求，转化为**完整、具体、可直接指导工程建设**的结构化工程需求(shall)。
要求：
- 充分运用你的专业领域知识，给出覆盖完整、具体可操作的工程需求，必要时给出工程上合理的参数/配置/验证方式。
- 这是**专业工程转化，不是语言润色**——不要只把原话换个说法，要补足工程上应当明确的内容。
- 保持工程严谨：对没有把握的强制性安全/法规限值，按工程惯例给出并标注需校核，不要臆造精确法规编号。
只输出 JSON：{"engineering_requirements":[{"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."]}]}"""

_RAG_SYSTEM = """你是资深船舶主机冷却水系统工程师。依据**检索到的证据**，把原始需求转化为完整、具体、可指导工程的结构化工程需求(shall)。
要求：
- 先判断每条证据与需求的相关性，只用相关证据；据证据给出具体工程要求与参数。
- 证据未覆盖的具体参数不要臆造，可写"待按厂家技术数据/规则条款确认"。
- 这是专业工程转化，不是语言润色。
只输出 JSON：{"engineering_requirements":[{"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."]}]}"""


def build_norag_messages(requirement_text: str) -> list[dict]:
    return [{"role": "system", "content": _NORAG_SYSTEM},
            {"role": "user", "content": f"原始需求：{requirement_text}"}]


def build_rag_messages(requirement_text: str, evidence_texts: list[str]) -> list[dict]:
    block = "\n".join(f"[E{i+1}] {t}" for i, t in enumerate(evidence_texts))
    return [{"role": "system", "content": _RAG_SYSTEM},
            {"role": "user", "content": f"原始需求：{requirement_text}\n\n证据：\n{block}"}]


def parse_requirements(raw: str, evidence_ids: list[str]) -> list[dict]:
    """解析 engineering_requirements；跳过非 dict 元素、非 list 直接 []；附 evidence_ids。"""
    ers = loads_lenient(raw).get("engineering_requirements", [])
    if not isinstance(ers, list):
        return []
    out = []
    for er in ers:
        if not isinstance(er, dict):
            continue
        er["evidence_ids"] = list(evidence_ids)
        er.setdefault("shall_statement", "")
        out.append(er)
    return out


def _gen(messages, evidence_ids, client, model, temperature, max_tokens=4000):
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(client, model=model, messages=messages,
                                 temperature=temperature, max_tokens=max_tokens,
                                 response_format={"type": "json_object"})
        return parse_requirements(resp.choices[0].message.content or "{}", evidence_ids)
    except Exception:
        return []


def generate_norag(requirement_text: str, client: Any, model: str, temperature: float = 0.2) -> list[dict]:
    return _gen(build_norag_messages(requirement_text), [], client, model, temperature)


def generate_rag(requirement_text: str, evidence_texts: list[str], evidence_ids: list[str],
                 client: Any, model: str, temperature: float = 0.2) -> list[dict]:
    return _gen(build_rag_messages(requirement_text, evidence_texts), evidence_ids, client, model, temperature)


# ── Per-shall evidence attribution (v3) ─────────────────────────────────────
# Each shall now cites only the specific evidence IDs that support it,
# rather than attributing all retrieved evidence to every shall.

_RAG_SYSTEM_V3 = """你是资深船舶主机冷却水系统工程师。依据**检索到的证据**，把原始需求转化为结构化工程需求(shall)。

要求：
- 判断每条证据与需求的相关性，只用相关证据；据证据给出具体工程要求与参数。
- 证据未覆盖的具体参数不要臆造，可写"待按厂家技术数据/规则条款确认"。
- **关键**：每条 shall 只引用真正支撑该 shall 内容的证据编号（E1/E2…）；
  若某 shall 无对应证据支撑，evidence_refs 写空列表 []。

输出 JSON：
{"engineering_requirements":[
  {"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."],"evidence_refs":["E1","E3"]},
  {"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."],"evidence_refs":[]}
]}"""


def build_rag_messages_v3(
    requirement_text: str,
    evidence_list: list[dict],
) -> list[dict]:
    """Build prompt with numbered evidence block for per-shall attribution."""
    lines = []
    for i, ev in enumerate(evidence_list, 1):
        text = ev.get("text") or ev.get("search_text") or ""
        comp = ev.get("primary_component", "")
        intent = ev.get("primary_intent", "")
        tag = f"[E{i}]({comp}×{intent})"
        lines.append(f"{tag} {text[:300]}")
    block = "\n".join(lines)
    return [
        {"role": "system", "content": _RAG_SYSTEM_V3},
        {"role": "user",   "content": f"原始需求：{requirement_text}\n\n证据：\n{block}"},
    ]


def parse_requirements_v3(
    raw: str,
    evidence_list: list[dict],
) -> list[dict]:
    """Parse v3 output: resolve evidence_refs (E1/E2…) → actual evidence IDs."""
    ers = loads_lenient(raw).get("engineering_requirements", [])
    if not isinstance(ers, list):
        return []

    # build index: "E1" → actual evidence id
    ref_to_id: dict[str, str] = {
        f"E{i}": ev.get("id") or ev.get("chunk_id") or f"E{i}"
        for i, ev in enumerate(evidence_list, 1)
    }

    out = []
    for er in ers:
        if not isinstance(er, dict):
            continue
        refs = er.pop("evidence_refs", []) or []
        if isinstance(refs, str):
            refs = [refs]
        # resolve to real IDs, skip unknown refs
        resolved = [ref_to_id[r] for r in refs if r in ref_to_id]
        er["evidence_ids"] = resolved
        er.setdefault("shall_statement", "")
        out.append(er)
    return out


def generate_rag_v3(
    requirement_text: str,
    evidence_list: list[dict],
    client: Any,
    model: str,
    temperature: float = 0.2,
) -> list[dict]:
    """Generate RAG requirements with per-shall evidence attribution.

    Parameters
    ----------
    evidence_list : list of evidence dicts from aligned_retrieve (with 'id',
                    'text', 'primary_component', 'primary_intent').
    Returns list of requirement dicts, each with evidence_ids = only the
    specific evidence IDs that support that particular shall.
    """
    from cooling_rag_mg.llm_cache import cached_completion
    if not evidence_list:
        return []
    messages = build_rag_messages_v3(requirement_text, evidence_list)
    try:
        resp = cached_completion(
            client, model=model, messages=messages,
            temperature=temperature, max_tokens=8192,
            response_format={"type": "json_object"},
        )
        return parse_requirements_v3(resp.choices[0].message.content or "{}", evidence_list)
    except Exception:
        return []
