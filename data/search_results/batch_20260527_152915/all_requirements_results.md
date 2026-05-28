# 需求证据包（V2 工程字段版）

## R001 船东代表
我希望主机冷却水系统运行稳定，不能因为冷却不足影响航行安全。泵和冷却器的配置要有冗余，单台设备故障时，主机仍应具备基本运行能力。

### R001-01 系统运行稳定性
主机冷却水系统应保证在各种工况下稳定运行，不因冷却不足影响主机安全。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'cooler', 'temperature_control_valve']；方面=['reliability', 'safety', 'capacity', 'temperature', 'pressure', 'flow', 'redundancy', 'control', 'alarm']；可支撑=['system_design', 'equipment_selection', 'parameter_limit', 'calculation', 'test', 'alarm_protection', 'operation']

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

- E-DNV-COOL-001｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, temperature_control_valve, central_cooling_system｜方面：parameter_limit, capacity, system_design｜可支撑：parameter_limit, capacity, system_design｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems
The cooling water system for main propulsion engines shall be designed so that the cooling water temperatures at the engine inlet are maintained within the limits specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat opening temperature under worst-case ambient conditions. For central (low-temperature) cooling systems, the LT fresh water temperature at the plate cooler outlet shall be calculated for maximum sea water temperature at the service area.
整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。
```

- E-IACS-M3-002｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：main_engine_cooling_water_system, alarm_system, temperature_sensor｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Temperature Monitoring and Alarm
Cooling water temperature of main propulsion engines shall be continuously monitored. High temperature alarms shall be set not to exceed the engine manufacturer's maximum permissible cooling water temperature. Where automatic slow-down or shutdown is fitted, the activation set-point shall be above the alarm set-point and shall not exceed the manufacturer's absolute maximum cooling water temperature limit.
整理说明：IACS UR M3.1 对主机冷却水温度监控、报警设定及自动降速/停机要求提供了规范级依据。可支撑温度监控、报警阈值及自动保护类需求。
```

### R001-02 冷却水泵冗余配置
冷却水泵应配置冗余，单台故障时系统仍能提供主机基本冷却能力。

检索画像：部件=['cooling_water_pump', 'sea_water_pump', 'cooler', 'main_engine_cooling_water_system']；方面=['capacity', 'redundancy', 'reliability', 'control', 'alarm']；可支撑=['system_design', 'equipment_selection', 'redundancy', 'alarm_protection']

- E-PUMP-RED-004｜direct｜primary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P197｜部件：cooling_water_pump｜方面：redundancy, capacity｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
11.1.2 The main engines cooling water systems shall fulfil the following requirements:.1 Sea-water cooling system of one main engine shall be provided with two pumps, one of which shall be a stand-by pump. The capacity of the stand-by pump shall not be less than that of the main pump. At least one of the pumps shall have independent drive. It is admissible to apply one common, independently driven stand -by pump for both sea and fresh water. The capacity of the pump shall not be less than that of the main pumps. Provision shall be made, however, to prevent the mixing of seawater and fresh water..2 Sea and fresh water cooling systems of two or more engines, may be served by: – separate pumps for each engine and in such a case no stand-by pumps are required, or – one pump for sea -water system of capacity sufficient for simultaneous cooling of all
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
capacity 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-IACS-M3-001｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump｜方面：capacity, redundancy, operation｜可支撑：capacity, redundancy, operation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Systems
At least two independent cooling water pumps shall be fitted for the cooling of main propulsion machinery. Where engine-driven pumps are fitted, at least one independently driven pump shall be provided. Each pump shall have sufficient capacity to supply the full cooling water flow required by the main engine under maximum continuous rating (MCR) conditions. The pumps shall be capable of being started independently and the changeover shall be achievable without interrupting operation.
整理说明：IACS UR M3.1 为主机冷却水泵数量、独立驱动要求及泵容量提供了规范级依据。可支撑冷却水泵冗余配置、容量设计及换泵操作类需求。
```

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
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

### R001-03 冷却器冗余配置
冷却器应配置冗余，单台故障时系统仍能提供主机基本冷却能力。

检索画像：部件=['cooler', 'cooling_water_pump', 'sea_water_pump', 'main_engine_cooling_water_system']；方面=['capacity', 'redundancy', 'reliability', 'control', 'alarm']；可支撑=['system_design', 'equipment_selection', 'redundancy', 'alarm_protection']

- E-SOLAS-COOL-001｜direct｜primary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, alarm_system｜方面：redundancy, alarm, monitoring, safety｜可支撑：redundancy, alarm, monitoring, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — Machinery: Cooling
26.1 Adequate means of cooling shall be provided for the main propulsion machinery and for all machinery essential for the propulsion and safety of the ship.
26.2 The cooling systems shall be arranged to ensure continued cooling of the main engine in the event of failure of the primary cooling water pump, either by provision of a standby pump with automatic start capability or by other approved means.
26.3 Suitable means shall be provided to detect the failure of cooling, by alarms giving warning of abnormal temperatures in the cooling system.
整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。
```

- E-IACS-M3-001｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump｜方面：capacity, redundancy, operation｜可支撑：capacity, redundancy, operation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Systems
At least two independent cooling water pumps shall be fitted for the cooling of main propulsion machinery. Where engine-driven pumps are fitted, at least one independently driven pump shall be provided. Each pump shall have sufficient capacity to supply the full cooling water flow required by the main engine under maximum continuous rating (MCR) conditions. The pumps shall be capable of being started independently and the changeover shall be achievable without interrupting operation.
整理说明：IACS UR M3.1 为主机冷却水泵数量、独立驱动要求及泵容量提供了规范级依据。可支撑冷却水泵冗余配置、容量设计及换泵操作类需求。
```

- E-DNV-COOL-002｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：cooling_water_pump, control_system｜方面：redundancy, capacity, alarm, operation｜可支撑：redundancy, capacity, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Pump Redundancy
At least two cooling water pumps shall be provided for the main engine cooling circuit. The pumps shall be arranged so that failure of one pump does not prevent the operation of the remaining pump(s). Where one pump is engine-driven, the other shall be electrically driven. Each pump shall be capable of maintaining required cooling water flow at all engine load conditions from idle to MCR. Automatic changeover to the standby pump shall be provided in case of pump failure, with alarm indication.
整理说明：DNV规则对主机冷却水泵冗余配置、独立驱动要求及自动切换功能提供了规范级依据。可支撑冗余泵配置、自动切换逻辑及报警要求。
```

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

### R001-04 单设备故障下主机运行能力
单台冷却水泵或冷却器故障时，主机应能维持基本运行能力。

检索画像：部件=['cooling_water_pump', 'cooler', 'main_engine_cooling_water_system', 'temperature_control_valve', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['monitoring', 'control', 'alarm', 'reliability', 'maintenance', 'temperature', 'pressure', 'flow', 'capacity']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-CTRL-COOL-001｜indirect｜supporting
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

- E-CCS-COOL-001｜indirect｜supporting
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-DNV-COOL-002｜indirect｜supporting
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：cooling_water_pump, control_system｜方面：redundancy, capacity, alarm, operation｜可支撑：redundancy, capacity, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Pump Redundancy
At least two cooling water pumps shall be provided for the main engine cooling circuit. The pumps shall be arranged so that failure of one pump does not prevent the operation of the remaining pump(s). Where one pump is engine-driven, the other shall be electrically driven. Each pump shall be capable of maintaining required cooling water flow at all engine load conditions from idle to MCR. Automatic changeover to the standby pump shall be provided in case of pump failure, with alarm indication.
整理说明：DNV规则对主机冷却水泵冗余配置、独立驱动要求及自动切换功能提供了规范级依据。可支撑冗余泵配置、自动切换逻辑及报警要求。
```
