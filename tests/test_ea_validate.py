"""按《EA_XML生成规范.txt》第九节静态验收：生成的 XMI 必须通过确定性校验，
不能只凭"XML 可解析"宣称成功；身份映射与标题缓存保证重复生成是更新语义，
样式调整不得重新调用模型改写需求。"""
import re
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ea", Path("scripts/92_export_ea_native_xmi.py"))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)


def _mini_xml(mut=None):
    """用生成器的确定性部件拼一个最小合规文档（1 父 1 子 1 连线 + 包络框）。"""
    rid, rguid = ea.new_guid(); cid, cguid = ea.new_guid()
    pdu, cdu, pkg_du = ea.duid(), ea.duid(), ea.duid()
    aid, _ = ea.new_guid(); did, _ = ea.new_guid(); coll, _ = ea.new_guid()
    roles = [ea.classifier_role("OR001  Src req", rid, rguid, 10, "src notes", grade="_src"),
             ea.classifier_role("OR001.1  Child req", cid, cguid, 11, "child notes", grade="B")]
    assocs = [ea.association(aid, 12, rid, 10, "OR001  Src req", cid, 11, "OR001.1  Child req")]
    reqtext = ("\t\t" + ea.req_id_value("OR001", rid)
               + "\n\t\t" + ea.req_text_value("full source text", rid)
               + "\n\t\t" + ea.req_id_value("OR001.1", cid)
               + "\n\t\t" + ea.req_text_value("full child text", cid))
    pkg_tvs = '\t\t\t\t\t\t<UML:TaggedValue tag="version" value="1.0"/>'
    diag_tvs = ('\t\t\t\t<UML:TaggedValue tag="styleex" '
                'value="MDGDgm=SysML1.4::Requirement;ShowNotes=0;"/>')
    de = [
        f'\t\t\t\t<UML:DiagramElement geometry="Left=70;Top=30;Right=180;Bottom=200;" '
        f'subject="{rid}" seqno="1" style="DUID={pdu};{ea.DIAG_ELEM_STYLE}"/>',
        f'\t\t\t\t<UML:DiagramElement geometry="Left=40;Top=270;Right=150;Bottom=440;" '
        f'subject="{cid}" seqno="2" style="DUID={cdu};{ea.DIAG_ELEM_STYLE}"/>',
        f'\t\t\t\t<UML:DiagramElement geometry="Left=10;Top=10;Right=210;Bottom=470;" '
        f'subject="{ea.PKG}" seqno="3" style="DUID={pkg_du};NSL=1;"/>',
        f'\t\t\t\t<UML:DiagramElement geometry="SX=0;SY=0;EX=0;EY=0;EDGE=3;'
        f'$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;" subject="{aid}" '
        f'style="Mode=3;EOID={cdu};SOID={pdu};Color=-1;LWidth=0;Hidden=0;"/>',
    ]
    xml = ea.assemble_xml(roles=roles, assocs=assocs, reqtext_block=reqtext,
                          diag_elements=de, dname="REQ_Test", did=did,
                          diag_tvs=diag_tvs, pkg_tvs=pkg_tvs, coll_id=coll)
    return mut(xml) if mut else xml


def test_validate_accepts_minimal_document():
    assert ea.validate_xmi(_mini_xml(), n_reqs=2, n_edges=1) == []


def test_validate_rejects_duplicate_xmi_id():
    def mut(xml):
        # 把连线的 xmi.id 改成父需求的 id：重复且导致 subject 悬空
        aid = re.search(r'<UML:Association xmi\.id="([^"]+)"', xml).group(1)
        rid = re.search(r'xmi\.id="([^"]+)"', xml).group(1)
        return xml.replace(f'<UML:Association xmi.id="{aid}"',
                           f'<UML:Association xmi.id="{rid}"')
    probs = ea.validate_xmi(_mini_xml(mut), n_reqs=2, n_edges=1)
    assert any("重复" in p for p in probs)


def test_validate_rejects_dangling_connector_duid():
    def mut(xml):
        return re.sub(r'SOID=[0-9A-F]{8};', 'SOID=DEADBEEF;', xml, count=1)
    probs = ea.validate_xmi(_mini_xml(mut), n_reqs=2, n_edges=1)
    assert any("DUID" in p for p in probs)


def test_validate_rejects_overlapping_boxes():
    def mut(xml):
        return xml.replace("Left=40;Top=270;Right=150;Bottom=440;",
                           "Left=70;Top=30;Right=180;Bottom=200;")
    probs = ea.validate_xmi(_mini_xml(mut), n_reqs=2, n_edges=1)
    assert any("相交" in p for p in probs)


def test_validate_rejects_double_escaped_memo():
    def mut(xml):
        return xml.replace("&lt;memo&gt;#NOTES#full child",
                           "&amp;lt;memo&amp;gt;#NOTES#full child")
    probs = ea.validate_xmi(_mini_xml(mut), n_reqs=2, n_edges=1)
    assert any("二次转义" in p for p in probs)


def test_validate_rejects_missing_text_property():
    def mut(xml):
        cid = re.findall(r'<UML:ClassifierRole name="[^"]*" xmi\.id="([^"]+)"', xml)[1]
        return re.sub(r'\s*<UML:TaggedValue tag="text"[^>]*modelElement="' + cid + r'"/>',
                      "", xml)
    probs = ea.validate_xmi(_mini_xml(mut), n_reqs=2, n_edges=1)
    assert any("text" in p for p in probs)


def test_unknown_grade_uses_ea_default_style_not_source_grey():
    """规范五：未知等级显式报告，用 EA 默认色(-1)，不得借源需求灰隐式表示。"""
    xml = ea.classifier_role("OR009.1  No grade", "EAID_R", "{G}", 10, "notes", grade="Q")
    assert "BackColor=-1" in xml
    assert f"BackColor={ea._cr(232, 232, 232)}" not in xml  # 源需求灰


def test_titles_are_cached_and_not_regenerated_for_style_only_changes(tmp_path, monkeypatch):
    """规范四：标题缓存可审核；仅调整样式时不得重新调用模型。"""
    calls = {"n": 0}

    def fake_llm(prompt, system, max_tokens=3000):
        calls["n"] += 1
        return {"S_OR999": "Fresh water cooling"}

    monkeypatch.setattr(ea, "_llm_json", fake_llm)
    cache = tmp_path / "llm_cache.json"
    t1 = ea.gen_titles([("S_OR999", "淡水冷却")], cache_path=cache)
    assert t1["S_OR999"] == "Fresh water cooling" and calls["n"] == 1

    def boom(*a, **k):
        raise RuntimeError("must not be called for cached items")

    monkeypatch.setattr(ea, "_llm_json", boom)
    t2 = ea.gen_titles([("S_OR999", "淡水冷却")], cache_path=cache)
    assert t2["S_OR999"] == "Fresh water cooling"


def test_identity_map_stable_across_runs(tmp_path):
    """规范三：业务编号 -> GUID 稳定映射，重复生成复用身份，新对象才分配新身份。"""
    p = tmp_path / "identity.json"
    m1 = ea.load_identity(p)
    x1, g1 = ea.elem_identity(m1, "OR041")
    ea.save_identity(m1, p)
    m2 = ea.load_identity(p)
    assert ea.elem_identity(m2, "OR041") == (x1, g1)
    x3, _ = ea.elem_identity(m2, "OR052")
    assert x3 != x1
