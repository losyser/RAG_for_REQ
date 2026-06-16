"""
导出 Enterprise Architect 可导入的需求模型。

产出两份(放到 data/search_results/exp_v4/):
  1) ea_requirements.xmi  —— XMI 2.1 (UML)，每个源需求一个 package：
        源需求(父 «requirement») + 工程需求(子 «requirement») + «deriveReqt» 依赖；
        grade / criterion / source / verification 作为 EA tagged values。
        EA 导入：Project > Model Import/Export > Import Package from XMI File。
  2) ea_requirements.csv  —— 需求表(EA CSV 导入最稳)：
        EA: Specification Manager / Requirements > Import CSV。

数据源：data/search_results/exp_v4/rag_v4_results.json + original_requirements_v2.jsonl
仅导出 RAG 臂(可溯源)结果。
"""
from __future__ import annotations
import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "data" / "search_results" / "exp_v4"
RAG = EXP / "rag_v4_results.json"
ORIG = ROOT / "data" / "processed" / "original_requirements_v2.jsonl"
OUT_XMI = EXP / "ea_requirements.xmi"
OUT_CSV = EXP / "ea_requirements.csv"

UML = "http://schema.omg.org/spec/UML/2.1"
XMINS = "http://schema.omg.org/spec/XMI/2.1"


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def xid(s: str) -> str:
    """合法 XMI id：字母数字下划线。"""
    return "EAID_" + re.sub(r"[^0-9A-Za-z]", "_", str(s))


def cite_str(cits) -> str:
    out = []
    for c in cits or []:
        if isinstance(c, dict):
            out.append(c.get("kb_id", ""))
        elif isinstance(c, str):
            m = re.search(r"E-[A-Z0-9]+-[A-Z0-9]+-\d+", c)
            out.append(m.group(0) if m else c)
    return "; ".join(x for x in out if x)


def main() -> None:
    orig = {}
    for line in ORIG.open(encoding="utf-8"):
        r = json.loads(line)
        orig[r["requirement_id"]] = r
    data = json.loads(RAG.read_text(encoding="utf-8"))

    elements: list[str] = []      # packagedElement XML 片段
    ea_elem_ext: list[str] = []   # EA extension: element 节点(打 stereotype)
    ea_tag_ext: list[str] = []    # EA extension: tagged values
    csv_rows: list[dict] = []

    def add_tag(elem_id: str, name: str, value: str):
        if value:
            ea_tag_ext.append(
                f'      <tag xmi:id="{xid(elem_id+"_"+name)}" name="{esc(name)}" '
                f'value="{esc(value)}" modelElement="{elem_id}"/>'
            )

    def add_req(elem_id: str, name: str, notes: str, etype: str):
        elements.append(
            f'      <packagedElement xmi:type="uml:Class" xmi:id="{elem_id}" name="{esc(name)}">\n'
            f'        <ownedComment xmi:type="uml:Comment" xmi:id="{xid(elem_id+"_note")}" '
            f'body="{esc(notes)}"/>\n'
            f'      </packagedElement>'
        )
        ea_elem_ext.append(
            f'      <element xmi:idref="{elem_id}" xmi:type="uml:Class" name="{esc(name)}" '
            f'scope="public">\n'
            f'        <properties stereotype="requirement"/>\n'
            f'        <stereotype stereotype="requirement"/>\n'
            f'      </element>'
        )

    for rs in data["result_sets"]:
        sid = rs["source_requirement_id"]
        sid_norm = sid if sid.startswith("OR") else "OR" + sid
        src = orig.get(sid, {})
        src_text = src.get("requirement_text", "")
        stakeholder = src.get("stakeholder", rs.get("stakeholder", ""))
        pkg_id = xid("pkg_" + sid)
        src_id = xid("req_" + sid)

        pkg_inner: list[str] = []
        # 父：源需求
        add_req(src_id, f"{sid_norm} (source)", src_text, "source")
        add_tag(src_id, "type", "source requirement")
        add_tag(src_id, "stakeholder", stakeholder)
        csv_rows.append({"ID": sid_norm, "Name": (src_text[:60] or sid_norm),
                         "Type": "source", "Parent": "", "Grade": "",
                         "Criterion": "", "Source": "", "Notes": src_text})
        # 把父需求片段移入本 package
        src_frag = elements.pop()

        child_frags = []
        derive_frags = []
        for k, er in enumerate(rs.get("engineering_requirements", []), 1):
            eid = f"{sid_norm}-ER{k}"
            elem_id = xid("req_" + eid)
            shall = er.get("shall_statement", "")
            crit = er.get("measurable_criterion", "")
            grade = er.get("_grade", "")
            verif = er.get("verification_method", "")
            src_ref = cite_str(er.get("evidence_citations"))
            notes = (f"{shall}\nCriterion: {crit}\nGrade: {grade}\n"
                     f"Verification: {verif}\nCited evidence: {src_ref}")
            add_req(elem_id, f"{eid} [{grade}]", notes, "engineering")
            child_frags.append(elements.pop())
            add_tag(elem_id, "grade", grade)
            add_tag(elem_id, "measurable_criterion", str(crit))
            add_tag(elem_id, "verification_method", verif)
            add_tag(elem_id, "cited_evidence", src_ref)
            # «deriveReqt» 依赖：子 -> 父
            dep_id = xid("der_" + eid)
            derive_frags.append(
                f'      <packagedElement xmi:type="uml:Abstraction" xmi:id="{dep_id}" '
                f'name="deriveReqt" client="{elem_id}" supplier="{src_id}"/>'
            )
            ea_elem_ext.append(
                f'      <connector xmi:idref="{dep_id}">\n'
                f'        <properties ea_type="Abstraction" stereotype="deriveReqt"/>\n'
                f'        <source xmi:idref="{elem_id}"/><target xmi:idref="{src_id}"/>\n'
                f'      </connector>'
            )
            csv_rows.append({"ID": eid, "Name": (shall[:60] or eid),
                             "Type": "engineering", "Parent": sid_norm, "Grade": grade,
                             "Criterion": str(crit), "Source": src_ref, "Notes": notes})

        pkg_inner = [src_frag] + child_frags + derive_frags
        elements.append(
            f'    <packagedElement xmi:type="uml:Package" xmi:id="{pkg_id}" '
            f'name="{esc(sid_norm)}">\n' + "\n".join(pkg_inner) + "\n    </packagedElement>"
        )

    xmi = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<xmi:XMI xmi:version="2.1" xmlns:uml="{UML}" xmlns:xmi="{XMINS}">\n'
        '  <xmi:Documentation exporter="cooling_rag_mg" exporterVersion="1.0"/>\n'
        '  <uml:Model xmi:type="uml:Model" name="ShipCoolingRequirements">\n'
        + "\n".join(elements) + "\n"
        '  </uml:Model>\n'
        '  <xmi:Extension extender="Enterprise Architect" extenderID="6.5">\n'
        '    <elements>\n' + "\n".join(ea_elem_ext) + "\n    </elements>\n"
        '    <tags>\n' + "\n".join(ea_tag_ext) + "\n    </tags>\n"
        '  </xmi:Extension>\n'
        '</xmi:XMI>\n'
    )
    OUT_XMI.write_text(xmi, encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ID", "Name", "Type", "Parent", "Grade",
                                          "Criterion", "Source", "Notes"])
        w.writeheader()
        w.writerows(csv_rows)

    n_src = len(data["result_sets"])
    n_er = sum(len(rs.get("engineering_requirements", [])) for rs in data["result_sets"])
    print(f"XMI 写入: {OUT_XMI}  ({n_src} 源需求 + {n_er} 工程需求)")
    print(f"CSV 写入: {OUT_CSV}  ({len(csv_rows)} 行)")


if __name__ == "__main__":
    main()
