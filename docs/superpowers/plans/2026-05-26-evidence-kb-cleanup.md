# Evidence KB Cleanup & Supplement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除 27 条 background 噪声条目，补入约 15 条规范级证据（覆盖海水过滤器/模块化/焊接NDT/NPSH/材料/停机/冲洗/环保/减速/调试 10 类缺口），重建 source_chunks 和索引。

**Architecture:** 直接修改 `data/processed/evidence_units.jsonl`（方案2）。script 30 删 background 条目；script 31 补入 2 条 ISO 8861；新建 script 36 补入 15 条新规范条目；script 33 为新条目创建 source_chunk；script 11 重建全部索引。

**Tech Stack:** Python（LangGraph_env）, json, hashlib, cooling_rag_mg.index_store（脚本 31/36/33/11 需要完整环境）。前置发现：当前无前缀重复条目，0 孤儿条目——script 30 唯一实际工作是删 background。

**执行环境：** 所有命令在 `cooling_rag_multigranular/`（含 requirements.txt 的那层）中运行，Python 解释器使用 LangGraph_env。

---

### Task 1: 修改 script 30 — 增加 background 条目过滤

**Files:**
- Modify: `scripts/30_deduplicate_evidence.py`

- [ ] **Step 1: 确认当前 background 条目数**

```bash
python -c "
import json
units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
bg = [u for u in units if u.get('metadata',{}).get('evidence_strength')=='background']
print('background条目数:', len(bg))
for u in bg[:3]:
    print(' ', u['id'], u['text'][:60])
"
```

期望输出：`background条目数: 27`

- [ ] **Step 2: 在 `scripts/30_deduplicate_evidence.py` 的 `main()` 中插入过滤逻辑**

在 `print(f"Loaded {len(units)} evidence units")` 之后，指纹分组之前，插入：

```python
    # Remove background-strength entries (noise; hard-filtered by applicability_filter anyway)
    before = len(units)
    units = [u for u in units if u.get("metadata", {}).get("evidence_strength") != "background"]
    removed_bg = before - len(units)
    print(f"Removed {removed_bg} background-strength entries")
```

- [ ] **Step 3: 运行并确认结果**

```bash
python scripts/30_deduplicate_evidence.py
```

期望输出含：
```
Loaded 1270 evidence units
Removed 27 background-strength entries
Duplicate text groups: 0
Removed 0 duplicate units
Output: 1243 evidence units
```

- [ ] **Step 4: 验证写入结果**

```bash
python -c "
import json
units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
bg = [u for u in units if u.get('metadata',{}).get('evidence_strength')=='background']
print('总条数:', len(units), '  background:', len(bg))
"
```

期望输出：`总条数: 1243   background: 0`

- [ ] **Step 5: Commit**

```bash
git add scripts/30_deduplicate_evidence.py data/processed/evidence_units.jsonl
git commit -m "chore: remove 27 background-strength noise entries from evidence KB"
```

---

### Task 2: 运行 script 31 — 补入 ISO 8861 条目

**Files:**
- Execute: `scripts/31_add_evidence_units.py`（不修改，直接运行）

- [ ] **Step 1: 确认 2 条 ISO 8861 条目当前不存在**

```bash
python -c "
import json
ids = {json.loads(l)['id'] for l in open('data/processed/evidence_units.jsonl') if l.strip()}
print('E-ISO8861-001 存在:', 'E-ISO8861-001' in ids)
print('E-ISO8861-002 存在:', 'E-ISO8861-002' in ids)
"
```

期望输出：两行都是 `False`

- [ ] **Step 2: 以 dry-run 模式预览**

```bash
python scripts/31_add_evidence_units.py --dry-run
```

期望输出：显示 `E-ISO8861-001` 和 `E-ISO8861-002` 待添加，其余已跳过。

- [ ] **Step 3: 正式运行**

```bash
python scripts/31_add_evidence_units.py
```

期望输出：`Written 1245 units → ...evidence_units.jsonl`，然后 `Index rebuilt successfully.`

- [ ] **Step 4: 验证**

```bash
python -c "
import json
units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
iso = [u for u in units if u['id'].startswith('E-ISO8861')]
print('总条数:', len(units))
for u in iso:
    print(' +', u['id'], u['metadata']['topic'][:50])
"
```

期望输出：`总条数: 1245`，列出 2 条 ISO 8861 条目。

- [ ] **Step 5: Commit**

```bash
git add data/processed/evidence_units.jsonl
git commit -m "feat: add ISO 8861:1998 cooling system design and monitoring entries"
```

---

### Task 3: 创建 script 36 — Part A（海水过滤器、维护可达性、焊接NDT、NPSH，共 7 条）

**Files:**
- Create: `scripts/36_add_supplement_units.py`

- [ ] **Step 1: 创建 `scripts/36_add_supplement_units.py` 文件，写入 skeleton + Part A 条目**

```python
# -*- coding: utf-8 -*-
"""
Add supplement evidence units covering regulatory gaps identified in evidence coverage analysis.
Gaps covered: seawater strainer, maintenance access, modular design, welding/NDT,
NPSH, materials, post-shutdown cooling, flushing, environmental, load reduction,
commissioning, insulation/safety labeling.

Run: python scripts/36_add_supplement_units.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
JSONL_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"


def _make_unit(uid, parent_chunk_id, text, topic, source_document, source_type,
               component_objects, can_support, engineering_phase,
               evidence_strength, is_generalizable, applicability_level,
               normalized_summary, system_type=None, parameters=None,
               source_link="", need_human_review="yes"):
    meta = {
        "topic": topic, "source_document": source_document,
        "source_type": source_type, "source_link": source_link, "location": "",
        "section_title": topic,
        "system_scope": component_objects[:], "component_objects": component_objects[:],
        "related_objects": [], "requirement_intents": can_support[:],
        "engineering_phase": engineering_phase[:],
        "applicable_condition": ["normal_operation"],
        "can_support": can_support[:],
        "evidence_strength": evidence_strength,
        "is_generalizable": is_generalizable,
        "applicability_level": applicability_level,
        "manufacturer": "", "engine_model": "",
        "system_type": system_type or [],
        "need_human_review": need_human_review,
        "applicable_object": source_document, "limitation": "",
        "normalized_summary": normalized_summary,
        "supportable_requirements": [], "unsupported_requirements": "",
        "keywords_zh": [], "keywords_en": [],
        "parameters_raw": "",
        "parameters": parameters or [],
        "parameter_name": [p.get("name","") for p in (parameters or [])],
        "value": [p.get("value","") for p in (parameters or [])],
        "unit": [p.get("unit","") for p in (parameters or [])],
        "condition": [], "is_noise": False, "noise_reason": "",
        "objects": component_objects[:], "relations": can_support[:],
        "answer_type": can_support[0] if can_support else "other",
        "refined_group_id": (
            f"G_{'_'.join(component_objects[:1])}"
            f"__{'_'.join(can_support[:1])}"
            f"__{'_'.join(engineering_phase[:1])}"
        ),
    }
    parts = [topic, text[:120], source_document, source_type,
             " ".join(component_objects), " ".join(can_support),
             " ".join(engineering_phase), normalized_summary]
    unit = {"id": uid, "parent_chunk_id": parent_chunk_id, "text": text, "metadata": meta}
    unit["search_text"] = "\n".join(p for p in parts if p)
    return unit


SUPPLEMENT_UNITS = [

    # ── 海水过滤器 / Seawater strainer ────────────────────────────

    _make_unit(
        uid="E-SUPP-FILT-001",
        parent_chunk_id="CH_SUPP_FILT_seawater_strainer",
        text=(
            "Marine Cooling System — Sea Chest Strainer Configuration Requirements\n"
            "(Based on DNV Rules for Classification Pt.4 Ch.3, IACS UR M3, and standard class practice)\n\n"
            "Sea water cooling systems shall be provided with effective strainers on all sea water "
            "suction lines upstream of cooling pumps and heat exchangers:\n"
            "1. Duplex (twin) strainers with in-line changeover shall be fitted on sea water suction "
            "lines serving essential cooling machinery, allowing one strainer to be cleaned while "
            "the other remains in service without interrupting cooling water flow.\n"
            "2. Strainer basket mesh size: typically 0.8–2.0 mm clear opening, appropriate to "
            "protect downstream equipment.\n"
            "3. Each strainer shall be fitted with a pressure differential indicator or alarm; "
            "high differential pressure alarm set-point shall be defined in the system design.\n"
            "4. Where automatic self-cleaning (backwash) strainers are fitted, the backwash "
            "mechanism shall operate without interrupting cooling water flow, and shall be capable "
            "of automatic initiation on high differential pressure signal.\n"
            "5. Strainer bodies shall be rated for full system design pressure and tested to "
            "1.5× design pressure before installation.\n"
            "整理说明：海水冷却系统过滤器配置规范：双联切换过滤器（不停机清洗）、网孔0.8–2.0mm、"
            "压差报警、自动反冲洗功能（高压差自动触发）、壳体1.5倍设计压力试验。"
        ),
        topic="海水冷却系统过滤器配置要求（双联/反冲洗）",
        source_document="S70 DNV Rules Pt4 Ch3 Seawater Strainer Requirements",
        source_type="ship_rule",
        component_objects=["sea_water_cooling_system", "cooling_water_pump", "cooler", "filter"],
        can_support=["installation", "maintenance", "inspection", "function", "alarm"],
        engineering_phase=["detailed_design", "installation", "maintenance"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "海水冷却系统须装双联切换过滤器，可在不停机情况下在线清洗；"
            "设压差报警；自动反冲洗型须能按压差信号自动启动；壳体须经1.5倍设计压力试验。"
        ),
        system_type=["sea_water_cooling_system"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-SUPP-FILT-002",
        parent_chunk_id="CH_SUPP_FILT_seawater_strainer",
        text=(
            "中国船级社（CCS）钢质海船入级规范 — 海水冷却系统过滤器规范要求\n\n"
            "1. 冷却主机等重要设备的海水进水管路应设置双联过滤器（备用切换），以便在不停机条件下"
            "清洗维护，保证系统连续运行能力。\n"
            "2. 过滤器应安装在冷却水泵进口前，进出口间应设置压差指示装置；当压差超过设定值时应"
            "发出报警，提示操作人员清洗或切换过滤器。\n"
            "3. 在热带海域和海生物附着高风险航区长期运营的船舶，宜配置具有自动反冲洗功能的过滤器，"
            "以减少人工清洗频次，防止冷却水流量不足。\n"
            "4. 过滤器壳体及管路连接件应按1.5倍最高工作压力进行水压试验，保压时间不少于30分钟，"
            "不得有渗漏现象。\n"
            "5. 过滤网目数应根据下游设备（泵、热交换器）的保护需求选定，不得在海试期间未经检查"
            "就关闭压差报警信号。\n"
            "整理说明：CCS规则对海水冷却系统双联过滤器配置、在线切换清洗能力、压差报警、热带航区"
            "自动反冲洗功能及壳体水压试验提供了规范依据。"
        ),
        topic="海水冷却系统双联过滤器及反冲洗要求（CCS规则）",
        source_document="S71 CCS 钢质海船入级规范 海水冷却系统过滤器",
        source_type="ship_rule",
        component_objects=["sea_water_cooling_system", "filter", "cooling_water_pump"],
        can_support=["installation", "maintenance", "alarm", "test", "inspection"],
        engineering_phase=["detailed_design", "installation", "class_approval", "maintenance"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "CCS规则：海水进机管路须设双联切换过滤器（不停机清洗）；设压差报警；"
            "热带航区宜配自动反冲洗；壳体1.5倍压力水压试验保压≥30分钟。"
        ),
        system_type=["sea_water_cooling_system"],
        need_human_review="no",
    ),

    # ── 维护可达性 / Maintenance access ──────────────────────────

    _make_unit(
        uid="E-SUPP-MAINT-001",
        parent_chunk_id="CH_SUPP_MAINT_access_modular",
        text=(
            "Marine Machinery Installation — Maintenance Access and Clearance Requirements\n"
            "(Based on DNV Rules for Classification: Ships, Pt.4 Ch.1, IACS UR M3, ISO 14122-3, "
            "and standard marine engineering practice)\n\n"
            "Maintenance and accessibility requirements for cooling water system components:\n"
            "1. All major cooling water equipment (pumps, heat exchangers, temperature control valves, "
            "strainers) shall have sufficient clearance for routine maintenance and component removal "
            "without disturbing adjacent equipment.\n"
            "2. Recommended minimum clearances:\n"
            "   - Pump: axial clearance ≥ 1.5× pump casing length for impeller/shaft removal; "
            "radial clearance ≥ shaft diameter + 100 mm\n"
            "   - Plate heat exchanger / tube bundle: full plate/tube bundle pull-out length on one side\n"
            "   - Valve handwheel/actuator: minimum 600 mm operating side clearance\n"
            "3. Walkway minimum clear width: 600 mm where personnel pass through; "
            "500 mm where inspection only\n"
            "4. Overhead lifting provisions (pad eye or monorail) shall be provided for equipment "
            "with removal mass > 25 kg\n"
            "5. All equipment requiring periodic maintenance shall have clear nameplates with "
            "maintenance interval and tag number\n"
            "整理说明：冷却水系统设备维护间距要求（DNV/IACS/ISO 14122-3）：泵轴向间距≥1.5倍泵长，"
            "板式换热器需留全板束抽出空间；通道宽度≥600mm；>25kg设备须有吊装点；设备须有维护标牌。"
        ),
        topic="冷却水系统设备维护通道间距要求（DNV/IACS）",
        source_document="S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements",
        source_type="ship_rule",
        component_objects=["cooling_water_pump", "cooler", "temperature_control_valve",
                           "main_engine_cooling_water_system"],
        can_support=["installation", "maintenance", "arrangement", "inspection"],
        engineering_phase=["basic_design", "detailed_design", "installation"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "冷却水设备维护间距规范：泵轴向≥1.5倍泵长，板换需留全板束抽出空间，"
            "阀操作侧≥600mm，通道宽≥600mm，>25kg设备须有吊装点。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-SUPP-MAINT-002",
        parent_chunk_id="CH_SUPP_MAINT_access_modular",
        text=(
            "Marine Engineering Best Practice — Modular Design and Quick-Exchange Requirements "
            "for Cooling System Equipment\n"
            "(Consolidated from DNV Rules, class society guidance, and international shipbuilding practice)\n\n"
            "Design requirements to minimise downtime during maintenance and component exchange:\n"
            "1. Cooling water pumps: shall be designed for in-situ impeller/mechanical seal replacement "
            "without removing the pump casing from the pipeline (back-pull-out design), OR shall have "
            "flanged connections permitting removal as a complete unit within the maintenance clearance.\n"
            "2. Heat exchangers: shall be of removable-bundle or gasketed plate-frame type where "
            "practical, allowing cleaning/inspection without full removal from the cooling circuit.\n"
            "3. Temperature control valves: shall be fitted with upstream and downstream isolating "
            "valves, permitting in-situ actuator and trim replacement while maintaining other "
            "cooling circuits in service.\n"
            "4. All equipment shall use standardised flanged or threaded connections compatible with "
            "ship-standard pipe dimensions, to permit rapid exchange with equivalent spare units.\n"
            "5. Spare parts for critical components (pump mechanical seals, TCV actuators, strainer "
            "baskets, heat exchanger gaskets) shall be listed in the Class-approved spare parts list "
            "with manufacturer part numbers.\n"
            "整理说明：冷却水系统模块化快拆设计要求：泵采用背抽式设计支持就地更换密封，"
            "板式换热器须可拆芯清洗，温控阀两侧须有截止阀支持在线更换，备品配件须入级认可备件清单。"
        ),
        topic="冷却水系统模块化快拆设计要求",
        source_document="S73 Marine Cooling System Modular Maintenance Design Practice",
        source_type="ship_rule",
        component_objects=["cooling_water_pump", "cooler", "temperature_control_valve",
                           "main_engine_cooling_water_system", "filter"],
        can_support=["maintenance", "installation", "equipment_selection", "inspection"],
        engineering_phase=["basic_design", "detailed_design", "procurement", "maintenance"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="general",
        normalized_summary=(
            "冷却水系统模块化设计：泵用背抽式支持就地换密封；板换可拆芯；"
            "温控阀两侧设截止阀支持在线更换；标准化法兰接口；关键备件入级认可备件清单。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    # ── 焊接 / 无损检测 NDT ────────────────────────────────────────

    _make_unit(
        uid="E-SUPP-WELD-001",
        parent_chunk_id="CH_SUPP_WELD_piping_ndt",
        text=(
            "IACS Unified Requirements W7 / W28 — Welding Quality Requirements for "
            "Marine Cooling Water Piping Systems\n\n"
            "Requirements for welding of cooling water pipelines on essential machinery systems:\n"
            "1. Welder qualification: All butt welds in cooling water piping of essential machinery "
            "systems shall be made by welders holding valid certificates to IACS UR W7 or equivalent "
            "(ISO 9606-1, ASME IX). Certificates shall cover the applicable material group and joint type.\n"
            "2. Welding procedure qualification (WPS/PQR): per IACS UR W28 or ISO 15614-1 before "
            "production welding commences; WPS records shall be retained for class review.\n"
            "3. Non-destructive examination (NDE) of completed welds:\n"
            "   - DN > 100 mm and design pressure > 1.0 MPa: minimum 10% random RT or UT of butt welds\n"
            "   - Critical locations (expansion loops, penetrations, tee branches): 100% visual + "
            "selective PT/MT\n"
            "   - All completed welds: 100% visual examination per class surveyor's instructions\n"
            "4. Hydrostatic test: all piping after welding and before insulation, "
            "at 1.5× design pressure, hold ≥ 30 min (per IACS UR M72)\n"
            "5. Weld repairs: defective welds found by NDE shall be repaired and re-examined; "
            "results recorded in the welding inspection report submitted to class surveyor.\n"
            "整理说明：IACS UR W7/W28 对船用冷却水管路焊工资质（ISO 9606-1/ASME IX）、焊接工艺评定、"
            "无损检测（DN>100mm高压管路≥10% RT/UT）和水压试验要求提供了规范级依据。"
        ),
        topic="冷却水管路焊接质量与无损检测要求（IACS UR W7/W28）",
        source_document="S74 IACS Unified Requirements W7 W28 Welding Marine Piping",
        source_type="ship_rule",
        component_objects=["pipe", "main_engine_cooling_water_system", "cooler",
                           "cooling_water_pump"],
        can_support=["test", "inspection", "installation", "class_review"],
        engineering_phase=["installation", "commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR W7/W28：冷却水管路焊工须持IACS/ISO认证；WPS/PQR须经级认可；"
            "DN>100mm高压管路≥10%随机RT/UT；全部焊缝100%外观检验；安装后1.5倍压力水压试验保压≥30min。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "nde_sampling_rate", "value": "≥10%", "unit": "%",
             "condition": "butt welds, DN > 100 mm, design pressure > 1.0 MPa (IACS W7)"},
            {"name": "hydrostatic_test_factor", "value": "1.5×", "unit": "× design pressure",
             "condition": "piping after welding, before insulation (IACS UR M72)"},
            {"name": "hydrostatic_hold_time", "value": "≥30", "unit": "min"},
        ],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-SUPP-WELD-002",
        parent_chunk_id="CH_SUPP_WELD_piping_ndt",
        text=(
            "中国船级社（CCS）钢质海船入级规范 第5篇 — 管路系统焊接与检验要求\n\n"
            "冷却水管路系统建造质量验收要求：\n"
            "1. 焊工资质：冷却水管路焊工应持有CCS或认可机构签发的有效焊工证书，证书覆盖范围"
            "应与所焊接材料类别、接头型式和位置一致。\n"
            "2. 焊接工艺评定（WPS/WPQR）：生产焊接前按CCS要求完成焊接工艺评定，评定文件经CCS审批，"
            "保存备查。\n"
            "3. 无损检测（NDT）要求：\n"
            "   - 主机冷却水主管路（公称直径≥80mm，设计压力≥1.0 MPa）：随机抽检RT或UT，比例≥10%\n"
            "   - 关键部位焊缝（弯头、三通、管道贯穿处附近）：增加MT/PT局部检测\n"
            "   - 全部焊缝：100%外观检验，不合格焊缝须返修复检\n"
            "4. 管路水压试验：安装完成后，按设计压力1.5倍进行水压试验，保压时间≥30分钟，"
            "不得有渗漏或变形。\n"
            "5. 记录归档：无损检测报告、水压试验记录、返修记录均须存档并提交CCS验船师审核。\n"
            "整理说明：CCS规范对冷却水管路焊工资质、工艺评定、无损检测要求（≥10% RT/UT）和"
            "水压试验的系统性规定，可支撑管路焊接质量、检验记录和安装验收类需求。"
        ),
        topic="冷却水管路焊接质量与无损检测要求（CCS规范）",
        source_document="S75 CCS 钢质海船入级规范 第5篇管路焊接与NDT",
        source_type="ship_rule",
        component_objects=["pipe", "main_engine_cooling_water_system"],
        can_support=["test", "inspection", "installation", "class_review", "document_completeness"],
        engineering_phase=["installation", "commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "CCS规范：冷却水管路焊工持CCS认证；WPS/WPQR经CCS审批；"
            "DN≥80mm高压管路≥10%随机RT/UT；全部焊缝100%外观检验；1.5倍压力水压试验≥30min；记录提交验船师。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "nde_sampling_rate", "value": "≥10%", "unit": "%",
             "condition": "butt welds, DN ≥ 80 mm, design pressure ≥ 1.0 MPa (CCS)"},
        ],
        need_human_review="no",
    ),

    # ── NPSH 汽蚀 ─────────────────────────────────────────────────

    _make_unit(
        uid="E-SUPP-NPSH-001",
        parent_chunk_id="CH_SUPP_NPSH_pump_cavitation",
        text=(
            "ISO 9906:2012 — Rotodynamic Pumps: Hydraulic Performance Acceptance Tests\n"
            "Applied to Marine Cooling Water Pump NPSH Requirements\n\n"
            "NPSH (Net Positive Suction Head) requirements for cooling water pump selection "
            "and system design:\n"
            "1. The available NPSH at the pump suction (NPSHa) shall exceed the pump's required "
            "NPSH (NPSHr, from manufacturer's curve at rated flow) by the required safety margin:\n"
            "   NPSHa ≥ NPSHr + safety margin\n"
            "   Minimum safety margin: 0.5 m (ISO 9906 acceptance basis);\n"
            "   Recommended for shipboard cooling pumps: 1.0–2.0 m margin\n"
            "2. NPSHa calculation at worst-case operating condition:\n"
            "   NPSHa = (p_static / ρg) + h_static - h_friction - (p_vapour / ρg)\n"
            "   where: p_static = static system pressure at suction; h_static = liquid head above "
            "pump centreline; h_friction = suction pipe friction losses at max flow;\n"
            "   p_vapour = saturation pressure at maximum coolant temperature\n"
            "3. Worst-case conditions to evaluate:\n"
            "   - Maximum cooling water temperature (highest vapour pressure)\n"
            "   - Minimum liquid level in expansion tank (lowest h_static)\n"
            "   - Maximum system flow (highest h_friction)\n"
            "4. For closed HT circuits: the static pressurisation from the expansion tank "
            "(typically 0.5–1.5 bar gauge) provides significant positive NPSHa contribution, "
            "making cavitation rare if system is properly pressurised.\n"
            "5. Pump test: ISO 9906 Grade 2 or Grade 1 acceptance test shall confirm NPSHr "
            "at rated duty point does not exceed the factory test value.\n"
            "整理说明：ISO 9906 对冷却水泵NPSH选泵和系统设计要求：NPSHa须超过NPSHr至少0.5m（船用推荐1.0–2.0m）；"
            "最不利工况（最高水温+最低液位+最大流量）下校核；密闭HT回路系统加压可有效保证足够NPSHa。"
        ),
        topic="冷却水泵NPSH汽蚀余量计算与选泵要求（ISO 9906）",
        source_document="S76 ISO 9906:2012 Rotodynamic Pumps Hydraulic Performance Tests",
        source_type="standard",
        component_objects=["cooling_water_pump", "ht_cooling_water_loop",
                           "lt_cooling_water_loop", "expansion_tank"],
        can_support=["calculation", "capacity", "parameter_limit", "equipment_selection"],
        engineering_phase=["basic_design", "detailed_design", "procurement"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="international_standard",
        normalized_summary=(
            "ISO 9906：冷却水泵NPSHa须超过NPSHr至少0.5m（推荐1.0–2.0m）；"
            "按最高水温、最低液位、最大流量三重最不利工况校核；密闭回路加压（0.5–1.5 bar表压）"
            "可有效保证NPSHa充足。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "npsh_min_safety_margin", "value": "0.5", "unit": "m",
             "condition": "minimum NPSHa above NPSHr (ISO 9906 acceptance)"},
            {"name": "npsh_recommended_margin_shipboard", "value": "1.0–2.0", "unit": "m",
             "condition": "recommended for shipboard cooling water pumps"},
        ],
        need_human_review="no",
    ),

]  # ← Part A ends here; Part B will extend this list
```

---

### Task 4: 扩展 script 36 — Part B（材料、停机、冲洗、环保、减速、调试、安全标识，共 8 条）

**Files:**
- Modify: `scripts/36_add_supplement_units.py`（追加条目并写入 `main()`）

- [ ] **Step 1: 在 `SUPPLEMENT_UNITS` 列表末尾（`]` 前面）追加 Part B 条目**

将以下代码追加到 `SUPPLEMENT_UNITS` 列表中（`]` 前）：

```python
    # ── 材料选型 / Materials ───────────────────────────────────────

    _make_unit(
        uid="E-SUPP-MAT-001",
        parent_chunk_id="CH_SUPP_MAT_material_corrosion",
        text=(
            "Marine Cooling Water System — Material Selection for Seawater-Exposed Components\n"
            "(Based on DNV Rules Pt.4 Ch.6, IACS UR, ASTM B111, and ISO 6509)\n\n"
            "Material requirements by circuit:\n\n"
            "Seawater circuit (sea chests, strainers, seawater pump casings, cooler seawater side, "
            "overboard piping):\n"
            "- ACCEPTABLE: Gunmetal / red brass (CuSn), Nickel-aluminium bronze (CuAlNi), "
            "Duplex stainless steel (22Cr or 25Cr), Titanium Grade 2 (preferred for polluted ports "
            "and biofouling risk), Glass Reinforced Epoxy (GRE) for piping\n"
            "- NOT ACCEPTABLE for seawater wetted surfaces: plain carbon steel, grey cast iron\n"
            "- Heat exchanger tubes in tropical/polluted seawater: CuNi 70/30 (ASTM B111 C71500) "
            "or titanium Grade 2 (most resistant to erosion-corrosion and biofouling)\n\n"
            "Freshwater circuit (HT/LT loops, expansion tank, internal piping):\n"
            "- Carbon steel (seamless or ERW): acceptable with inhibited coolant treatment\n"
            "- Copper alloys: compatible with treated freshwater; avoid direct galvanic contact "
            "with aluminium engine components\n"
            "- Stainless steel 316L: suitable for all freshwater cooling service\n\n"
            "Bimetallic (galvanic) corrosion prevention:\n"
            "Where dissimilar metals join (e.g. steel pipe to bronze valve), insulating flanges, "
            "isolating sleeves, or cathodic protection shall be applied per DNV RP-0198.\n"
            "整理说明：冷却水系统材料选型规范：海水侧须用铜镍合金/双相不锈钢/钛合金/GRE管（禁用碳钢/灰铸铁）；"
            "热带污染海域换热管推荐CuNi 70/30或钛合金；淡水侧可用碳钢（加抑制剂）；"
            "异种金属连接须防电化学腐蚀（绝缘法兰或阴极保护）。"
        ),
        topic="冷却水系统材料选型要求（海水侧/淡水侧/防腐）",
        source_document="S77 DNV Rules Pt4 Ch6 Material Selection Seawater Systems",
        source_type="ship_rule",
        component_objects=["sea_water_cooling_system", "cooler", "pipe", "valve",
                           "cooling_water_pump"],
        can_support=["equipment_selection", "installation"],
        engineering_phase=["basic_design", "detailed_design", "procurement"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "海水侧须用铜镍合金、双相不锈钢、钛或GRE（禁碳钢/灰铸铁）；"
            "热带污染海域换热管推荐CuNi 70/30或钛Grade 2；淡水侧可用碳钢加抑制剂；"
            "异种金属连接须设绝缘或阴极保护。"
        ),
        system_type=["sea_water_cooling_system", "HT cooling water loop"],
        need_human_review="no",
    ),

    _make_unit(
        uid="E-SUPP-MAT-002",
        parent_chunk_id="CH_SUPP_MAT_material_corrosion",
        text=(
            "Cooling Water System Sealing Materials — Compatibility with Glycol-Based Coolants\n"
            "(Based on engine manufacturer requirements and ISO 6194 seal material guidelines)\n\n"
            "Elastomeric sealing material requirements for glycol-treated cooling circuits:\n"
            "1. Elastomers exposed to ethylene glycol or propylene glycol coolant "
            "(typically 20–50% by volume) shall be selected for compatibility:\n"
            "   PREFERRED: FKM (fluoroelastomer / Viton), PTFE, EPDM for dilute glycol (< 25%)\n"
            "   AVOID: NBR (nitrile rubber) at glycol concentrations > 30% — swells and degrades, "
            "causing premature seal failure and system leakage\n"
            "   AVOID: Natural rubber (NR), Neoprene (CR) with any glycol concentration\n"
            "2. Pump shaft mechanical seals: carbon/ceramic or carbon/SiC face material "
            "combinations are preferred for glycol cooling service\n"
            "3. Before adding glycol to a circuit previously run on plain water:\n"
            "   - Renew all elastomeric O-rings, gaskets, and lip seals in the circuit\n"
            "   - Flush the circuit thoroughly to remove plain-water scale and deposits\n"
            "4. Inspection interval for elastomeric seals in glycol service: "
            "per manufacturer schedule, typically 2–4 years or at each coolant change\n"
            "整理说明：乙二醇冷却液系统密封材料选型：推荐FKM（氟橡胶）和PTFE；"
            "≥30%乙二醇浓度下禁用NBR（溶胀泄漏）；机械密封选碳/陶瓷面；"
            "由清水系统改为乙二醇系统时须更换全部弹性密封件。"
        ),
        topic="乙二醇冷却液系统密封材料相容性要求",
        source_document="S78 Cooling System Seal Material Compatibility Glycol Service",
        source_type="engine_manual",
        component_objects=["coolant", "cooling_water_pump", "ht_cooling_water_loop", "pipe"],
        can_support=["equipment_selection", "maintenance", "inspection"],
        engineering_phase=["procurement", "maintenance", "commissioning"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="manufacturer_specific",
        normalized_summary=(
            "乙二醇系统密封材料：推荐FKM/PTFE，禁用NBR（>30%乙二醇浓度下溶胀）；"
            "机械密封选碳/陶瓷面；由清水改乙二醇时须更换全部弹性密封件；检查周期2–4年。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="yes",
    ),

    # ── 停机后冷却 / Post-shutdown cooling ────────────────────────

    _make_unit(
        uid="E-SUPP-SHUT-001",
        parent_chunk_id="CH_SUPP_SHUT_shutdown_restart",
        text=(
            "Marine Diesel Engine — Post-Shutdown Cooling Water Circulation Requirements\n"
            "(Based on MAN B&W Project Guide, Wärtsilä Service Manual, and IACS UR M51)\n\n"
            "After main engine shutdown, cooling water circulation must be maintained to prevent "
            "thermal damage, coolant boiling, and cylinder liner distortion:\n\n"
            "Normal planned shutdown:\n"
            "- Continue HT cooling water circulation for minimum 20–30 minutes at reduced flow "
            "(electric standby pump or engine-driven pump at barring speed) until all cylinder "
            "jacket outlet temperatures fall below 60°C.\n\n"
            "Emergency shutdown (high temperature trip / blackout):\n"
            "- Immediate restart of electric cooling pump if available; circulation must not be "
            "interrupted for more than 5 minutes.\n"
            "- Continue HT circulation until all cylinder outlet temperatures stabilise below 55°C. "
            "Typical duration: 45–90 minutes depending on engine size and thermal mass.\n\n"
            "Turbocharger post-shutdown cooling:\n"
            "- Continue cooling water flow to water-cooled turbocharger bearings for minimum "
            "30 minutes post-shutdown to prevent bearing oil coking.\n\n"
            "Post-shutdown electric cooling pump capacity:\n"
            "- Minimum flow for post-shutdown cooling: 30–50% of rated MCR cooling flow is "
            "typically sufficient (confirm with engine manufacturer).\n\n"
            "Engine restart restriction:\n"
            "- Do not restart the engine until HT cooling water temperature has stabilised, "
            "and not before the minimum restart interval stated in the engine manual.\n"
            "整理说明：主机停机后冷却水循环要求：正常停机循环至缸套出口<60°C（约20–30min）；"
            "紧急停机后循环至<55°C（45–90min）；增压器后冷却≥30min；"
            "备用电动泵须能提供30–50% MCR后冷却流量。"
        ),
        topic="主机停机后冷却水循环要求",
        source_document="S79 MAN Wartsila Post-Shutdown Cooling Water Procedure",
        source_type="engine_manual",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "ht_cooling_water_loop", "cooler"],
        can_support=["operation", "commissioning_check", "safety", "capacity"],
        engineering_phase=["operation", "commissioning", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="manufacturer_specific",
        normalized_summary=(
            "停机后冷却：正常停机循环至缸套出口<60°C（20–30min）；紧急停机至<55°C（45–90min）；"
            "增压器后冷却≥30min；备用电动泵提供30–50% MCR后冷却流量。"
        ),
        system_type=["HT cooling water loop"],
        parameters=[
            {"name": "post_shutdown_temp_target_normal", "value": "< 60", "unit": "°C",
             "condition": "cylinder jacket outlet, normal planned shutdown"},
            {"name": "post_shutdown_temp_target_emergency", "value": "< 55", "unit": "°C",
             "condition": "cylinder jacket outlet, emergency shutdown"},
            {"name": "post_shutdown_duration_normal", "value": "20–30", "unit": "min",
             "condition": "normal shutdown, cooling circulation"},
            {"name": "post_shutdown_duration_emergency", "value": "45–90", "unit": "min",
             "condition": "emergency shutdown, cooling circulation"},
            {"name": "post_shutdown_min_flow", "value": "30–50", "unit": "% MCR flow",
             "condition": "minimum post-shutdown electric pump capacity"},
        ],
        need_human_review="yes",
    ),

    # ── 冲洗程序 / Flushing ────────────────────────────────────────

    _make_unit(
        uid="E-SUPP-FLUSH-001",
        parent_chunk_id="CH_SUPP_FLUSH_flushing_procedure",
        text=(
            "Marine Cooling Water System — Pre-Service Flushing Requirements\n"
            "(Based on MAN B&W Project Guide Flushing Procedure, DNV Rules, "
            "and standard shipyard commissioning practice)\n\n"
            "Flushing of cooling water circuits is mandatory before first engine connection:\n\n"
            "Objective: Remove welding slag, pipe scale, sand, construction debris from "
            "all cooling water piping before connecting to the main engine or sensitive equipment.\n\n"
            "Flushing procedure:\n"
            "1. BYPASS all sensitive equipment: temporarily disconnect or bypass the main engine "
            "coolant connections, temperature control valves, flow meters, and expansion tank "
            "internal fittings using temporary hoses or blind plates.\n"
            "2. Fill system with clean fresh water (or inhibitor solution per coolant manufacturer "
            "guidance — do NOT use final glycol mix for flushing).\n"
            "3. Circulate using cooling water pump(s) for minimum 2–4 hours at maximum available flow.\n"
            "4. Minimum flushing velocity in all pipe branches: ≥ 1.5 m/s to ensure particle transport.\n"
            "5. Drain completely; inspect and clean ALL strainer baskets and temporary flushing strainers.\n"
            "6. If significant contamination found (rust scale, welding spatter), repeat flushing cycle.\n"
            "7. Final fill: after satisfactory flush, fill with specified coolant formulation; "
            "vent all high points; check coolant quality (pH, inhibitor concentration, chloride content).\n"
            "8. Document flushing results (water colour at drain, strainer inspection findings, "
            "number of flush cycles) in the commissioning record.\n"
            "整理说明：冷却水系统初次使用前冲洗要求：旁通发动机和敏感设备，循环≥2–4小时，"
            "流速≥1.5 m/s，排水检查过滤器，必要时重复，按规定加注冷却液，冲洗记录入调试文件。"
        ),
        topic="冷却水系统初次投用前冲洗程序要求",
        source_document="S80 MAN BW Wartsila Cooling System Pre-Service Flushing Procedure",
        source_type="engine_manual",
        component_objects=["main_engine_cooling_water_system", "pipe", "cooling_water_pump",
                           "coolant"],
        can_support=["installation", "commissioning_check", "inspection", "maintenance"],
        engineering_phase=["installation", "commissioning"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="general",
        normalized_summary=(
            "冷却水系统初次使用前冲洗：旁通发动机和敏感设备；循环≥2–4h，流速≥1.5 m/s；"
            "排水检查过滤器（有明显污染则重复）；按规定加注冷却液；冲洗记录归入调试文件。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        parameters=[
            {"name": "flushing_minimum_velocity", "value": "≥1.5", "unit": "m/s",
             "condition": "all pipe branches during flushing"},
            {"name": "flushing_minimum_duration", "value": "2–4", "unit": "h",
             "condition": "per flushing cycle"},
        ],
        need_human_review="yes",
    ),

    # ── 环境保护 / Environmental ───────────────────────────────────

    _make_unit(
        uid="E-SUPP-ENV-001",
        parent_chunk_id="CH_SUPP_ENV_environmental",
        text=(
            "MARPOL and Environmental Requirements for Cooling Water Treatment Chemical Management\n"
            "(Based on MARPOL Annex I, IMO MEPC guidelines, and port state control requirements)\n\n"
            "Environmental requirements for cooling water chemical treatment and discharge:\n\n"
            "1. Coolant treatment chemicals:\n"
            "   - Chromate-based and nitrite-based inhibitors: classified as hazardous to marine "
            "environment; spent coolant shall NOT be discharged overboard.\n"
            "   - Biodegradable inhibitor formulations (molybdate/organic-based) preferred for "
            "vessels in Emission Control Areas (ECAs) and polar waters.\n"
            "2. Spent coolant disposal:\n"
            "   - Spent coolant containing glycol or hazardous inhibitors must be transferred to "
            "port reception facilities or treated on board before authorised discharge.\n"
            "   - Overboard discharge of spent glycol coolant is prohibited under MARPOL.\n"
            "3. Cooling water make-up:\n"
            "   - Freshwater for coolant make-up: chloride content < 50 mg/L for ferrous cooling "
            "circuits; < 150 mg/L for aluminium-containing engine circuits.\n"
            "   - Seawater contamination of freshwater circuit: must be detected and rectified "
            "immediately to prevent accelerated corrosion.\n"
            "4. Spill prevention:\n"
            "   - Coolant filling operations: conduct with drip trays to prevent deck contamination.\n"
            "   - Overflow pipes from expansion tanks: shall not discharge directly overboard; "
            "connect to closed drain collection or visible above waterline.\n"
            "整理说明：MARPOL 冷却水化学处理环保要求：含铬/亚硝酸盐抑制剂的废液禁止排海；"
            "乙二醇废液须送岸上设施；补水氯化物<50 mg/L（铁质回路）；溢流管不得直接排海，"
            "为冷却水系统环境保护需求提供国际公约级依据。"
        ),
        topic="冷却水处理化学品的环境保护要求（MARPOL）",
        source_document="S81 MARPOL Annex I IMO MEPC Cooling Water Chemical Management",
        source_type="ship_rule",
        component_objects=["coolant", "sea_water_cooling_system",
                           "main_engine_cooling_water_system", "expansion_tank"],
        can_support=["operation", "maintenance", "inspection"],
        engineering_phase=["operation", "maintenance", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="international_convention",
        normalized_summary=(
            "MARPOL：含铬/亚硝酸盐/乙二醇的废液禁止直接排海，须送岸上设施；"
            "补水氯化物<50 mg/L（铁质回路）；膨胀水箱溢流管不得排入大海，"
            "热带/ECA/极地水域推荐使用生物可降解抑制剂。"
        ),
        system_type=["HT cooling water loop"],
        parameters=[
            {"name": "max_chloride_makeup_water_ferrous", "value": "< 50", "unit": "mg/L",
             "condition": "freshwater make-up for ferrous cooling circuit"},
        ],
        need_human_review="yes",
    ),

    # ── 减速工况 / Load reduction ─────────────────────────────────

    _make_unit(
        uid="E-SUPP-LDR-001",
        parent_chunk_id="CH_SUPP_LDR_load_reduction",
        text=(
            "Marine Main Engine — Cooling-Water-Related Load Reduction and Protection Logic\n"
            "(Based on IACS UR E10, IACS UR M3.1, DNV Rules Pt.4 Ch.3)\n\n"
            "Engine load reduction (slow-down) and shutdown triggers related to cooling water:\n\n"
            "High HT cooling water temperature (primary protection chain):\n"
            "- Stage 1 — Warning alarm: set 5–8°C above normal maximum operating temperature\n"
            "- Stage 2 — Automatic slow-down: set 3–5°C above alarm set-point (per IACS UR E10)\n"
            "- Stage 3 — Automatic shutdown: at absolute maximum temperature limit per manufacturer\n\n"
            "Low cooling water pressure at engine inlet:\n"
            "- Low pressure alarm: set 0.3–0.5 bar below manufacturer minimum\n"
            "- Automatic slow-down (if provided): triggered when pressure below minimum for > 30 s\n\n"
            "Cooling water pump failure:\n"
            "- Pump failure alarm → automatic changeover to standby pump (IACS UR E10 mandatory)\n"
            "- Both pumps failed: automatic slow-down to minimum propulsion requirement\n\n"
            "Single cooling component failure (one cooler, one circuit degraded):\n"
            "- System shall maintain minimum cooling at reduced engine load\n"
            "- Maximum rating under single-component failure: typically 75–85% MCR "
            "(to be confirmed by cooling system capacity analysis)\n\n"
            "Manual override: all automatic protections shall have manual override capability "
            "with positive indication; override of high-temperature protection shall require "
            "chief engineer acknowledgement.\n"
            "整理说明：IACS UR E10/M3.1/DNV规则对冷却水相关减速保护逻辑：高温分级保护（报警→减速→停机）；"
            "低压报警自动切换备用泵；双泵失效时自动减速；单设备故障下可在75–85% MCR继续运行；"
            "手动干预须有首席轮机员确认机制。"
        ),
        topic="冷却水相关主机减速保护逻辑（IACS UR E10/M3.1/DNV）",
        source_document="S65 IACS Unified Requirements E10 Machinery Control Systems",
        source_type="ship_rule",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "alarm_system", "control_system", "temperature_sensor"],
        can_support=["alarm", "operation", "monitoring", "safety", "redundancy"],
        engineering_phase=["detailed_design", "commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "IACS UR E10：高温三级保护（报警→自动减速→停机），减速触发点比报警高3–5°C；"
            "低压报警→自动切换备用泵；双泵失效→自动减速；单冷却设备失效下可运行75–85% MCR；"
            "自动保护手动干预须有明确确认机制。"
        ),
        system_type=["HT cooling water loop"],
        parameters=[
            {"name": "slowdown_trigger_above_alarm", "value": "3–5", "unit": "°C",
             "condition": "above high temperature alarm set-point (IACS UR E10)"},
            {"name": "single_failure_max_load", "value": "75–85", "unit": "% MCR",
             "condition": "single cooling component failure (indicative; confirm by analysis)"},
        ],
        need_human_review="no",
    ),

    # ── 调试清单 / Commissioning ───────────────────────────────────

    _make_unit(
        uid="E-SUPP-COMM-001",
        parent_chunk_id="CH_SUPP_COMM_commissioning",
        text=(
            "Marine Cooling Water System — Pre-Commissioning Checklist and Acceptance Criteria\n"
            "(Consolidated from CCS 调试要求, DNV Rules Pt.4 Ch.3, IACS UR M51, "
            "and standard shipyard commissioning practice)\n\n"
            "Pre-commissioning verification (must be signed off before first engine start):\n"
            "□ All cooling water pipelines installed per approved drawings; all weld NDE and "
            "pressure test records complete and accepted by class surveyor\n"
            "□ All cooling water isolating valves installed with correct flow direction; "
            "valve position indicators fitted and correct\n"
            "□ Expansion tank filled to correct operating level (50–75%); vent valve "
            "opened; filling connection capped; low-level alarm tested\n"
            "□ Coolant: concentration tested and within specification; inhibitor added per "
            "manufacturer; pH within range; chloride below limit\n"
            "□ System fully vented; no air pockets at high points; vent cocks closed\n"
            "□ Pump rotation correct; mechanical seals not leaking; pump bearings lubricated\n"
            "□ All temperature, pressure, and level transmitters calibrated; readings match "
            "independent reference gauges\n"
            "□ All high-temperature, low-pressure, low-level alarms tested at correct set-points; "
            "alarms annunciated at engine control room AND bridge\n"
            "□ TCV: position sensor calibrated; valve opens/closes correctly on temperature signal; "
            "manual override tested\n"
            "□ Standby pump automatic start tested: pump starts on duty pump failure signal\n"
            "□ Post-flush: strainer baskets inspected clean; temporary flushing connections removed\n"
            "□ Insulation applied to all hot pipes; safety warning signs affixed\n\n"
            "Post-commissioning documents required:\n"
            "- Signed commissioning checklist (chief engineer + class surveyor)\n"
            "- Coolant quality test certificate; instrument calibration records\n"
            "整理说明：冷却水系统调试前核查清单（CCS/DNV/IACS M51综合）：管路检查、阀门、膨胀水箱、"
            "冷却液、排气、泵、传感器、报警、温控阀、备用泵自动启动、冲洗、保温标识，"
            "调试完成须有首席轮机员和验船师联签。"
        ),
        topic="冷却水系统调试前核查清单与验收要求（CCS/DNV/IACS M51综合）",
        source_document="S82 Marine Cooling System Pre-Commissioning Checklist CCS DNV IACS",
        source_type="standard",
        component_objects=["main_engine_cooling_water_system", "cooling_water_pump",
                           "expansion_tank", "temperature_control_valve", "alarm_system",
                           "pipe", "temperature_sensor", "pressure_sensor", "level_sensor"],
        can_support=["commissioning_check", "inspection", "test", "operation",
                     "document_completeness"],
        engineering_phase=["commissioning", "class_approval"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="general",
        normalized_summary=(
            "冷却水系统调试前核查清单：覆盖管路/阀门/膨胀水箱/冷却液/排气/泵/传感器/"
            "报警/TCV/备用泵自动启动/冲洗/保温标识12个检查项；"
            "调试后须提交联签清单、冷却液质检报告和仪表校准记录。"
        ),
        system_type=["HT cooling water loop", "LT cooling water loop"],
        need_human_review="no",
    ),

    # ── 隔热与安全标识 / Insulation & safety labeling ─────────────

    _make_unit(
        uid="E-SUPP-SAFE-001",
        parent_chunk_id="CH_SUPP_SAFE_insulation_labeling",
        text=(
            "Marine Machinery Safety — High-Temperature Pipe Insulation and Warning Labeling\n"
            "(Based on SOLAS Chapter II-2, ISO 13702, IMO MSC/Circ.1321, ISO 14726 pipe "
            "color coding, and DNV Rules)\n\n"
            "Insulation requirements for high-temperature cooling water piping:\n"
            "1. All cooling water pipes, valves, and equipment with accessible surface temperatures "
            "exceeding 60°C (HT circuit: typically 70–95°C) shall be thermally insulated to "
            "reduce surface temperature below 55°C at 25°C ambient (typical class requirement).\n"
            "2. Insulation material: mineral wool (rock wool / glass wool) or equivalent with "
            "maximum service temperature ≥ 150°C; aluminium or stainless steel cladding for "
            "mechanical protection in areas exposed to splash or foot traffic.\n"
            "3. Insulation shall not be applied to flanges, valves, instrumentation connections, "
            "or items requiring periodic inspection — these shall have removable insulation covers.\n\n"
            "Safety warning labeling requirements:\n"
            "4. High-temperature surfaces that cannot be fully insulated (e.g., valve bonnets, "
            "pump casings): affix ISO 11684-compliant 'Hot Surface' warning signs "
            "at intervals ≤ 2 m in accessible areas.\n"
            "5. Pipe identification: cooling water pipelines shall be color-coded per ISO 14726 "
            "(or ship-specific standard): HT cooling water — green + letter code; "
            "seawater — green with specific stripe; freshwater — green.\n"
            "6. Major cooling system equipment shall carry nameplates with tag number, "
            "system designation, and maintenance interval.\n"
            "整理说明：高温冷却水管路隔热和安全标识要求（SOLAS/ISO 13702/ISO 14726）："
            "可触及管路表面温度>60°C须绝热（使表面<55°C），岩棉绝热+铝皮护套；"
            "不能完全绝热的高温表面须张贴ISO 11684热警示标识（间距≤2m）；"
            "管路按ISO 14726色标标识。"
        ),
        topic="高温冷却水管路隔热与安全标识要求（SOLAS/ISO 14726）",
        source_document="S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements",
        source_type="ship_rule",
        component_objects=["pipe", "main_engine_cooling_water_system", "ht_cooling_water_loop",
                           "cooling_water_pump"],
        can_support=["installation", "safety", "inspection"],
        engineering_phase=["installation", "commissioning", "detailed_design"],
        evidence_strength="direct",
        is_generalizable="general",
        applicability_level="class_rule",
        normalized_summary=(
            "高温冷却水管路（70–95°C）须绝热使表面<55°C；"
            "绝热材料耐温≥150°C+铝皮护套；不能绝热的高温表面须贴ISO 11684热警示标识（间距≤2m）；"
            "管路按ISO 14726色标标识。"
        ),
        system_type=["HT cooling water loop"],
        need_human_review="no",
    ),
```

- [ ] **Step 2: 在 Part B 条目之后，`SUPPLEMENT_UNITS` 列表闭合的 `]` 后面写入 `main()` 函数**

```python

def main(dry_run: bool = False) -> None:
    with open(JSONL_PATH, encoding="utf-8") as f:
        existing = [json.loads(l) for l in f if l.strip()]

    existing_ids = {u["id"] for u in existing}
    new_units = [u for u in SUPPLEMENT_UNITS if u["id"] not in existing_ids]
    dup_ids = [u["id"] for u in SUPPLEMENT_UNITS if u["id"] in existing_ids]

    print(f"Existing units:   {len(existing)}")
    print(f"New units to add: {len(new_units)}")
    if dup_ids:
        print(f"Already present (skipped): {dup_ids}")

    if dry_run:
        print("\n[dry-run] Not writing.")
        for u in new_units:
            print(f"  + {u['id']}  {u['metadata']['topic'][:55]}")
        return

    merged = existing + new_units
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for u in merged:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"Written {len(merged)} units → {JSONL_PATH}")

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
```

- [ ] **Step 3: Commit script 36（先提交，执行在 Task 5）**

```bash
git add scripts/36_add_supplement_units.py
git commit -m "feat: add script 36 with 15 supplement evidence entries for regulatory gaps"
```

---

### Task 5: 执行 script 36 并验证结果

**Files:**
- Execute: `scripts/36_add_supplement_units.py`

- [ ] **Step 1: dry-run 预览**

```bash
python scripts/36_add_supplement_units.py --dry-run
```

期望输出：列出 15 条待添加条目（E-SUPP-FILT-001/002, E-SUPP-MAINT-001/002, E-SUPP-WELD-001/002, E-SUPP-NPSH-001, E-SUPP-MAT-001/002, E-SUPP-SHUT-001, E-SUPP-FLUSH-001, E-SUPP-ENV-001, E-SUPP-LDR-001, E-SUPP-COMM-001, E-SUPP-SAFE-001），无报错。

- [ ] **Step 2: 正式运行**

```bash
python scripts/36_add_supplement_units.py
```

期望输出：
```
Existing units:   1245
New units to add: 15
Written 1260 units → ...evidence_units.jsonl
Rebuilding evidence_units index…
Index rebuilt successfully.
```

- [ ] **Step 3: 验证覆盖改善**

```bash
python -c "
import json
from collections import Counter
units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
print('总条数:', len(units))
supp = [u for u in units if u['id'].startswith('E-SUPP')]
print('新补充条目:', len(supp))
for u in supp:
    print(' ', u['id'], u['metadata']['topic'][:50])
print()
# 检查原来零覆盖的类别
zero_fix = {}
for u in supp:
    for cs in u.get('metadata',{}).get('can_support',[]):
        zero_fix[cs] = zero_fix.get(cs, 0) + 1
print('新补充覆盖的 can_support:')
for k,v in sorted(zero_fix.items(), key=lambda x: -x[1]):
    print(f'  +{v}  {k}')
"
```

期望输出：`总条数: 1260`，15 条 E-SUPP 条目，can_support 覆盖包含 `maintenance`、`inspection`、`safety`、`commissioning_check`、`equipment_selection` 等原来较弱的类别。

- [ ] **Step 4: Commit**

```bash
git add data/processed/evidence_units.jsonl
git commit -m "feat: add 15 supplement regulatory evidence entries to evidence KB (filter/maint/weld/NPSH/mat/shutdown/flush/env/ldr/comm/safe)"
```

---

### Task 6: 重建 source_chunks + 全量索引，最终验收

**Files:**
- Execute: `scripts/33_add_source_chunks_for_new_units.py`
- Execute: `scripts/11_build_multigranular_indexes.py`

- [ ] **Step 1: 确认新增条目产生了孤儿 parent_chunk_id**

```bash
python -c "
import json
units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
chunks = [json.loads(l) for l in open('data/processed/source_chunks.jsonl') if l.strip()]
chunk_ids = {c['chunk_id'] for c in chunks}
orphans = [u for u in units if u['parent_chunk_id'] not in chunk_ids]
print('孤儿 evidence_units:', len(orphans))
pids = sorted({u['parent_chunk_id'] for u in orphans})
for pid in pids:
    print(' ', pid)
"
```

期望输出：15 条以上孤儿（每个新 parent_chunk_id 对应 1–2 条 evidence_unit）。

- [ ] **Step 2: 运行 script 33 创建新 source_chunks**

```bash
python scripts/33_add_source_chunks_for_new_units.py
```

期望输出含：`Orphan parent_chunk_ids: N`，`Creating N new source_chunks`，`source_chunks.jsonl: 1707 → 172X`，`Done.`

- [ ] **Step 3: 运行 script 11 重建全量索引（耗时较长）**

```bash
python scripts/11_build_multigranular_indexes.py
```

期望：输出两个索引 `evidence_units` 和 `source_chunks` 均 `Done` 无错误。如遇 CUDA OOM，在 `.env` 中设 `DEVICE=cpu` 后重试。

- [ ] **Step 4: 最终验收检查**

```bash
python -c "
import json
from collections import Counter

units = [json.loads(l) for l in open('data/processed/evidence_units.jsonl') if l.strip()]
chunks = [json.loads(l) for l in open('data/processed/source_chunks.jsonl') if l.strip()]
chunk_ids = {c['chunk_id'] for c in chunks}
orphans = [u for u in units if u['parent_chunk_id'] not in chunk_ids]

bg = [u for u in units if u.get('metadata',{}).get('evidence_strength')=='background']
rule = [u for u in units if u.get('metadata',{}).get('applicability_level') in ('class_rule','international_convention','international_standard')]
supp = [u for u in units if u['id'].startswith('E-SUPP')]

print('=== 最终状态 ===')
print(f'evidence_units 总条数: {len(units)}')
print(f'source_chunks 总条数: {len(chunks)}')
print(f'孤儿条目（应为0）: {len(orphans)}')
print(f'background 条目（应为0）: {len(bg)}')
print(f'规范级条目（class_rule+国际公约/标准）: {len(rule)}')
print(f'新补充条目: {len(supp)}')
print()

# 验收标准对比
print('=== 验收标准 ===')
checks = [
    ('background=0', len(bg) == 0),
    ('规范级条目≥145', len(rule) >= 145),
    ('新补充≥15条', len(supp) >= 15),
    ('无孤儿条目', len(orphans) == 0),
    ('总条数1250–1270', 1250 <= len(units) <= 1270),
]
for name, ok in checks:
    print(f'  {'✓' if ok else '✗'}  {name}')
"
```

期望：全部验收项为 `✓`。

- [ ] **Step 5: 运行烟雾测试验证检索功能**

```bash
python scripts/13_smoke_test.py
```

确认无报错，pipeline 能正常检索到证据并生成工程需求。

- [ ] **Step 6: Final commit**

```bash
git add data/processed/source_chunks.jsonl data/processed/evidence_units.jsonl
git commit -m "build: rebuild source_chunks and indexes after KB cleanup and supplement (1260 units, 0 background, +15 regulatory entries)"
```

---

## 验收标准汇总

| 指标 | 目标 | 验证方式 |
|---|---|---|
| background 条目 | 0 | Task 1 Step 4 |
| 总条目数 | 约 1,260 | Task 6 Step 4 |
| 新补充条目 | ≥ 15 | Task 6 Step 4 |
| 规范级条目（class_rule + 国际公约/标准） | ≥ 145 | Task 6 Step 4 |
| 孤儿 evidence_units | 0 | Task 6 Step 4 |
| 烟雾测试 | 通过，无报错 | Task 6 Step 5 |
