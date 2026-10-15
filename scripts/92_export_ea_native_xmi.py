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
import argparse, html, json, re, sys, textwrap, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.review_routing import derivation_type, review_route  # noqa: E402

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
}


def classifier_role(name, rid, guid, lid, notes, grade="_src") -> str:
    back, border = GRADE_STYLE.get(grade, GRADE_STYLE["_src"])
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
    """
    return (f"{wrap_cn(shall, width)}\n"
            f"Criterion: {wrap_cn(str(crit), width)}\n"
            f"Grade: {grade}\n"
            f"Derivation: {derivation}\n"
            f"Route: {route} --- {wrap_cn(route_reason, width)}\n"
            f"Verification: {wrap_cn(verif, width)}\n"
            f"Cited: {wrap_cn(cited, width)}")


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


def gen_titles(items: list[tuple[str, str]]) -> dict[str, str]:
    """items=[(key, 中文文本)]；用 DeepSeek 一次生成简短**英文**概括标题。失败则兜底。"""
    try:
        listing = "\n".join(f"{k}: {t}" for k, t in items)
        prompt = (
            "For each ship cooling-water requirement below, produce a concise **English** "
            "title: a noun phrase of at most 6 words, **no digits, units, placeholders "
            "({{...}}) or citations**. Return ONLY a JSON object keyed by the IDs I gave, "
            "values are the titles.\n\n" + listing
        )
        titles = _llm_json(prompt, "You are a marine systems-engineering expert. Be concise.")
    except Exception as exc:  # noqa
        print(f"[titles] LLM failed, using fallback: {exc}")
        titles = {}
    out = {}
    for k, t in items:
        v = str(titles.get(k, "")).strip()
        out[k] = re.sub(r"[0-9{}|]", "", v)[:40] or short_fallback(t)
    return out


def translate_en(items: list[tuple[str, str]]) -> dict[str, str]:
    """items=[(key, 中文文本)]；忠实英译。失败则保留原文。"""
    try:
        listing = "\n".join(f"{k}: {t}" for k, t in items)
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
    except Exception as exc:  # noqa
        print(f"[translate] LLM failed, keeping source text: {exc}")
        tr = {}
    return {k: (str(tr.get(k, "")).strip() or t) for k, t in items}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="*", default=["OR041", "OR052", "OR008"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--per-row", type=int, default=4,
                    help="子需求每行最多几个（0 = 全部排成一行，即旧版布局）")
    args = ap.parse_args()

    orig = {json.loads(l)["requirement_id"]: json.loads(l) for l in ORIG.open(encoding="utf-8")}
    kb = {json.loads(l)["id"]: json.loads(l) for l in KB_AUDITED.open(encoding="utf-8")}
    data = json.loads(RAG.read_text(encoding="utf-8"))
    by_sid = {rs["source_requirement_id"]: rs for rs in data["result_sets"]}
    sids = list(by_sid) if args.all else [s for s in args.sets if s in by_sid]
    if not sids:
        raise SystemExit(f"未找到指定源需求；可选: {list(by_sid)[:5]}...")

    # 预生成英文概括标题(name 用) + 正文英译
    title_items, trans_items = [], []
    for sid in sids:
        rs = by_sid[sid]
        st = orig.get(sid, {}).get("requirement_text", "")
        title_items.append((f"S_{sid}", st))
        trans_items.append((f"T_{sid}", st))
        for k, er in enumerate(rs.get("engineering_requirements", []), 1):
            sh = er.get("shall_statement", "")
            title_items.append((f"E_{sid}_{k}", sh))
            trans_items.append((f"H_{sid}_{k}", sh))
            trans_items.append((f"V_{sid}_{k}", er.get("verification_method", "")))
            trans_items.append((f"C_{sid}_{k}", str(er.get("measurable_criterion", ""))))
    titles = gen_titles(title_items)
    tr = translate_en(trans_items)

    roles, assocs, diag_nodes, diag_edges, meta = [], [], [], [], []
    lid = 10
    y0 = 30
    bw, bh, gapx, gapy = 300, 200, 350, 320
    y_cursor = y0
    WRAP = 34
    for si, sid in enumerate(sids, 1):
        rs = by_sid[sid]
        ev_values = rs.get("_evidence_values") or {}
        sid_norm = sid if sid.startswith("OR") else "OR" + sid
        src_text = tr.get(f"T_{sid}", orig.get(sid, {}).get("requirement_text", ""))
        pid, pguid = new_guid(); plid = lid; lid += 1
        pdu = duid()
        pname = f"{sid_norm}  {titles.get('S_'+sid, '')}"
        roles.append(classifier_role(pname, pid, pguid, plid,
                                     wrap_cn(f"[Source requirement] {src_text}", WRAP)))
        meta.append((pid, sid_norm, wrap_cn("[Source requirement] " + src_text, WRAP)))
        ers = rs.get("engineering_requirements", [])
        # 父框居中；子需求按 --per-row 换行，组与组之间留一个 gapy
        (px, py), kid_xy, group_h = group_layout(len(ers), per_row=args.per_row, y_top=y_cursor,
                                                bw=bw, gapx=gapx, gapy=gapy)
        y_cursor += group_h + gapy
        diag_nodes.append((pid, pdu, px, py, px + bw, py + bh))
        for k, er in enumerate(ers, 1):
            cid, cguid = new_guid(); clid = lid; lid += 1
            cdu = duid()
            grade = er.get("_grade", "")
            crit = tr.get(f"C_{sid}_{k}", str(er.get("measurable_criterion", "")))
            shall = tr.get(f"H_{sid}_{k}", er.get("shall_statement", ""))
            verif = tr.get(f"V_{sid}_{k}", er.get("verification_method", ""))
            cname = f"{sid_norm}.{k}  {titles.get(f'E_{sid}_{k}', '')}"
            deriv = derivation_type(er, kb)
            route, route_reason = review_route(er, kb, ev_values)
            notes = er_notes(shall, crit, grade, verif,
                             cite_ids(er.get("evidence_citations")),
                             deriv, route, route_reason, WRAP)
            roles.append(classifier_role(cname, cid, cguid, clid, notes, grade=grade))
            meta.append((cid, f"{sid_norm}.{k}",
                         wrap_cn(f"{shall} (criterion: {crit}; grade: {grade}; "
                                 f"derivation: {deriv}; route: {route})", WRAP)))
            aid, _ = new_guid(); alid = lid; lid += 1
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
                  f'subject="{eid}" seqno="{seq}" style="DUID={du};HideIcon=0;UCRect=1;Tag=1;'
                  f'AttCustom=0;OpCustom=0;RzO=1;"/>')
        seq += 1
    de.append(f'\t\t\t\t<UML:DiagramElement geometry="Left=10;Top=10;Right={allx2+30};'
              f'Bottom={ally2+30};" subject="{PKG}" seqno="{seq}" style="DUID={pkg_du};NSL=1;"/>')
    for (aid, sdu, edu) in diag_edges:
        de.append(f'\t\t\t\t<UML:DiagramElement geometry="SX=0;SY=0;EX=0;EY=0;EDGE=3;'
                  f'$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;" subject="{aid}" '
                  f'style="Mode=3;EOID={edu};SOID={sdu};Color=-1;LWidth=0;Hidden=0;"/>')

    did, _ = new_guid()
    dname = "REQ_" + (sids[0] if len(sids) == 1 else "Selected_Requirements")
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

    # 内容级 id/text taggedValue(EA 需求的外部编号与 Text 字段)
    reqtext = []
    for (rid, ext_id, text) in meta:
        tid1, _ = new_guid(); tid2, _ = new_guid()
        reqtext.append(
            f'\t\t<UML:TaggedValue tag="id" xmi.id="{tid1}" value="{esc(ext_id)}" '
            f'modelElement="{rid}"/>\n'
            f'\t\t<UML:TaggedValue tag="text" xmi.id="{tid2}" '
            f'value="&lt;memo&gt;#NOTES#{esc(text)}" modelElement="{rid}"/>'
        )
    reqtext_block = "\n".join(reqtext)

    coll_id, _ = new_guid()
    xml = (
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
        + "\n".join(de) + "\n"
        '\t\t\t</UML:Diagram.element>\n'
        '\t\t</UML:Diagram>\n'
        '\t</XMI.content>\n'
        '\t<XMI.difference/>\n'
        '\t<XMI.extensions xmi.extender="Enterprise Architect 2.5"/>\n'
        '</XMI>\n'
    )
    tag = sids[0] if len(sids) == 1 else ("all" if args.all else "sel")
    out = EXP / f"ea_native_{tag}.xml"
    out.write_text(xml, encoding="utf-8")
    print(f"写入: {out}  ({len(diag_nodes)} 需求框, {len(diag_edges)} Nesting 连线, sets={sids})")


if __name__ == "__main__":
    main()
