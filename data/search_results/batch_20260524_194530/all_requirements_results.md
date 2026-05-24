# 需求证据包（V2 工程字段版）

## R001 船东代表
主机冷却水系统应保证船舶在连续运行、负荷变化和高温环境下具有稳定可靠的冷却能力，避免因冷却不足影响推进安全和运行经济性。

### R001-01 冷却水系统运行稳定性
主机冷却水系统在连续运行、负荷变化和高温环境下应具有稳定可靠的冷却能力，避免因冷却不足影响推进安全和运行经济性。

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

## R002 主机厂家
主机入口和出口冷却水的温度、压力、流量及控制范围应满足主机厂家技术文件要求，并适应启动、低负荷、正常运行和停机后冷却等工况。

### R002-01 冷却水温度压力流量参数
主机入口和出口冷却水的温度、压力、流量及控制范围应满足主机厂家技术文件要求。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'temperature_control_valve']；方面=['temperature', 'pressure', 'flow', 'control', 'document_completeness', 'capacity', 'monitoring']；可支撑=['parameter_limit', 'calculation', 'test', 'monitoring', 'equipment_selection']

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

### R002-02 冷却水系统多工况适应性
冷却水系统应适应启动、低负荷、正常运行和停机后冷却等工况。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'cooler', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['shutdown', 'monitoring', 'control', 'alarm', 'reliability', 'maintenance', 'temperature', 'pressure', 'flow', 'capacity']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

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

- E-PUMP-TEMP-003｜direct｜supporting
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

- E-SYS-CLEAN-020｜direct｜supporting
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P244｜部件：main_engine_cooling_water_system｜方面：cleaning, temperature, flushing｜可支撑：parameter_limit, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
发动机启动与冷却水预热条件
General The engine may be started and loaded according to the following procedure: A: Normal start without preheated cooling water. Only on MDO. B: Normal start with preheated cooling water. MDO or HFO. C: Stand-by engine. Emergency start, with pre- heated cooling water, intermediate prelubri- cating or continuos prelubricating. MDO or HFO. Starting on HFO During shorter stops or if the engine is in stand-by on HFO the engine must be preheated. During preheating the cooling water outlet tempera- ture should be kept as high as possible at least 60°C (± 5°C) -either by means of cooling water from engines which are running or by means of a built-in preheater. If the engine normally runs on HFO preheated fuel must be circulated through the engine while pre- heating although the engine has run or has been flushed on MDO for a short period.
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-SYS-CLEAN-019｜direct｜supporting
  - 来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜位置：P259｜部件：main_engine_cooling_water_system｜方面：cleaning, temperature, flushing｜可支撑：parameter_limit, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
发动机启动与冷却水预热条件
are running or with a built-in pre-heater. If the engine normally runs on HFO, pre-heated fuel must be circulated through the injection pumps while pre-heating the engine, although the engine just has run or has been flushed on MDO/MGO for a short period. Starting on MDO/MGO For starting on MDO/MGO, there are no restrictions except lubricating oil vis- cosity may not by higher than 1500 cSt. (5°C for SAE 30 or 10°C for SAE 40). Initial ignition may be difficult if the engine and the ambient temperature are lower than 5°C and the cooling water temperature is lower than 15°C. Prelubricating The engine shall always be pre-lubricated 2 minutes prior to start if there is no pre-lubrication at intervals or continuous pre-lubrication installed. Pre-lubrication at intervals is 2 minutes every 10 minutes.
整理说明：原文涉及冷却水系统、换热器或管路的清洗、冲洗、结垢处理或清洗后复查，可支撑维护清洗类要求。若原文未给出药剂浓度、流速、周期或验收指标，则这些参数仍需由项目维护程序或厂家文件确认。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R011 船级社验船师
系统设计、材料、设备选型、管路布置、报警保护、备用冷却能力、试验验证和技术文件应满足适用船级社审查和验收要求。

### R011-01 系统设计审查与验收
系统设计、材料、设备选型、管路布置、报警保护、备用冷却能力、试验验证和技术文件应满足适用船级社审查和验收要求。

检索画像：部件=['pipe']；方面=['capacity', 'redundancy', 'alarm', 'arrangement', 'document_completeness', 'material', 'class_approval', 'inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

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

- E-PIPE-PTEST-012｜indirect｜supporting
  - 来源：S47 46 CFR 58.20-25 Tests｜位置：58.20-25(a)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-58/subpart-58.20/section-58.20-25｜部件：pipe｜方面：pressure_test, inspection｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
安装后管路设计压力泄漏试验要求
All pressure vessels, compressors, piping, and direct expansion cooling coils must be leak tested after installation to their design pressures. S48 46 CFR 197.462 Pressure vessels and pressure piping
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

## R012 运维管理人员
系统应支持冷却液和水质管理，便于记录温度、压力、液位、泵状态、报警事件、冷却液补充、更换、取样、清洗和维护情况。

### R012-01 冷却水系统过程参数监测
系统应支持记录温度、压力、液位、泵状态等过程参数。

检索画像：部件=['main_engine_cooling_water_system', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['temperature', 'pressure', 'monitoring', 'control', 'flow', 'alarm', 'redundancy']；可支撑=['control', 'monitoring', 'operation', 'alarm_protection', 'parameter_limit']

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

### R012-02 冷却水系统报警事件记录
系统应支持记录报警事件。

检索画像：部件=['main_engine_cooling_water_system', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['alarm', 'shutdown', 'load_reduction', 'monitoring', 'temperature', 'pressure', 'flow']；可支撑=['alarm_protection', 'monitoring', 'operation', 'test', 'parameter_limit']

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

- E-SOLAS-COOL-001｜direct｜primary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, alarm_system｜方面：redundancy, alarm, monitoring, safety｜可支撑：redundancy, alarm, monitoring, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — Machinery: Cooling
26.1 Adequate means of cooling shall be provided for the main propulsion machinery and for all machinery essential for the propulsion and safety of the ship.
26.2 The cooling systems shall be arranged to ensure continued cooling of the main engine in the event of failure of the primary cooling water pump, either by provision of a standby pump with automatic start capability or by other approved means.
26.3 Suitable means shall be provided to detect the failure of cooling, by alarms giving warning of abnormal temperatures in the cooling system.
整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。
```

- E-IACS-M3-002｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：main_engine_cooling_water_system, alarm_system, temperature_sensor｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Temperature Monitoring and Alarm
Cooling water temperature of main propulsion engines shall be continuously monitored. High temperature alarms shall be set not to exceed the engine manufacturer's maximum permissible cooling water temperature. Where automatic slow-down or shutdown is fitted, the activation set-point shall be above the alarm set-point and shall not exceed the manufacturer's absolute maximum cooling water temperature limit.
整理说明：IACS UR M3.1 对主机冷却水温度监控、报警设定及自动降速/停机要求提供了规范级依据。可支撑温度监控、报警阈值及自动保护类需求。
```

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-PARAM-HT-001｜indirect｜secondary
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

### R012-03 冷却水系统维护管理
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

- E-EXP-INSP-022｜indirect｜supporting
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P227｜部件：expansion_tank｜方面：inspection, water_quality, cleaning｜可支撑：parameter_limit, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液水质检测方法
been done, the engine coolant must be immediately treated with anticorro- sive agent. Once the engine has been brought back into operation, the cleaned system must be checked for leaks. Regular checks of the coolant condition and coolant system Treated coolant may become contaminated when the engine is in operation, which causes the additive to loose some of its effectiveness. It is therefore advisable to regularly check the cooling system and the coolant condition. To determine leakages in the lube oil system, it is advisable to carry out regular checks of water in the expansion tank. Indications of oil content in water are, e.g. discoloration or a visible oil film on the surface of the water sample. The additive concentration must be checked at least once a week using the test kits specified by the manufacturer. The results must be documented.
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
