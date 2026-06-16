# -*- coding: utf-8 -*-
"""
Export engineering requirements to M-design (HuaWang SysML) XMI format.

The output conforms to the HuaWang XMI schema observed in exported M-design
project files (namespaces: http://localhost/spec/XMI/20131001,
http://localhost/spec/UML/20131001, http://localhost/spec/SysML/20150709/SysML,
http://localhost/spec/UML/20131001/HuaWangProfile).

Usage::

    from cooling_rag_mg.mdesign_exporter import export_to_mdesign

    xml_bytes = export_to_mdesign(engineering_payload, project_name="冷却水系统工程需求")
    Path("output.xml").write_bytes(xml_bytes)
"""
from __future__ import annotations

import html
import time
from pathlib import Path
from typing import Any


# ── XMI text constants ─────────────────────────────────────────────────────

_UML_BASE = "http://www.omg.org/spec/UML/20131001/UML.xmi#"
_REQ_TYPE_HREF = (
    "http://www.omg.org/spec/SysML/20181001/SysML.xmi"
    "#_11_5EAPbeta_be00301_1147873190330_159934_2220"
)

_NAMESPACES = """\
 xmlns:SimulationProfile="http://www.huawang.com/schemas/SimulationProfile.xmi"\
 xmlns:Dependency_Matrix_Profile="http://www.huawang.com/schemas/Dependency_Matrix_Profile.xmi"\
 xmlns:Validation_Profile="http://www.huawang.com/schemas/Validation_Profile.xmi"\
 xmlns:StandardProfile="http://localhost/spec/UML/20131001/StandardProfile"\
 xmlns:HuaWang_Customization_for_SysML__additional_stereotypes="http://www.huawang.com/spec/Customization/180/SysML"\
 xmlns:DSL_Customization="http://www.huawang.com/schemas/DSL_Customization.xmi"\
 xmlns:uml="http://localhost/spec/UML/20131001"\
 xmlns:xmi="http://localhost/spec/XMI/20131001"\
 xmlns:project.options="http://www.huawang.com/ns/huawang/core/project/options/1.0"\
 xmlns:sysml="http://localhost/spec/SysML/20150709/SysML"\
 xmlns:ns11="http://localhost/XMI"\
 xmlns:HuaWang_Profile="http://localhost/spec/UML/20131001/HuaWangProfile"\
 xmlns:UI_Prototyping_Profile="http://www.huawang.com/schemas/UI_Prototyping_Profile.xmi"\
 xmlns:diagram="http://www.huawang.com/ns/huawang/core/diagram/1.0"\
 xmlns:project="http://www.huawang.com/ns/client/project/1.0"\
 xmlns:ns17="http://localhost/spec/UML/20161101"\
 xmlns:ns18="http://localhost/spec/SysML/20131001/SysML"\
 xmlns:xsi="http://localhost/2001/XMLSchema-instance"\
 xmlns:ns20="http://localhost/spec/UML/20131001/Profile"\
 xmlns:ns21="http://localhost/spec/MOF/20131001"\
 xmlns:ns22="http://localhost/spec/UML/20161101/StandardProfile"\
"""

# Fixed stereotypesHREFS block (copied from M-design exports)
_STEREO_HREFS = """\
<xmi:Extension><stereotypesHREFS>\
<stereotype name="DSL_Customization:NumberOwner" stereotypeHREF="#NumberOwner"/>\
<tag name="DSL_Customization:NumberOwner:customNumberingData" tagID="NumberOwner-customNumberingData"/>\
<stereotype name="HuaWang_Profile:SysMLRequirementDiagram" stereotypeHREF="#SysMLDI::SysMLRequirementDiagram"/>\
<stereotype name="HuaWang_Profile:RequirementTable" stereotypeHREF="#TableAndMatrix::CustomizeTable::RequirementTable"/>\
<tag name="HuaWang_Profile:RequirementTable:rowElements" tagID="DiagramTable-rowElements"/>\
<tag name="HuaWang_Profile:RequirementTable:rowElementType" tagID="DiagramTable-rowElementType"/>\
<tag name="HuaWang_Profile:RequirementTable:excludedElements" tagID="DiagramTable-excludedElements"/>\
<tag name="HuaWang_Profile:RequirementTable:additionalElements" tagID="DiagramTable-additionalElements"/>\
<tag name="HuaWang_Profile:RequirementTable:columnIds" tagID="DiagramTable-columnIds"/>\
<tag name="HuaWang_Profile:RequirementTable:hideColumns" tagID="DiagramTable-hideColumns"/>\
<tag name="HuaWang_Profile:RequirementTable:scope" tagID="DiagramTable-scope"/>\
<tag name="HuaWang_Profile:RequirementTable:displayMode" tagID="DiagramTable-displayMode"/>\
<tag name="HuaWang_Profile:RequirementTable:columnWidth" tagID="DiagramTable-columnWidth"/>\
<tag name="HuaWang_Profile:RequirementTable:sort" tagID="DiagramTable-sort"/>\
<tag name="HuaWang_Profile:RequirementTable:expandedRows" tagID="DiagramTable-expandedRows"/>\
<tag name="HuaWang_Profile:RequirementTable:rowFilters" tagID="DiagramTable-rowFilters"/>\
<tag name="HuaWang_Profile:RequirementTable:customColumns" tagID="DiagramTable-customColumns"/>\
<tag name="HuaWang_Profile:RequirementTable:rowsOrder" tagID="DiagramTable-rowsOrder"/>\
<tag name="HuaWang_Profile:RequirementTable:legends" tagID="DiagramTable-legends"/>\
<stereotype name="sysml:Requirement" stereotypeHREF="#SysML::Requirements::Requirement"/>\
<tag name="sysml:Requirement:Derived" tagID="SysML.AbstractRequirement.derived"/>\
<tag name="sysml:Requirement:DerivedFrom" tagID="SysML.AbstractRequirement.derivedFrom"/>\
<tag name="sysml:Requirement:Id" tagID="SysML.AbstractRequirement.id"/>\
<tag name="sysml:Requirement:Master" tagID="SysML.AbstractRequirement.master"/>\
<tag name="sysml:Requirement:RefinedBy" tagID="SysML.AbstractRequirement.refinedBy"/>\
<tag name="sysml:Requirement:SatisfiedBy" tagID="SysML.AbstractRequirement.satisfiedBy"/>\
<tag name="sysml:Requirement:Text" tagID="SysML.AbstractRequirement.text"/>\
<tag name="sysml:Requirement:TracedTo" tagID="SysML.AbstractRequirement.tracedTo"/>\
<tag name="sysml:Requirement:VerifiedBy" tagID="SysML.AbstractRequirement.verifiedBy"/>\
<tag name="sysml:Requirement:reqNo" tagID="SysML.AbstractRequirement.reqNo"/>\
<stereotype name="HuaWang_Profile:DiagramTable" stereotypeHREF="#TableAndMatrix::CustomizeTable::DiagramTable"/>\
<tag name="HuaWang_Profile:DiagramTable:rowElements" tagID="DiagramTable-rowElements"/>\
<tag name="HuaWang_Profile:DiagramTable:rowElementType" tagID="DiagramTable-rowElementType"/>\
<stereotype name="HuaWang_Profile:DiagramInfo" stereotypeHREF="#SysMLDI::DiagramInfo"/>\
<tag name="HuaWang_Profile:DiagramInfo:creationDate" tagID="DiagramInfo-creationDate"/>\
<tag name="HuaWang_Profile:DiagramInfo:author" tagID="DiagramInfo-author"/>\
<tag name="HuaWang_Profile:DiagramInfo:modificationDate" tagID="DiagramInfo-modificationDate"/>\
<tag name="HuaWang_Profile:DiagramInfo:lastModifiedBy" tagID="DiagramInfo-lastModifiedBy"/>\
</stereotypesHREFS></xmi:Extension>"""


# ── ID generators ────────────────────────────────────────────────────────────

def _make_id_gen() -> Any:
    """Return a callable that yields unique integer IDs."""
    base = int(time.time() * 1000) % (10 ** 10)
    counter = [0]

    def gen() -> str:
        counter[0] += 1
        return str(base + counter[0])

    return gen


def _make_vid_gen() -> Any:
    """Return a callable that yields short alphanumeric view IDs."""
    _CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    counter = [0]

    def gen(prefix: str = "V") -> str:
        counter[0] += 1
        n = counter[0]
        result = ""
        while n:
            result = _CHARS[n % 62] + result
            n //= 62
        return f"{prefix}-{result or '0'}"

    return gen


# ── XML escape ───────────────────────────────────────────────────────────────

def _xa(text: str) -> str:
    """Escape for XML attribute value."""
    return html.escape(str(text or ""), quote=True)


# ── Diagram fragment builders ────────────────────────────────────────────────

_FONT_PROP = (
    '<mdElement elementClass="FontProperty">'
    '<propertyID>FONT</propertyID>'
    '<propertyDescriptionID>FONT_DESCRIPTION</propertyDescriptionID>'
    '<fontName>微软雅黑</fontName>'
    '<size>12</size>'
    '<mdOwnedViews/>'
    '</mdElement>'
)

_FONT_PROP_DEFAULT = (
    '<mdElement elementClass="FontProperty">'
    '<propertyID>FONT</propertyID>'
    '<propertyDescriptionID>FONT_DESCRIPTION</propertyDescriptionID>'
    '<size>12</size>'
    '<mdOwnedViews/>'
    '</mdElement>'
)

_COLOR_PROP = (
    '<mdElement elementClass="ColorProperty">'
    '<propertyID>PEN_COLOR</propertyID>'
    '<propertyDescriptionID>PEN_COLOR_DESCRIPTION</propertyDescriptionID>'
    '<value>-6191771</value>'
    '<mdOwnedViews/>'
    '</mdElement>'
)

_TAGGED_CHOICE = (
    '<mdElement elementClass="ChoiceProperty">'
    '<propertyID>TAGGED_VALUES_DISPLAY_MODE</propertyID>'
    '<propertyDescriptionID>TAGGED_VALUES_DISPLAY_MODE_DESCRIPTION</propertyDescriptionID>'
    '<index>1</index>'
    '<mdOwnedViews/>'
    '<propertyGroup>MODE</propertyGroup>'
    '</mdElement>'
)

_OBLIQUE_CHOICE = (
    '<mdElement elementClass="ChoiceProperty">'
    '<propertyID>LINK_LINE_STYLE</propertyID>'
    '<propertyDescriptionID>LINK_LINE_STYLE_DESCRIPTION</propertyDescriptionID>'
    '<value>OBLIQUE</value>'
    '<choice>RECTILINEAR^OBLIQUE^BEZIER</choice>'
    '<index>1</index>'
    '<mdOwnedViews/>'
    '</mdElement>'
)


def _class_view(vid: str, element_id: str, x: int, y: int, w: int = 200, h: int = 80) -> str:
    return (
        f'<mdElement elementClass="Class" xmi:id="{vid}">'
        f'<elementID xmi:idref="{element_id}"/>'
        f'<properties>{_COLOR_PROP}{_FONT_PROP}{_TAGGED_CHOICE}</properties>'
        f'<geometry>{x}, {y}, {w}, {h}</geometry>'
        f'<compartment compartmentID="TAGGED_VALUES" isContentLocked="false"/>'
        f'<mdOwnedViews/>'
        f'</mdElement>'
    )


def _pkg_view(vid: str, element_id: str, x: int, y: int, w: int = 100, h: int = 60) -> str:
    return (
        f'<mdElement elementClass="Package" xmi:id="{vid}">'
        f'<elementID xmi:idref="{element_id}"/>'
        f'<properties>{_FONT_PROP_DEFAULT}</properties>'
        f'<geometry>{x}, {y}, {w}, {h}</geometry>'
        f'<compartment compartmentID="TAGGED_VALUES" isContentLocked="false"/>'
        f'<mdOwnedViews/>'
        f'</mdElement>'
    )


def _link_view(vid: str, from_vid: str, to_vid: str,
               fx: int, fy: int, tx: int, ty: int) -> str:
    return (
        f'<mdElement elementClass="ContainmentLink" xmi:id="{vid}">'
        f'<properties>{_OBLIQUE_CHOICE}</properties>'
        f'<linkFirstEndID xmi:idref="{from_vid}"/>'
        f'<linkSecondEndID xmi:idref="{to_vid}"/>'
        f'<geometry>{fx}, {fy}; {tx}, {ty}; </geometry>'
        f'<mdOwnedViews/>'
        f'</mdElement>'
    )


def _diagram_frame(vid: str, diag_id: str, canvas_w: int = 1800, canvas_h: int = 800) -> str:
    return (
        f'<mdElement elementClass="DiagramFrame" xmi:id="{vid}">'
        f'<elementID xmi:idref="{diag_id}"/>'
        f'<properties>{_FONT_PROP_DEFAULT}</properties>'
        f'<geometry>12, 5, {canvas_w}, {canvas_h}</geometry>'
        f'<compartment compartmentID="TAGGED_VALUES" isContentLocked="false"/>'
        f'<mdOwnedViews/>'
        f'</mdElement>'
    )


def _build_req_diagram(diag_id: str, pkg_id: str, root_id: str,
                       child_ids: list[str], vid_gen: Any) -> str:
    """Build the <filePart> XML fragment for one Requirement Diagram."""
    n = len(child_ids)
    cell_w = 200
    cell_h = 80
    gap_x = 30
    gap_y = 100
    total_w = max(1800, n * (cell_w + gap_x) + 100)
    canvas_h = 600

    # Layout
    pkg_x, pkg_y = 50, 50
    root_x = max(50, (total_w - cell_w) // 2)
    root_y = 180
    child_y = root_y + cell_h + gap_y

    child_start_x = max(50, (total_w - n * (cell_w + gap_x)) // 2)

    parts: list[str] = []

    # DiagramFrame
    frame_vid = vid_gen("F")
    parts.append(_diagram_frame(frame_vid, diag_id, total_w, canvas_h))

    # Package view
    pkg_vid = vid_gen("P")
    parts.append(_pkg_view(pkg_vid, pkg_id, pkg_x, pkg_y))

    # Root class view
    root_vid = vid_gen("R")
    parts.append(_class_view(root_vid, root_id, root_x, root_y))

    # ContainmentLink: pkg → root
    lnk_pr_vid = vid_gen("L")
    parts.append(_link_view(
        lnk_pr_vid, pkg_vid, root_vid,
        pkg_x + 50, pkg_y + 60,
        root_x + cell_w // 2, root_y,
    ))

    # Children
    for i, cid in enumerate(child_ids):
        cx = child_start_x + i * (cell_w + gap_x)
        cy = child_y
        child_vid = vid_gen("C")
        parts.append(_class_view(child_vid, cid, cx, cy))

        lnk_vid = vid_gen("L")
        parts.append(_link_view(
            lnk_vid, root_vid, child_vid,
            root_x + cell_w // 2, root_y + cell_h,
            cx + cell_w // 2, cy,
        ))

    inner = "".join(parts)
    header_escaped = "&lt;?xml version=&#39;1.0&#39; encoding=&#39;UTF-8&#39;?&gt;"
    return (
        f'<xmi:Extension>'
        f'<filePart name="BINARY-{diag_id}" type="XML" header="{header_escaped}">'
        f'<mdOwnedViews>{inner}</mdOwnedViews>'
        f'</filePart>'
        f'</xmi:Extension>'
    )


# ── Per-package XMI builders ─────────────────────────────────────────────────

def _build_package(
    req_set: dict[str, Any],
    pkg_idx: int,
    id_gen: Any,
    vid_gen: Any,
) -> tuple[str, str, str]:
    """
    Build model elements, stereotype applications, and diagram fileParts
    for one requirement_set.

    Returns (model_xml, stereo_xml, diagram_xml).
    """
    src_id = str(req_set.get("source_requirement_id") or f"OR{pkg_idx:03d}")
    summary = str(req_set.get("professional_summary") or src_id)[:80]
    ers: list[dict] = req_set.get("engineering_requirements") or []
    pkg_name = f"{src_id} — {summary}"

    # Generate IDs
    pkg_id = id_gen()
    diag_id = id_gen()   # Requirement Diagram
    table_id = id_gen()  # Requirement Table
    root_id = id_gen()   # top-level Class (= source requirement)

    # ER IDs and names
    child_data: list[tuple[str, str, str, str]] = []  # (xmi_id, req_id_str, name, text)
    for j, er in enumerate(ers, start=1):
        cid = id_gen()
        req_id_str = f"ER-{pkg_idx}.{j}"
        name = _xa(str(er.get("topic") or er.get("id") or f"需求{j}"))
        text = _xa(str(er.get("shall_statement") or ""))
        child_data.append((cid, req_id_str, name, text))

    child_ids = [cd[0] for cd in child_data]

    # ── Model section ────────────────────────────────────────────────────────
    nested_xml = "".join(
        f'<nestedClassifier name="{name}" nestingClass="{root_id}" '
        f'visibility="public" xmi:id="{cid}" xmi:type="uml:Class"/>'
        for cid, _, name, _ in child_data
    )

    diag_decl = (
        f'<xmi:Extension><modelExtension>'
        f'<ownedDiagram context="{pkg_id}" name="需求图" '
        f'ownerOfDiagram="{pkg_id}" visibility="public" '
        f'xmi:id="{diag_id}" xmi:type="uml:Diagram">'
        f'<xmi:Extension><diagramRepresentation>'
        f'<diagram:DiagramRepresentationObject type="Requirement Diagram" umlType="Class Diagram">'
        f'<diagramContents><binaryObject streamContentID="BINARY-{diag_id}" '
        f'xsi:type="binary:StreamIdentityBinaryObject"/></diagramContents>'
        f'</diagram:DiagramRepresentationObject>'
        f'</diagramRepresentation></xmi:Extension>'
        f'</ownedDiagram></modelExtension></xmi:Extension>'
    )

    table_decl = (
        f'<xmi:Extension><modelExtension>'
        f'<ownedDiagram context="{pkg_id}" name="需求表" '
        f'ownerDiagram="{pkg_id}" ownerOfDiagram="{pkg_id}" '
        f'xmi:id="{table_id}" xmi:type="uml:Diagram">'
        f'<xmi:Extension><diagramRepresentation>'
        f'<diagram:DiagramRepresentationObject type="Requirement Table" umlType="Class Diagram">'
        f'<diagramContents/>'
        f'</diagram:DiagramRepresentationObject>'
        f'</diagramRepresentation></xmi:Extension>'
        f'</ownedDiagram></modelExtension></xmi:Extension>'
    )

    pkg_name_safe = _xa(pkg_name)
    src_name_safe = _xa(src_id)

    model_xml = (
        f'<packagedElement name="{pkg_name_safe}" visibility="public" '
        f'xmi:id="{pkg_id}" xmi:type="uml:Package">'
        f'{diag_decl}{table_decl}'
        f'<packagedElement name="{src_name_safe}" visibility="public" '
        f'xmi:id="{root_id}" xmi:type="uml:Class">'
        f'{nested_xml}'
        f'</packagedElement>'
        f'</packagedElement>'
    )

    # ── Stereotype applications ──────────────────────────────────────────────
    numbering_data = _xa(
        '{"autoNumberName":"Multi-level","usePrefixOnOwner":true,'
        f'"prefix":"ER-{pkg_idx}.","separator":".","lastInitialValue":"1",'
        '"numberingSchemeId":"Customization::MultiLevel",'
        '"numberPropertyId":"SysML.AbstractRequirement.id",'
        '"stereotypeId":"SysML::Requirements::AbstractRequirement","unKnown":false}'
    )

    row_els = "".join(f'<rowElements href="{cid}"/>' for cid, *_ in child_data)
    row_els = f'<rowElements href="{root_id}"/>' + row_els

    stereo_xml = (
        # NumberOwner on the package
        f'<DSL_Customization:NumberOwner base_Package="{pkg_id}" '
        f'customNumberingData="{_UML_BASE}{numbering_data}" '
        f'xmi:id="{pkg_id}_application"/>'

        # Requirement Diagram stereotype
        f'<HuaWang_Profile:SysMLRequirementDiagram '
        f'base_UMLDiagram="{diag_id}" xmi:id="{diag_id}_application"/>'

        # Requirement Table stereotype
        f'<HuaWang_Profile:RequirementTable base_Diagram="{table_id}" '
        f'displayMode="{_UML_BASE}DisplayMode-Tree" '
        f'scope="{pkg_id}" '
        f'sort="{_UML_BASE}SysML.AbstractRequirement.id ascending" '
        f'xmi:id="{table_id}_application">'
        f'{row_els}'
        f'<columnWidth href="0"/><columnWidth href="96"/>'
        f'<columnIds href="{_UML_BASE}SysML.AbstractRequirement.text"/>'
        f'<columnIds href="{_UML_BASE}NamedElement-name"/>'
        f'<columnIds href="{_UML_BASE}SysML.AbstractRequirement.id"/>'
        f'<rowElementType href="{_REQ_TYPE_HREF}"/>'
        f'</HuaWang_Profile:RequirementTable>'

        # Root class: sysml:Requirement (container, no text)
        f'<sysml:Requirement Id="{_UML_BASE}ER-{pkg_idx}" '
        f'Text="{_UML_BASE}" '
        f'base_Class="{root_id}" xmi:id="{root_id}_application"/>'
    )

    # Children: sysml:Requirement with Id and Text
    for cid, req_id_str, _, text in child_data:
        stereo_xml += (
            f'<sysml:Requirement Id="{_UML_BASE}{_xa(req_id_str)}" '
            f'Text="{_UML_BASE}{text}" '
            f'base_Class="{cid}" xmi:id="{cid}_application"/>'
        )

    # ── Diagram layout ───────────────────────────────────────────────────────
    diagram_xml = _build_req_diagram(diag_id, pkg_id, root_id, child_ids, vid_gen)

    return model_xml, stereo_xml, diagram_xml


# ── Public API ───────────────────────────────────────────────────────────────

def export_to_mdesign(
    engineering_payload: dict[str, Any],
    project_name: str = "冷却水系统工程需求",
) -> bytes:
    """
    Convert the engineering requirements payload (as produced by
    engineering_requirement_agent) to M-design XMI format.

    Args:
        engineering_payload: Dict with key ``requirement_sets``.
        project_name:        Top-level model name shown in M-design.

    Returns:
        UTF-8 encoded XMI bytes ready to write to a .xml file.
    """
    id_gen = _make_id_gen()
    vid_gen = _make_vid_gen()

    model_id = id_gen()
    req_sets: list[dict] = engineering_payload.get("requirement_sets") or []

    all_model: list[str] = []
    all_stereo: list[str] = []
    all_diag: list[str] = []

    for idx, rs in enumerate(req_sets, start=1):
        m, s, d = _build_package(rs, idx, id_gen, vid_gen)
        all_model.append(m)
        all_stereo.append(s)
        all_diag.append(d)

    model_name_safe = _xa(project_name)
    model_inner = "".join(all_model)
    stereo_block = "".join(all_stereo)
    diag_block = "".join(all_diag)

    xml_str = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<xmi:XMI{_NAMESPACES}>"
        f'<uml:Model name="{model_name_safe}" xmi:id="{model_id}" xmi:type="uml:Model">'
        f"{model_inner}"
        f"</uml:Model>"
        f"{stereo_block}"
        f"{_STEREO_HREFS}"
        f"{diag_block}"
        f"</xmi:XMI>"
    )

    return xml_str.encode("utf-8")


def export_to_mdesign_file(
    engineering_payload: dict[str, Any],
    output_path: str | Path,
    project_name: str = "冷却水系统工程需求",
) -> Path:
    """Write M-design XMI to *output_path* and return the resolved path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(export_to_mdesign(engineering_payload, project_name))
    return out.resolve()
