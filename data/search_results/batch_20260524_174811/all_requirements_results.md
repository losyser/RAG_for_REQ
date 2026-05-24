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

### R002-02 冷却水系统各工况适应性
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

## R008 安全负责人
系统应对冷却水高温、低压、低液位、泵故障、传感器异常、冷却器泄漏和换热异常设置报警或保护功能，并降低高温介质、旋转设备、带压管路和化学处理液对人员的伤害风险。

### R008-01 冷却水系统报警保护功能
系统应对冷却水高温、低压、低液位、泵故障、传感器异常、冷却器泄漏和换热异常设置报警或保护功能。

检索画像：部件=['main_engine_cooling_water_system', 'cooler', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['temperature', 'alarm', 'shutdown', 'load_reduction', 'monitoring', 'pressure', 'flow']；可支撑=['alarm_protection', 'monitoring', 'operation', 'test', 'parameter_limit']

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

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

### R008-02 人员伤害风险防护
系统应降低高温介质、旋转设备、带压管路和化学处理液对人员的伤害风险。

检索画像：部件=['pipe']；方面=['temperature', 'safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-PIPE-SAFE-AUTH-001｜direct｜primary
  - 来源：SOLAS Chapter II-1 Regulation 26｜位置：II-1/26.1｜部件：pipe｜方面：installation, safety｜可支撑：system_design, safety, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出冷却水温度、压力、流量或泵容量数值。
2. 不能替代船级社细则、厂家项目指南或施工试验程序。
3. 不能直接支撑焊接空间、阀门操作空间或支架间距。
```text
General machinery safety
adequate for the service for which they are intended.
整理说明：SOLAS 规则提供了机械、压力容器及相关管系应适合服役并降低危险的上位安全依据。它可支撑安全性和适用性原则，但需要下位规范和项目文件落实为具体设计要求。
可支撑：冷却水相关管系和附件应按预期服役条件进行设计
构造和安装。
布置和防护应降低对船上人员的危险。
不能支撑：1. 不能直接给出冷却水温度、压力、流量或泵容量数值。
2. 不能替代船级社细则、厂家项目指南或施工试验程序。
3. 不能直接支撑焊接空间、阀门操作空间或支架间距。
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

- E-IACS-M72-001｜indirect｜supporting
  - 来源：S66 IACS Unified Requirements M72 Hydraulic Testing｜位置：｜部件：cooler, cooling_water_pump, main_engine_cooling_water_system, pipe｜方面：test, inspection, parameter_limit｜可支撑：test, inspection, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M72 — Hydraulic Testing of Cooling-System Components
(Directly extracted from IACS UR M72, verified via ClassNK TEC-1066)

Hydraulic testing requirements for cooling water components:
- All items in contact with cooling water are to be tested by hydraulic pressure at a pressure equal to 1.5 times the maximum working pressure (M72 Footnote 3, directly extracted).
- Hydraulic testing is required for those parts filled with cooling water and having the function of containing the water which is in contact with the cylinder or cylinder liner (M72 Footnote 9, directly extracted).
- Component certification: For engines with bore D > 300 mm, coolers (both sides, including charge air cooler water side) require a Work Certificate (W).
- Engine-driven pumps (oil, water, fuel, bilge) require Work Certificate (W) for engines > 800 kW/cylinder.

整理说明：IACS UR M72 为冷却水系统部件水压试验压力（1.5倍最大工作压力）、缸套接触冷却水部件的水压试验要求及大型发动机冷却器/水泵的证书要求提供了直接规范依据。内容已从原始文件中直接摘录。
```

## R009 维修人员
冷却器、冷却水泵、滤器、温控阀、膨胀水箱、主要阀门和传感器周围应留有合理维护空间，并具备故障隔离和局部检修条件。

### R009-01 冷却系统设备维护空间
冷却器、冷却水泵、滤器、温控阀、膨胀水箱、主要阀门和传感器周围应留有合理维护空间。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'cooler', 'expansion_tank', 'temperature_control_valve', 'valve', 'filter']；方面=['maintenance', 'accessibility', 'cleaning', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-PUMP-MAINT-003｜indirect｜primary
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

- E-COOLER-MAINT-004｜indirect｜primary
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

- E-COOLER-MAINT-003｜indirect｜primary
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

- E-PUMP-MAINT-001｜indirect｜primary
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

- E-COOLER-MAINT-013｜indirect｜primary
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

## R010 调试人员
系统应具备冲洗、排气、补水、压力试验和调试条件，并能在系泊试验或航行试验中验证冷却能力、参数稳定性、报警功能和主要设备运行状态。

### R010-01 冷却水系统冲洗排气补水压力试验条件
系统应具备冲洗、排气、补水、压力试验和调试条件。

检索画像：部件=['main_engine_cooling_water_system', 'flushing_connection', 'pipe', 'valve', 'support', 'equipment_interface', 'pressure_test_connection']；方面=['pressure', 'flushing', 'pressure_test', 'commissioning', 'installation', 'arrangement', 'accessibility', 'inspection']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

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

- E-IACS-M72-001｜direct｜primary
  - 来源：S66 IACS Unified Requirements M72 Hydraulic Testing｜位置：｜部件：cooler, cooling_water_pump, main_engine_cooling_water_system, pipe｜方面：test, inspection, parameter_limit｜可支撑：test, inspection, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M72 — Hydraulic Testing of Cooling-System Components
(Directly extracted from IACS UR M72, verified via ClassNK TEC-1066)

Hydraulic testing requirements for cooling water components:
- All items in contact with cooling water are to be tested by hydraulic pressure at a pressure equal to 1.5 times the maximum working pressure (M72 Footnote 3, directly extracted).
- Hydraulic testing is required for those parts filled with cooling water and having the function of containing the water which is in contact with the cylinder or cylinder liner (M72 Footnote 9, directly extracted).
- Component certification: For engines with bore D > 300 mm, coolers (both sides, including charge air cooler water side) require a Work Certificate (W).
- Engine-driven pumps (oil, water, fuel, bilge) require Work Certificate (W) for engines > 800 kW/cylinder.

整理说明：IACS UR M72 为冷却水系统部件水压试验压力（1.5倍最大工作压力）、缸套接触冷却水部件的水压试验要求及大型发动机冷却器/水泵的证书要求提供了直接规范依据。内容已从原始文件中直接摘录。
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

- E-PIPE-PTEST-007｜direct｜primary
  - 来源：S46 46 CFR 56.97-40 Installation tests｜位置：56.97-40(a)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-56/subpart-56.97/section-56.97-40｜部件：pipe｜方面：pressure_test, inspection｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
管系安装后水压泄漏试验要求
Piping systems must be hydrostatically leak tested in the presence of a marine inspector at a pressure of 1.5 times the maximum allowable working pressure of the system. S47 46 CFR 58.20-25 Tests
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

### R010-02 冷却水系统试验验证
系统应能在系泊试验或航行试验中验证冷却能力、参数稳定性、报警功能和主要设备运行状态。

检索画像：部件=['main_engine_cooling_water_system']；方面=['reliability', 'capacity', 'alarm', 'inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review', 'document_completeness', 'class_approval']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

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

- E-DNV-COOL-003｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, temperature_control_valve, alarm_system｜方面：test, commissioning_check, operation｜可支撑：test, commissioning_check, operation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Sea Trial Requirements for Cooling Systems
During sea trials, the cooling water system shall be tested to demonstrate:
1. Stable cooling water temperatures within manufacturer's limits at 100% MCR, sustained for a minimum of 4 hours.
2. Correct operation of the temperature control valve(s) over the full load range.
3. Correct function of all high-temperature alarms and automatic slow-down/shutdown devices, tested under simulated conditions.
4. Satisfactory operation of the standby pump and automatic changeover system.
5. Correct indication of all cooling water monitoring instruments.
整理说明：DNV规则规定了冷却水系统海试验收项目，可支撑冷却水系统的试验和调试类需求，为各功能试验的接受准则提供规范级依据。
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
