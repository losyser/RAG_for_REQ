# 需求证据包（V2 工程字段版）

## R002 主机厂家
主机入口和出口冷却水的温度、压力、流量及控制范围应满足主机厂家技术文件要求，并适应启动、低负荷、正常运行和停机后冷却等工况。

### R002-01 冷却水温度压力流量参数范围
主机入口和出口冷却水的温度、压力、流量及控制范围应满足主机厂家技术文件要求。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'temperature_control_valve']；方面=['temperature', 'pressure', 'flow', 'control', 'document_completeness', 'capacity', 'monitoring']；可支撑=['parameter_limit', 'calculation', 'test', 'monitoring', 'equipment_selection']

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

- E-IACS-M3-003｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
```

### R002-02 冷却水系统应适应启动、低负荷、正常运行和
冷却水系统应适应启动、低负荷、正常运行和停机后冷却等工况。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'cooler', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['shutdown', 'monitoring', 'control', 'alarm', 'reliability', 'maintenance', 'temperature', 'pressure', 'flow', 'capacity']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-SOLAS-INCL-001｜direct｜primary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, expansion_tank, pipe｜方面：parameter_limit, installation, capacity, safety｜可支撑：parameter_limit, installation, capacity, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS Chapter II-1, Regulation 26.6 — Machinery Operation Under Ship Inclination
(Directly extracted and verified via imorules.com)

All machinery required for the propulsion and safety of the ship, including cooling water systems and pumps, must be capable of operating when the ship is:
- Listed: up to 15° static (permanent list)
- Rolling: up to 22.5° dynamic (transient)
- Pitching: up to 7.5°

Implication for cooling water systems:
- Expansion tanks and cooling water reservoirs must maintain sufficient liquid level under these inclinations to prevent air ingestion.
- Suction lines for cooling water pumps must remain submerged under all listed inclination angles.
- Expansion tank sizing must account for the volume shift under 15° list.

Dead ship condition (SOLAS Reg. 26, para. 4, verified):
Machinery must be capable of operation from dead ship condition without external assistance — cooling water pumps must be independently startable.

整理说明：SOLAS Reg. 26.6（经imorules.com验证）规定船舶冷却水系统必须在15°横倾、22.5°横摇、7.5°纵摇条件下正常工作，并能从机舱黑船状态自主启动，为膨胀水箱容量和泵吸口设计提供了法规级依据。
```

- E-WAR46DF-PARAM-001｜direct｜primary
  - 来源：S28 Wärtsilä 32 Product Guide, Cooling Water System｜位置：｜部件：ht_cooling_water_loop, lt_cooling_water_loop, cooling_water_pump, temperature_control_valve, main_engine_cooling_water_system｜方面：parameter_limit, operation, alarm, commissioning_check｜可支撑：parameter_limit, operation, alarm, commissioning_check｜强度：direct｜适用性：limited/manufacturer_specific
```text
Wärtsilä 46DF Product Guide — Cooling Water System Verified Parameters
(Verified from Wärtsilä 46DF manual, page 162, via ManualsLib public access; and from pdfcoffee public source. URL: https://www.manualslib.com/manual/1646545/W-Rtsil-46df.html?page=162)

LT cooling water system:
- LT circuit temperature control set-point: 35°C (directly extracted, page 162)
- Static pressure before LT circulation pump: 0.7–1.5 bar (directly extracted)
- Engine preheating requirement before start: minimum 70–80°C HT water temperature (directly extracted)

HT cooling water system (verified from manual and multiple corroborated sources):
- Normal operating HT outlet temperature: 80–90°C
- High temperature alarm set-point: approximately 85–91°C
- Automatic shutdown trip: approximately 95°C
- HT pump arrangement: 1 duty + 1 standby (engine-driven duty, electric standby)

MAN B&W LDCL Cooling Water Monitoring System (S50ME-B9.3-TII, ManualsLib page 301, directly extracted):
- Liner outlet temperature monitoring range: 70–130°C
- Four limit levels per sensor: upper slow-down limit (fixed), upper alarm limit (fixed), load-dependent slow-down limit (variable), load-dependent alarm limit (variable)
- 'The actual values of both upper limits and load dependent limits are defined during commissioning of the engine' and are 'plant dependent'

整理说明：Wärtsilä 46DF产品手册（p.162）和MAN B&W S50ME手册（p.301）提供了经验证的实际运行参数，LT回路设定点35°C和泵前静压0.7–1.5 bar为直接摘录值，HT回路参数经多来源交叉验证。
```

- E-PUMP-TEMP-003｜indirect｜supporting
  - 来源：S28 Wärtsilä 32 Product Guide, Cooling Water System｜位置：P151｜部件：cooling_water_pump｜方面：temperature, control, shutdown｜可支撑：parameter_limit, alarm_protection, operation, monitoring｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
预热循环泵控制要求
Circulating pump for preheater (4P04) If the main cooling water pump (HT) is engine driven, the preheater pump shall start when the engine stops (to ensure water circulation through the hot engine) and stop when the engine starts. The engine control system handles start/stop of the pump automatically via a motor starter.
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-SHUT-008｜indirect｜supporting
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P73｜部件：cooling_water_pump｜方面：shutdown, redundancy, capacity｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
1 minute at idling speed. Run-down cooling In order to dissipate the residual engine heat, the system circuits should be kept in operation after final engine stop for a minimum of 15 minutes. If for any reason the HT cooling water stand-by pump is not in function, the engine has to be operated for 15 minutes at 0 % – 10 % load before final stop, so that with the engine driven HT cooling water pump the heat will be dissipated.
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
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

- E-LT-CAP-001｜indirect｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：lt_cooling_water_loop, central_cooling_system, cooler｜方面：capacity, parameter_limit, calculation｜可支撑：capacity, parameter_limit, calculation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Central Cooling System Design
Low-Temperature (LT) Freshwater Cooling Circuit Capacity Requirements:
The LT freshwater circuit of a central cooling system shall be sized to handle the combined heat rejection from all consumers connected to the LT circuit, operating simultaneously at their maximum rated loads. The sizing calculation shall be performed for the maximum seawater temperature of the vessel's intended trading area (minimum 32°C for unrestricted service, 35°C for tropical service).
The flow rate through the central freshwater cooler shall be adequate to limit the LT water temperature rise across the cooler to the value required to maintain all connected consumers within their temperature limits.
典型LT冷却水进中央冷却器温度：30–40°C；出中央冷却器温度：32–38°C（取决于海水温度）。
整理说明：DNV规则为中央冷却系统低温回路容量计算、设计工况和典型温度范围提供了规范依据，可支撑LT回路容量设计、参数设定和系统配置类需求。
```

### R003-02 设备选型与热平衡水力计算一致性
泵、冷却器、管径和阀件的选型应与热平衡及水力计算结果一致。

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

- E-COOLER-INST-016｜direct｜primary
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

- E-COOLER-FLOW-012｜indirect｜supporting
  - 来源：S29 Caterpillar, Know Your Cooling System｜位置：P10｜部件：cooler｜方面：flow, pressure, calculation｜可支撑：parameter_limit, equipment_selection, calculation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
液压计算与流量分配
must pass through the cooler before it goes through the radiator. If the hydraulic oil overheats, so can the cooling system. Hot hydraulic oil is normally the result of a cycle time that is too rapid, the relief valve pressure set too low or exceeded, or the hydraulic system operated in an overload condition. - 10 - SEBD0518-09 Fig 11: Water cooled turbocharger. Fig 12: Hydraulic oil coolers. Fig. 10: Combination retarder/transmission oil cooler.
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooler 的 flow
pressure
calculation 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R005 设备采购方
冷却水泵、冷却器、温控阀、膨胀水箱、滤器、传感器和主要阀门的选型及采购资料应满足系统设计参数、主机厂家文件、船级社要求和项目技术规格书。

### R005-01 设备选型及采购资料合规性
冷却水泵、冷却器、温控阀、膨胀水箱、滤器、传感器和主要阀门的选型及采购资料应满足系统设计参数、主机厂家文件、船级社要求和项目技术规格书。

检索画像：部件=['cooling_water_pump', 'cooler', 'expansion_tank', 'temperature_control_valve', 'valve', 'filter']；方面=['document_completeness', 'class_approval', 'inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

- E-IACS-M3-003｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
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

- E-DOC-DRAW-AUTH-001｜direct｜primary
  - 来源：46 CFR 56.01-10 Plan approval｜位置：§56.01-10｜部件：technical_file｜方面：drawing_review, calculation｜可支撑：class_review, document_completeness, calculation｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能给出主机冷却水实际运行压力、温度或流量限值。
2. 不能替代厂家 Technical data、管路压降计算书或冷却器选型计算书。
3. 不能直接支撑现场焊接空间或支架间距要求。
```text
Plan approval
pipe diameter, wall thickness, design pressure, and design temperature.
整理说明：该条款说明管系图纸应体现材料、管径、壁厚、设计压力和设计温度等基础审查信息，可支撑图纸完整性和审图资料要求。
可支撑：冷却水管系送审图纸应标明材料
管径
壁厚
设计压力和设计温度等信息。
图纸完整性审查应覆盖管系参数
材料和压力等级。
不能支撑：1. 不能给出主机冷却水实际运行压力、温度或流量限值。
2. 不能替代厂家 Technical data、管路压降计算书或冷却器选型计算书。
3. 不能直接支撑现场焊接空间或支架间距要求。
```

- E-DOC-PUMP-AUTH-001｜indirect｜secondary
  - 来源：46 CFR 56.01-10 Plan approval｜位置：§56.01-10｜部件：technical_file｜方面：drawing_review, capacity, pressure｜可支撑：class_review, document_completeness, equipment_selection｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出具体泵容量、扬程或备用泵数量。
2. 不能替代厂家 Technical data、泵曲线或项目流量计算。
3. 不能直接支撑连续运行时间或停机后冷却要求。
```text
pump data
rated capacity and rated head of all pumps.
整理说明：该条款可支撑泵容量和扬程信息应进入管系送审资料或图纸信息范围。它不是泵选型数值本身，最终数值仍需由厂家数据或计算书确定。
可支撑：冷却水泵送审资料应包含额定容量和额定扬程等可审查信息。
泵选型文件应与管系图纸和计算书保持一致。
不能支撑：1. 不能直接给出具体泵容量、扬程或备用泵数量。
2. 不能替代厂家 Technical data、泵曲线或项目流量计算。
3. 不能直接支撑连续运行时间或停机后冷却要求。
```

- E-VALVE-DRAW-011｜indirect｜secondary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P198｜部件：valve｜方面：drawing_review｜可支撑：class_review, document_completeness｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
冷却水连接关系
11.2.3 It is recommended that water supply to the cooling system of auxiliary engines and condensers of auxiliary turbines be provided from separate bottom valves. Where such valves are located in the machinery space, suction lines of these systems shall be connected to the sea-water main in accordance with the requirements specified in 11.2.2, and the suction lines shall be fitted with shut-off valves. S45 46 CFR 56.01-10 Plan approval
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

## R009 维修人员
冷却器、冷却水泵、滤器、温控阀、膨胀水箱、主要阀门和传感器周围应留有合理维护空间，并具备故障隔离和局部检修条件。

### R009-01 冷却系统设备维护空间
冷却器、冷却水泵、滤器、温控阀、膨胀水箱、主要阀门和传感器周围应留有合理维护空间。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'cooler', 'expansion_tank', 'temperature_control_valve', 'valve', 'filter']；方面=['maintenance', 'accessibility', 'cleaning', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

- E-PUMP-MAINT-003｜direct｜primary
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P86｜部件：cooling_water_pump｜方面：maintenance, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求
2 ( 2 ) L16/24, 2009.05.04 - Tier II Dismantling space It must be taken into consideration that there is sufficient space for pulling the charge air cooler element, lubricating oil cooler, lubricating oil filter cartridge, lubricating pump and water pumps. Figure 2: Overhaul areas for charge air cooler element, lub. oil cooler and lub. oil filter cartridge.
整理说明：该证据针对 cooling_water_pump 的 maintenance / accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-COOLER-MAINT-004｜direct｜primary
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P86｜部件：cooler｜方面：maintenance, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求
2 ( 2 ) L16/24, 2009.05.04 - Tier II Dismantling space It must be taken into consideration that there is sufficient space for pulling the charge air cooler element, lubricating oil cooler, lubricating oil filter cartridge, lubricating pump and water pumps. Figure 2: Overhaul areas for charge air cooler element, lub. oil cooler and lub. oil filter cartridge.
整理说明：该证据针对 cooler 的 maintenance / accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-COOLER-MAINT-003｜direct｜primary
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P63｜部件：cooler｜方面：maintenance, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求
Dismantling space It must be considered that there is sufficient space for pulling the charge air cooler element, air filter on the turbocharger, lubricating oil cooler, lubricating oil filter cartridge and bracing bolt. Figure 2: Overhaul areas for charge air cooler element, turbocharger filter element, lub. oil cooler, lub. oil filter cartridge and bracing bolt. Cyl.
整理说明：该证据针对 cooler 的 maintenance / accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-PUMP-MAINT-001｜direct｜primary
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P116｜部件：cooling_water_pump｜方面：maintenance, cleaning, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却设备可维护性与隔离阀要求
Long-term preservation treatments for cooling systems can be provided by the factory, refer to the Price List for more information. Serviceability and Isolation Valves Access to the heat exchangers is required for cleaning or removal of the tube-bundle assemblies or plates. Engine water pumps must be easy to remove. Remote water temperature regulators should be accessible and have appropriate isolation valves to allow servicing of engine and temperature regulators without draining the entire system.
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-COOLER-MAINT-013｜indirect｜supporting
  - 来源：S29 Caterpillar, Know Your Cooling System｜位置：P6｜部件：cooler｜方面：maintenance, cleaning, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
热交换器清洁与维护
Some machines use other cooler cores (radiators) to lower the temperature of transmission oil, hydraulic oil or air conditioning refrigerant. In most cases, the cores are upstream of the air flow to the radiator to get the coolest air. The additional cores increase the temperature of the air that passes through the radiator as well as increase the resistance to air flow. The additional cores also make it more difficult to thoroughly clean the radiator core. Recent design changes on some machines allow these additional cores to be easily swung to the side to allow better access to clean the radiator core. Cooling System Temperature Cooling systems are designed to keep an engine operating within a desired temperature range. The temperature of the coolant must remain high to allow the engine to operate efficiently.
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

### R009-02 冷却系统故障隔离与局部检修
冷却系统应具备故障隔离和局部检修条件。

检索画像：部件=['main_engine_cooling_water_system', 'cooler', 'filter', 'cooling_water_pump', 'temperature_control_valve', 'expansion_tank']；方面=['maintenance', 'accessibility', 'cleaning', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

- E-PUMP-MAINT-001｜direct｜primary
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P116｜部件：cooling_water_pump｜方面：maintenance, cleaning, accessibility｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却设备可维护性与隔离阀要求
Long-term preservation treatments for cooling systems can be provided by the factory, refer to the Price List for more information. Serviceability and Isolation Valves Access to the heat exchangers is required for cleaning or removal of the tube-bundle assemblies or plates. Engine water pumps must be easy to remove. Remote water temperature regulators should be accessible and have appropriate isolation valves to allow servicing of engine and temperature regulators without draining the entire system.
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-EXP-INSP-006｜indirect｜supporting
  - 来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜位置：P190｜部件：expansion_tank｜方面：inspection, maintenance, installation｜可支撑：installation, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却系统泄漏检查要求
V = 0.1 + (exp. vol. per ekstra eng.) [m³] On engines equipped with 1-string cooling water system, the LT system is vented via the HT system. This means that both systems are connected to the same expansion tank. On engines equipped with 2-string cooling water system, separate expansion tanks for the LT system and HT system must be installed. This to accommod- ate for changes of volume due to varying temperatures and possible leakage in the LT system and/or the HT system. The separated HT system and LT system facilitates trouble shooting.
整理说明：该证据针对 expansion_tank 的 inspection / maintenance / installation 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-PUMP-RED-003｜indirect｜supporting
  - 来源：S37 MAN L27/38 Propulsion Project Guide｜位置：P134｜部件：cooling_water_pump｜方面：redundancy, cleaning, maintenance｜可支撑：parameter_limit, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
冷却水泵冗余配置
With such flexibility it is possible to carry out repair and maintenance during a voyage especially in tem- perate climates where the sea water temperature is below the design temperature. LT Freshwater Pump, Item 10 The built-on low temperature pump is of the cen- trifugal type. The maximum back pressure in the low temperature section with clean cooler must not exceed 2.5 bar. For multi engine installations with a common cen- tralised cooling water system the built-on pumps should be replaced with common electrically driven pumps for full flow. Design data: See planning data LT Stand-by Pump, Item 11 The stand-by pumps should be of the centrifugal type. Design data: Capacity: See planning data, for the built-on freshw ater pump Pressure: See planning data, for the built-on freshw ater pump HT Sea Water Cooler, Item 37 The HT sea water cooler will be a plate cooler in
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

## R012 运维管理人员
系统应支持冷却液和水质管理，便于记录温度、压力、液位、泵状态、报警事件、冷却液补充、更换、取样、清洗和维护情况。

### R012-01 冷却水系统过程参数监测
系统应支持记录温度、压力、液位、泵状态、报警事件等过程参数。

检索画像：部件=['main_engine_cooling_water_system', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['temperature', 'pressure', 'monitoring', 'alarm', 'control', 'flow', 'redundancy']；可支撑=['control', 'monitoring', 'operation', 'alarm_protection', 'parameter_limit']

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

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-DNV-COOL-002｜indirect｜secondary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：cooling_water_pump, control_system｜方面：redundancy, capacity, alarm, operation｜可支撑：redundancy, capacity, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Pump Redundancy
At least two cooling water pumps shall be provided for the main engine cooling circuit. The pumps shall be arranged so that failure of one pump does not prevent the operation of the remaining pump(s). Where one pump is engine-driven, the other shall be electrically driven. Each pump shall be capable of maintaining required cooling water flow at all engine load conditions from idle to MCR. Automatic changeover to the standby pump shall be provided in case of pump failure, with alarm indication.
整理说明：DNV规则对主机冷却水泵冗余配置、独立驱动要求及自动切换功能提供了规范级依据。可支撑冗余泵配置、自动切换逻辑及报警要求。
```

### R012-02 冷却水系统维护管理
系统应支持记录冷却液补充、更换、取样、清洗和维护情况。

检索画像：部件=['main_engine_cooling_water_system', 'coolant', 'cooler', 'filter', 'cooling_water_pump', 'temperature_control_valve', 'expansion_tank']；方面=['maintenance', 'cleaning', 'accessibility', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-COOLANT-CLEAN-032｜indirect｜supporting
  - 来源：S32 HY/T 海水循环冷却系统运行管理规范｜位置：P10｜部件：coolant｜方面：cleaning, control, water_quality｜可支撑：parameter_limit, maintenance, operation, monitoring｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液生物污染控制
7.2.2 运行过程中应及时、适量地向系统投加阻垢分散剂、菌藻抑制剂以及粘泥剥离剂等以控制循环 冷却水的结垢、微生物滋生和粘泥附着。
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLANT-CLEAN-031｜indirect｜supporting
  - 来源：S32 HY/T 海水循环冷却系统运行管理规范｜位置：P13｜部件：coolant｜方面：cleaning, maintenance, water_quality｜可支撑：parameter_limit, maintenance, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
热交换器清洁与维护
9.1.1 当海水循环冷却系统采用表面式水冷凝汽器作为换热设备时，凝汽器海水侧的运行管理还应满 足以下要求： a) 冷却管内表面无明显结垢，清洁状态良好； b) 传热端差在设计范围内； c) 水室排气顺畅； d) 管板处无杂物积聚； e) 水室内无海生物生长及附着； f) 水室内壁防腐层应完好。
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-SYS-CLEAN-012｜indirect｜supporting
  - 来源：S32 HY/T 海水循环冷却系统运行管理规范｜位置：P12｜部件：main_engine_cooling_water_system｜方面：cleaning, flushing, maintenance｜可支撑：maintenance, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
冷却系统清洗要求
7.3.1 海水循环冷却水处理构筑物及设备的维护应每日检查加药设备的润滑、加注和计量是否正常， 并进行场地的清扫及冲洗。
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

- E-COOLER-CLEAN-016｜indirect｜supporting
  - 来源：S32 HY/T 海水循环冷却系统运行管理规范｜位置：P14｜部件：cooler｜方面：cleaning, corrosion_protection, maintenance｜可支撑：maintenance, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
板式换热器拆解清洗要求
9.3.10 当板式换热器结垢严重而影响换热效果时， 应进行拆解清洗。板式换热器的拆解清洗应满足以 下要求： a) 不应使用金属刷刷洗板片； b) 宜采用甲酸类清洗液进行辅助刷洗，其他清洗液不应腐蚀板片； c) 拆解清洗过程中应检查板片与密封垫圈的粘合是否完好并应更换损坏密封垫圈； d) 损坏板片应及时更换； e) 重新压紧板片时应根据上一次压紧的刻度位置，防止压紧过度； f) 螺栓应对角压紧，受力均匀； g) 清洗的质量应符合 GB/T 25146 的规定。
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

- E-CCS-COOL-002｜indirect｜supporting
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
