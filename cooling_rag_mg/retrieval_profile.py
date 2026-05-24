from __future__ import annotations

from typing import Any


def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item or item in seen:
            continue
        out.append(item)
        seen.add(item)
    return out


# ─────────────────────────────────────────────
# 部件映射：大幅扩充同义词，覆盖实际工程文档的表达变体
# ─────────────────────────────────────────────
COMPONENT_MAP: dict[str, list[str]] = {
    "main_engine_cooling_water_system": [
        "主机冷却水", "冷却水系统", "冷却水回路", "主机冷却",
        "cooling water system", "cooling system", "main engine cooling",
        "冷却系统", "淡水冷却", "淡水冷却系统",
    ],
    "central_cooling_system": [
        "中央冷却", "中央冷却系统", "central cooling",
    ],
    "sea_water_cooling_system": [
        "海水冷却", "海水侧", "海水泵", "海水管", "舷外水",
        "sea water", "raw water", "seawater",
    ],
    "jacket_water_cooling_system": [
        "缸套水", "缸套冷却", "jacket water", "jacket cooling",
        "高温淡水", "HT回路",
    ],
    "ht_cooling_water_loop": [
        "高温冷却", "高温水", "高温回路", "HT", "ht cooling",
        "高温淡水回路",
    ],
    "lt_cooling_water_loop": [
        "低温冷却", "低温水", "低温回路", "LT", "lt cooling",
        "低温淡水",
    ],
    "cooling_water_pump": [
        "冷却水泵", "淡水泵", "冷水泵", "循环泵", "循环水泵",
        "cooling water pump", "fresh water pump", "circulating pump",
        "水泵", "泵组",
    ],
    "sea_water_pump": [
        "海水泵", "原水泵", "舷外水泵",
        "sea water pump", "raw water pump",
    ],
    "cooler": [
        "冷却器", "换热器", "热交换器", "板式冷却器", "管壳式冷却器",
        "cooler", "heat exchanger", "plate cooler", "shell and tube",
    ],
    "central_cooler": [
        "中央冷却器", "central cooler",
    ],
    "charge_air_cooler": [
        "增压空气冷却器", "中冷器", "charge air cooler", "air cooler",
        "扫气冷却", "扫气冷却器",
    ],
    "jacket_water_cooler": [
        "缸套水冷却器", "jacket water cooler", "高温冷却器",
    ],
    "expansion_tank": [
        "膨胀水箱", "膨胀箱", "高位水箱", "补水箱",
        "expansion tank", "header tank", "surge tank",
    ],
    "temperature_control_valve": [
        "温控阀", "温度控制阀", "热力阀", "三通阀", "恒温阀",
        "thermostatic valve", "temperature control valve",
        "thermostatic mixing valve", "three-way valve",
    ],
    "pipe": [
        "管路", "管道", "管系", "配管", "管线",
        "pipe", "piping", "pipeline", "tubing",
    ],
    "valve": [
        "阀门", "截止阀", "闸阀", "蝶阀", "止回阀", "球阀",
        "valve", "gate valve", "butterfly valve", "check valve",
    ],
    "support": [
        "支架", "支吊架", "管夹", "固定件", "托架",
        "support", "bracket", "hanger", "clamp",
    ],
    "equipment_interface": [
        "设备接口", "法兰接口", "管口", "连接口", "接头",
        "connection", "interface", "flange", "nozzle",
    ],
    "filter": [
        "滤器", "过滤器", "海水滤器", "自清洗滤器", "Y型滤器",
        "strainer", "filter", "duplex strainer",
    ],
    "temperature_sensor": [
        "温度传感器", "温度计", "热电偶", "PT100",
        "temperature sensor", "thermometer", "temperature transmitter",
    ],
    "pressure_sensor": [
        "压力传感器", "压力表", "压差计",
        "pressure sensor", "pressure gauge", "pressure transmitter",
    ],
    "flow_sensor": [
        "流量传感器", "流量计", "流量开关",
        "flow sensor", "flow meter", "flow switch",
    ],
    "level_sensor": [
        "液位传感器", "液位计", "液位开关", "水位传感器",
        "level sensor", "level gauge", "level switch",
    ],
    "alarm_system": [
        "报警系统", "报警装置", "警报", "报警器",
        "alarm", "alarm system", "alarm device",
    ],
    "control_system": [
        "控制系统", "监控系统", "集控室", "PLC", "IAS", "AMS",
        "control system", "monitoring system", "automation system",
        "integrated alarm system", "engine control room",
    ],
    "coolant": [
        # 注意：不包含"冷却水"本身，避免误把系统级需求召回水质/防腐类证据
        "冷却液", "防冻液", "防腐剂", "缓蚀剂", "水处理剂", "添加剂", "乙二醇",
        "coolant additive", "inhibitor", "corrosion inhibitor", "antifreeze",
        "glycol", "water treatment chemical",
    ],
    "drain_point": [
        "放水点", "排放口", "疏水口",
        "drain", "drain point", "drain valve",
    ],
    "vent_point": [
        "排气点", "通气口", "放气阀", "脱气",
        "vent", "vent point", "deaeration", "air vent",
    ],
    "flushing_connection": [
        "冲洗接口", "冲洗管", "冲洗",
        "flushing", "flush", "flushing connection",
    ],
    "pressure_test_connection": [
        "试压接口", "压力试验接口", "水压试验",
        "pressure test", "hydrostatic test", "pressure test connection",
    ],
}

# ─────────────────────────────────────────────
# 方面映射：扩充同义词
# ─────────────────────────────────────────────
ASPECT_MAP: dict[str, list[str]] = {
    "reliability": [
        "可靠", "稳定", "航行安全", "可靠性", "故障率", "可用性",
        "reliability", "stable", "availability", "MTBF",
    ],
    "capacity": [
        "冷却能力", "换热能力", "容量", "散热", "热平衡",
        "capacity", "heat rejection", "heat transfer", "thermal balance",
    ],
    "temperature": [
        "温度", "热带", "高温", "进口温度", "出口温度",
        "temperature", "inlet temperature", "outlet temperature",
        "high temperature", "tropical",
    ],
    "pressure": [
        "压力", "背压", "压差", "工作压力", "设计压力",
        "pressure", "back pressure", "differential pressure",
    ],
    "flow": [
        "流量", "流速", "循环量", "额定流量",
        "flow", "flow rate", "circulation", "rated flow",
    ],
    "redundancy": [
        "冗余", "备用", "一用一备", "双泵", "备用泵", "冗余配置",
        "standby", "backup", "redundancy", "two-pump", "N+1",
    ],
    "control": [
        "控制", "调节", "自动控制", "手动控制", "远程控制",
        "control", "regulation", "automatic", "manual",
    ],
    "monitoring": [
        "监测", "监控", "显示", "集控", "远程监视", "参数显示",
        "monitor", "display", "remote monitoring",
    ],
    "alarm": [
        "报警", "警报", "高温报警", "低压报警",
        "alarm", "warning", "high temperature alarm",
    ],
    "shutdown": [
        "停机", "紧急停机", "保护停机",
        "shutdown", "emergency shutdown", "trip",
    ],
    "load_reduction": [
        "降负荷", "功率限制", "自动降速",
        "derating", "load reduction", "power limitation",
    ],
    "installation": [
        "安装", "施工", "现场安装", "安装工艺",
        "installation", "site installation", "mounting",
    ],
    "arrangement": [
        "布置", "管路布置", "走向", "紧凑", "布局",
        "arrangement", "layout", "routing",
    ],
    "accessibility": [
        "可达性", "操作空间", "检修空间", "通道", "可及性",
        "accessibility", "access", "working space",
    ],
    "maintenance": [
        "维护", "检修", "日常维护", "定期维护", "维修",
        "maintenance", "service", "overhaul",
    ],
    "cleaning": [
        "清洗", "清理", "除垢", "清洁",
        "cleaning", "clean", "descaling",
    ],
    "flushing": [
        "冲洗", "冲洗程序", "系统冲洗",
        "flushing", "flush", "system flushing",
    ],
    "pressure_test": [
        "压力试验", "水压试验", "试压", "气压试验",
        "pressure test", "hydrostatic test", "pressure testing",
    ],
    "commissioning": [
        "调试", "试车", "试航", "调试程序",
        "commissioning", "sea trial", "startup test",
    ],
    "inspection": [
        "检查", "检验", "巡检", "目视检查", "功能检查",
        "inspection", "check", "visual inspection",
    ],
    "calculation": [
        "计算", "计算书", "热平衡计算", "流量计算",
        "calculation", "heat balance", "flow calculation",
    ],
    "drawing_review": [
        "图纸", "审图", "图纸审查", "原理图", "布置图",
        "drawing", "review", "P&ID", "diagram",
    ],
    "document_completeness": [
        "资料", "文件", "技术文件", "完整性", "文档",
        "document", "documentation", "completeness", "technical file",
    ],
    "material": [
        "材料", "材质", "耐腐蚀材料", "不锈钢", "铜合金",
        "material", "stainless steel", "copper alloy",
    ],
    "water_quality": [
        "水质", "硬度", "pH", "氯离子", "水处理", "水质指标",
        "water quality", "hardness", "chloride", "pH value",
    ],
    "corrosion_protection": [
        "腐蚀", "防腐", "防锈", "腐蚀防护",
        "corrosion", "corrosion protection", "anti-corrosion",
    ],
    "environmental_protection": [
        "环保", "排放", "废液处理", "污水",
        "environment", "emission", "waste water",
    ],
    "safety": [
        "安全", "安全风险", "烫伤", "误操作", "防护",
        "safety", "risk", "burn protection", "inadvertent operation",
    ],
    "class_approval": [
        "船级社", "验船", "审查要求", "认证", "发证",
        "class", "classification", "class approval", "survey",
    ],
}

# ─────────────────────────────────────────────
# 按需求类型给出默认 profile（大幅扩充 keywords）
# ─────────────────────────────────────────────
TYPE_PROFILE: dict[str, dict] = {
    "reliability": {
        "aspects": ["reliability", "capacity", "temperature", "pressure", "flow", "redundancy", "control", "alarm"],
        "can_support": ["system_design", "equipment_selection", "parameter_limit", "calculation", "test", "alarm_protection", "operation"],
        "phases": ["basic_design", "detailed_design", "commissioning", "operation"],
        "keywords": [
            "稳定", "可靠", "航行安全", "冷却能力", "连续运行", "热带", "负荷变化",
            "冗余", "备用", "双泵", "故障切换", "reliability", "stable",
        ],
    },
    "redundancy": {
        "aspects": ["redundancy", "reliability", "control", "alarm", "capacity"],
        "can_support": ["system_design", "equipment_selection", "redundancy", "alarm_protection"],
        "phases": ["basic_design", "detailed_design"],
        "keywords": [
            "冗余", "备用", "一用一备", "双泵", "备用泵", "单台故障",
            "standby", "backup", "redundancy", "N+1",
        ],
    },
    "parameter": {
        "aspects": ["temperature", "pressure", "flow", "capacity", "monitoring"],
        "can_support": ["parameter_limit", "calculation", "test", "monitoring", "equipment_selection"],
        "phases": ["detailed_design", "commissioning", "operation"],
        "keywords": [
            "温度", "压力", "流量", "厂家", "技术数据", "参数", "限值",
            "inlet", "outlet", "rated", "Technical Data",
        ],
    },
    "installation": {
        "aspects": ["installation", "arrangement", "accessibility", "flushing", "pressure_test", "inspection"],
        "can_support": ["installation", "arrangement", "inspection", "test", "flushing", "pressure_test"],
        "phases": ["installation", "inspection", "commissioning"],
        "keywords": [
            "施工", "安装", "布置", "焊接", "冲洗", "压力试验", "支架", "接口",
            "管路走向", "阀门位置", "现场", "installation", "flushing", "pressure test",
        ],
    },
    "maintainability": {
        "aspects": ["maintenance", "accessibility", "cleaning", "inspection", "flushing"],
        "can_support": ["maintenance", "inspection", "operation", "cleaning"],
        "phases": ["operation", "maintenance", "inspection"],
        "keywords": [
            "维护", "检修", "清洗", "拆卸", "更换", "复装", "检修空间",
            "维护周期", "maintenance", "overhaul", "access",
        ],
    },
    "control": {
        "aspects": ["control", "monitoring", "temperature", "pressure", "flow", "alarm", "redundancy"],
        "can_support": ["control", "monitoring", "operation", "alarm_protection", "parameter_limit"],
        "phases": ["detailed_design", "commissioning", "operation"],
        "keywords": [
            "控制", "监控", "集控", "传感器", "趋势", "故障判断", "自动",
            "PLC", "IAS", "control", "monitoring", "automation",
        ],
    },
    "alarm_protection": {
        "aspects": ["alarm", "shutdown", "load_reduction", "monitoring", "temperature", "pressure", "flow"],
        "can_support": ["alarm_protection", "monitoring", "operation", "test", "parameter_limit"],
        "phases": ["detailed_design", "commissioning", "operation", "class_approval"],
        "keywords": [
            "报警", "保护", "停机", "降负荷", "故障安全", "高温报警", "低压报警",
            "alarm", "shutdown", "trip", "high temperature", "low pressure",
        ],
    },
    "verification": {
        "aspects": ["inspection", "commissioning", "pressure_test", "calculation", "drawing_review", "document_completeness", "class_approval"],
        "can_support": ["test", "inspection", "class_review", "document_completeness", "calculation", "pressure_test"],
        "phases": ["commissioning", "inspection", "class_approval"],
        "keywords": [
            "试验", "检查", "验收", "图纸", "计算书", "审查", "完整", "认证",
            "船级社", "class", "approval", "test", "inspection", "calculation",
        ],
    },
    "safety_environment": {
        "aspects": ["safety", "corrosion_protection", "environmental_protection", "alarm", "maintenance"],
        "can_support": ["safety", "environment", "maintenance", "alarm_protection", "inspection"],
        "phases": ["detailed_design", "installation", "operation", "maintenance"],
        "keywords": [
            "泄漏", "腐蚀", "环保", "烫伤", "误操作", "防护", "标识",
            "safety", "leak", "corrosion", "environment",
        ],
    },
    "water_treatment": {
        "aspects": ["water_quality", "corrosion_protection", "cleaning", "maintenance", "environmental_protection"],
        "can_support": ["maintenance", "parameter_limit", "inspection", "environment", "water_quality"],
        "phases": ["operation", "maintenance", "inspection"],
        "keywords": [
            "水质", "防腐剂", "缓蚀剂", "硬度", "氯离子", "pH",
            "inhibitor", "water treatment", "water quality",
        ],
    },
    "configuration": {
        "aspects": ["arrangement", "capacity", "flow", "control", "redundancy", "reliability"],
        "can_support": ["system_design", "equipment_selection", "arrangement", "redundancy"],
        "phases": ["basic_design", "detailed_design"],
        "keywords": [
            "配置", "组成", "系统", "设备", "回路", "系统配置",
            "configuration", "system design", "composition",
        ],
    },
    "operation": {
        # 覆盖工况稳定性：启动/低负荷/满负荷/负荷变化/停机后冷却
        "aspects": [
            "monitoring", "control", "alarm", "reliability", "maintenance",
            "temperature", "pressure", "flow", "capacity",
        ],
        "can_support": [
            "operation", "monitoring", "alarm_protection", "maintenance",
            "parameter_limit", "operation_parameter", "commissioning",
            "system_design", "calculation",
        ],
        "phases": ["operation", "commissioning", "detailed_design"],
        "keywords": [
            "操作", "运行", "日常运行", "工况", "稳定",
            "启动", "低负荷", "满负荷", "负荷变化", "停机后冷却",
            "参数稳定", "冷却水参数",
            "operation", "operating", "steady state", "transient",
            "startup", "low load", "full load", "load change", "shutdown cooling",
            "parameter stability", "cooling water parameter",
        ],
    },
    "other": {
        "aspects": ["reliability", "capacity", "temperature", "pressure", "flow"],
        "can_support": ["system_design", "equipment_selection", "parameter_limit", "calculation"],
        "phases": ["basic_design", "detailed_design"],
        "keywords": ["冷却水", "主机", "cooling", "main engine"],
    },
}

# ─────────────────────────────────────────────
# 工况映射
# ─────────────────────────────────────────────
CONDITION_MAP: dict[str, list[str]] = {
    "continuous_operation": [
        "连续运行", "长时间", "持续", "长时间连续",
        "continuous", "prolonged", "continuous operation", "continuous running",
    ],
    "tropical_condition": [
        "热带", "高温环境", "热带海区", "热带海域",
        "tropical", "tropical condition", "high seawater temperature", "hot climate",
    ],
    "high_seawater_temperature": [
        "海水温度", "高海水温度", "海水高温",
        "seawater temperature", "high sea water temp",
    ],
    "startup": [
        "启动", "起机", "开机", "启动工况",
        "start", "startup", "starting", "start-up", "engine start",
    ],
    "low_load": [
        "低负荷", "部分负荷", "低工况", "轻载",
        "low load", "part load", "partial load", "light load", "low power",
    ],
    "full_load": [
        "满负荷", "额定", "额定工况", "满载", "全负荷",
        "rated", "full load", "MCR", "100%", "maximum continuous rating", "full power",
    ],
    "rapid_load_change": [
        "快速负荷", "负荷变化", "负荷变动", "负荷阶跃", "快速变化",
        "load change", "load variation", "load step", "transient", "rapid load",
        "load fluctuation",
    ],
    "shutdown_cooling": [
        "停机后冷却", "停机冷却", "停机后", "停机余热",
        "post-cooling", "shutdown cooling", "after shutdown", "post-shutdown",
        "after stop", "residual heat", "cooldown",
    ],
    "fault_condition": [
        "故障", "单台故障", "泵故障", "设备故障",
        "fault", "failure", "failure condition", "pump failure", "equipment failure",
    ],
    "normal_operation": [
        "正常运行", "正常工况", "日常运行",
        "normal operation", "normal running", "steady state", "steady-state",
    ],
    "standby_mode": [
        "备用状态", "待机", "备用",
        "standby", "standby mode", "stand-by",
    ],
}


def _match_components(text: str) -> list[str]:
    """从文本中识别涉及的部件，返回 component key 列表。"""
    matched = []
    text_lower = text.lower()
    for comp, aliases in COMPONENT_MAP.items():
        if any(a.lower() in text_lower for a in aliases):
            matched.append(comp)
    return matched


def _match_aspects(text: str) -> list[str]:
    """从文本中识别涉及的需求方面，返回 aspect key 列表。"""
    matched = []
    text_lower = text.lower()
    for aspect, aliases in ASPECT_MAP.items():
        if any(a.lower() in text_lower for a in aliases):
            matched.append(aspect)
    return matched


def _match_conditions(text: str) -> list[str]:
    """从文本中识别工况，返回 condition key 列表。"""
    matched = []
    text_lower = text.lower()
    for cond, aliases in CONDITION_MAP.items():
        if any(a.lower() in text_lower for a in aliases):
            matched.append(cond)
    return matched


def _collect_positive_keywords(text: str) -> list[str]:
    """收集文本中出现的同义词作为正向关键词，用于 BM25 增强。"""
    keywords = []
    text_lower = text.lower()
    for aliases in list(COMPONENT_MAP.values()) + list(ASPECT_MAP.values()) + list(CONDITION_MAP.values()):
        for a in aliases:
            if a.lower() in text_lower and a not in keywords:
                keywords.append(a)
    return keywords


def build_profile(sub_requirement: dict[str, Any]) -> dict[str, Any]:
    """
    根据子需求构建检索画像。

    改进点：
    1. 同义词表大幅扩充，减少 profile 为空的情况
    2. 按需求类型叠加默认方面和 can_support，确保即使文本匹配不到也有合理默认值
    3. positive_keywords 来自实际匹配的同义词，提升 BM25 权重
    4. 安装/参数/报警类需求默认追加相关部件
    """
    text = " ".join([
        sub_requirement.get("topic") or "",
        sub_requirement.get("text") or "",
    ])
    rtype = sub_requirement.get("requirement_type") or "other"

    # 从文本中识别部件、方面和工况
    matched_components = _match_components(text)
    matched_aspects = _match_aspects(text)
    matched_conditions = _match_conditions(text)
    positive_keywords = _collect_positive_keywords(text)

    # 按需求类型加载默认配置
    type_cfg = TYPE_PROFILE.get(rtype, TYPE_PROFILE["other"])

    # 合并方面：文本识别 + 类型默认
    all_aspects = unique_keep_order(matched_aspects + type_cfg.get("aspects", []))

    # 合并部件：文本识别 + 类型补充
    all_components = list(matched_components)

    # 类型专属补充部件
    if rtype == "installation":
        all_components = unique_keep_order(
            all_components + ["pipe", "valve", "support", "equipment_interface", "flushing_connection", "pressure_test_connection"]
        )
    elif rtype == "parameter":
        all_components = unique_keep_order(
            all_components + [
                "main_engine_cooling_water_system", "cooling_water_pump",
                "temperature_sensor", "pressure_sensor", "flow_sensor",
                "temperature_control_valve",
            ]
        )
    elif rtype in {"alarm_protection", "control"}:
        all_components = unique_keep_order(
            all_components + [
                "control_system", "alarm_system",
                "temperature_sensor", "pressure_sensor", "flow_sensor", "level_sensor",
            ]
        )
    elif rtype == "maintainability":
        all_components = unique_keep_order(
            all_components + ["cooler", "filter", "cooling_water_pump", "temperature_control_valve", "expansion_tank"]
        )
    elif rtype == "reliability":
        all_components = unique_keep_order(
            all_components + ["cooling_water_pump", "cooler", "temperature_control_valve", "main_engine_cooling_water_system"]
        )
    elif rtype == "redundancy":
        all_components = unique_keep_order(
            all_components + ["cooling_water_pump", "sea_water_pump", "cooler", "main_engine_cooling_water_system"]
        )
    elif rtype == "operation":
        # 工况稳定性：关联泵、温控阀、冷却器、传感器
        all_components = unique_keep_order(
            all_components + [
                "main_engine_cooling_water_system", "cooling_water_pump",
                "temperature_control_valve", "cooler",
                "temperature_sensor", "pressure_sensor", "flow_sensor",
            ]
        )

    # 确保至少有系统级默认部件
    if not all_components:
        all_components = ["main_engine_cooling_water_system"]

    # 合并 positive_keywords：文本匹配 + 类型默认
    all_keywords = unique_keep_order(positive_keywords + type_cfg.get("keywords", []))

    # must_have_any：至少包含冷却水相关词
    # operation 类型额外追加工况关键词，防止退化到通用"冷却"后召回无关证据
    if rtype == "operation" and matched_conditions:
        condition_words = [a for cond in matched_conditions for a in CONDITION_MAP.get(cond, []) if len(a) >= 2]
        must_have = unique_keep_order(condition_words[:8] + ["冷却水", "参数稳定", "cooling water"])
    else:
        must_have = unique_keep_order(
            [kw for kw in positive_keywords if len(kw) >= 2][:10] or ["冷却", "cooling"]
        )

    profile = {
        "intent": rtype,
        "target_systems": ["main_engine_cooling_water_system"],
        "target_components": unique_keep_order(all_components),
        "target_aspects": unique_keep_order(all_aspects),
        "target_phases": unique_keep_order(type_cfg.get("phases", [])),
        "target_conditions": unique_keep_order(matched_conditions),
        "required_can_support": unique_keep_order(type_cfg.get("can_support", [])),
        "preferred_evidence_strength": ["direct", "indirect"],
        "preferred_applicability": ["class_rule", "manufacturer_specific", "project_specific", "general_engineering"],
        "must_have_any": must_have,
        "positive_keywords": all_keywords,
        "preferred_evidence_types": list(type_cfg.get("aspects", [])),
        "negative_evidence_types": [],
    }

    return profile
