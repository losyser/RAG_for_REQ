"""
Evidence taxonomy for ship main engine cooling water systems.

Design principle: each evidence unit should map to exactly ONE primary component
and ONE primary intent. This enables precise metadata-filtered retrieval:
  given requirement → extract (component, intent) → filter evidence → vector search.

Usage:
    from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, TAXONOMY, \
        valid_pair, get_intents_for, all_pairs
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Components  (部件)
# ─────────────────────────────────────────────────────────────────────────────

COMPONENTS: dict[str, str] = {
    # 动设备
    "cooling_water_pump":       "冷却水泵（含海水泵）",
    # 静设备
    "cooler":                   "冷却器 / 热交换器",
    "expansion_tank":           "膨胀水箱 / 高位水箱",
    "temperature_control_valve":"温控阀 / 温度调节阀",
    # 管路系统
    "pipe":                     "冷却水管路",
    "valve":                    "阀门（截止阀、球阀、蝶阀、止回阀、安全阀等）",
    "pipe_fitting":             "管件（弯头、三通、异径管、法兰等）",
    "filter":                   "过滤器 / 滤网",
    "pipe_support":             "管路支架 / 吊架",
    # 仪表与控制
    "temperature_sensor":       "温度传感器 / 温度计",
    "pressure_sensor":          "压力传感器 / 压力表",
    "level_sensor":             "液位传感器 / 液位计",
    "flow_meter":               "流量计",
    "alarm_system":             "报警与保护系统",
    "control_system":           "自动控制系统（PLC / 集控）",
    # 介质
    "coolant":                  "淡水冷却液（含缓蚀剂、防冻剂）",
    "sea_water":                "海水（冷却侧介质）",
    # 辅助结构
    "anode":                    "牺牲阳极（锌块 / 铝块）",
    "insulation":               "隔热保温材料及护套",
    "sea_chest":                "海水箱（金水箱）",
    # 系统层面（跨部件规范才用）
    "cooling_system":           "冷却水系统（系统级，不能归入具体部件时使用）",
}

# ─────────────────────────────────────────────────────────────────────────────
# Intents  (工程方面)
# ─────────────────────────────────────────────────────────────────────────────

INTENTS: dict[str, str] = {
    # 技术参数
    "specification":            "额定参数（容量、流量、扬程、功率、换热量、压力等级等）",
    "material":                 "材料选择（牌号、标准、兼容性要求）",
    "wall_thickness":           "壁厚 / 强度等级",
    "pressure_rating":          "设计压力等级（PN 等级、管路类别）",
    "connection_type":          "连接方式（焊接、法兰、螺纹、卡压等）",
    # 功能与控制
    "redundancy":               "冗余配置（一用一备、切换条件、切换方式）",
    "auto_start":               "备用设备自动启动逻辑与条件",
    "control_logic":            "自动控制逻辑（启停、调节、联锁）",
    "set_point":                "调节设定值（温度设定、开启点、全开点）",
    "fail_safe":                "故障安全状态（失电 / 失信号后的默认位置）",
    "manual_override":          "手动操控要求（就地操作、手动旁通）",
    "bypass":                   "旁通阀配置与旁通逻辑",
    # 报警与保护
    "alarm_setpoint":           "报警定值（高温、低压、低液位、高压差等）",
    "trip_setpoint":            "停机保护定值（超温、失压、失流等触发停机的阈值）",
    "alarm_response":           "报警处置程序（操作员响应、自动联锁动作）",
    # 安装与施工
    "installation":             "安装要求（方位、间距、坡度、膨胀补偿、穿舱封堵等）",
    "pipe_support":             "管路支架间距、固定方式、减振要求",
    "welding":                  "焊接工艺（WPS/WPQR）、焊工资质、无损检测比例",
    "thermal_insulation":       "隔热保温材料、厚度、护套施工",
    "labeling":                 "色标（ISO 14726）、流向标识、铭牌",
    "hot_surface_warning":      "高温表面警示标识（ISO 11684）",
    "vent_drain":               "排气点与放水点的设置位置、数量、阀门要求",
    # 防护
    "corrosion_protection":     "防腐处理（涂层、电化学保护、材料防腐措施）",
    "cathodic_protection":      "阴极保护（牺牲阳极布置、连接方式、电气隔离）",
    "biofouling":               "防海生物附着（防污涂料、机械清除）",
    # 质量验证
    "pressure_test":            "水压试验（试验压力倍数、保压时间、合格判据）",
    "test_procedure":           "功能试验程序（调试前、调试中、验收试验）",
    "calibration":              "仪表校验（校验方法、周期、允许误差）",
    # 运行与维护
    "inspection":               "检查项目与周期（外观、性能、完整性检查）",
    "maintenance":              "维护保养程序（定期维护、易损件更换）",
    "cleaning":                 "清洗方式与周期（机械清洗、化学清洗）",
    "replacement_cycle":        "更换周期（介质更换、阳极更换等）",
    # 水质管理（仅介质类部件）
    "water_quality":            "水质指标（pH、硬度、电导率、氯离子、含氧量等）",
    "corrosion_inhibitor":      "缓蚀剂种类、浓度范围、补加方法",
    "antifreeze":               "防冻剂（乙二醇比例、冰点要求）",
    "sampling":                 "取样检测方法、频率、送检要求",
    "compatibility":            "介质与管材 / 设备材料的兼容性限制",
    "environmental_protection": "废液处置（乙二醇含量、排放标准）",
    "initial_fill":             "首次充注程序（冲洗、加药、排气）",
    # 文件与审批
    "documentation":            "文件要求（厂家说明书、图纸、计算书、备件目录）",
    "drawing_requirement":      "图纸提交要求（系统图、布置图、单线图提交节点）",
    "class_approval":           "船级社审批 / 认可 / 检验要求",
    "spare_parts":              "备品备件清单与最低储量要求",
    "interface":                "与其他系统或设备的接口要求",
    # 系统级（仅 cooling_system 使用）
    "system_description":       "系统功能描述、工作原理、系统边界",
}

# ─────────────────────────────────────────────────────────────────────────────
# Taxonomy  ── (component → applicable intents)
# ─────────────────────────────────────────────────────────────────────────────
# Rule: if a (component, intent) pair is not listed here, it is invalid.
# Evidence units MUST have a primary_component + primary_intent that forms a
# valid pair.  KB gaps (zero evidence for a valid pair) are expected and honest.

TAXONOMY: dict[str, list[str]] = {

    "cooling_water_pump": [
        "specification",        # 额定流量、扬程、转速、功率
        "redundancy",           # 一用一备、自动切换
        "auto_start",           # 备泵自启逻辑、延时
        "material",             # 泵体、叶轮、轴材料
        "corrosion_protection", # 泵体内壁防腐
        "installation",         # 基座、对中、振动隔离
        "alarm_setpoint",       # 流量低、出口压力低报警
        "trip_setpoint",        # 失流停机保护
        "pressure_test",        # 出厂水压试验
        "inspection",           # 检查项目与周期
        "maintenance",          # 机械密封、轴承更换
        "documentation",        # 厂家文件、备件目录
        "class_approval",       # 型式认可、船检
        "spare_parts",          # 关键备件储量
    ],

    "cooler": [
        "specification",        # 换热量、设计温度/压力、传热面积
        "pressure_drop",        # 水侧/海水侧允许压降
        "material",             # 管束、壳体、管板、密封材料
        "corrosion_protection", # 海水侧防腐（涂层、牺牲阳极）
        "fouling",              # 结垢系数、防污措施
        "cleaning",             # 清洗方式（机械/化学）、周期
        "bypass",               # 旁通阀配置
        "alarm_setpoint",       # 出口温度高报警
        "installation",         # 安装方位、进出口方向、支撑
        "pressure_test",        # 管侧/壳侧水压试验
        "inspection",           # 泄漏、腐蚀、结垢检查
        "maintenance",          # 管束更换、端盖拆装
        "documentation",        # 换热计算书、厂家图纸
        "drawing_requirement",  # 冷却器图纸提交要求
        "class_approval",       # 设计审批、材料证书
        "spare_parts",          # 密封件备件
        "interface",            # 与高温/低温回路的接口
    ],

    "expansion_tank": [
        "specification",        # 容积、设计压力、设计温度等额定参数
        "capacity",             # 有效容积计算依据（系统膨胀量）
        "level_control",        # 正常液位范围、控制逻辑
        "makeup_water",         # 自动补水触发条件、补水源
        "venting",              # 排气管管径、连接位置
        "pressure",             # 工作压力（膨胀压力）
        "alarm_setpoint",       # 液位高/低报警定值
        "trip_setpoint",        # 液位极低停机保护
        "control_logic",        # 液位控制、补水联锁逻辑
        "material",             # 箱体材料、内壁防腐
        "corrosion_protection", # 内壁防腐处理
        "installation",         # 安装高度（需高于系统最高点）、支撑
        "inspection",           # 液位计检查、内壁腐蚀检查
        "maintenance",          # 清洗、防腐涂层更新
        "documentation",        # 容积计算书
        "drawing_requirement",  # 膨胀箱图纸提交要求
        "class_approval",       # 船级社审核（若压力容器需要）
    ],

    "temperature_control_valve": [
        "specification",        # 调节范围、额定流量、额定压降
        "set_point",            # 开启温度、全开温度设定值
        "control_logic",        # 三通调节原理、混合/分流
        "fail_safe",            # 失效后位置（全开热旁通 / 全开冷却）
        "bypass",               # 手动旁通阀配置
        "redundancy",           # 是否需配备用阀
        "material",             # 阀体、温感元件材料
        "installation",         # 安装方向、前后直管段要求
        "inspection",           # 调节特性、温感元件检查
        "maintenance",          # 温感元件更换、校验
        "drawing_requirement",  # 温控阀图纸提交要求
        "class_approval",       # 认可型号要求
    ],

    "pipe": [
        "material",             # 管材牌号（碳钢、铜镍合金、不锈钢等）及标准
        "wall_thickness",       # 壁厚选取（计算方法、最小壁厚）
        "pressure_rating",      # 设计压力等级（CCS 管路类别 I/II/III）
        "connection_type",      # 法兰/对焊/螺纹/卡压接头选用规则
        "corrosion_protection", # 内外防腐处理（涂层、镀锌、牺牲阳极）
        "cathodic_protection",  # 电化学防腐（双金属接触的电气隔离）
        "thermal_insulation",   # 隔热保温材料、厚度、护套（含高温管路）
        "pipe_support",         # 支架最大间距（按管径）、固定方式
        "welding",              # 焊接工艺评定、焊工资质、NDT 比例
        "vent_drain",           # 排气点（最高处）、放水点（最低处）设置
        "installation",         # 坡度、膨胀补偿（膨胀节/弯管）、穿舱封堵
        "labeling",             # 色标（ISO 14726）、流向箭头、管径标注
        "hot_surface_warning",  # 高温管路警示标识
        "pressure_test",        # 水压试验压力（1.5×设计压力）、保压时长
        "cleaning",             # 管路冲洗（安装后冲洗、化学清洗）
        "inspection",           # 外观、壁厚测量、泄漏检查
        "documentation",        # 管系图（P&ID）、材料证书
        "drawing_requirement",  # 管系图、单线图提交要求
        "class_approval",       # 管路认可（材料证书、焊接检验）
    ],

    "valve": [
        "type",                 # 阀门类型选用（截止/球/蝶/止回/安全阀）
        "specification",        # 公称压力（PN）、公称通径（DN）
        "material",             # 阀体、阀瓣、阀座、密封材料
        "installation",         # 安装方向（截止阀流向）、操作空间
        "drawing_requirement",  # 阀门图纸、数据单提交要求
        "position_indicator",   # 开/关状态指示（就地 + 远程）
        "lockout",              # 锁定要求（防误关的常开阀）
        "drain",                # 阀体排空（低点阀门的排空接头）
        "inspection",           # 密封性、填料泄漏检查
        "maintenance",          # 填料更换、阀座研磨
        "class_approval",       # 认可证书
    ],

    "pipe_fitting": [
        "material",             # 与管路材质一致性要求
        "pressure_rating",      # 压力等级匹配（不得低于管路 PN）
        "welding",              # 焊接坡口要求
        "class_approval",       # 认可证书（与管材相同等级）
    ],

    "filter": [
        "specification",        # 过滤精度（孔径 μm）、额定流量
        "redundancy",           # 双联过滤器、不断流切换
        "pressure_drop",        # 清洁/堵塞状态允许压降
        "alarm_setpoint",       # 压差高报警定值
        "bypass",               # 旁通阀（仅检修用，正常关闭）
        "cleaning",             # 滤芯清洗、反冲洗程序
        "material",             # 滤网材料（与介质兼容）
        "installation",         # 安装位置（泵进口前）、方向
        "inspection",           # 压差、滤网破损检查
        "maintenance",          # 滤芯更换周期
    ],

    "pipe_support": [
        "spacing",              # 支架最大间距（按管径/壁厚查表）
        "material",             # 支架材料（防腐要求）
        "vibration_isolation",  # 减振垫、弹性支架选用条件
        "installation",         # 安装方式（焊接/夹式）、与结构连接
    ],

    "temperature_sensor": [
        "specification",        # 测量范围、精度等级、响应时间
        "installation",         # 插入深度、套管（保护管）、位置
        "alarm_setpoint",       # 高温报警定值（分级）
        "trip_setpoint",        # 超温停机定值
        "calibration",          # 校验周期、方法、允许误差
        "redundancy",           # 双传感器（主备）配置要求
        "class_approval",       # 型式认可
    ],

    "pressure_sensor": [
        "specification",        # 测量范围、精度等级
        "installation",         # 取压口位置、隔离阀、冲洗接头
        "alarm_setpoint",       # 低压报警定值
        "trip_setpoint",        # 失压停机定值
        "calibration",          # 校验周期与方法
        "class_approval",       # 型式认可
    ],

    "level_sensor": [
        "specification",        # 测量范围、精度
        "installation",         # 安装位置（膨胀箱侧壁/顶部）
        "alarm_setpoint",       # 高液位 / 低液位报警定值
        "trip_setpoint",        # 低液位极低停机定值
        "calibration",          # 校验周期
    ],

    "flow_meter": [
        "specification",        # 量程、精度、允许压降
        "installation",         # 上下游直管段长度要求、安装方位
        "alarm_setpoint",       # 低流量报警定值
        "calibration",          # 校验周期
    ],

    "alarm_system": [
        "alarm_setpoint",       # 各测点报警分级定值（一级/二级）
        "trip_setpoint",        # 各停机保护触发定值
        "alarm_response",       # 报警处置程序（操作员动作 + 自动联锁）
        "test_procedure",       # 报警系统功能试验（FAT/SAT）
        "redundancy",           # 报警系统冗余（双回路、UPS 供电）
        "documentation",        # 报警清单（逐点说明）
        "class_approval",       # 安全系统型式认可
    ],

    "control_system": [
        "control_logic",        # 自动控制逻辑（启停顺序、切换、联锁）
        "manual_override",      # 就地手动操控、集控室手动覆盖
        "fail_safe",            # 控制失电 / 通信中断后的安全状态
        "redundancy",           # 控制器冗余、I/O 冗余
        "interface",            # 与机舱集控（AMS/IAS）的硬接线 + 通信接口
        "documentation",        # 控制逻辑图、软件说明书
        "class_approval",       # 型式认可（含软件审核）
    ],

    "coolant": [
        "water_quality",        # pH、硬度、电导率、氯离子、溶解氧等指标限值
        "corrosion_inhibitor",  # 缓蚀剂种类（亚硝酸盐/钼酸盐/有机）、浓度范围
        "antifreeze",           # 防冻剂（乙二醇比例）、适用温度
        "sampling",             # 取样检测频率、送检项目、现场快检方法
        "inspection",           # 冷却液状态检查（颜色、气味、污染物）
        "replacement_cycle",    # 冷却液更换周期、更换判据
        "compatibility",        # 与铜铝等金属材料的兼容性限制
        "environmental_protection", # 废液乙二醇含量、禁止直接排放要求
        "initial_fill",         # 首次充注程序（系统冲洗、加药比例、排气）
    ],

    "sea_water": [
        "corrosion_protection", # 海水侧防腐措施（涂层、牺牲阳极）
        "cathodic_protection",  # 电化学防腐（阳极布置、双金属电气隔离）
        "biofouling",           # 防海生物附着（防污涂料、电解法）
        "material",             # 接触海水的材料选择（禁用材料清单）
        "cleaning",             # 海生物、结垢清除方法与周期
        "water_quality",        # 海水水质特殊要求（盐度、悬浮物）
    ],

    "anode": [
        "material",             # 锌阳极 / 铝阳极选择（材料标准）
        "specification",        # 规格（重量、尺寸）
        "installation",         # 安装位置、间距、固定方式
        "inspection",           # 腐蚀损耗程度评估（剩余重量比）
        "replacement_cycle",    # 更换触发条件（剩余 50% 时更换）
    ],

    "insulation": [
        "specification",        # 材料种类（岩棉、玻璃棉等）、导热系数
        "thickness",            # 隔热厚度（按表面温度和环境温度计算）
        "installation",         # 施工要求、护套（铝皮 / 不锈钢皮）
        "hot_surface_warning",  # 高温表面警示标识（ISO 11684，间距 ≤2 m）
    ],

    "sea_chest": [
        "specification",        # 尺寸、数量、位置（高海胸 + 低海胸）
        "redundancy",           # 高低海胸切换要求
        "material",             # 箱体及格栅材料（耐海水腐蚀）
        "corrosion_protection", # 内壁防腐涂层
        "cathodic_protection",  # 牺牲阳极配置
        "installation",         # 位置（水线以下）、格栅开孔比
        "inspection",           # 堵塞、腐蚀、阳极状态检查
        "class_approval",       # 船级社检验（开孔位置审批）
    ],

    "cooling_system": [
        "system_description",   # 系统功能、工作原理、系统边界定义
        "interface",            # 与主机冷却回路、海水系统、淡水系统的接口
        "drawing_requirement",  # P&ID、系统原理图、设备布置图提交要求
        "test_procedure",       # 系统联调试验程序（码头试验、海试）
        "spare_parts",          # 系统级备品备件最低储量
        "documentation",        # 系统操作手册、维护手册
        "class_approval",       # 系统级船级社审批（设计图纸审批）
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def valid_pair(component: str, intent: str) -> bool:
    """Return True if (component, intent) is a defined taxonomy pair."""
    return intent in TAXONOMY.get(component, [])


def get_intents_for(component: str) -> list[str]:
    """Return all valid intents for a given component."""
    return list(TAXONOMY.get(component, []))


def get_components_for(intent: str) -> list[str]:
    """Return all components that have this intent."""
    return [c for c, intents in TAXONOMY.items() if intent in intents]


def all_pairs() -> list[tuple[str, str]]:
    """Return every (component, intent) pair in the taxonomy."""
    return [(c, i) for c, intents in TAXONOMY.items() for i in intents]


def summary() -> dict:
    """Return a summary dict for quick inspection."""
    pairs = all_pairs()
    return {
        "n_components": len(TAXONOMY),
        "n_intents": len(INTENTS),
        "n_pairs": len(pairs),
        "components": list(TAXONOMY.keys()),
        "intents_per_component": {c: len(v) for c, v in TAXONOMY.items()},
    }


if __name__ == "__main__":
    import json, sys
    sys.stdout.reconfigure(encoding="utf-8")
    s = summary()
    print(f"部件数:        {s['n_components']}")
    print(f"方面数:        {s['n_intents']}")
    print(f"(部件×方面)对: {s['n_pairs']}")
    print()
    print("各部件方面数:")
    for comp, n in s["intents_per_component"].items():
        label = COMPONENTS.get(comp, "")
        print(f"  {comp:<30s} {n:3d}  {label}")
    print()
    print("各方面适用的部件数:")
    for intent, desc in INTENTS.items():
        comps = get_components_for(intent)
        print(f"  {intent:<30s} {len(comps):2d}个部件  {desc[:30]}")
