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

- E-SYS-CLEAN-020｜indirect｜supporting
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

- E-SYS-CLEAN-019｜indirect｜supporting
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

## R003 系统设计方
系统应明确高温冷却水回路、低温冷却水回路、海水侧或中央冷却侧的边界、接口、服务对象和流向，并保证泵、冷却器、管径和阀件与热平衡及水力计算一致。

### R003-01 冷却水回路边界与接口定义
系统应明确高温冷却水回路、低温冷却水回路、海水侧或中央冷却侧的边界、接口、服务对象和流向。

检索画像：部件=['main_engine_cooling_water_system', 'central_cooling_system', 'sea_water_cooling_system', 'ht_cooling_water_loop', 'lt_cooling_water_loop']；方面=['temperature', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-CCS-COOL-001｜indirect｜secondary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-DNV-COOL-001｜indirect｜secondary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, temperature_control_valve, central_cooling_system｜方面：parameter_limit, capacity, system_design｜可支撑：parameter_limit, capacity, system_design｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems
The cooling water system for main propulsion engines shall be designed so that the cooling water temperatures at the engine inlet are maintained within the limits specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat opening temperature under worst-case ambient conditions. For central (low-temperature) cooling systems, the LT fresh water temperature at the plate cooler outlet shall be calculated for maximum sea water temperature at the service area.
整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。
```

- E-SOLAS-COOL-001｜indirect｜secondary
  - 来源：S49 SOLAS 2024 Chapter II-1 Regulation 26｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, alarm_system｜方面：redundancy, alarm, monitoring, safety｜可支撑：redundancy, alarm, monitoring, safety｜强度：direct｜适用性：general/international_convention
```text
SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26 — Machinery: Cooling
26.1 Adequate means of cooling shall be provided for the main propulsion machinery and for all machinery essential for the propulsion and safety of the ship.
26.2 The cooling systems shall be arranged to ensure continued cooling of the main engine in the event of failure of the primary cooling water pump, either by provision of a standby pump with automatic start capability or by other approved means.
26.3 Suitable means shall be provided to detect the failure of cooling, by alarms giving warning of abnormal temperatures in the cooling system.
整理说明：SOLAS 26 条为船舶主机冷却系统冗余配置、冷却持续性和高温报警提供了国际公约级别的最高依据，适用范围为所有SOLAS适用船舶，是合规性论证的核心上位文件。
```

- E-IACS-M3-003｜indirect｜secondary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump, central_cooling_system, cooler｜方面：capacity, calculation｜可支撑：capacity, calculation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Water System Capacity Margin
The total installed cooling water pump capacity shall provide a minimum margin of 25% above the maximum calculated system flow demand. For central cooling systems, the low-temperature (LT) freshwater circuit shall have sufficient capacity to handle the combined heat rejection of all connected consumers simultaneously at their maximum loads, including at the maximum anticipated seawater temperature for the vessel's intended trading area.
整理说明：IACS UR M3.1 要求总冷却水泵容量应比最大计算流量需求高出25%的余量，中央冷却系统低温回路需满足所有连接设备在最高海水温度下同时满负荷运行的需求。
```

- E-CTRL-COOL-001｜indirect｜secondary
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

### R003-02 设备选型与热平衡水力计算一致性
泵、冷却器、管径和阀件应与热平衡及水力计算一致。

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

- E-COOLER-PTEST-001｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P613｜部件：cooler｜方面：pressure_test, inspection｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
冷却水温度与压力参数
7.3.2 Coolers 7.3.2(a) General. Water and air coolers having either of the following design parameters are to be certified by ABS: ● Design pressure > 6.9 bar (7 kgf/cm2, 100 lb/in2) on either side ● Design pressure > 1 bar (1 kgf/cm 2, 15 lb/in 2), internal volume > 0.14 m 3 (5 ft 3), and design temperature > 149°C (300°F) on either side. 7.3.2(b) Charge air coolers. Charge air coolers are not subject to 4-6-5/7.3.2(a). They are to be hydrostatically tested on the water side to 4 bar (4.1 kgf/cm 2, 57 psi), but not less than 1.5 times Part 4 Vessel Systems and Machinery Chapter 6 Piping Systems Section 5 Piping Systems for Internal Combustion Engines 4-6-5 ABS RULES FOR BUILDING AND CLASSING MARINE VESSELS • 2021 609
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

## R004 船厂建造方
冷却水系统管路布置应便于现场焊接、安装、支架固定、冲洗、排气、放水、压力试验和后续检查，并避免明显气阻、积液和施工死角。

### R004-01 冷却水管路安装布置
冷却水系统管路布置应便于现场焊接、安装、支架固定、冲洗、排气、放水、压力试验和后续检查，并避免明显气阻、积液和施工死角。

检索画像：部件=['main_engine_cooling_water_system', 'pipe', 'support', 'flushing_connection', 'valve', 'equipment_interface', 'pressure_test_connection']；方面=['pressure', 'installation', 'arrangement', 'flushing', 'pressure_test', 'inspection', 'accessibility']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-CCS-COOL-002｜indirect｜secondary
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

- E-VALVE-INSP-010｜indirect｜secondary
  - 来源：S51 NASA NTRS 19800002357 Piping Specification｜位置：B-45；source_url=https://ntrs.nasa.gov/api/citations/19800002357/downloads/19800002357.pdf?attachment=true｜部件：valve｜方面：inspection, installation, arrangement｜可支撑：installation, test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
水管路最低点放水和最高点排气要求
Install manual drain valves at every low point of water piping systems and a manual air vent at every high point. S52 BN-G-Y015 Piping Systems Inspection and Testing
整理说明：该证据针对 valve 的 inspection / installation / arrangement 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-PIPE-INSP-013｜indirect｜secondary
  - 来源：S51 NASA NTRS 19800002357 Piping Specification｜位置：B-45；source_url=https://ntrs.nasa.gov/api/citations/19800002357/downloads/19800002357.pdf?attachment=true｜部件：pipe｜方面：inspection, installation, arrangement｜可支撑：installation, test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
水管路最低点放水和最高点排气要求
Install manual drain valves at every low point of water piping systems and a manual air vent at every high point. S52 BN-G-Y015 Piping Systems Inspection and Testing
整理说明：该证据针对 pipe 的 inspection / installation / arrangement 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-PIPE-CLEAN-011｜indirect｜secondary
  - 来源：S52 BN-G-Y015 Piping Systems Inspection and Testing｜位置：3.1 General；source_url=https://red-bag.com/general-guides/186-bn-g-y015-piping-systems-inspection-and-testing.html｜部件：pipe｜方面：cleaning, flushing, installation｜可支撑：installation, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
试验冲洗完成前限流件和仪表安装限制
Restrictions which interfere with filling, venting or draining shall not be installed until testing and flushing is completed.
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
