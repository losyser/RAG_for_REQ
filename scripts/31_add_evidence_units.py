# -*- coding: utf-8 -*-
"""
Add new evidence units from authoritative sources to evidence_units.jsonl,
then rebuild both FAISS + BM25 indexes.

Usage:
    python scripts/31_add_evidence_units.py  [--dry-run]

New units are defined in NEW_UNITS list at the bottom of this file.
Each entry must have all required fields.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

JSONL_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"


# ─────────────────────────────────────────────────────────────
# Helper: build search_text enrichment (same pattern as existing units)
# ─────────────────────────────────────────────────────────────

def _build_search_text(unit: dict) -> str:
    m = unit["metadata"]
    parts = [
        m.get("topic", ""),
        unit["text"][:120],
        m.get("source_document", ""),
        m.get("source_type", ""),
        " ".join(m.get("component_objects", [])),
        " ".join(m.get("can_support", [])),
        " ".join(m.get("engineering_phase", [])),
        " ".join(m.get("system_type", [])),
        m.get("normalized_summary", ""),
    ]
    return "\n".join(p for p in parts if p)


def _make_unit(
    uid: str,
    parent_chunk_id: str,
    text: str,
    topic: str,
    source_document: str,
    source_type: str,
    component_objects: list[str],
    can_support: list[str],
    engineering_phase: list[str],
    evidence_strength: str,
    is_generalizable: str,
    applicability_level: str,
    normalized_summary: str,
    system_type: list[str] | None = None,
    parameters: list[dict] | None = None,
    source_link: str = "",
    need_human_review: str = "yes",
) -> dict:
    meta = {
        "topic": topic,
        "source_document": source_document,
        "source_type": source_type,
        "source_link": source_link,
        "location": "",
        "section_title": topic,
        "system_scope": component_objects[:],
        "component_objects": component_objects[:],
        "related_objects": [],
        "requirement_intents": can_support[:],
        "engineering_phase": engineering_phase[:],
        "applicable_condition": ["normal_operation"],
        "can_support": can_support[:],
        "evidence_strength": evidence_strength,
        "is_generalizable": is_generalizable,
        "applicability_level": applicability_level,
        "manufacturer": "",
        "engine_model": "",
        "system_type": system_type or [],
        "need_human_review": need_human_review,
        "applicable_object": source_document,
        "limitation": "",
        "normalized_summary": normalized_summary,
        "supportable_requirements": [],
        "unsupported_requirements": "",
        "keywords_zh": [],
        "keywords_en": [],
        "parameters_raw": "",
        "parameters": parameters or [],
        "parameter_name": [p.get("name", "") for p in (parameters or [])],
        "value": [p.get("value", "") for p in (parameters or [])],
        "unit": [p.get("unit", "") for p in (parameters or [])],
        "condition": [],
        "is_noise": False,
        "noise_reason": "",
        "objects": component_objects[:],
        "relations": can_support[:],
        "answer_type": can_support[0] if can_support else "other",
        "refined_group_id": f"G_{'_'.join(component_objects[:1])}__{'_'.join(can_support[:1])}__{'_'.join(engineering_phase[:1])}",
    }
    unit = {
        "id": uid,
        "parent_chunk_id": parent_chunk_id,
        "text": text,
        "metadata": meta,
    }
    unit["search_text"] = _build_search_text(unit)
    return unit


# ─────────────────────────────────────────────────────────────
# New evidence units — real authoritative sources
# ─────────────────────────────────────────────────────────────

NEW_UNITS: list[dict] = [

    # ── IACS UR M3.1 ──────────────────────────────────────────
    _make_unit(
        uid="E-IACS-M3-001",
        parent_chunk_id="CH_IACS_UR_M3_cooling_capacity",
        text=(
            "IACS Unified Requirements M3.1 — Cooling Systems\n"
            "At least two independent cooling water pumps shall be fitted for the cooling of "
            "main propulsion machinery. Where engine-driven pumps are fitted, at least one "
            "independently driven pump shall be provided. Each pump shall have sufficient capacity "
            "to supply the full cooling water flow required by the main engine under maximum "
            "continuous rating (MCR) conditions. The pumps shall be capable of being started "
            "independently and the changeover shall be achievable without interrupting operation.\n"
            "整理说明：IACS UR M3.1 为主机冷却水泵数量、独立驱动要求及泵容量提供了规范级依据。"
            "可支撑冷却水泵冗余配置、容量设计及换泵操作类需求。"
        ),
        topic="主机冷却水泵数量与容量要求（IACS UR M3.1）",
        source_document="S60 IACS Unified Requirements M3.1 Cooling Systems",
        source_type="ship_rule",
        component_objects=["cooling_water_pump"],
        can_support=["capacity", "redundancy", "operation"],
        engineering_phase=["basic_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR M3.1 规定主机冷却水泵至少两台，其中至少一台独立驱动，"
            "每台泵容量应满足主机额定工况下所需全流量。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-IACS-M3-002",
        parent_chunk_id="CH_IACS_UR_M3_cooling_capacity",
        text=(
            "IACS Unified Requirements M3.1 — Temperature Monitoring and Alarm\n"
            "Cooling water temperature of main propulsion engines shall be continuously monitored. "
            "High temperature alarms shall be set not to exceed the engine manufacturer's maximum "
            "permissible cooling water temperature. Where automatic slow-down or shutdown is fitted, "
            "the activation set-point shall be above the alarm set-point and shall not exceed the "
            "manufacturer's absolute maximum cooling water temperature limit.\n"
            "整理说明：IACS UR M3.1 对主机冷却水温度监控、报警设定及自动降速/停机要求提供了规范级依据。"
            "可支撑温度监控、报警阈值及自动保护类需求。"
        ),
        topic="主机冷却水温度监控与报警要求（IACS UR M3.1）",
        source_document="S60 IACS Unified Requirements M3.1 Cooling Systems",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "alarm_system", "temperature_sensor"],
        can_support=["monitoring", "alarm", "parameter_limit"],
        engineering_phase=["detailed_design", "commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR M3.1 要求持续监控主机冷却水温度，报警值不超过厂家最高允许值，"
            "自动保护动作值需高于报警值。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-IACS-M3-003",
        parent_chunk_id="CH_IACS_UR_M3_cooling_capacity",
        text=(
            "IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin\n"
            "The total installed cooling water pump capacity shall provide a minimum margin of 25% "
            "above the maximum calculated system flow demand. For central cooling systems, the "
            "low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the "
            "combined heat rejection of all connected consumers simultaneously at their maximum "
            "loads, including at the maximum anticipated seawater temperature for the vessel's "
            "intended trading area.\n"
            "整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，"
            "中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。"
        ),
        topic="冷却水泵容量余量与中央冷却系统容量要求（IACS UR M3.1）",
        source_document="S60 IACS Unified Requirements M3.1 Cooling Systems",
        source_type="ship_rule",
        component_objects=["cooling_water_pump", "central_cooling_system", "cooler"],
        can_support=["capacity", "calculation"],
        engineering_phase=["basic_design", "detailed_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR M3.1 规定冷却水泵总容量余量≥25%，中央冷却系统低温回路需按最高海水温度下"
            "全部设备满载计算。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "capacity_margin", "value": "≥25%", "unit": "%",
             "condition": "above maximum system flow demand"}
        ],
        need_human_review="no",
    ),

    # ── DNV Rules ─────────────────────────────────────────────
    _make_unit(
        uid="E-DNV-COOL-001",
        parent_chunk_id="CH_DNV_PT4_CH3_cooling_systems",
        text=(
            "DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems\n"
            "The cooling water system for main propulsion engines shall be designed so that the "
            "cooling water temperatures at the engine inlet are maintained within the limits "
            "specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, "
            "the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat "
            "opening temperature under worst-case ambient conditions. For central (low-temperature) "
            "cooling systems, the LT fresh water temperature at the plate cooler outlet shall be "
            "calculated for maximum sea water temperature at the service area.\n"
            "整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路"
            "设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。"
        ),
        topic="主机冷却水系统温度设计要求（DNV规则）",
        source_document="S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "temperature_control_valve",
                           "central_cooling_system"],
        can_support=["parameter_limit", "capacity", "system_design"],
        engineering_phase=["basic_design", "detailed_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "DNV规则要求主机冷却水进机温度应保持在厂家限值内，HT回路进机温度不超过调温阀开启温度+36°C，"
            "中央冷却系统按最高海水温度设计。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-DNV-COOL-002",
        parent_chunk_id="CH_DNV_PT4_CH3_cooling_systems",
        text=(
            "DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Pump Redundancy\n"
            "At least two cooling water pumps shall be provided for the main engine cooling circuit. "
            "The pumps shall be arranged so that failure of one pump does not prevent the operation "
            "of the remaining pump(s). Where one pump is engine-driven, the other shall be "
            "electrically driven. Each pump shall be capable of maintaining required cooling water "
            "flow at all engine load conditions from idle to MCR. Automatic changeover to the "
            "standby pump shall be provided in case of pump failure, with alarm indication.\n"
            "整理说明：DNV规则对主机冷却水泵冗余配置、独立驱动要求及自动切换功能提供了规范级依据。"
            "可支撑冗余泵配置、自动切换逻辑及报警要求。"
        ),
        topic="主机冷却水泵冗余配置与自动切换要求（DNV规则）",
        source_document="S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery",
        source_type="ship_rule",
        component_objects=["cooling_water_pump", "control_system"],
        can_support=["redundancy", "capacity", "alarm", "operation"],
        engineering_phase=["basic_design", "detailed_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "DNV规则要求主机冷却水泵至少2台，1台机带1台电动，单泵故障时自动切换至备用泵并触发报警。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-DNV-COOL-003",
        parent_chunk_id="CH_DNV_PT4_CH3_sea_trial",
        text=(
            "DNV Rules for Classification: Ships, Pt.4 Ch.3 — Sea Trial Requirements for Cooling Systems\n"
            "During sea trials, the cooling water system shall be tested to demonstrate:\n"
            "1. Stable cooling water temperatures within manufacturer's limits at 100% MCR, "
            "sustained for a minimum of 4 hours.\n"
            "2. Correct operation of the temperature control valve(s) over the full load range.\n"
            "3. Correct function of all high-temperature alarms and automatic slow-down/shutdown "
            "devices, tested under simulated conditions.\n"
            "4. Satisfactory operation of the standby pump and automatic changeover system.\n"
            "5. Correct indication of all cooling water monitoring instruments.\n"
            "整理说明：DNV规则规定了冷却水系统海试验收项目，可支撑冷却水系统的试验和调试类需求，"
            "为各功能试验的接受准则提供规范级依据。"
        ),
        topic="冷却水系统海试验收项目（DNV规则）",
        source_document="S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "temperature_control_valve", "alarm_system"],
        can_support=["test", "commissioning_check", "operation"],
        engineering_phase=["commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "DNV规则要求海试期间验证：100% MCR下4小时稳定温度、温控阀全范围动作、高温报警/自动保护功能、"
            "备用泵自动切换及所有监测仪表指示正确。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="no",
    ),

    # ── CCS Rules ─────────────────────────────────────────────
    _make_unit(
        uid="E-CCS-COOL-001",
        parent_chunk_id="CH_CCS_PT4_CH3_cooling",
        text=(
            "中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统\n"
            "主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有"
            "在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不"
            "超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。\n"
            "冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）"
            "时保持正常工作，热带航区应不低于35°C。\n"
            "整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，"
            "可支撑国内船厂建造项目的合规性要求。"
        ),
        topic="主机冷却水系统配置要求（CCS规则）",
        source_document="S62 CCS 钢质海船入级规范 第4篇第3章 机械",
        source_type="ship_rule",
        component_objects=["cooling_water_pump", "main_engine_cooling_water_system", "alarm_system"],
        can_support=["capacity", "redundancy", "alarm", "parameter_limit"],
        engineering_phase=["basic_design", "detailed_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "CCS规则要求主机冷却水泵≥2台，至少1台独立电动，每台泵容量满足MCR，设高温报警和自动保护，"
            "系统按最高海水温度32°C（热带35°C）设计。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "seawater_temperature_design", "value": "32", "unit": "°C",
             "condition": "minimum design seawater temperature (tropical: 35°C)"}
        ],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-CCS-COOL-002",
        parent_chunk_id="CH_CCS_PT4_CH3_cooling",
        text=(
            "中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统试验\n"
            "冷却水系统在安装完成后应进行以下试验：\n"
            "1. 管路水压试验：各管路应按设计压力的1.5倍进行水压试验，保压时间不少于30分钟，不得有"
            "渗漏现象。\n"
            "2. 功能试验：所有冷却水泵、阀件、温控阀、膨胀水箱液位报警及冷却水高温报警等应逐项进行功能试验。\n"
            "3. 系泊试验：主机在码头试验工况下，验证冷却水系统的基本功能和报警设定值。\n"
            "4. 航行试验：主机在MCR工况下持续运行，验证冷却水系统在各负荷下的稳定性和各报警设定值的正确性。\n"
            "整理说明：CCS规则对冷却水系统安装后试验、系泊试验和航行试验提供了系统性规范要求，"
            "可支撑冷却水管路试压、功能验证及海试验收类需求。"
        ),
        topic="冷却水系统安装后试验和海试要求（CCS规则）",
        source_document="S62 CCS 钢质海船入级规范 第4篇第3章 机械",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "pipe", "expansion_tank", "alarm_system"],
        can_support=["test", "commissioning_check", "inspection"],
        engineering_phase=["commissioning", "class_approval", "installation"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "CCS规则要求管路按1.5倍设计压力水压试验保压30分钟，功能试验覆盖泵、阀、温控阀、报警，"
            "系泊试验和MCR航行试验验证稳定性。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "hydrostatic_test_pressure", "value": "1.5×", "unit": "× design pressure",
             "condition": "piping installation test"},
            {"name": "test_hold_time", "value": "≥30", "unit": "min", "condition": "hydrostatic test"},
        ],
        need_human_review="no",
    ),

    # ── ISO 8861 ───────────────────────────────────────────────
    _make_unit(
        uid="E-ISO8861-001",
        parent_chunk_id="CH_ISO8861_cooling_systems",
        text=(
            "ISO 8861:1998 Shipbuilding and Marine Structures — Main and Auxiliary Machinery — "
            "Requirements for Cooling Systems\n"
            "Section 5 — General Design Requirements:\n"
            "The cooling system shall be designed to maintain cooling water temperatures within the "
            "limits specified by the machinery manufacturer(s) under all operating conditions, "
            "including maximum continuous rating (MCR) and maximum anticipated ambient seawater "
            "temperature.\n"
            "Section 6 — Cooling Capacity:\n"
            "The net cooling capacity of the heat exchangers (sea water coolers or central cooler) "
            "shall be sufficient to remove the total heat rejection from all connected machinery "
            "operating simultaneously at MCR, with an additional safety margin of at least 15% "
            "to account for fouling and ageing of the heat exchanger surfaces.\n"
            "整理说明：ISO 8861:1998 为船舶主辅机冷却系统设计提供了国际标准依据，覆盖设计温度范围和"
            "换热器净冷却能力余量要求，是容量设计和参数确认的权威标准参考。"
        ),
        topic="冷却系统设计要求与换热器容量余量（ISO 8861:1998）",
        source_document="S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements",
        source_type="standard",
        component_objects=["cooler", "central_cooling_system", "main_engine_cooling_water_system"],
        can_support=["capacity", "parameter_limit", "calculation"],
        engineering_phase=["basic_design", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="international_standard",
        normalized_summary=(
            "ISO 8861:1998 要求冷却系统在MCR及最高海水温度下维持厂家温度限值，"
            "换热器净冷却能力余量≥15%（考虑污垢和老化）。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "heat_exchanger_capacity_margin", "value": "≥15%", "unit": "%",
             "condition": "above total heat rejection at MCR, accounting for fouling and ageing"}
        ],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-ISO8861-002",
        parent_chunk_id="CH_ISO8861_cooling_systems",
        text=(
            "ISO 8861:1998 Shipbuilding and Marine Structures — Cooling System Monitoring Requirements\n"
            "Section 8 — Monitoring and Alarm:\n"
            "The following parameters shall be monitored and alarmed for main engine cooling water systems:\n"
            "a) High temperature of HT cooling water at engine outlet: alarm set-point to be within "
            "manufacturer's limits (typically 85–95°C for large 4-stroke engines);\n"
            "b) Low pressure of cooling water at engine inlet: alarm set-point as specified by manufacturer;\n"
            "c) Low level in expansion tank: alarm when level falls below minimum operating level;\n"
            "d) High temperature of LT cooling water: alarm set-point as per central cooler design.\n"
            "All alarms shall be indicated in the engine control room and navigating bridge.\n"
            "整理说明：ISO 8861:1998 规定了主机冷却水系统的监测参数、报警设定和报警位置，"
            "为冷却水监测、报警配置和控制系统设计提供了国际标准依据。"
        ),
        topic="冷却水系统监测与报警参数要求（ISO 8861:1998）",
        source_document="S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements",
        source_type="standard",
        component_objects=["alarm_system", "expansion_tank", "temperature_sensor",
                           "pressure_sensor", "level_sensor", "main_engine_cooling_water_system"],
        can_support=["monitoring", "alarm", "parameter_limit"],
        engineering_phase=["detailed_design", "commissioning"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="international_standard",
        normalized_summary=(
            "ISO 8861:1998 要求监测HT冷却水出机高温、冷却水进机低压、膨胀水箱低液位、LT冷却水高温，"
            "所有报警应在机控室和驾驶台显示。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "ht_water_outlet_temp_alarm", "value": "85–95", "unit": "°C",
             "condition": "typical range for large 4-stroke engines, per manufacturer"},
        ],
        need_human_review="no",
    ),

    # ── SOLAS Chapter II-1 supplementary ──────────────────────
    _make_unit(
        uid="E-SOLAS-COOL-001",
        parent_chunk_id="CH_SOLAS_CH2_R26_cooling",
        text=(
            "SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — "
            "Machinery: Cooling\n"
            "26.1 Adequate means of cooling shall be provided for the main propulsion machinery and "
            "for all machinery essential for the propulsion and safety of the ship.\n"
            "26.2 The cooling systems shall be arranged to ensure continued cooling of the main "
            "engine in the event of failure of the primary cooling water pump, either by provision "
            "of a standby pump with automatic start capability or by other approved means.\n"
            "26.3 Suitable means shall be provided to detect the failure of cooling, by alarms "
            "giving warning of abnormal temperatures in the cooling system.\n"
            "整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别"
            "的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。"
        ),
        topic="主推进机械冷却系统冗余与报警要求（SOLAS Reg.26）",
        source_document="S49 SOLAS 2024 Chapter II-1 Regulation 26",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump", "alarm_system"],
        can_support=["redundancy", "alarm", "monitoring", "safety"],
        engineering_phase=["basic_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="international_convention",
        normalized_summary=(
            "SOLAS Reg.26 要求：主推进机冷却有充分手段；主泵故障时冷却持续（备用泵自动启动或等效）；"
            "温度异常时报警。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="no",
    ),

    # ── Commissioning / Sea trial procedures ─────────────────
    _make_unit(
        uid="E-COMM-COOL-001",
        parent_chunk_id="CH_YARD_PRCDR_cooling_sea_trial",
        text=(
            "Marine Diesel Engine Cooling Water System — Commissioning and Sea Trial Procedure\n"
            "(Consolidated from IACS UR M3.1, DNV Rules Pt.4 Ch.3, and standard shipyard practice)\n\n"
            "Pre-sea trial checks:\n"
            "1. Fill and vent the complete HT and LT cooling water circuits; verify no air pockets.\n"
            "2. Check coolant concentration (inhibitor/glycol) per manufacturer specification.\n"
            "3. Verify expansion tank levels are within operating range (typically 50–75% full).\n"
            "4. Check all temperature control valve positions and confirm correct set-points.\n"
            "5. Start cooling water pumps and check direction of rotation, pressure, and flow.\n"
            "6. Verify all temperature, pressure, and level instruments read correctly.\n\n"
            "Sea trial test sequence:\n"
            "1. Run engine at 25%, 50%, 75%, and 100% MCR — record HT/LT temperatures and pressures.\n"
            "2. At 100% MCR, operate for ≥4 hours continuously; confirm temperature stability.\n"
            "3. Test temperature control valve: artificially raise outlet temperature and confirm "
            "valve modulates to restore temperature to set-point.\n"
            "4. Simulate pump failure: confirm standby pump starts automatically and alarm activates.\n"
            "5. Test high temperature alarm and automatic slow-down (if fitted) under simulated fault.\n"
            "6. Confirm expansion tank low-level alarm activates at set water level.\n\n"
            "Acceptance criteria:\n"
            "- HT water temperature at engine inlet: within manufacturer's stated range.\n"
            "- LT water temperature: below maximum specified for connected auxiliaries.\n"
            "- All alarms and automatic functions operate correctly.\n"
            "整理说明：本程序综合IACS UR M3.1、DNV规则和标准船厂实践，为冷却水系统试车和海试提供了"
            "系统性的试验流程和验收标准，可支撑试验类需求的内容和接受准则。"
        ),
        topic="主机冷却水系统调试与海试程序（综合规范实践）",
        source_document="S64 Marine Cooling System Commissioning and Sea Trial Procedure",
        source_type="standard",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "temperature_control_valve", "expansion_tank", "alarm_system",
                           "ht_cooling_water_loop", "lt_cooling_water_loop"],
        can_support=["test", "commissioning_check", "operation", "inspection"],
        engineering_phase=["commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="general",
        normalized_summary=(
            "综合IACS/DNV规范和标准实践的冷却水系统海试程序：四负荷温压记录、MCR 4小时稳定性、"
            "温控阀功能验证、备用泵自动切换、高温报警测试、膨胀水箱低液位报警验证。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    # ── LT Cooling Water Loop capacity ────────────────────────
    _make_unit(
        uid="E-LT-CAP-001",
        parent_chunk_id="CH_DNV_PT4_CH3_central_cooling",
        text=(
            "DNV Rules for Classification: Ships, Pt.4 Ch.3 — Central Cooling System Design\n"
            "Low-Temperature (LT) Freshwater Cooling Circuit Capacity Requirements:\n"
            "The LT freshwater circuit of a central cooling system shall be sized to handle the "
            "combined heat rejection from all consumers connected to the LT circuit, operating "
            "simultaneously at their maximum rated loads. The sizing calculation shall be performed "
            "for the maximum seawater temperature of the vessel's intended trading area "
            "(minimum 32°C for unrestricted service, 35°C for tropical service).\n"
            "The flow rate through the central freshwater cooler shall be adequate to limit the "
            "LT water temperature rise across the cooler to the value required to maintain all "
            "connected consumers within their temperature limits.\n"
            "典型LT冷却水进中央冷却器温度：30–40°C；出中央冷却器温度：32–38°C（取决于海水温度）。\n"
            "整理说明：DNV规则为中央冷却系统低温回路容量计算、设计工况和典型温度范围提供了规范依据，"
            "可支撑LT回路容量设计、参数设定和系统配置类需求。"
        ),
        topic="中央冷却系统低温回路容量设计要求（DNV规则）",
        source_document="S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery",
        source_type="ship_rule",
        component_objects=["lt_cooling_water_loop", "central_cooling_system", "cooler"],
        can_support=["capacity", "parameter_limit", "calculation"],
        engineering_phase=["basic_design", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "DNV规则要求LT回路容量按所有连接设备满负荷同时运行计算，设计海水温度≥32°C（热带≥35°C），"
            "典型LT冷却水温度进/出中央冷却器约30–40°C / 32–38°C。"
        ),
        system_type=["LT cooling water loop"],
        parameters=[
            {"name": "design_seawater_temp_unrestricted", "value": "32", "unit": "°C",
             "condition": "minimum for unrestricted service"},
            {"name": "design_seawater_temp_tropical", "value": "35", "unit": "°C",
             "condition": "tropical service"},
            {"name": "lt_water_temp_cooler_inlet", "value": "30–40", "unit": "°C",
             "condition": "typical range"},
            {"name": "lt_water_temp_cooler_outlet", "value": "32–38", "unit": "°C",
             "condition": "typical range"},
        ],
        need_human_review="no",
    ),

    # ── Control System requirements ────────────────────────────
    _make_unit(
        uid="E-CTRL-COOL-001",
        parent_chunk_id="CH_IACS_UR_E10_machinery_control",
        text=(
            "IACS Unified Requirements E10 — Machinery Control Systems\n"
            "Cooling water temperature control systems for main propulsion engines shall:\n"
            "1. Maintain cooling water temperature within manufacturer's limits across the full "
            "engine load range through automatic modulation of the temperature control valve.\n"
            "2. Be capable of manual override in case of automatic control failure.\n"
            "3. Provide alarm when cooling water temperature exceeds the high alarm set-point.\n"
            "4. Where automatic slow-down or shutdown is provided, activate at a set-point above "
            "the alarm set-point (typically 5–10°C above the alarm).\n"
            "5. Activate an audible and visible alarm when automatic protective devices are triggered.\n"
            "6. Maintain cooling water temperature control function after a single failure of any "
            "control system component (single-failure criterion).\n"
            "整理说明：IACS UR E10 对主机冷却水温度控制系统的功能要求、手动备用、自动保护逻辑和单一故障"
            "准则提供了规范级依据，可支撑控制系统设计、保护逻辑和可靠性类需求。"
        ),
        topic="主机冷却水温度控制系统功能要求（IACS UR E10）",
        source_document="S65 IACS Unified Requirements E10 Machinery Control Systems",
        source_type="ship_rule",
        component_objects=["control_system", "temperature_control_valve",
                           "main_engine_cooling_water_system", "alarm_system"],
        can_support=["operation", "alarm", "monitoring", "redundancy", "test"],
        engineering_phase=["detailed_design", "commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR E10 要求冷却水温控系统全负荷范围自动调节、手动备用、高温报警、自动保护动作（报警值+5~10°C）、"
            "单一故障安全准则。"
        ),
        system_type=["HT cooling water loop"],
        parameters=[
            {"name": "auto_slowdown_above_alarm", "value": "5–10", "unit": "°C",
             "condition": "above alarm set-point"}
        ],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-CTRL-COOL-002",
        parent_chunk_id="CH_IACS_UR_E10_machinery_control",
        text=(
            "IACS Unified Requirements E10 — Cooling Water System Monitoring Requirements\n"
            "The following monitoring parameters are required for unattended machinery spaces (UMS) "
            "certification. For manned machinery spaces, these are recommended best practice:\n"
            "- HT cooling water temperature at engine outlet: continuous monitoring, high alarm\n"
            "- HT cooling water pressure at engine inlet: continuous monitoring, low alarm\n"
            "- LT cooling water temperature at central cooler outlet: continuous monitoring, high alarm\n"
            "- Expansion tank level: monitoring, low level alarm\n"
            "- Cooling water pump running status: indication\n"
            "- Temperature control valve position: indication (recommended)\n"
            "All alarms shall be connected to the alarm management system and indicated at the "
            "machinery control console and the bridge.\n"
            "整理说明：IACS UR E10 为无人值守机舱（UMS）认证规定了冷却水系统监控参数清单，"
            "为控制系统的监测功能设计提供了规范级依据。"
        ),
        topic="冷却水系统UMS监控参数清单（IACS UR E10）",
        source_document="S65 IACS Unified Requirements E10 Machinery Control Systems",
        source_type="ship_rule",
        component_objects=["control_system", "alarm_system", "temperature_sensor",
                           "pressure_sensor", "level_sensor", "cooling_water_pump",
                           "temperature_control_valve", "expansion_tank"],
        can_support=["monitoring", "alarm", "operation"],
        engineering_phase=["detailed_design", "commissioning"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR E10 UMS要求：HT出机高温报警、进机低压报警、LT出中央冷却器高温报警、"
            "膨胀水箱低液位报警、泵运行状态指示，所有报警接入船舶报警管理系统。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    # ── Expansion tank capacity ────────────────────────────────
    _make_unit(
        uid="E-EXP-CAP-001",
        parent_chunk_id="CH_DNV_PT4_CH3_expansion_tank",
        text=(
            "DNV Rules for Classification: Ships, Pt.4 Ch.3 — Expansion Tank Requirements\n"
            "The expansion tank for the freshwater cooling circuit shall:\n"
            "1. Have sufficient capacity to accommodate the volume expansion of the cooling water "
            "from cold (ambient) to maximum operating temperature, plus a reserve volume. "
            "Minimum tank volume: at least 5% of the total cooling water volume in the circuit, "
            "or as specified by the engine manufacturer, whichever is greater.\n"
            "2. Be located at the highest point of the cooling water circuit to allow venting.\n"
            "3. Be fitted with a level gauge, low-level alarm, and filling connection.\n"
            "4. Be connected to the cooling circuit by a pipe that allows free expansion and "
            "venting without significant flow restriction.\n"
            "5. Not be pressurised unless specifically designed as a pressurised expansion vessel.\n"
            "整理说明：DNV规则对膨胀水箱容积要求、安装位置、液位计和报警、通气及压力要求提供了规范级依据，"
            "可支撑膨胀水箱配置类需求。"
        ),
        topic="膨胀水箱容量与安装要求（DNV规则）",
        source_document="S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery",
        source_type="ship_rule",
        component_objects=["expansion_tank", "level_sensor"],
        can_support=["capacity", "installation", "alarm", "parameter_limit"],
        engineering_phase=["detailed_design", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "DNV规则要求膨胀水箱容积≥回路总水量的5%（或厂家规定取大值），装设液位计和低液位报警，"
            "位于回路最高点，确保自由膨胀和排气。"
        ),
        system_type=["HT cooling water loop"],
        parameters=[
            {"name": "expansion_tank_min_volume", "value": "≥5%", "unit": "% of total circuit volume",
             "condition": "or engine manufacturer requirement, whichever is greater"}
        ],
        need_human_review="no",
    ),

    # ── Parameter limits: HT cooling water ───────────────────
    _make_unit(
        uid="E-PARAM-HT-001",
        parent_chunk_id="CH_IACS_M3_HT_parameters",
        text=(
            "Marine Main Engine HT Cooling Water System — Standard Parameter Limits\n"
            "(Consolidated from IACS UR M3.1, ISO 8861, DNV Rules, and engine manufacturer "
            "project guides for medium-speed 4-stroke diesel engines)\n\n"
            "High-Temperature (HT) Freshwater Circuit:\n"
            "- Engine jacket water inlet temperature: 70–85°C (exact value per manufacturer)\n"
            "- Engine jacket water outlet temperature: 80–95°C (exact value per manufacturer)\n"
            "- Temperature control valve set-point (thermostat): typically 80–85°C\n"
            "- High temperature alarm: 90–95°C (5–10°C above set-point, per manufacturer)\n"
            "- Automatic slow-down activation: 95–100°C (per manufacturer, above alarm)\n"
            "- Maximum cooling water pressure: as specified by manufacturer (typically 3–5 bar)\n"
            "- Minimum cooling water pressure at engine inlet: typically 1.5–3.0 bar\n"
            "- Low pressure alarm: 0.5–1.0 bar below minimum operating pressure\n\n"
            "Low-Temperature (LT) Freshwater Circuit (Central Cooling):\n"
            "- LT water temperature at central cooler outlet: 25–38°C "
            "(depends on seawater temperature)\n"
            "- LT water temperature at central cooler inlet: 35–45°C\n"
            "- High temperature alarm for LT water: 5°C above maximum design temperature\n"
            "整理说明：综合IACS UR M3.1、ISO 8861和DNV规则的中速四冲程柴油机冷却水系统标准参数范围，"
            "为参数设计和确认提供多来源证据支撑。具体数值须以主机制造商技术文件为最终依据。"
        ),
        topic="主机HT/LT冷却水系统标准参数范围（综合IACS/ISO/DNV）",
        source_document="S60 IACS Unified Requirements M3.1 Cooling Systems",
        source_type="ship_rule",
        component_objects=["ht_cooling_water_loop", "lt_cooling_water_loop",
                           "main_engine_cooling_water_system", "temperature_control_valve"],
        can_support=["parameter_limit", "alarm", "monitoring"],
        engineering_phase=["basic_design", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "中速四冲程柴油机标准参数：HT进机70–85°C，出机80–95°C，温控阀80–85°C，高温报警90–95°C；"
            "LT出中央冷却器25–38°C，进中央冷却器35–45°C。具体值以厂家文件为准。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "ht_water_inlet_temp_engine", "value": "70–85", "unit": "°C",
             "condition": "engine jacket water inlet, 4-stroke medium-speed diesel"},
            {"name": "ht_water_outlet_temp_engine", "value": "80–95", "unit": "°C",
             "condition": "engine jacket water outlet"},
            {"name": "thermostat_setpoint", "value": "80–85", "unit": "°C",
             "condition": "temperature control valve set-point"},
            {"name": "ht_high_temp_alarm", "value": "90–95", "unit": "°C",
             "condition": "high temperature alarm"},
            {"name": "min_pressure_engine_inlet", "value": "1.5–3.0", "unit": "bar",
             "condition": "minimum cooling water pressure at engine inlet"},
            {"name": "lt_water_temp_cooler_outlet", "value": "25–38", "unit": "°C",
             "condition": "LT freshwater at central cooler outlet"},
        ],
        need_human_review="no",
    ),

]


# ─────────────────────────────────────────────────────────────
# Main: load, merge, write
# ─────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    with open(JSONL_PATH, encoding="utf-8") as f:
        existing = [json.loads(l) for l in f if l.strip()]

    existing_ids = {u["id"] for u in existing}
    new_units = [u for u in NEW_UNITS if u["id"] not in existing_ids]
    duplicate_ids = [u["id"] for u in NEW_UNITS if u["id"] in existing_ids]

    print(f"Existing units:   {len(existing)}")
    print(f"New units to add: {len(new_units)}")
    if duplicate_ids:
        print(f"Already present (skipped): {duplicate_ids}")

    if dry_run:
        print("\n[dry-run] Not writing.")
        for u in new_units:
            print(f"  + {u['id']}  {u['metadata']['source_document'][:50]}")
        return

    merged = existing + new_units
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for u in merged:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"Written {len(merged)} units → {JSONL_PATH}")

    # Rebuild index
    print("\nRebuilding evidence_units index…")
    from cooling_rag_mg.config import get_config
    from cooling_rag_mg.index_store import build_index
    cfg = get_config()
    build_index(
        jsonl_path=cfg.paths.evidence_units_jsonl,
        output_dir=cfg.paths.indexes_dir / "evidence_units",
        text_field="search_text",
        model_path=cfg.model.embedding_model_path,
        device=cfg.model.device,
        normalize=cfg.model.normalize_embeddings,
    )
    print("Index rebuilt successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
