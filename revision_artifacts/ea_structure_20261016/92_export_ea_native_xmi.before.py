"""
导出 **Enterprise Architect 原生 XMI 1.1 (UML 1.3)** 需求图——严格仿照
EA 自身导出的格式(参见 XML/XML_of_EA/reqFig.xml）:

  UML:Model > UML:Package > UML:Namespace.ownedElement
     UML:Collaboration > UML:ClassifierRole(stereotype=requirement, +documentation)
     UML:Association(ea_type=Nesting, 父->子) ...
  UML:Diagram(diagramType=CustomDiagram, MDGDgm=SysML1.4::Requirement)
     UML:DiagramElement(每个需求框 geometry + DUID;每条连线 SOID/EOID)

EA 导入：Project > Model Import/Export > Import Package from XMI File。

用法：
  python scripts/92_export_ea_native_xmi.py                 # 默认 OR001 案例
  python scripts/92_export_ea_native_xmi.py --sets OR001 OR007 OR046
  python scripts/92_export_ea_native_xmi.py --all
输出：data/search_results/exp_v4/ea_native_<...>.xml
"""
from __future__ import annotations
import argparse, html, json, re, sys, textwrap, uuid, csv, hashlib
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import classify_grade, valid_citation_ids
from cooling_rag_mg.numeric_norm import extract_numbers
from cooling_rag_mg.review_routing import derivation_type, review_route, derivation_assessment  # noqa: E402

EXP = ROOT / "data" / "search_results" / "exp_v4"
RAG = EXP / "rag_v4_results.json"
KB_AUDITED = ROOT / "data" / "processed" / "evidence_units_v3_audited.jsonl"
ORIG = ROOT / "data" / "processed" / "original_requirements_v2.jsonl"
ROOTCLS = "EAID_11111111_5487_4080_A7F4_41526CB0AA00"
PKG = "EAPK_3CC4E5A4_E927_4a10_A9FD_CAEAF8808A43"
PKGNAME = " 01_Requirements"
AUTHOR = "cooling_rag_mg"


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True).replace("\n", "&#xA;")


def wrap_cn(text, width=30) -> str:
    """硬换行：英文按词边界、中文按字数。EA 框内不会自动断长串，必须预插换行，
    手动拉宽框也无效。保留原有换行。"""
    out = []
    for line in str(text or "").split("\n"):
        if not line:
            out.append("")
            continue
        if " " in line.strip():  # 英文：按词边界
            out.extend(textwrap.wrap(line, width=width, break_long_words=False) or [""])
        else:                    # 无空格(中文)：按字数硬断
            for i in range(0, len(line), max(1, width // 2)):
                out.append(line[i:i + max(1, width // 2)])
    return "\n".join(out)


def new_guid() -> tuple[str, str]:
    """返回 (xmi_id 'EAID_..', guid '{....}')。"""
    h = uuid.uuid4().hex.upper()
    parts = (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])
    return "EAID_" + "_".join(parts), "{" + "-".join(parts) + "}"


def duid() -> str:
    return uuid.uuid4().hex[:8].upper()


def cite_ids(cits) -> str:
    out = []
    for c in cits or []:
        if isinstance(c, dict):
            out.append(c.get("kb_id", ""))
        elif isinstance(c, str):
            m = re.search(r"E-[A-Z0-9]+-[A-Z0-9]+-\d+", c)
            out.append(m.group(0) if m else "")
    return "; ".join(x for x in out if x)


# 按 grade 上色：COLORREF = R + G*256 + B*65536（EA style 用此十进制）
def _cr(r, g, b):
    return r + g * 256 + b * 65536


GRADE_STYLE = {
    "A": (_cr(200, 255, 200), _cr(34, 139, 34)),    # 浅绿 / 深绿
    "B": (_cr(210, 230, 255), _cr(0, 102, 204)),    # 浅蓝 / 蓝
    "C": (_cr(255, 245, 210), _cr(204, 102, 0)),    # 浅琥珀 / 橙
    "X": (_cr(255, 210, 210), _cr(180, 0, 0)),      # 浅红 / 红
    "_src": (_cr(232, 232, 232), _cr(110, 110, 110)),  # 灰(源需求)
    # 未知等级：EA 默认色(-1)。规范五——未知等级必须显式报告，
    # 不得借源需求灰隐式表示（灰色只表示源需求）。
    "_unknown": (-1, -1),
}

# 图块样式与尺寸，对齐 EA 原生需求图（XML/XML_of_EA/reqFig.xml、论文 fig5）：
# «requirement» + 名称 + tags 隔间（id = ORxxx / text = <memo> 两行）。
# Tag=1 显示 tags 隔间；完整正文在 text 属性里（memo 类型，图上只显示 <memo>）。
# 原生图块是 110 宽的窄栏，高随内容 160-223，RzO=1 让 EA 导入时自适应高度。
DIAG_ELEM_STYLE = "HideIcon=0;UCRect=1;Tag=1;AttCustom=0;OpCustom=0;RzO=1;"
BOX_W, BOX_H = 110, 170

# EA 把 SysML requirement 的 id/text 属性导出为内容级 tagged value，其 xmi.id
# 前三段是固定的属性类型 GUID（见 reqFig.xml 第 551-566 行）。只有用这两个
# 前缀，EA 导入时才把它们识别为内置 id/text——text 是 memo 类型，图块上只
# 显示 "text = <memo>"；用随机 GUID 会被当成普通 tagged value，Tag=1 时整段
# 正文直接画在图块上（此前图块被撑大、内容杂乱的根因）。
ID_TV_STEM = "EAID_00000DED_3AF1_773a_"
TEXT_TV_STEM = "EAID_00415985_D789_37d7_"


def _tv_guid(stem: str) -> str:
    """属性 tagged value 的 xmi.id：固定前缀 + 随机 4 段 + 随机 12 段（仿 reqFig.xml）。"""
    h = uuid.uuid4().hex.upper()
    return f"{stem}{h[8:12]}_{h[20:32]}"


def classifier_role(name, rid, guid, lid, notes, grade="_src") -> str:
    back, border = GRADE_STYLE.get(grade, GRADE_STYLE["_unknown"])
    xref = ("$XREFPROP=$XID=" + guid + "$XID;$NAM=Stereotypes$NAM;$TYP=element property$TYP;"
            "$VIS=Public$VIS;$PAR=0$PAR;$DES=@STEREO;Name=requirement;"
            "FQName=SysML1.4::requirement;@ENDSTEREO;$DES;$CLT=" + guid +
            "$CLT;$SUP=&lt;none&gt;$SUP;$ENDXREF;")
    tv = [
        ("isAbstract", "false"), ("isSpecification", "false"),
        ("ea_stype", "Requirement"), ("ea_ntype", "0"), ("version", "1.0"),
        ("isActive", "false"), ("package", PKG), ("gentype", "&lt;none&gt;"),
        ("tagged", "0"), ("package_name", PKGNAME), ("phase", "1.0"),
        ("author", AUTHOR), ("complexity", "1"), ("status", "Proposed"),
        ("stereotype", "requirement"), ("ea_localid", str(lid)),
        ("ea_eleType", "element"), ("documentation", esc(notes)),
        ("style", f"BackColor={back};BorderColor={border};BorderWidth=2;FontColor=-1;"
                  "VSwimLanes=1;HSwimLanes=1;BorderStyle=0;"),
        ("$ea_xref_property", xref),
    ]
    tvs = "\n".join(f'\t\t\t\t\t\t<UML:TaggedValue tag="{k}" value="{v}"/>' for k, v in tv)
    return (
        f'\t\t\t\t\t<UML:ClassifierRole name="{esc(name)}" xmi.id="{rid}" '
        f'visibility="public" base="{ROOTCLS}">\n'
        f'\t\t\t\t\t\t<UML:ModelElement.stereotype>\n'
        f'\t\t\t\t\t\t\t<UML:Stereotype name="requirement"/>\n'
        f'\t\t\t\t\t\t</UML:ModelElement.stereotype>\n'
        f'\t\t\t\t\t\t<UML:ModelElement.taggedValue>\n{tvs}\n'
        f'\t\t\t\t\t\t</UML:ModelElement.taggedValue>\n'
        f'\t\t\t\t\t</UML:ClassifierRole>'
    )


def association(aid, alid, pid, plid, pname, cid, clid, cname) -> str:
    tv = [
        ("style", "3"), ("ea_type", "Nesting"), ("direction", "Source -&gt; Destination"),
        ("linemode", "3"), ("linecolor", "-1"), ("linewidth", "0"), ("seqno", "0"),
        ("headStyle", "0"), ("lineStyle", "0"), ("ea_localid", str(alid)),
        ("ea_sourceName", esc(pname)), ("ea_targetName", esc(cname)),
        ("ea_sourceType", "Requirement"), ("ea_targetType", "Requirement"),
        ("ea_sourceID", str(plid)), ("ea_targetID", str(clid)),
        ("virtualInheritance", "0"),
    ]
    tvs = "\n".join(f'\t\t\t\t\t\t<UML:TaggedValue tag="{k}" value="{v}"/>' for k, v in tv)
    end = (lambda t, nav, side, sk: (
        f'\t\t\t\t\t\t\t<UML:AssociationEnd visibility="public" aggregation="none" '
        f'isOrdered="false" targetScope="instance" changeable="none" '
        f'isNavigable="{nav}" type="{t}">\n'
        f'\t\t\t\t\t\t\t\t<UML:ModelElement.taggedValue>\n'
        f'\t\t\t\t\t\t\t\t\t<UML:TaggedValue tag="containment" value="Unspecified"/>\n'
        f'\t\t\t\t\t\t\t\t\t<UML:TaggedValue tag="{sk}" value="Union=0;Derived=0;'
        f'AllowDuplicates=0;Owned=0;Navigable={"Navigable" if nav=="false" else "Unspecified"};"/>\n'
        f'\t\t\t\t\t\t\t\t\t<UML:TaggedValue tag="ea_end" value="{side}"/>\n'
        f'\t\t\t\t\t\t\t\t</UML:ModelElement.taggedValue>\n'
        f'\t\t\t\t\t\t\t</UML:AssociationEnd>'))
    return (
        f'\t\t\t\t\t<UML:Association xmi.id="{aid}" visibility="public" '
        f'isRoot="false" isLeaf="false" isAbstract="false">\n'
        f'\t\t\t\t\t\t<UML:ModelElement.taggedValue>\n{tvs}\n'
        f'\t\t\t\t\t\t</UML:ModelElement.taggedValue>\n'
        f'\t\t\t\t\t\t<UML:Association.connection>\n'
        f'{end(pid,"false","source","sourcestyle")}\n'
        f'{end(cid,"true","target","deststyle")}\n'
        f'\t\t\t\t\t\t</UML:Association.connection>\n'
        f'\t\t\t\t\t</UML:Association>'
    )


def er_notes(shall, crit, grade, verif, cited, derivation, route, route_reason,
             width=34) -> str:
    """需求元素的 notes：正文、判据、等级、派生类型、复核路由、引用单元。

    派生类型与路由是确定性规则（见 cooling_rag_mg.review_routing），随元素导出，
    使 EA 图中不只有等级，还能看出该需求为何被送到某一复核层级。
    缺失信息标明 (not provided)，不为填满模板编造内容。
    """
    na = "(not provided)"
    return (f"{wrap_cn(shall, width)}\n"
            f"Criterion: {wrap_cn(str(crit), width) if str(crit).strip() else na}\n"
            f"Grade: {grade or na}\n"
            f"Derivation: {derivation}\n"
            f"Route: {route} --- {wrap_cn(route_reason, width)}\n"
            f"Verification: {wrap_cn(verif, width) if str(verif).strip() else na}\n"
            f"Cited: {wrap_cn(cited, width) if str(cited).strip() else na}")


def req_id_value(ext_id: str, rid: str) -> str:
    """EA 需求的 id 属性（外部编号）：用属性类型 GUID 前缀，导入后识别为内置 id。"""
    return (f'<UML:TaggedValue tag="id" xmi.id="{_tv_guid(ID_TV_STEM)}" '
            f'value="{esc(ext_id)}" modelElement="{rid}"/>')


def req_text_value(text: str, rid: str) -> str:
    """EA 需求的 text 属性（<memo>#NOTES# 前缀 + 属性类型 GUID）：完整内容放这里，
    打开元素可见；图块 tags 隔间里只显示 text = <memo>（见 DIAG_ELEM_STYLE）。"""
    return (f'<UML:TaggedValue tag="text" xmi.id="{_tv_guid(TEXT_TV_STEM)}" '
            f'value="&lt;memo&gt;#NOTES#{esc(text)}" modelElement="{rid}"/>')


IDENTITY_PATH = EXP / "ea_identity_map.json"
LLM_CACHE_PATH = EXP / "ea_llm_cache.json"


def _load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def load_identity(path=None) -> dict:
    """规范三：稳定身份映射（业务编号 -> 元素 GUID；逻辑关系 -> 关系 GUID）。
    重复生成复用身份，EA 重复导入才是更新语义而不是每次复制一套新元素。"""
    d = _load_json(path or IDENTITY_PATH, {})
    d.setdefault("elements", {})
    d.setdefault("assocs", {})
    d.setdefault("diagrams", {})
    d.setdefault("package", PKG)
    d.setdefault("collaboration", "")
    return d


def save_identity(idmap: dict, path=None):
    Path(path or IDENTITY_PATH).write_text(
        json.dumps(idmap, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def elem_identity(idmap: dict, biz_id: str) -> tuple[str, str]:
    e = idmap["elements"].get(biz_id)
    if not e:
        xid, guid = new_guid()
        e = {"xmi_id": xid, "guid": guid}
        idmap["elements"][biz_id] = e
    return e["xmi_id"], e["guid"]


def assoc_identity(idmap: dict, key: str) -> str:
    a = idmap["assocs"].get(key)
    if not a:
        a, _ = new_guid()
        idmap["assocs"][key] = a
    return a


def diagram_identity(idmap: dict, dname: str) -> str:
    d = idmap["diagrams"].get(dname)
    if not d:
        d, _ = new_guid()
        idmap["diagrams"][dname] = d
    return d


def _save_llm_cache(path, section: str, values: dict):
    data = _load_json(path, {})
    data[section] = values
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def short_fallback(text: str) -> str:
    """无 LLM 时的兜底：去常见前缀 + 截断(首个分句)。"""
    t = re.sub(r"^\[Source requirement\]\s*", "", text or "")
    for pre in ("主机冷却水系统应", "冷却水系统应", "冷却系统应", "系统应", "应"):
        if t.startswith(pre):
            t = t[len(pre):]; break
    return re.sub(r"[，。；,.;].*$", "", t)[:40]


def _llm_json(prompt: str, system: str, max_tokens: int = 3000) -> dict:
    """调 DeepSeek 返回 JSON 对象；失败抛异常由调用方兜底。"""
    from cooling_rag_mg.config import DeepSeekConfig
    cfg = DeepSeekConfig()
    if not cfg.enabled:
        raise RuntimeError("no key")
    client = cfg.make_client()
    resp = client.chat.completions.create(
        model=cfg.model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": prompt}],
        temperature=0, max_tokens=max_tokens,
    )
    raw = resp.choices[0].message.content
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    return json.loads(m.group(0)) if m else {}


def gen_titles(items: list[tuple[str, str]], cache_path=None) -> dict[str, str]:
    """items=[(key, 中文文本)]；用 DeepSeek 一次生成简短**英文**概括标题。

    规范四：标题必须缓存并可审核；仅调整样式时不得重新调用模型改写需求。
    缓存只保存模型成功生成的标题；仅对未命中缓存的项调用 LLM；
    失败时 short_fallback 兜底（兜底结果不写入缓存）。"""
    cached = _load_json(cache_path, {}).get("titles", {}) if cache_path else {}
    titles = {k: cached[k] for k, _ in items if k in cached}
    missing = [(k, t) for k, t in items if k not in titles]
    if missing:
        try:
            listing = "\n".join(f"{k}: {t}" for k, t in missing)
            prompt = (
                "For each ship cooling-water requirement below, produce a concise **English** "
                "title: a noun phrase of at most 6 words, **no digits, units, placeholders "
                "({{...}}) or citations**. Return ONLY a JSON object keyed by the IDs I gave, "
                "values are the titles.\n\n" + listing
            )
            new = _llm_json(prompt, "You are a marine systems-engineering expert. Be concise.")
            for k, _t in missing:
                v = re.sub(r"[0-9{}|]", "", str(new.get(k, "")).strip())[:40]
                if v:
                    titles[k] = v
            if cache_path:
                merged = dict(cached)
                merged.update(titles)
                _save_llm_cache(cache_path, "titles", merged)
        except Exception as exc:  # noqa
            print(f"[titles] LLM failed, using fallback: {exc}")
    return {k: titles.get(k) or short_fallback(t) for k, t in items}


def translate_en(items: list[tuple[str, str]], cache_path=None) -> dict[str, str]:
    """items=[(key, 中文文本)]；忠实英译。缓存规则同 gen_titles；失败则保留原文。"""
    cached = _load_json(cache_path, {}).get("trans", {}) if cache_path else {}
    out = {k: cached[k] for k, _ in items if k in cached}
    missing = [(k, t) for k, t in items if k not in out]
    if missing:
        try:
            listing = "\n".join(f"{k}: {t}" for k, t in missing)
            prompt = (
                "Translate each ship cooling-water requirement text below into clear, faithful "
                "**English** engineering language. Translate ALL Chinese, including Chinese that "
                "appears INSIDE placeholder tokens like {{TBD|unit:s|ref:KB_DRAFT_v1|component:..|"
                "intent:..|hint:..}}. You MUST preserve exactly: all numbers and units; every "
                "evidence/KB id (tokens matching E-... or KB_...); the {{...}} wrapper and its "
                "field keys (TBD, unit, ref, component, intent, hint, reason). Only translate the "
                "human-language values after each colon. Return ONLY a JSON object keyed by the "
                "IDs I gave, values are the English translations.\n\n" + listing
            )
            tr = _llm_json(prompt, "You are a professional marine-engineering translator.")
            for k, _t in missing:
                v = str(tr.get(k, "")).strip()
                if v:
                    out[k] = v
            if cache_path:
                merged = dict(cached)
                merged.update({k: out[k] for k, _ in missing if k in out})
                _save_llm_cache(cache_path, "trans", merged)
        except Exception as exc:  # noqa
            print(f"[translate] LLM failed, keeping source text: {exc}")
    return {k: out.get(k) or t for k, t in items}


def group_layout(n_children: int, *, per_row: int, y_top: int, bw: int, gapx: int, gapy: int,
                 x0: int = 40):
    """Diagram coordinates for one source requirement and its children.

    per_row <= 0 keeps every child on one row (the original layout); otherwise children wrap
    into rows of ``per_row``.  Returns ((parent_x, parent_y), [(child_x, child_y)], height).
    """
    cols = n_children if per_row <= 0 else min(n_children, per_row)
    rows = 0 if n_children == 0 else (1 if per_row <= 0 else -(-n_children // per_row))
    px = x0 + max(1, cols) * gapx // 2 - bw // 2
    kids = []
    for k in range(n_children):
        r, c = (0, k) if per_row <= 0 else divmod(k, per_row)
        kids.append((x0 + c * gapx, y_top + gapy * (1 + r)))
    return (px, y_top), kids, gapy * (1 + rows)


def assemble_xml(*, roles, assocs, reqtext_block, diag_elements, dname, did,
                 diag_tvs, pkg_tvs, coll_id) -> str:
    """确定性拼合整份 XMI（规范二：模板结构冻结，元素/图元由代码拼写，不是模型）。"""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<XMI xmi.version="1.1" xmlns:UML="omg.org/UML1.3" timestamp="2026-06-15 00:00:00">\n'
        '\t<XMI.header>\n\t\t<XMI.documentation>\n'
        '\t\t\t<XMI.exporter>Enterprise Architect</XMI.exporter>\n'
        '\t\t\t<XMI.exporterVersion>2.5</XMI.exporterVersion>\n'
        '\t\t</XMI.documentation>\n\t</XMI.header>\n'
        '\t<XMI.content>\n'
        '\t\t<UML:Model name="EA Model" xmi.id="MX_EAID_COOLINGRAG_MODEL">\n'
        '\t\t\t<UML:Namespace.ownedElement>\n'
        f'\t\t\t\t<UML:Class name="EARootClass" xmi.id="{ROOTCLS}" isRoot="true" '
        'isLeaf="false" isAbstract="false"/>\n'
        f'\t\t\t\t<UML:Package name="{PKGNAME}" xmi.id="{PKG}" isRoot="false" '
        'isLeaf="false" isAbstract="false" visibility="public">\n'
        '\t\t\t\t\t<UML:ModelElement.taggedValue>\n'
        f'{pkg_tvs}\n'
        '\t\t\t\t\t</UML:ModelElement.taggedValue>\n'
        '\t\t\t\t\t<UML:Namespace.ownedElement>\n'
        f'\t\t\t\t\t<UML:Collaboration xmi.id="{coll_id}" name="Collaborations">\n'
        '\t\t\t\t\t\t<UML:Namespace.ownedElement>\n'
        + "\n".join(roles) + "\n"
        '\t\t\t\t\t\t</UML:Namespace.ownedElement>\n'
        '\t\t\t\t\t\t<UML:Collaboration.interaction/>\n'
        '\t\t\t\t\t</UML:Collaboration>\n'
        + "\n".join(assocs) + "\n"
        '\t\t\t\t\t</UML:Namespace.ownedElement>\n'
        '\t\t\t\t</UML:Package>\n'
        '\t\t\t</UML:Namespace.ownedElement>\n'
        '\t\t</UML:Model>\n'
        + reqtext_block + "\n"
        f'\t\t<UML:Diagram name="{esc(dname)}" xmi.id="{did}" diagramType="CustomDiagram" '
        f'owner="{PKG}" toolName="Enterprise Architect 2.5">\n'
        '\t\t\t<UML:ModelElement.taggedValue>\n'
        f'{diag_tvs}\n'
        '\t\t\t</UML:ModelElement.taggedValue>\n'
        '\t\t\t<UML:Diagram.element>\n'
        + "\n".join(diag_elements) + "\n"
        '\t\t\t</UML:Diagram.element>\n'
        '\t\t</UML:Diagram>\n'
        '\t</XMI.content>\n'
        '\t<XMI.difference/>\n'
        '\t<XMI.extensions xmi.extender="Enterprise Architect 2.5"/>\n'
        '</XMI>\n'
    )


def validate_xmi(xml_text: str, *, n_reqs: int, n_edges: int, compact: bool = False) -> list[str]:
    """规范九.4 静态验收。返回问题列表；空列表 = 静态检查通过。

    通过只证明结构契约成立，不代表 EA 导入外观正确（须目标 EA 实测）；
    有任何一个问题则文件不可交付。"""
    try:
        ET.fromstring(xml_text)
    except ET.ParseError as e:
        return [f"XML 不可解析: {e}"]
    probs = []
    ids = re.findall(r'xmi\.id="([^"]+)"', xml_text)
    idset = set(ids)
    for i, c in Counter(ids).items():
        if c > 1:
            probs.append(f"xmi.id 重复: {i} x{c}")
    for attr in ("subject", "modelElement", "type", "owner", "base"):
        for ref in sorted(set(re.findall(attr + r'="([^"]+)"', xml_text))):
            if ref not in idset:
                probs.append(f"引用无法解析: {attr}={ref}")
    roles = re.findall(r'<UML:ClassifierRole name="([^"]*)" xmi\.id="([^"]+)"', xml_text)
    if len(roles) != n_reqs:
        probs.append(f"需求元素数 {len(roles)} != 输入 {n_reqs}")
    for m in re.finditer(r'<UML:ClassifierRole .*?</UML:ClassifierRole>', xml_text, re.S):
        b = m.group(0)
        rid = re.search(r'xmi\.id="([^"]+)"', b).group(1)
        if '<UML:Stereotype name="requirement"/>' not in b:
            probs.append(f"{rid} 缺 stereotype requirement")
        if "FQName=SysML1.4::requirement" not in b:
            probs.append(f"{rid} xref 缺 FQName=SysML1.4::requirement")
        if 'tag="documentation"' not in b:
            probs.append(f"{rid} 缺 documentation")
    id_refs = re.findall(r'<UML:TaggedValue tag="id" xmi\.id="[^"]+" value="[^"]*" '
                         r'modelElement="([^"]+)"/>', xml_text)
    text_refs = re.findall(r'<UML:TaggedValue tag="text" xmi\.id="[^"]+" value="([^"]*)" '
                           r'modelElement="([^"]+)"/>', xml_text)
    for _name, rid in roles:
        if id_refs.count(rid) != 1:
            probs.append(f"{rid} 有 {id_refs.count(rid)} 个 id 属性（须恰好 1 个）")
        n_text = sum(1 for _v, r in text_refs if r == rid)
        if n_text != 1:
            probs.append(f"{rid} 有 {n_text} 个 text 属性（须恰好 1 个）")
    for val, rid in text_refs:
        if not val.startswith("&lt;memo&gt;#NOTES#"):
            probs.append(f"{rid} text 缺 <memo>#NOTES# 前缀")
    for bad in ("&amp;lt;", "&amp;gt;", "&amp;#xA;"):
        if bad in xml_text:
            probs.append(f"发现二次转义 {bad}")
    geom = re.findall(
        r'geometry="Left=(\d+);Top=(\d+);Right=(\d+);Bottom=(\d+);" subject="([^"]+)"'
        r'[^>]*style="([^"]*)"', xml_text)
    nodes = [(int(a), int(t), int(r), int(b), s, st) for a, t, r, b, s, st in geom
             if "NSL=1" not in st]
    envs = [(int(a), int(t), int(r), int(b)) for a, t, r, b, _s, st in geom if "NSL=1" in st]
    if len([node for node in nodes if node[4] != "EAID_COMPACT_LEGEND_00000000"]) != n_reqs:
        probs.append(f"图元数 {len(nodes)} != 需求数 {n_reqs}")
    rects = {}
    for a, t, r, b, s, st in nodes:
        if not (r > a and b > t):
            probs.append(f"geometry 非法(R<=L 或 B<=T): {s}")
        if s != "EAID_COMPACT_LEGEND_00000000" and (("Tag=0" if compact else "Tag=1") not in st or "RzO=1" not in st):
            probs.append(f"节点样式缺 Tag=1/RzO=1: {s}")
        rects[s] = (a, t, r, b)
    keys = sorted(rects)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            l1, t1, r1, b1 = rects[keys[i]]
            l2, t2, r2, b2 = rects[keys[j]]
            if l1 < r2 and l2 < r1 and t1 < b2 and t2 < b1:
                probs.append(f"框体相交: {keys[i]} vs {keys[j]}")
    if len(envs) != 1:
        probs.append(f"包络框数量 {len(envs)} != 1")
    elif rects:
        el, et, er, eb = envs[0]
        for k, (a, t, r, b) in rects.items():
            if not (el <= a and et <= t and er >= r and eb >= b):
                probs.append(f"包络框未覆盖节点 {k}")
    duids = set(re.findall(r'style="\s*DUID=([0-9A-F]+);', xml_text))
    edges = re.findall(r'style="Mode=3;EOID=([0-9A-F]+);SOID=([0-9A-F]+);', xml_text)
    if len(edges) != n_edges:
        probs.append(f"连线数 {len(edges)} != 关系数 {n_edges}")
    for eo, so in edges:
        if eo not in duids or so not in duids:
            probs.append(f"连线端点 DUID 无法解析: SOID={so} EOID={eo}")
    approved = {str(v) for pair in GRADE_STYLE.values() for v in pair} | {"-1"}
    for bc in set(re.findall(r'BackColor=(-?\d+)', xml_text)):
        if bc not in approved:
            probs.append(f"未批准的 BackColor={bc}")
    return probs


def single_line(value):
    return " ".join(str(value or "").split())


def property_value(key, value, rid):
    return f'<UML:TaggedValue tag="{esc(key)}" xmi.id="{new_guid()[0]}" value="{esc(single_line(value))}" modelElement="{rid}"/>'


def safe_translation(source, translated):
    # Compare all numeric occurrences, including placeholder hints, and preserve TBD verbatim.
    numbers = lambda t: Counter(re.findall(r"[+-]?\d+(?:\.\d+)?", t))
    placeholders = lambda t: re.findall(r"\{\{?TBD[^}]*\}\}?", t)
    if numbers(source) != numbers(translated) or placeholders(source) != placeholders(translated):
        print("[translation] numeric/placeholder mismatch; preserving source: " + source[:60])
        return source
    return translated


def build_xmi(sets, kb, titles, tr, per_row=4, *, idmap=None, review_out=None):
    """Pure construction: no API, filesystem writes, or translation generation."""
    by_sid = {rs["source_requirement_id"]:rs for rs in sets}
    if len(by_sid) != len(sets):
        raise ValueError("Duplicate source IDs")
    if not sets:
        raise ValueError("No source requirements")
    sids = list(by_sid)
    orig = {sid:{"requirement_text":rs.get("_source_text", "")} for sid,rs in by_sid.items()}
    roles, assocs, diag_nodes, diag_edges, meta = [], [], [], [], []
    idmap = idmap if idmap is not None else load_identity(Path("__no_identity__"))
    review_rows = []
    extra_tags = []
    unknown_grades = []
    lid = 10
    y0 = 30
    bw, bh, gapx, gapy = 160, 110, 190, 170
    y_cursor = y0
    WRAP = 34
    for si, sid in enumerate(sids, 1):
        rs = by_sid[sid]
        ev_values = rs.get("_evidence_values") or {}
        sid_norm = sid if sid.startswith("OR") else "OR" + sid
        src_original = orig.get(sid, {}).get("requirement_text", "")
        src_text = safe_translation(src_original, tr.get(f"T_{sid}", src_original))
        pid, pguid = elem_identity(idmap, sid_norm); plid = lid; lid += 1
        pdu = duid()
        pname = f"{sid_norm}  {titles.get('S_'+sid, '')}"
        roles.append(classifier_role(pname, pid, pguid, plid,
                                     ""))
        meta.append((pid, sid_norm, single_line(src_text)))
        extra_tags += [property_value("text_zh", src_original, pid), property_value("stakeholder", rs.get("stakeholder", ""), pid)]
        ers = rs.get("engineering_requirements", [])
        # 父框居中；子需求按 --per-row 换行，组与组之间留一个 gapy
        (px, py), kid_xy, group_h = group_layout(len(ers), per_row=per_row, y_top=y_cursor,
                                                bw=bw, gapx=gapx, gapy=gapy)
        y_cursor += group_h + gapy
        diag_nodes.append((pid, pdu, px, py, px + 200, py + 110))
        for k, er in enumerate(ers, 1):
            cid, cguid = elem_identity(idmap, f"{sid_norm}.{k}"); clid = lid; lid += 1
            cdu = duid()
            grade = classify_grade(er.get("measurable_criterion"), er.get("evidence_citations", []), kb)
            er = dict(er, _grade=grade)
            if grade not in ("A", "B", "C", "X"):
                unknown_grades.append(f"{sid_norm}.{k} (grade={grade!r})")
            crit = safe_translation(str(er.get("measurable_criterion") or ""), tr.get(f"C_{sid}_{k}", str(er.get("measurable_criterion") or "")))
            shall = safe_translation(er.get("shall_statement", ""), tr.get(f"H_{sid}_{k}", er.get("shall_statement", "")))
            verif = tr.get(f"V_{sid}_{k}", er.get("verification_method", ""))
            cname = f"{sid_norm}.{k}  {titles.get(f'E_{sid}_{k}', '')}"
            deriv = derivation_type(er, kb)
            route, route_reason = review_route(er, kb, ev_values)
            ids = valid_citation_ids(er.get("evidence_citations", []), kb)
            assessment = derivation_assessment(er, kb)
            fields = {"criterion":crit, "grade":grade, "derivation":deriv,
                "review_route":route, "route_reason":route_reason, "verification":verif,
                "evidence_ids":"; ".join(ids), "evidence_tiers":"; ".join(str(kb[i].get("kb_tier", "")) for i in ids),
                "evidence_sources":"; ".join(dict.fromkeys(str((kb[i].get("metadata") or {}).get("source_document", "")) for i in ids)),
                "shall_zh":er.get("shall_statement", ""), "classification_v2":assessment["classification"],
                "mathematical_derivation_verified":"false", "semantic_support_verified":"false",
                "relationship_semantics":"Nesting: generated output grouped under source; not verified deriveReqt or satisfy",
                "translation_status":"legacy_cache_or_source_fallback_requires_review"}
            notes = f"Grade {grade} | {deriv} | {route} | {fields['evidence_ids']}"
            roles.append(classifier_role(cname, cid, cguid, clid, single_line(notes), grade=grade))
            meta.append((cid, f"{sid_norm}.{k}", single_line(shall)))
            extra_tags += [property_value(key, value, cid) for key,value in fields.items()]
            review_rows.append({"id":f"{sid_norm}.{k}","name":cname,"text_en":single_line(shall),**fields})
            aid = assoc_identity(idmap, f"{sid_norm}->{sid_norm}.{k}"); alid = lid; lid += 1
            assocs.append(association(aid, alid, pid, plid, pname, cid, clid, cname))
            cx, cy = kid_xy[k - 1]
            diag_nodes.append((cid, cdu, cx, cy, cx + bw, cy + bh))
            diag_edges.append((aid, pdu, cdu))

    # 包络框
    allx2 = max(n[4] for n in diag_nodes); ally2 = max(n[5] for n in diag_nodes)
    pkg_du = duid()
    de = []
    seq = 1
    for (eid, du, l, t, r, b) in diag_nodes:
        de.append(f'\t\t\t\t<UML:DiagramElement geometry="Left={l};Top={t};Right={r};Bottom={b};" '
                  f'subject="{eid}" seqno="{seq}" style="DUID={du};{DIAG_ELEM_STYLE}"/>')
        seq += 1
    de.append(f'\t\t\t\t<UML:DiagramElement geometry="Left=10;Top=10;Right={allx2+30};'
              f'Bottom={ally2+30};" subject="{PKG}" seqno="{seq}" style="DUID={pkg_du};NSL=1;"/>')
    for (aid, sdu, edu) in diag_edges:
        de.append(f'\t\t\t\t<UML:DiagramElement geometry="SX=0;SY=0;EX=0;EY=0;EDGE=3;'
                  f'$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;" subject="{aid}" '
                  f'style="Mode=3;EOID={edu};SOID={sdu};Color=-1;LWidth=0;Hidden=0;"/>')

    dname = "REQ_" + (sids[0] if len(sids) == 1 else "Selected_Requirements")
    did = diagram_identity(idmap, dname)
    diag_tv = [
        ("version", "1.0"), ("author", AUTHOR), ("package", PKG), ("type", "Custom"),
        ("ea_localid", "1"),
        ("styleex", "MDGDgm=SysML1.4::Requirement;ShowNotes=0;"),
    ]
    diag_tvs = "\n".join(f'\t\t\t\t<UML:TaggedValue tag="{k}" value="{v}"/>' for k, v in diag_tv)

    pkg_tv = [
        ("ea_package_id", "3"), ("iscontrolled", "FALSE"), ("version", "1.0"),
        ("isprotected", "FALSE"), ("packageFlags", "isModel=1;VICON=3;CRC=0;"),
        ("phase", "1.0"), ("status", "Proposed"), ("author", AUTHOR),
        ("ea_stype", "Public"),
    ]
    pkg_tvs = "\n".join(f'\t\t\t\t\t\t<UML:TaggedValue tag="{k}" value="{v}"/>' for k, v in pkg_tv)

    # 内容级 id/text taggedValue(EA 需求的外部编号与 Text 字段，用属性类型 GUID 前缀)
    reqtext = []
    for (rid, ext_id, text) in meta:
        reqtext.append(f'\t\t{req_id_value(ext_id, rid)}\n\t\t{req_text_value(text, rid)}')
    reqtext_block = "\n".join(reqtext + extra_tags)

    coll_id = idmap["collaboration"] or new_guid()[0]
    idmap["collaboration"] = coll_id
    xml = assemble_xml(roles=roles, assocs=assocs, reqtext_block=reqtext_block,
                       diag_elements=de, dname=dname, did=did, diag_tvs=diag_tvs,
                       pkg_tvs=pkg_tvs, coll_id=coll_id)

    # 规范九.4 静态验收：有问题则不交付；通过仅代表结构契约成立
    problems = validate_xmi(xml, n_reqs=len(diag_nodes), n_edges=len(diag_edges))
    if unknown_grades:
        print("[验收] 显式报告——以下工程需求没有 A/B/C/X 等级"
              "（图上用 EA 默认色，未按等级着色，灰色仅表示源需求）:")
        for u in unknown_grades:
            print("  - " + u)
    if problems:
        print("[验收] 静态检查未通过，文件未写出:")
        for p in problems:
            print("  - " + p)
        raise SystemExit(1)

    if review_out is not None:
        review_out.extend(review_rows)
    return xml


def main():
    ap = argparse.ArgumentParser(description="Offline EA export; no paid translation calls")
    ap.add_argument("--sets", nargs="*", default=["OR041", "OR052", "OR008"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--compact", action="store_true", help="Presentation-only labels; full properties retained")
    ap.add_argument("--input-xmi", help="Transform an audited detailed XMI; preserves its exact IDs, links and DUIDs")
    ap.add_argument("--identity-map", help="Reuse detailed model IDs in a new independent export directory")
    ap.add_argument("--per-row", type=int, default=4)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir).resolve()
    if out == EXP.resolve() or ROOT.parent / "paper_wiley_submission_to_be_revised" in out.parents:
        raise SystemExit("Use an independent revision artifact directory")
    out.mkdir(parents=True, exist_ok=True)
    if args.input_xmi:
        if not args.compact: raise SystemExit("--input-xmi requires --compact")
        from cooling_rag_mg.ea_compact import compact_xml, validate_compact
        source=Path(args.input_xmi).resolve()
        original=source.read_text(encoding="utf-8")
        xml=compact_xml(original,GRADE_STYLE)
        tree=ET.fromstring(original)
        n=len(tree.findall(".//{omg.org/UML1.3}ClassifierRole"))
        edges=len(tree.findall(".//{omg.org/UML1.3}Association"))
        errors=validate_compact(original,xml,GRADE_STYLE)+validate_xmi(xml,n_reqs=n,n_edges=edges,compact=True)
        if errors: raise SystemExit(str(errors))
        destination=out/(source.stem+"_compact.xml")
        if destination==source or destination.exists(): raise SystemExit("Refusing overwrite; select a fresh output directory")
        destination.write_text(xml,encoding="utf-8")
        print(f"STATIC PASS: {n} requirements / {edges} links; {destination}; native EA import not tested")
        return
    orig = {u["requirement_id"]:u for u in map(json.loads, ORIG.read_text(encoding="utf-8").splitlines())}
    kb = {u["id"]:u for u in map(json.loads, KB_AUDITED.read_text(encoding="utf-8").splitlines())}
    by_sid = {r["source_requirement_id"]:r for r in json.loads(RAG.read_text(encoding="utf-8"))["result_sets"]}
    wanted = list(by_sid) if args.all else args.sets
    missing = set(wanted)-set(by_sid)
    if missing: raise SystemExit(f"Unknown source IDs: {missing}")
    sets = [dict(by_sid[sid], _source_text=orig[sid]["requirement_text"]) for sid in wanted]
    legacy = _load_json(LLM_CACHE_PATH, {})
    cache_path = out / "ea_translation_cache.json"
    cache = _load_json(cache_path, {})
    titles, tr = {}, {}
    for rs in sets:
        sid=rs["source_requirement_id"]
        items=[(f"T_{sid}",rs["_source_text"])]
        title_items=[(f"S_{sid}",rs["_source_text"])]
        for k,er in enumerate(rs["engineering_requirements"],1):
            title_items.append((f"E_{sid}_{k}",er.get("shall_statement", "")))
            for prefix,field in [("H","shall_statement"),("C","measurable_criterion"),("V","verification_method")]:
                items.append((f"{prefix}_{sid}_{k}",str(er.get(field) or "")))
        for section, entries, dest in [("trans",items,tr),("titles",title_items,titles)]:
            for key,source in entries:
                digest=hashlib.sha1(source.encode("utf-8")).hexdigest()
                ck=section+":"+digest
                record=cache.get(ck)
                candidate=record["value"] if record else legacy.get(section,{}).get(key,source if section=="trans" else "Engineering Requirement")
                if section=="trans": candidate=safe_translation(source,candidate)
                else:
                    candidate=" ".join(re.findall(r"[A-Za-z]+",candidate)[:6]) or "Engineering Requirement"
                dest[key]=candidate
                cache[ck]={"value":candidate,"source_sha1":digest,"provenance":"legacy_cache_unverified_or_source_fallback","human_translation_review_required":True}
    idpath=out/"ea_identity_map.json"
    idmap=load_identity(Path(args.identity_map) if args.identity_map else idpath)
    review=[]
    xml=build_xmi(sets,kb,titles,tr,args.per_row,idmap=idmap,review_out=review)
    tag=wanted[0] if len(wanted)==1 else "sel"
    if args.compact:
        from cooling_rag_mg.ea_compact import compact_xml, validate_compact
        detailed=xml
        xml=compact_xml(detailed,GRADE_STYLE)
        problems=validate_compact(detailed,xml,GRADE_STYLE)+validate_xmi(xml,n_reqs=len(sets)+len(review),n_edges=len(review),compact=True)
        if problems: raise SystemExit("Compact validation failed: "+str(problems))
        tag += "_compact"
    (out/f"ea_native_{tag}.xml").write_text(xml,encoding="utf-8")
    with (out/f"ea_review_{tag}.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(review[0])); w.writeheader(); w.writerows(review)
    save_identity(idmap,idpath)
    cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"STATIC PASS: {len(sets)+len(review)} requirements, {len(review)} Nesting edges; output {out}. EA import not yet verified.")


if __name__ == "__main__":
    main()
