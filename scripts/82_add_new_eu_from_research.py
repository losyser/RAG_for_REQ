"""
基于网络研究结果向 evidence_units_v2.jsonl 添加新的高质量 EU 条目。

来源：
  - IACS UR M28 / M72 / M35（L1）
  - SOLAS Chapter II-1（L1）
  - MAN Energy Solutions 项目指南和服务信（L2）
  - Wärtsilä 46F / 34SG 产品手册（L2）
  - 行业通用冷却水技术规范（L2/L3）

运行前先备份：
  copy data/processed/evidence_units_v2.jsonl data/processed/evidence_units_v2.jsonl.bak
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EU_JSONL = ROOT / "data/processed/evidence_units_v2.jsonl"


def make_eu(
    eu_id: str,
    tier: str,
    source_type: str,
    source_document: str,
    location: str,
    manufacturer: str,
    primary_component: str,
    primary_intent: str,
    text: str,
    component_objects: list[str],
    requirement_intents: list[str],
    can_support: list[str],
    engine_model: str = "",
    is_generalizable: str = "limited",
    keywords_en: list[str] = None,
) -> dict:
    search_text = f"{' '.join(component_objects)} {' '.join(requirement_intents)} - {text[:120]} {source_document}"
    tier_reason_map = {
        "L1": "规则: ship_rule",
        "L2": "制造商技术指南",
        "L3": "行业通用指导",
    }
    return {
        "id": eu_id,
        "unit_id": eu_id,
        "original_id": eu_id,
        "parent_chunk_id": f"CH_{eu_id}",
        "kb_tier": tier,
        "kb_version": "v2",
        "primary_component": primary_component,
        "primary_intent": primary_intent,
        "evidence_strength": "direct",
        "tier_reason": tier_reason_map.get(tier, tier),
        "source_type": source_type,
        "source_document": source_document,
        "location": location,
        "manufacturer": manufacturer,
        "engine_model": engine_model,
        "text": text,
        "search_text": search_text,
        "metadata": {
            "source_document": source_document,
            "source_type": source_type,
            "location": location,
            "component_objects": component_objects,
            "requirement_intents": requirement_intents,
            "can_support": can_support,
            "evidence_strength": "direct",
            "is_generalizable": is_generalizable,
            "applicability_level": "class_rule" if tier == "L1" else "manufacturer_spec",
            "manufacturer": manufacturer,
            "engine_model": engine_model,
            "keywords_en": keywords_en or [],
            "is_noise": False,
            "noise_reason": "",
        },
    }


# ── 新EU条目列表 ──────────────────────────────────────────────

NEW_EUS = [

    # ═══════════════════════════════════════════════════════════
    # L1 — IACS UR M28：环境参考条件
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-IACS-M28-001",
        tier="L1",
        source_type="ship_rule",
        source_document="IACS Unified Requirements M28 Ambient Reference Conditions",
        location="UR M28",
        manufacturer="IACS",
        primary_component="main_engine_cooling_water_system",
        primary_intent="temperature",
        text=(
            "IACS UR M28 Ambient Reference Conditions for Marine Diesel Engine Design:\n"
            "- Sea water reference temperature (tropical design basis): 32°C\n"
            "- Air inlet (blower inlet) reference temperature: 45°C\n"
            "- Blower inlet pressure: 1,000 mbar\n"
            "- Relative humidity: 60%\n"
            "All class society requirements and manufacturer cooling system sizing are based on these reference conditions. "
            "The 32°C seawater inlet is the standard tropical baseline for central cooler and heat exchanger design."
        ),
        component_objects=["main_engine_cooling_water_system", "sea_water_cooling_system", "central_cooler"],
        requirement_intents=["temperature", "design_basis", "ambient_condition"],
        can_support=["parameter_limit", "calculation", "equipment_selection"],
        is_generalizable="yes",
        keywords_en=["IACS M28", "32°C", "seawater", "ambient", "tropical", "reference temperature"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L1 — IACS UR M72：冷却器水压试验
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-IACS-M72-001",
        tier="L1",
        source_type="ship_rule",
        source_document="IACS Unified Requirements M72 Rev.3 2023 Hydraulic Testing",
        location="UR M72 Rev.3",
        manufacturer="IACS",
        primary_component="central_cooler",
        primary_intent="pressure_test",
        text=(
            "IACS UR M72 Rev.3 (2023) — Hydraulic Test Requirements for Cooling Water Components:\n"
            "Heat exchangers, central coolers and charge air coolers shall be hydraulically tested at "
            "1.5 × maximum working pressure on the water/oil side before installation.\n"
            "Charge air coolers: tested on water side only.\n"
            "This test shall be conducted by the manufacturer and documented for class approval."
        ),
        component_objects=["central_cooler", "charge_air_cooler", "heat_exchanger"],
        requirement_intents=["pressure_test", "commissioning", "class_approval"],
        can_support=["parameter_limit", "calculation", "test_requirement"],
        is_generalizable="yes",
        keywords_en=["IACS M72", "hydraulic test", "1.5x", "working pressure", "heat exchanger", "cooler"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L1 — IACS UR M35：无人机舱报警与保护
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-IACS-M35-001",
        tier="L1",
        source_type="ship_rule",
        source_document="IACS Unified Requirements M35 Rev.8 Alarms and Safeguards for Main IC Engines in UMS",
        location="UR M35 Rev.8",
        manufacturer="IACS",
        primary_component="alarm_system",
        primary_intent="alarm_protection",
        text=(
            "IACS UR M35 Rev.8 — Mandatory Alarms and Safeguards for Main IC Engines in Unattended Machinery Spaces (UMS):\n"
            "- High cooling water temperature: mandatory alarm AND automatic slowdown or shutdown trigger\n"
            "- Low cooling water pressure (HT and LT circuits): mandatory alarm\n"
            "- Deaerating/expansion tank low level: mandatory alarm\n"
            "- All parameters that could cause engine damage if unattended must have alarm + automatic protective response\n"
            "Note: Numerical setpoints for alarms and slowdown/shutdown are engine manufacturer-specific and "
            "must be approved by the class society. The UR mandates the alarm exists; the threshold values "
            "are defined in the engine manufacturer's project guide and control system."
        ),
        component_objects=["alarm_system", "main_engine_cooling_water_system", "expansion_tank"],
        requirement_intents=["alarm_protection", "monitoring", "safety"],
        can_support=["alarm_protection", "parameter_limit", "equipment_selection"],
        is_generalizable="yes",
        keywords_en=["IACS M35", "UMS", "alarm", "slowdown", "shutdown", "cooling water", "high temperature", "low pressure"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L1 — SOLAS：冷却水泵冗余与本质服务
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-SOLAS-COOL-001",
        tier="L1",
        source_type="ship_rule",
        source_document="SOLAS Chapter II-1 Machinery Safety Requirements",
        location="Chapter II-1",
        manufacturer="IMO",
        primary_component="cooling_water_pump",
        primary_intent="redundancy",
        text=(
            "SOLAS Chapter II-1 — Cooling Water Pump Redundancy and Essential Services:\n"
            "- Cooling water pumps for main and auxiliary engines are classified as primary essential services "
            "requiring continuous electrical supply from the main switchboard.\n"
            "- Ships must maintain essential services (including cooling water supply) when any one generating set "
            "is out of operation.\n"
            "- Structural redundancy requirement: minimum two cooling water pumps required for the primary coolant circuit. "
            "Typical configurations: (a) 2 × 100% capacity, one as standby; or (b) 3 × 50% capacity.\n"
            "- Dead-ship requirement: remaining generating capacity must be sufficient to restart propulsion from dead-ship condition, "
            "including bringing cooling water systems online."
        ),
        component_objects=["cooling_water_pump", "sea_water_cooling_system"],
        requirement_intents=["redundancy", "power_supply", "safety"],
        can_support=["equipment_selection", "parameter_limit", "redundancy_design"],
        is_generalizable="yes",
        keywords_en=["SOLAS", "essential services", "redundancy", "standby pump", "100%", "dead ship", "cooling pump"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — MAN B&W 2冲程：HT冷却水温度控制
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-MAN-2S-TEMP-001",
        tier="L2",
        source_type="project_guide",
        source_document="MAN B&W 2-Stroke Engine Project Guide Section 12.01 HT Cooling Water System",
        location="Section 12.01",
        manufacturer="MAN Energy Solutions",
        primary_component="ht_cooling_water_system",
        primary_intent="temperature",
        text=(
            "MAN B&W Two-Stroke Engine HT (High-Temperature) Jacket Water Temperature Specifications:\n"
            "- Jacket water outlet temperature (after engine), normal operating range: 75–85°C\n"
            "- Thermostat control target (Valve A - max): maintains jacket water outlet T < 80°C\n"
            "- Thermostat control target (Valve B - min): maintains jacket water outlet T > 75°C\n"
            "- Jacket water inlet temperature (before engine): typically 65–75°C (≈ outlet – 10°C)\n"
            "- Standby pre-heating setpoint (hot engine on standby): 80–85°C\n"
            "- Minimum jacket water temperature before loading to >80% SMCR: 50°C\n"
            "- Normal pre-heating maintenance temperature: 60–80°C (pre-heater keeps engine warm)\n"
            "These values apply to standard central cooling configurations. The thermostatic valve "
            "must maintain a constant 80°C at engine outlet regardless of seawater temperature."
        ),
        component_objects=["ht_cooling_water_system", "main_engine_cooling_water_system"],
        requirement_intents=["temperature", "control", "preheat"],
        can_support=["parameter_limit", "equipment_selection", "calculation"],
        engine_model="MAN B&W S/G-ME/ME-C/ME-GI series",
        keywords_en=["MAN", "2-stroke", "jacket water", "75°C", "80°C", "85°C", "thermostat", "pre-heat", "50°C"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — MAN B&W 2冲程：LT冷却水温度
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-MAN-2S-LT-001",
        tier="L2",
        source_type="project_guide",
        source_document="MAN B&W 2-Stroke Engine Project Guide HT/LT Cooling System",
        location="Section 12",
        manufacturer="MAN Energy Solutions",
        primary_component="lt_cooling_water_system",
        primary_intent="temperature",
        text=(
            "MAN B&W Two-Stroke Engine LT (Low-Temperature) Cooling Water Specifications:\n"
            "- LT water temperature setpoint (central cooler outlet / before engine LT consumers): 36°C standard\n"
            "- This 36°C setpoint is the standard fixed-temperature specification used by most shipyards\n"
            "- LT circuit serves: charge air coolers (2nd stage), lubricating oil coolers\n"
            "- SFOC impact: operating central cooler at 36°C vs. 10°C results in approximately +2 g/kWh higher SFOC\n"
            "- Reference: MAN Service Letter SL2014-589 — each 10°C rise in LT coolant temperature at the "
            "scavenge air cooler inlet causes +0.60% SFOC increase (with p_max adjustment) or "
            "+0.41% SFOC increase (without p_max adjustment)\n"
            "- Design tropical basis: LT circuit must maintain ≤36°C outlet with 32°C seawater inlet (IACS M28 conditions)"
        ),
        component_objects=["lt_cooling_water_system", "central_cooler", "charge_air_cooler"],
        requirement_intents=["temperature", "efficiency", "design_basis"],
        can_support=["parameter_limit", "calculation", "equipment_selection"],
        engine_model="MAN B&W S/G-ME/ME-C/ME-GI series",
        keywords_en=["MAN", "LT", "36°C", "central cooler", "charge air cooler", "SFOC", "2-stroke"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — MAN B&W：冷却水处理要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-MAN-TREATMENT-001",
        tier="L2",
        source_type="service_letter",
        source_document="MAN Service Letter SL2016-623 Cooling Water Treatment",
        location="SL2016-623",
        manufacturer="MAN Energy Solutions",
        primary_component="ht_cooling_water_system",
        primary_intent="water_quality",
        text=(
            "MAN Energy Solutions SL2016-623 — Cooling Water Treatment Requirements:\n"
            "- Only nitrite-borate based corrosion inhibitors are recommended for MAN diesel engines\n"
            "- Onboard test frequency: at minimum once per week (inhibitor concentration, pH, chloride ion)\n"
            "- Independent laboratory analysis frequency: every 2–6 months (send sample to certified lab)\n"
            "- System must be kept free from rust, scale, and deposits\n"
            "- Key parameters to monitor and control: inhibitor concentration, pH value, chloride ion concentration\n"
            "Reference SL2014-589: minimum jacket water temperature for normal operation per maker recommendations."
        ),
        component_objects=["ht_cooling_water_system", "main_engine_cooling_water_system"],
        requirement_intents=["water_quality", "maintenance", "monitoring"],
        can_support=["parameter_limit", "maintenance_requirement", "monitoring"],
        engine_model="MAN B&W diesel engines (all types)",
        keywords_en=["MAN", "cooling water treatment", "nitrite", "borate", "inhibitor", "weekly test", "SL2016-623"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — Wärtsilä 4冲程：HT温度与报警
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-WAR-46F-HT-TEMP-001",
        tier="L2",
        source_type="project_guide",
        source_document="Wärtsilä 46F Series Product Manual",
        location="Pages 103-120",
        manufacturer="Wärtsilä",
        primary_component="ht_cooling_water_system",
        primary_intent="temperature",
        text=(
            "Wärtsilä 46F Series Four-Stroke Engine HT Cooling Water Temperature Requirements:\n"
            "- HT water outlet temperature after engine, normal operating range: 86–95°C\n"
            "- HT water high-temperature alarm setpoint: 105°C\n"
            "- HT water high-temperature shutdown (automatic stop) setpoint: 110°C\n"
            "- Minimum HT water temperature before normal engine start: 60°C (minimum), 70°C preferred\n"
            "- Standby keep-hot configuration: maintain HT water at 60–70°C\n"
            "- Pre-heating power requirement: P < 10 kW/cylinder maximum; typically 6–12 kW/cylinder\n"
            "These are pressurized closed freshwater jacket cooling systems; the higher temperature range "
            "(vs. open 2-stroke systems) reflects system pressurization allowing above 100°C operation."
        ),
        component_objects=["ht_cooling_water_system", "main_engine_cooling_water_system"],
        requirement_intents=["temperature", "alarm_protection", "preheat"],
        can_support=["parameter_limit", "alarm_protection", "equipment_selection"],
        engine_model="Wärtsilä 46F, 46DF",
        keywords_en=["Wärtsilä", "46F", "HT", "86°C", "95°C", "105°C", "110°C", "alarm", "shutdown", "4-stroke"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — Wärtsilä 4冲程：LT温度与压力
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-WAR-46F-LT-001",
        tier="L2",
        source_type="project_guide",
        source_document="Wärtsilä 46F Series Product Manual",
        location="Pages 103-120",
        manufacturer="Wärtsilä",
        primary_component="lt_cooling_water_system",
        primary_intent="temperature",
        text=(
            "Wärtsilä 46F Series LT Cooling Water Temperature and Pressure Specifications:\n"
            "- LT water temperature at central cooler outlet (max, full load, tropical): 38°C\n"
            "- Standard shipyard LT circuit setpoint (3-way thermostat valve): 36°C\n"
            "- Static pressure before pump (minimum): 0.7–1.5 bar at pump inlet\n"
            "- Pre-heating circulation pump delivery pressure: 0.8–1.0 bar (80–100 kPa)\n"
            "- Central cooler pressure drop, fresh water side (maximum): 0.6 bar (60 kPa)\n"
            "- Central cooler pressure drop, sea water side: 0.8–1.4 bar (80–140 kPa)\n"
            "- Pre-heating circulation pump flow rate: 1.6 m³/h per cylinder\n"
            "- Expansion tank minimum pressure at pump inlet: 70–150 kPa\n"
            "Design basis: tropical conditions with 32°C seawater (IACS M28)."
        ),
        component_objects=["lt_cooling_water_system", "central_cooler", "cooling_water_pump"],
        requirement_intents=["temperature", "pressure", "flow_rate"],
        can_support=["parameter_limit", "calculation", "equipment_selection"],
        engine_model="Wärtsilä 46F, 46DF",
        keywords_en=["Wärtsilä", "LT", "38°C", "36°C", "0.7 bar", "1.5 bar", "pressure drop", "60 kPa"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — Wärtsilä：膨胀水箱要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-WAR-EXPANSION-001",
        tier="L2",
        source_type="project_guide",
        source_document="Wärtsilä 46F Series Product Manual",
        location="Page 108",
        manufacturer="Wärtsilä",
        primary_component="expansion_tank",
        primary_intent="volume",
        text=(
            "Wärtsilä Cooling Water Expansion Tank / Deaerating Tank Requirements:\n"
            "- Minimum volume: 1.2–1.5 L/kW of installed engine power (Wärtsilä 46F series)\n"
            "- Alternative sizing: minimum 10% of total cooling water system volume\n"
            "- Operating pressure at pump inlet: 70–150 kPa\n"
            "- Required fittings: inspection hatch, level gauge, low level alarm (mandatory), "
            "means for dosing cooling water chemical additives\n"
            "- Low level alarm: mandatory per IACS UR M35 for UMS vessels\n"
            "- High level alarm: required if no overflow arrangement is provided (IACS UR M35)\n"
            "The expansion tank serves as deaerator for the closed freshwater cooling circuit; "
            "proper sizing is critical to prevent cavitation in circulating pumps."
        ),
        component_objects=["expansion_tank"],
        requirement_intents=["volume", "alarm_protection", "design_requirement"],
        can_support=["parameter_limit", "equipment_selection", "alarm_protection"],
        engine_model="Wärtsilä 46F; general 4-stroke",
        keywords_en=["expansion tank", "1.2 L/kW", "1.5 L/kW", "70 kPa", "150 kPa", "low level alarm", "deaerator"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — Wärtsilä 34SG：冷却水水质要求（处理后）
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-WAR-WATER-QUALITY-001",
        tier="L2",
        source_type="project_guide",
        source_document="Wärtsilä 20V34SG Training Document — Cooling Water System",
        location="Water Quality Section",
        manufacturer="Wärtsilä",
        primary_component="ht_cooling_water_system",
        primary_intent="water_quality",
        text=(
            "Wärtsilä — Treated Freshwater Quality Requirements for Closed Cooling Circuit:\n"
            "- pH at 25°C: 8–11\n"
            "- Conductivity at 25°C: ≤ 100 µS/cm\n"
            "- Total Dissolved Solids (TDS): ≤ 3,500 mg/L\n"
            "- Nitrite (NO₂, as corrosion inhibitor): 1,000–1,500 mg/L operating range\n"
            "- Total Hardness (Ca + Mg): < 10 °dH\n"
            "- Chlorides (Cl⁻): < 40 mg/L\n"
            "- Sulphates (SO₄²⁻): < 100 mg/L\n"
            "- Copper (Cu): < 1 mg/L\n"
            "Inhibitor dosing: Nalfleet 2000 or equivalent nitrite-based inhibitor.\n"
            "New system: 32–48 L per 1,000 L system volume. Maintenance: 1 L per 100 L.\n"
            "Only treated freshwater with approved inhibitors may circulate through the engine jacket cooling circuit."
        ),
        component_objects=["ht_cooling_water_system", "lt_cooling_water_system"],
        requirement_intents=["water_quality", "corrosion_protection"],
        can_support=["parameter_limit", "maintenance_requirement"],
        engine_model="Wärtsilä 34SG; general 4-stroke",
        keywords_en=["water quality", "pH", "8-11", "nitrite", "1000 mg/L", "chloride", "40 mg/L", "conductivity", "100 µS/cm"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — 冷却水原水（未处理）水质要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-WAR-RAW-WATER-001",
        tier="L2",
        source_type="project_guide",
        source_document="Wärtsilä 46F Series Product Manual",
        location="Page 103",
        manufacturer="Wärtsilä",
        primary_component="ht_cooling_water_system",
        primary_intent="water_quality",
        text=(
            "Wärtsilä — Raw (Untreated) Water Quality Limits Before Chemical Treatment:\n"
            "These limits apply to the source water used to fill the closed cooling circuit BEFORE treatment:\n"
            "- pH: 6.5–8.5\n"
            "- Total Hardness (Ca + Mg): ≤ 10 °dH\n"
            "- Chlorides (Cl⁻): ≤ 80 mg/L (Wärtsilä 46F); ≤ 40 mg/L (Wärtsilä 34SG)\n"
            "- Sulphates (SO₄²⁻): ≤ 150 mg/L (Wärtsilä 46F); ≤ 100 mg/L (Wärtsilä 34SG)\n"
            "Note: Only treated freshwater with approved corrosion inhibitors (nitrite-borate based) "
            "may circulate through the engine. Glycol addition: engine de-rated 0.23% per 1% glycol added; "
            "maximum glycol concentration permitted: 60%."
        ),
        component_objects=["ht_cooling_water_system"],
        requirement_intents=["water_quality", "material_protection"],
        can_support=["parameter_limit", "maintenance_requirement"],
        engine_model="Wärtsilä 46F, 34SG",
        keywords_en=["raw water", "pH 6.5", "hardness", "10 dH", "chloride", "80 mg/L", "sulphate", "glycol"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — 海水管路流速与材料要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-SW-PIPE-VELOCITY-001",
        tier="L2",
        source_type="industry_standard",
        source_document="BS MA 18 Salt Water Piping Systems in Ships; Copper-Nickel Alloy Institute Guidelines",
        location="BS MA 18; Copper.org Marine Materials",
        manufacturer="Industry Standard",
        primary_component="sea_water_cooling_system",
        primary_intent="flow_velocity",
        text=(
            "Sea Water Piping System — Maximum Flow Velocity Requirements (Erosion-Corrosion Prevention):\n"
            "90-10 Cu-Ni alloy (most common marine seawater pipe material):\n"
            "- Piping ≥ DN100: maximum 3.5 m/s\n"
            "- Heat exchangers and condensers: maximum 2.5 m/s\n"
            "70-30 Cu-Ni alloy:\n"
            "- Piping ≥ DN100: maximum 4.0 m/s\n"
            "- Heat exchangers and condensers: maximum 3.0 m/s\n"
            "- Maximum zinc content in 90-10 Cu-Ni (dezincification prevention): 1.0% Zn\n"
            "Standard: BS MA 18 Salt Water Piping Systems in Ships\n"
            "Exceeding these velocities causes accelerated erosion-corrosion of Cu-Ni alloys "
            "and will lead to premature failure of sea water piping, strainers and heat exchanger tubes."
        ),
        component_objects=["sea_water_cooling_system", "sea_water_pump"],
        requirement_intents=["flow_velocity", "material_selection", "piping"],
        can_support=["parameter_limit", "material_selection", "calculation"],
        keywords_en=["Cu-Ni", "90-10", "3.5 m/s", "2.5 m/s", "seawater velocity", "BS MA 18", "erosion"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — 海水冷却出口温度限值
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-SW-OUTLET-TEMP-001",
        tier="L2",
        source_type="industry_standard",
        source_document="Marine Engineering General Practice — Sea Water Cooling System Design",
        location="Industry consensus",
        manufacturer="General",
        primary_component="sea_water_cooling_system",
        primary_intent="temperature",
        text=(
            "Sea Water Cooling System — Outlet Temperature Limits:\n"
            "- Maximum sea water outlet temperature (from heat exchangers): 50°C\n"
            "  Above 50°C, unacceptable calcium carbonate scale formation and accelerated corrosion occur.\n"
            "- Minimum sea water inlet temperature (cold climate design consideration): 10°C\n"
            "  Below 10°C, lubricating oil may thicken excessively in LO coolers; "
            "viscosity by-pass controls must be considered.\n"
            "- Sea water outlet temperature from central cooler (normal operating, tropical): 38–45°C\n"
            "These limits apply to the seawater side of central coolers, separate coolers, "
            "and all heat exchangers in the raw seawater circuit."
        ),
        component_objects=["sea_water_cooling_system", "central_cooler"],
        requirement_intents=["temperature", "design_limit"],
        can_support=["parameter_limit", "calculation", "equipment_selection"],
        keywords_en=["seawater", "50°C", "maximum outlet", "10°C", "scale", "corrosion", "cooling"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — 泵容量设计余量
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-PUMP-CAPACITY-001",
        tier="L2",
        source_type="project_guide",
        source_document="MAN B&W Two-Stroke Engine Project Guide Cooling Water System",
        location="Section 12 — Cooling Water Pumps",
        manufacturer="MAN Energy Solutions",
        primary_component="cooling_water_pump",
        primary_intent="flow_rate",
        text=(
            "Cooling Water Pump Capacity Design Requirements:\n"
            "- Total installed cooling water pump capacity shall provide a minimum margin of 25% above the "
            "maximum calculated system flow demand at rated conditions.\n"
            "- This 25% minimum margin applies to both HT and LT fresh water circuits.\n"
            "- Pump selection must account for: maximum system resistance at design flow, "
            "filter/strainer fouling factor, and future system additions.\n"
            "- For central cooling systems with one standby pump: each pump shall be capable of delivering "
            "100% of required flow when operating alone.\n"
            "- Pump discharge pressure (general indicative range): 3–4 bar for main circulation pumps."
        ),
        component_objects=["cooling_water_pump"],
        requirement_intents=["flow_rate", "redundancy", "design_margin"],
        can_support=["parameter_limit", "calculation", "equipment_selection"],
        engine_model="MAN B&W general",
        keywords_en=["pump capacity", "25% margin", "100%", "standby", "3 bar", "4 bar", "flow rate"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L3 — 通用：HT/LT冷却水报警阈值参考范围
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-GENERAL-ALARM-TEMP-001",
        tier="L3",
        source_type="industry_reference",
        source_document="Marine Engineering Operational Reference — Cooling Water System Alarm Setpoints",
        location="Multiple sources (MarineNotes, MEO Class 4 references, operational practice)",
        manufacturer="General",
        primary_component="alarm_system",
        primary_intent="alarm_setpoint",
        text=(
            "Industry Reference — Typical Cooling Water Alarm and Trip Setpoints:\n\n"
            "For non-pressurized 2-stroke diesel engines (e.g., MAN B&W standard):\n"
            "- Jacket water outlet high-temperature ALARM: typically 85°C (≈ 5°C above normal 80°C)\n"
            "- Jacket water outlet high-temperature SLOWDOWN: typically 88–90°C\n"
            "- Jacket water outlet high-temperature SHUTDOWN: typically 95°C\n\n"
            "For pressurized 4-stroke diesel engines (e.g., Wärtsilä 46F):\n"
            "- Jacket water high-temperature ALARM: 105°C\n"
            "- Jacket water high-temperature SHUTDOWN: 110°C\n\n"
            "LT circuit (general):\n"
            "- LT water high-temperature ALARM: typically 45°C (≈ 7°C above 38°C max design)\n\n"
            "Note: These are typical industry reference values. Actual setpoints must be confirmed "
            "against the specific engine maker's project guide and commissioning documentation. "
            "IACS UR M35 requires these safeguards to exist but does not specify the numerical values."
        ),
        component_objects=["alarm_system", "ht_cooling_water_system", "lt_cooling_water_system"],
        requirement_intents=["alarm_setpoint", "alarm_protection"],
        can_support=["alarm_protection", "parameter_limit"],
        keywords_en=["alarm", "85°C", "95°C", "105°C", "110°C", "slowdown", "shutdown", "jacket water", "trip"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L3 — 淡水发生器集成：最低负荷要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-FWG-INTEGRATION-001",
        tier="L3",
        source_type="project_guide",
        source_document="MAN B&W S50ME-B9.3-TII Project Manual",
        location="Page 147",
        manufacturer="MAN Energy Solutions",
        primary_component="fresh_water_generator",
        primary_intent="operating_condition",
        text=(
            "MAN B&W — Fresh Water Generator (FWG) Integration Requirements with Jacket Cooling:\n"
            "- Minimum engine load for FWG operation: above 50% MCR (insufficient waste heat at lower loads)\n"
            "- Maximum recommended jacket heat utilization for FWG: 50% of available heat at MCR\n"
            "  (effectively ~38% accounting for ±10% cooler margin)\n"
            "- FWG capacity formula (indicative): M_fw = 0.03 × Q_jw tonnes/24h ± 15%/-0%\n"
            "  where Q_jw = total jacket water heat rejection in kW\n"
            "- The jacket water circuit to FWG must be arranged so FWG bypass is available at all times\n"
            "- FWG should not be operated when maneuvering, in port, or at reduced loads below 50% MCR"
        ),
        component_objects=["fresh_water_generator", "ht_cooling_water_system"],
        requirement_intents=["operating_condition", "heat_recovery", "system_integration"],
        can_support=["parameter_limit", "equipment_selection", "calculation"],
        engine_model="MAN B&W S50ME-B9.3",
        keywords_en=["FWG", "fresh water generator", "50%", "MCR", "jacket heat", "0.03", "heat recovery"],
    ),

    # ═══════════════════════════════════════════════════════════
    # L2 — IACS/CCS：海水冷却系统过滤器要求
    # ═══════════════════════════════════════════════════════════
    make_eu(
        eu_id="E-SW-FILTER-001",
        tier="L2",
        source_type="ship_rule",
        source_document="CCS 钢质海船入级规范 海水冷却系统过滤器要求",
        location="第4篇第3章",
        manufacturer="CCS",
        primary_component="sea_water_strainer",
        primary_intent="filtration",
        text=(
            "CCS 入级规范 — 海水冷却系统过滤器（海水滤器）要求：\n"
            "- 主海水冷却泵入口管路应设置海水滤器，防止海洋生物及杂质堵塞冷却系统\n"
            "- 每台冷却海水泵应设置独立的海水滤器，或设置公用滤器并配备清洁时不中断供水的旁通装置\n"
            "- 滤器网孔尺寸：应与所保护设备（中央冷却器、舷外换热器等）的流道尺寸相适应，通常≤5mm\n"
            "- 压差监测：滤器前后应设置压差表或压差报警，高压差时提示清洁\n"
            "- 自清洗滤器：对于无人机舱（UMS）船舶，宜设置自动反冲洗海水滤器\n"
            "整理说明：该要求为CCS规范强制性要求，适用于入级船舶的海水冷却系统。"
        ),
        component_objects=["sea_water_strainer", "sea_water_cooling_system"],
        requirement_intents=["filtration", "maintenance", "monitoring"],
        can_support=["equipment_selection", "alarm_protection", "parameter_limit"],
        keywords_en=["sea water strainer", "filter", "5mm", "pressure differential", "self-cleaning", "UMS"],
    ),
]


# ── 写入JSONL ─────────────────────────────────────────────────

def main():
    # 加载现有EU
    existing = []
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                existing.append(json.loads(line))

    existing_ids = {eu["id"] for eu in existing}

    # 过滤掉已存在的（幂等）
    to_add = [eu for eu in NEW_EUS if eu["id"] not in existing_ids]
    skipped = [eu["id"] for eu in NEW_EUS if eu["id"] in existing_ids]

    if skipped:
        print(f"已存在跳过: {skipped}")

    if not to_add:
        print("无需添加（全部已存在）")
        return

    with open(EU_JSONL, "a", encoding="utf-8") as f:
        for eu in to_add:
            f.write(json.dumps(eu, ensure_ascii=False) + "\n")

    print(f"新增 {len(to_add)} 条 EU：")
    for eu in to_add:
        print(f"  [{eu['kb_tier']}] {eu['id']} — {eu['text'][:60].strip()}...")
    print(f"\n写入完成：{EU_JSONL}")
    print(f"总EU数: {len(existing) + len(to_add)}")


if __name__ == "__main__":
    main()
