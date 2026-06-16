# 需求证据包（V2 工程字段版）

## R001 船东代表
我希望主机冷却水系统运行稳定，不能因为冷却不足影响航行安全。泵和冷却器的配置要有冗余，单台设备故障时，主机仍应具备基本运行能力。

### R001-01 系统运行稳定性
主机冷却水系统应确保在各种工况下稳定运行，不因冷却不足影响主机安全及航行安全。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'cooler', 'temperature_control_valve']；方面=['reliability', 'safety', 'capacity', 'temperature', 'pressure', 'flow', 'redundancy', 'control', 'alarm']；可支撑=['system_design', 'equipment_selection', 'parameter_limit', 'calculation', 'test', 'alarm_protection', 'operation']

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-PUMP-RED-002｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P614｜部件：cooling_water_pump｜方面：redundancy, capacity, composition, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
7.7.1 Cooling Water Pumps 7.7.1(a) Standby pump. (2020) There are to be at least two means to supply cooling water or other medium to the engines, and air compressors, coolers, reduction gears, etc, associated with the operation of these engines. The capacity of each means is to be sufficient for continuous operation of the engines at rated power. One of these means is to be independently driven and may consists of a connection from a suitable Part 4 Vessel Systems and Machinery Chapter 6 Piping Systems Section 5 Piping Systems for Internal Combustion Engines 4-6-5 ABS RULES FOR BUILDING AND CLASSING MARINE VESSELS • 2021 610
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
capacity
composition 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-RED-004｜indirect｜supporting
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P197｜部件：cooling_water_pump｜方面：redundancy, capacity, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
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

- E-SYS-CAP-001｜indirect｜supporting
  - 来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜位置：P191｜部件：main_engine_cooling_water_system｜方面：capacity, flow, temperature｜可支撑：parameter_limit, equipment_selection, calculation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
外部冷却水系统设计原则
Data for external preheating system The capacity of the external preheater should be 0.8-1.0 kW/cyl. The flow through the engine should for each cylinder be approx. 1.4 l/min with flow from top and downwards and 10 l/min with flow from bottom and upwards. See also table 1 below. Cyl. No. 5 6 7 8 Quantity of water in eng: HT-system (litre) LT-system (litre) Expansion vol. (litre) 11 13 15 17 Preheating data: Radiation area (m2) Thermal coeff. (kJ/°C) 14.0 16.1 18.2 20.3 Table 1: Showing cooling water data which are depending on the number of cylinders. Design data for the external cooling water system 1613441-5.6
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：main_engine_cooling_water_system 的 capacity
flow
temperature 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R001-02 冷却水泵冗余配置
主机冷却水系统应配置冗余冷却水泵，单台泵故障时系统仍能维持主机基本冷却需求。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'sea_water_pump', 'cooler']；方面=['redundancy', 'reliability', 'control', 'alarm', 'capacity']；可支撑=['system_design', 'equipment_selection', 'redundancy', 'alarm_protection']

- E-CCS-COOL-001｜direct｜primary
  - 来源：S62 CCS 钢质海船入级规范 第4篇第3章 机械｜位置：｜部件：cooling_water_pump, main_engine_cooling_water_system, alarm_system｜方面：capacity, redundancy, alarm, parameter_limit｜可支撑：capacity, redundancy, alarm, parameter_limit｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第4篇 第3章 — 冷却水系统
主推进机械的冷却水系统应设有不少于2台冷却水泵，其中至少1台应为独立电力驱动。各泵应具有在主机额定功率工况下单独满足冷却水流量需求的能力。系统应设置冷却水高温报警，报警值应不超过主机制造商规定的最高允许温度。当冷却水温度超过允许值时，应能自动减速或停机保护。
冷却水系统的设计应能在主机最大连续功率（MCR）条件下，在航行海区最高海水温度（不低于32°C）时保持正常工作，热带航区应不低于35°C。
整理说明：CCS规则对主机冷却水系统泵配置、报警和系统设计提供了中国船级社规范级依据，可支撑国内船厂建造项目的合规性要求。
```

- E-DNV-COOL-002｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：cooling_water_pump, control_system｜方面：redundancy, capacity, alarm, operation, reliability｜可支撑：redundancy, capacity, alarm, operation｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Pump Redundancy
At least two cooling water pumps shall be provided for the main engine cooling circuit. The pumps shall be arranged so that failure of one pump does not prevent the operation of the remaining pump(s). Where one pump is engine-driven, the other shall be electrically driven. Each pump shall be capable of maintaining required cooling water flow at all engine load conditions from idle to MCR. Automatic changeover to the standby pump shall be provided in case of pump failure, with alarm indication.
整理说明：DNV规则对主机冷却水泵冗余配置、独立驱动要求及自动切换功能提供了规范级依据。可支撑冗余泵配置、自动切换逻辑及报警要求。
```

- E-IACS-M3-001｜direct｜primary
  - 来源：S60 IACS Unified Requirements M3.1 Cooling Systems｜位置：｜部件：cooling_water_pump｜方面：capacity, redundancy, operation, reliability｜可支撑：capacity, redundancy, operation｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements M3.1 — Cooling Systems
At least two independent cooling water pumps shall be fitted for the cooling of main propulsion machinery. Where engine-driven pumps are fitted, at least one independently driven pump shall be provided. Each pump shall have sufficient capacity to supply the full cooling water flow required by the main engine under maximum continuous rating (MCR) conditions. The pumps shall be capable of being started independently and the changeover shall be achievable without interrupting operation.
整理说明：IACS UR M3.1 为主机冷却水泵数量、独立驱动要求及泵容量提供了规范级依据。可支撑冷却水泵冗余配置、容量设计及换泵操作类需求。
```

- E-PUMP-RED-024｜indirect｜supporting
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P198｜部件：cooling_water_pump｜方面：redundancy, capacity, flow, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
11.1.8 Oil coolers of the main turbine sets shall be served by circulating pumps of main condensers. Where a separate cooling water pump for oil coolers is provided, a stand-by pump with a capacity not less than 2/3 of the cooling water demand for the cooler at the rated power of the turbine set shall be provided. For cooling of steam turbines’ condensers – see Chapter 15.
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
capacity
flow 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R001-03 冷却器冗余配置
主机冷却水系统应配置冗余冷却器，单台冷却器故障时系统仍能维持主机基本冷却需求。

检索画像：部件=['main_engine_cooling_water_system', 'cooler', 'cooling_water_pump', 'sea_water_pump']；方面=['redundancy', 'reliability', 'control', 'alarm', 'capacity']；可支撑=['system_design', 'equipment_selection', 'redundancy', 'alarm_protection']

- E-DNV-COOL-002｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：cooling_water_pump, control_system｜方面：redundancy, capacity, alarm, operation, reliability｜可支撑：redundancy, capacity, alarm, operation｜强度：direct｜适用性：general/class_rule
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

- E-PUMP-RED-002｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P614｜部件：cooling_water_pump｜方面：redundancy, capacity, composition, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
7.7.1 Cooling Water Pumps 7.7.1(a) Standby pump. (2020) There are to be at least two means to supply cooling water or other medium to the engines, and air compressors, coolers, reduction gears, etc, associated with the operation of these engines. The capacity of each means is to be sufficient for continuous operation of the engines at rated power. One of these means is to be independently driven and may consists of a connection from a suitable Part 4 Vessel Systems and Machinery Chapter 6 Piping Systems Section 5 Piping Systems for Internal Combustion Engines 4-6-5 ABS RULES FOR BUILDING AND CLASSING MARINE VESSELS • 2021 610
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
capacity
composition 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-RED-004｜indirect｜supporting
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P197｜部件：cooling_water_pump｜方面：redundancy, capacity, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
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

### R001-04 单设备故障下主机运行能力
在单台冷却水泵或冷却器故障时，主机应具备基本运行能力，确保航行安全。

检索画像：部件=['cooling_water_pump', 'cooler', 'main_engine_cooling_water_system', 'temperature_control_valve', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['reliability', 'safety', 'monitoring', 'control', 'alarm', 'maintenance', 'temperature', 'pressure', 'flow', 'capacity']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-PUMP-RED-026｜indirect｜primary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P209｜部件：cooling_water_pump｜方面：redundancy, capacity, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
15.2.4 Where provision is made for cooling the main condenser by simultaneous operation of two pumps, each having a capacity not less than 0.5 of the rated demand for water, the stand -by cooling water pump is not required.
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

- E-PUMP-RED-024｜indirect｜primary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P198｜部件：cooling_water_pump｜方面：redundancy, capacity, flow, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
11.1.8 Oil coolers of the main turbine sets shall be served by circulating pumps of main condensers. Where a separate cooling water pump for oil coolers is provided, a stand-by pump with a capacity not less than 2/3 of the cooling water demand for the cooler at the rated power of the turbine set shall be provided. For cooling of steam turbines’ condensers – see Chapter 15.
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
capacity
flow 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-RED-021｜indirect｜primary
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P695｜部件：cooling_water_pump｜方面：redundancy, flow, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
3.5.3(c) Cooling water supply. Cooling water supply to the refrigerating plant (where required) is to be provided from at least two circulating pumps one of which being used as a stand-by. The stand-by pump may be a pump used for other services so long as its use for cooling would not interfere with any other essential service of the vessel. Cooling water is to be taken from not less than two sea connections, preferably one port and one starboard.
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 redundancy
flow 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-RED-025｜indirect｜primary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P209｜部件：cooling_water_pump｜方面：redundancy, capacity, reliability｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水泵冗余配置
15.2.5 Where the auxiliary condenser is common for all auxiliary turbines, it shall be served by two independent cooling water pumps – one main and one stand-by pump. Any pump of sufficient capacity may be used as a stand-by pump.
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
