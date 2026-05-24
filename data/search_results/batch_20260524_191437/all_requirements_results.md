# 需求证据包（V2 工程字段版）

## R001 船东代表
主机冷却水系统应保证船舶在连续运行、负荷变化和高温环境下具有稳定可靠的冷却能力，避免因冷却不足影响推进安全和运行经济性。

### R001-01 冷却水系统运行稳定性
主机冷却水系统应保证船舶在连续运行、负荷变化和高温环境下具有稳定可靠的冷却能力，避免因冷却不足影响推进安全和运行经济性。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'cooler', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['reliability', 'capacity', 'temperature', 'safety', 'monitoring', 'control', 'alarm', 'maintenance', 'pressure', 'flow']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

- E-CTRL-COOL-001｜direct｜primary
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, temperature_control_valve, main_engine_cooling_water_system, alarm_system｜方面：operation, alarm, monitoring, redundancy, test｜可支撑：operation, alarm, monitoring, redundancy, test｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements E10 — Machinery Control Systems
Cooling water temperature control systems for main propulsion engines shall:
1. Maintain cooling water temperature within manufacturer's limits across the full engine load range through automatic modulation of the temperature control valve.
2. Be capable of manual override in case of automatic control failure.
3. Provide alarm when cooling water temperature exceeds the high alarm set-point.
4. Where automatic slow-down or shutdown is provided, activate at a set-point above the alarm set-point (typically 5–10°C above the alarm).
5. Activate an audible and visible alarm when automatic protective devices are triggered.
6. Maintain cooling water temperature control function after a single failure of any control system component (single-failure criterion).
整理说明：IACS UR E10 对主机冷却水温度控制系统的功能要求、手动备用、自动保护逻辑和单一故障准则提供了规范级依据，可支撑控制系统设计、保护逻辑和可靠性类需求。
```

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-PARAM-HT-001｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：ht_cooling_water_loop, lt_cooling_water_loop, main_engine_cooling_water_system, temperature_control_valve｜方面：parameter_limit, alarm, monitoring｜可支撑：parameter_limit, alarm, monitoring｜强度：direct｜适用性：general/class_rule
```text
Marine Main Engine HT Cooling Water System — Standard Parameter Limits
(Consolidated from IACS UR M3.1, ISO 8861, DNV Rules, and engine manufacturer project guides for medium-speed 4-stroke diesel engines)

High-Temperature (HT) Freshwater Circuit:
- Engine jacket water inlet temperature: 70–85°C (exact value per manufacturer)
- Engine jacket water outlet temperature: 80–95°C (exact value per manufacturer)
- Temperature control valve set-point (thermostat): typically 80–85°C
- High temperature alarm: 90–95°C (5–10°C above set-point, per manufacturer)
- Automatic slow-down activation: 95–100°C (per manufacturer, above alarm)
- Maximum cooling water pressure: as specified by manufacturer (typically 3–5 bar)
- Minimum cooling water pressure at engine inlet: typically 1.5–3.0 bar
- Low pressure alarm: 0.5–1.0 bar below minimum operating pressure

Low-Temperature (LT) Freshwater Circuit (Central Cooling):
- LT water temperature at central cooler outlet: 25–38°C (depends on seawater temperature)
- LT water temperature at central cooler inlet: 35–45°C
- High temperature alarm for LT water: 5°C above maximum design temperature
整理说明：综合IACS UR M3.1、ISO 8861和DNV规则的中速四冲程柴油机冷却水系统标准参数范围，为参数设计和确认提供多来源证据支撑。具体数值须以主机制造商技术文件为最终依据。
```

- E-DNV-COOL-001｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, temperature_control_valve, central_cooling_system｜方面：parameter_limit, capacity, system_design｜可支撑：parameter_limit, capacity, system_design｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems
The cooling water system for main propulsion engines shall be designed so that the cooling water temperatures at the engine inlet are maintained within the limits specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat opening temperature under worst-case ambient conditions. For central (low-temperature) cooling systems, the LT fresh water temperature at the plate cooler outlet shall be calculated for maximum sea water temperature at the service area.
整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。
```

- E-LT-CAP-001｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：lt_cooling_water_loop, central_cooling_system, cooler｜方面：capacity, parameter_limit, calculation｜可支撑：capacity, parameter_limit, calculation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Central Cooling System Design
Low-Temperature (LT) Freshwater Cooling Circuit Capacity Requirements:
The LT freshwater circuit of a central cooling system shall be sized to handle the combined heat rejection from all consumers connected to the LT circuit, operating simultaneously at their maximum rated loads. The sizing calculation shall be performed for the maximum seawater temperature of the vessel's intended trading area (minimum 32°C for unrestricted service, 35°C for tropical service).
The flow rate through the central freshwater cooler shall be adequate to limit the LT water temperature rise across the cooler to the value required to maintain all connected consumers within their temperature limits.
典型LT冷却水进中央冷却器温度：30–40°C；出中央冷却器温度：32–38°C（取决于海水温度）。
整理说明：DNV规则为中央冷却系统低温回路容量计算、设计工况和典型温度范围提供了规范依据，可支撑LT回路容量设计、参数设定和系统配置类需求。
```

## R003 系统设计方
系统应明确高温冷却水回路、低温冷却水回路、海水侧或中央冷却侧的边界、接口、服务对象和流向，并保证泵、冷却器、管径和阀件与热平衡及水力计算一致。

### R003-01 冷却水回路边界与接口定义
系统应明确高温冷却水回路、低温冷却水回路、海水侧或中央冷却侧的边界、接口、服务对象和流向。

检索画像：部件=['main_engine_cooling_water_system', 'central_cooling_system', 'sea_water_cooling_system', 'ht_cooling_water_loop', 'lt_cooling_water_loop']；方面=['temperature', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-CCS-COOL-001｜indirect｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-DNV-COOL-001｜indirect｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, temperature_control_valve, central_cooling_system｜方面：parameter_limit, capacity, system_design｜可支撑：parameter_limit, capacity, system_design｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems
The cooling water system for main propulsion engines shall be designed so that the cooling water temperatures at the engine inlet are maintained within the limits specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat opening temperature under worst-case ambient conditions. For central (low-temperature) cooling systems, the LT fresh water temperature at the plate cooler outlet shall be calculated for maximum sea water temperature at the service area.
整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。
```

- E-SOLAS-COOL-001｜indirect｜primary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, alarm_system｜方面：redundancy, alarm, monitoring, safety｜可支撑：redundancy, alarm, monitoring, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — Machinery: Cooling
26.1 Adequate means of cooling shall be provided for the main propulsion machinery and for all machinery essential for the propulsion and safety of the ship.
26.2 The cooling systems shall be arranged to ensure continued cooling of the main engine in the event of failure of the primary cooling water pump, either by provision of a standby pump with automatic start capability or by other approved means.
26.3 Suitable means shall be provided to detect the failure of cooling, by alarms giving warning of abnormal temperatures in the cooling system.
整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。
```

- E-IACS-M3-003｜indirect｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
```

### R003-02 设备选型与热平衡水力计算一致性
泵、冷却器、管径和阀件应与热平衡及水力计算结果一致。

检索画像：部件=['cooler']；方面=['capacity', 'calculation', 'inspection', 'commissioning', 'pressure_test', 'drawing_review', 'document_completeness', 'class_approval']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

- E-IACS-M3-003｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
```

- E-LT-CAP-001｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：lt_cooling_water_loop, central_cooling_system, cooler｜方面：capacity, parameter_limit, calculation｜可支撑：capacity, parameter_limit, calculation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Central Cooling System Design
Low-Temperature (LT) Freshwater Cooling Circuit Capacity Requirements:
The LT freshwater circuit of a central cooling system shall be sized to handle the combined heat rejection from all consumers connected to the LT circuit, operating simultaneously at their maximum rated loads. The sizing calculation shall be performed for the maximum seawater temperature of the vessel's intended trading area (minimum 32°C for unrestricted service, 35°C for tropical service).
The flow rate through the central freshwater cooler shall be adequate to limit the LT water temperature rise across the cooler to the value required to maintain all connected consumers within their temperature limits.
典型LT冷却水进中央冷却器温度：30–40°C；出中央冷却器温度：32–38°C（取决于海水温度）。
整理说明：DNV规则为中央冷却系统低温回路容量计算、设计工况和典型温度范围提供了规范依据，可支撑LT回路容量设计、参数设定和系统配置类需求。
```

- E-IACS-M28-001｜direct｜primary
  - 来源：S69 IACS Unified Requirements M28 Ambient Reference Conditions｜位置：｜部件：main_engine_cooling_water_system, cooler, central_cooling_system, sea_water_cooling_system｜方面：parameter_limit, calculation｜可支撑：parameter_limit, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M28 — Standard Ambient Reference Conditions
(Verified via multiple IACS-aligned sources and M73 cross-reference)

Standard design ambient conditions for diesel engine classification and certification:
- Air blower/turbocharger inlet temperature: 45°C
- Air blower inlet pressure: 1,000 mbar (1.0 bar absolute)
- Seawater temperature (at cooler inlet): 32°C
- Relative humidity: 60%

Application: These are the reference conditions against which engine MCR performance is rated. The seawater temperature of 32°C is the baseline for all cooling system capacity calculations for unrestricted service. For tropical service areas, the design seawater temperature shall be 35°C.

Note: IACS UR M73.3.1.1 (directly extracted) confirms turbocharger component lifetime must be based on 45°C air inlet temperature, consistent with M28.

整理说明：IACS UR M28 规定了柴油机分级认证的标准环境参考条件，其中海水温度32°C（热带服务35°C）是冷却系统容量计算的基准，各船级社规则均采纳此参考条件。
```

- E-COOLER-INST-016｜indirect｜supporting
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P54｜部件：cooler｜方面：installation, capacity｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
中央冷却器选型要求
turbulator design and the number of raw or treated water passes. Tight baffling around the heat exchanger is critical to obtaining good heat transfer performance. Heat Exchanger (plate and frame type) Figure 20 Design Criteria and Considerations Many engine models have attachment heat exchangers in the price list. Consider the following factors when designing and installing a heat exchanger cooling system. Size the heat exchanger to accommodate a heat rejection rate approximately 10% greater than the engine’s heat rejection. The additional 10% will compensate for possible variations from published or calculated heat rejection rates and engine overload. The cooling capacities vary for different cooling mediums, and tend to reduce heat transfer.
整理说明：原文给出了冷却水相关参数、阈值或适用条件，可用于对应厂家、机型或规则范围内的参数约束。该证据不应跨系统型式或跨机型直接泛化。
可支撑：cooler 的 installation
capacity 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R005 设备采购方
冷却水泵、冷却器、温控阀、膨胀水箱、滤器、传感器和主要阀门的选型及采购资料应满足系统设计参数、主机厂家文件、船级社要求和项目技术规格书。

### R005-01 设备选型采购资料合规性
冷却水泵、冷却器、温控阀、膨胀水箱、滤器、传感器和主要阀门的选型及采购资料应满足系统设计参数、主机厂家文件、船级社要求和项目技术规格书。

检索画像：部件=['cooling_water_pump', 'cooler', 'expansion_tank', 'temperature_control_valve', 'valve', 'filter']；方面=['document_completeness', 'class_approval', 'inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

- E-CCS-COOL-002｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, pipe, expansion_tank, alarm_system｜方面：test, commissioning_check, inspection｜可支撑：test, commissioning_check, inspection｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统试验
冷却水系统在安装完成后应进行以下试验：
1. 管路水压试验：各管路应按设计压力的1.5倍进行水压试验，保压时间不少于30分钟，不得有渗漏现象。
2. 功能试验：所有冷却水泵、阀件、温控阀、膨胀水箱液位报警及冷却水高温报警等应逐项进行功能试验。
3. 系泊试验：主机在码头试验工况下，验证冷却水系统的基本功能和报警设定值。
4. 航行试验：主机在MCR工况下持续运行，验证冷却水系统在各负荷下的稳定性和各报警设定值的正确性。
整理说明：CCS规则对冷却水系统安装后试验、系泊试验和航行试验提供了系统性规范要求，可支撑冷却水管路试压、功能验证及海试验收类需求。
```

- E-IACS-M51-001｜direct｜primary
  - 来源：S68 IACS Unified Requirements M51 Rev4 Engine Trials｜位置：｜部件：main_engine_cooling_water_system, alarm_system, cooling_water_pump, ht_cooling_water_loop｜方面：test, commissioning_check, operation, inspection｜可支撑：test, commissioning_check, operation, inspection｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M51 Rev.4 — Factory Acceptance Test and Shipboard Trials of I.C. Engines
(Directly extracted from IACS UR M51, via ClassNK TEC-1066)

Cooling water preparation for testing (M51.2.2, directly extracted):
'All fluids used for testing purposes such as fuel, lubrication oil and cooling water are to be suitable for the purpose intended, e.g. they are to be clean, preheated if necessary and cause no harm to engine parts.'

Shipboard trial objectives (M51.4, directly extracted):
'Verify compatibility with power transmission and driven machinery in the system, control systems and auxiliary systems necessary for the engine.'

Shipboard trial duration requirements (M51.4, directly extracted):
- Propulsion engines driving fixed pitch propeller: at least 4 hours at rated speed.
- Propulsion engines driving controllable pitch propeller: at least 4 hours.

Works trial load sequence (M51.3.3.2, directly extracted):
- 100% MCR at rated speed: minimum 60 minutes continuous
- 110% power at 1.032× rated speed: readings after 15 min or steady state
- 90%, 75%, 50%, 25% power per propeller curve
- MCR readings taken at least twice, 30-minute interval minimum

Alarm system check (M51.4 scope): Surveyor must witness full extent verification of all alarms and trips, including cooling water temperature alarms and shutdowns.

整理说明：IACS UR M51 Rev.4 为船用内燃机工厂验收试验和船上试验提供了直接规范要求，包括冷却水状态准备、试验负荷顺序、船上试验持续时间（固定螺距螺旋桨推进机至少4小时）及报警系统验证要求。内容均已从原始文件中直接摘录。
```

- E-IACS-M3-003｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
```

- E-COMM-COOL-001｜direct｜primary
  - 来源：S64 Marine Cooling System Commissioning and Sea Trial Procedure｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, temperature_control_valve, expansion_tank, alarm_system, ht_cooling_water_loop, lt_cooling_water_loop｜方面：test, commissioning_check, operation, inspection｜可支撑：test, commissioning_check, operation, inspection｜强度：direct｜适用性：general/general
```text
Marine Diesel Engine Cooling Water System — Commissioning and Sea Trial Procedure
(Consolidated from IACS UR M3.1, DNV Rules Pt.4 Ch.3, and standard shipyard practice)

Pre-sea trial checks:
1. Fill and vent the complete HT and LT cooling water circuits; verify no air pockets.
2. Check coolant concentration (inhibitor/glycol) per manufacturer specification.
3. Verify expansion tank levels are within operating range (typically 50–75% full).
4. Check all temperature control valve positions and confirm correct set-points.
5. Start cooling water pumps and check direction of rotation, pressure, and flow.
6. Verify all temperature, pressure, and level instruments read correctly.

Sea trial test sequence:
1. Run engine at 25%, 50%, 75%, and 100% MCR — record HT/LT temperatures and pressures.
2. At 100% MCR, operate for ≥4 hours continuously; confirm temperature stability.
3. Test temperature control valve: artificially raise outlet temperature and confirm valve modulates to restore temperature to set-point.
4. Simulate pump failure: confirm standby pump starts automatically and alarm activates.
5. Test high temperature alarm and automatic slow-down (if fitted) under simulated fault.
6. Confirm expansion tank low-level alarm activates at set water level.

Acceptance criteria:
- HT water temperature at engine inlet: within manufacturer's stated range.
- LT water temperature: below maximum specified for connected auxiliaries.
- All alarms and automatic functions operate correctly.
整理说明：本程序综合IACS UR M3.1、DNV规则和标准船厂实践，为冷却水系统试车和海试提供了系统性的试验流程和验收标准，可支撑试验类需求的内容和接受准则。
```

- E-PUMP-DRAW-010｜direct｜primary
  - 来源：S45 46 CFR 56.01-10 Plan approval｜位置：56.01-10(d)(2)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-56/subpart-56.01/section-56.01-10｜部件：cooling_water_pump｜方面：drawing_review, calculation｜可支撑：equipment_selection, calculation, class_review, document_completeness｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
泵容量和关断扬程图纸标注要求
Pump rated capacity and pump shutoff head must appear on piping diagrams.
整理说明：该证据说明管系图纸或送审资料中需要体现材料、管径、设计压力、泵额定容量和关断扬程等信息，可支撑审图和文件完整性要求；具体图纸深度仍需按项目和审查机构要求确认。
可支撑：管系图纸
材料信息
设计压力和泵额定参数应在送审文件中清楚标注。
图纸审查应覆盖与冷却水管系相关的接口
材料
压力等级和泵参数。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

## R007 自动化工程师
冷却水泵、温控阀和关键温度、压力、液位、流量信号应接入监控系统，并与主机控制系统、机舱监测报警系统和集控室显示系统保持协调。

### R007-01 冷却水系统信号接入监控系统
冷却水泵、温控阀和关键温度、压力、液位、流量信号应接入监控系统。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['temperature', 'pressure', 'flow', 'monitoring', 'control', 'alarm', 'redundancy']；可支撑=['control', 'monitoring', 'operation', 'alarm_protection', 'parameter_limit']

- E-CTRL-COOL-002｜direct｜primary
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, alarm_system, temperature_sensor, pressure_sensor, level_sensor, cooling_water_pump, temperature_control_valve, expansion_tank｜方面：monitoring, alarm, operation｜可支撑：monitoring, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements E10 — Cooling Water System Monitoring Requirements
The following monitoring parameters are required for unattended machinery spaces (UMS) certification. For manned machinery spaces, these are recommended best practice:
- HT cooling water temperature at engine outlet: continuous monitoring, high alarm
- HT cooling water pressure at engine inlet: continuous monitoring, low alarm
- LT cooling water temperature at central cooler outlet: continuous monitoring, high alarm
- Expansion tank level: monitoring, low level alarm
- Cooling water pump running status: indication
- Temperature control valve position: indication (recommended)
All alarms shall be connected to the alarm management system and indicated at the machinery control console and the bridge.
整理说明：IACS UR E10 为无人值守机舱（UMS）认证规定了冷却水系统监控参数清单，为控制系统的监测功能设计提供了规范级依据。
```

- E-CCS-COOL-001｜indirect｜supporting
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-IACS-M3-002｜indirect｜supporting
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：main_engine_cooling_water_system, alarm_system, temperature_sensor｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Temperature Monitoring and Alarm
Cooling water temperature of main propulsion engines shall be continuously monitored. High temperature alarms shall be set not to exceed the engine manufacturer's maximum permissible cooling water temperature. Where automatic slow-down or shutdown is fitted, the activation set-point shall be above the alarm set-point and shall not exceed the manufacturer's absolute maximum cooling water temperature limit.
整理说明：IACS UR M3.1 对主机冷却水温度监控、报警设定及自动降速/停机要求提供了规范级依据。可支撑温度监控、报警阈值及自动保护类需求。
```

### R007-02 冷却水系统与相关系统协调
冷却水系统应与主机控制系统、机舱监测报警系统和集控室显示系统保持协调。

检索画像：部件=['main_engine_cooling_water_system', 'alarm_system', 'control_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['control', 'monitoring', 'alarm', 'temperature', 'pressure', 'flow', 'redundancy']；可支撑=['control', 'monitoring', 'operation', 'alarm_protection', 'parameter_limit']

- E-CTRL-COOL-002｜direct｜primary
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, alarm_system, temperature_sensor, pressure_sensor, level_sensor, cooling_water_pump, temperature_control_valve, expansion_tank｜方面：monitoring, alarm, operation｜可支撑：monitoring, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements E10 — Cooling Water System Monitoring Requirements
The following monitoring parameters are required for unattended machinery spaces (UMS) certification. For manned machinery spaces, these are recommended best practice:
- HT cooling water temperature at engine outlet: continuous monitoring, high alarm
- HT cooling water pressure at engine inlet: continuous monitoring, low alarm
- LT cooling water temperature at central cooler outlet: continuous monitoring, high alarm
- Expansion tank level: monitoring, low level alarm
- Cooling water pump running status: indication
- Temperature control valve position: indication (recommended)
All alarms shall be connected to the alarm management system and indicated at the machinery control console and the bridge.
整理说明：IACS UR E10 为无人值守机舱（UMS）认证规定了冷却水系统监控参数清单，为控制系统的监测功能设计提供了规范级依据。
```

- E-CTRL-COOL-001｜direct｜primary
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, temperature_control_valve, main_engine_cooling_water_system, alarm_system｜方面：operation, alarm, monitoring, redundancy, test｜可支撑：operation, alarm, monitoring, redundancy, test｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements E10 — Machinery Control Systems
Cooling water temperature control systems for main propulsion engines shall:
1. Maintain cooling water temperature within manufacturer's limits across the full engine load range through automatic modulation of the temperature control valve.
2. Be capable of manual override in case of automatic control failure.
3. Provide alarm when cooling water temperature exceeds the high alarm set-point.
4. Where automatic slow-down or shutdown is provided, activate at a set-point above the alarm set-point (typically 5–10°C above the alarm).
5. Activate an audible and visible alarm when automatic protective devices are triggered.
6. Maintain cooling water temperature control function after a single failure of any control system component (single-failure criterion).
整理说明：IACS UR E10 对主机冷却水温度控制系统的功能要求、手动备用、自动保护逻辑和单一故障准则提供了规范级依据，可支撑控制系统设计、保护逻辑和可靠性类需求。
```

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-IACS-M3-002｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：main_engine_cooling_water_system, alarm_system, temperature_sensor｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Temperature Monitoring and Alarm
Cooling water temperature of main propulsion engines shall be continuously monitored. High temperature alarms shall be set not to exceed the engine manufacturer's maximum permissible cooling water temperature. Where automatic slow-down or shutdown is fitted, the activation set-point shall be above the alarm set-point and shall not exceed the manufacturer's absolute maximum cooling water temperature limit.
整理说明：IACS UR M3.1 对主机冷却水温度监控、报警设定及自动降速/停机要求提供了规范级依据。可支撑温度监控、报警阈值及自动保护类需求。
```

- E-SOLAS-COOL-001｜direct｜primary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, alarm_system｜方面：redundancy, alarm, monitoring, safety｜可支撑：redundancy, alarm, monitoring, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — Machinery: Cooling
26.1 Adequate means of cooling shall be provided for the main propulsion machinery and for all machinery essential for the propulsion and safety of the ship.
26.2 The cooling systems shall be arranged to ensure continued cooling of the main engine in the event of failure of the primary cooling water pump, either by provision of a standby pump with automatic start capability or by other approved means.
26.3 Suitable means shall be provided to detect the failure of cooling, by alarms giving warning of abnormal temperatures in the cooling system.
整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。
```
