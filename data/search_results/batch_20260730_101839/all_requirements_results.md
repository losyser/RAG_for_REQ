# 需求证据包（V2 工程字段版）

## R001 船东代表
主机冷却水系统应具备较高运行可靠性，不能因冷却能力不足、冷却水循环中断或温度失控影响推进装置安全运行。系统应能在连续运行、热带海区高温环境和主机负荷变化时保持稳定冷却能力。

### R001-01 系统运行可靠性
主机冷却水系统应设计为高可靠性，确保在连续运行、热带高温及负荷变化工况下不因冷却能力不足、循环中断或温度失控影响主机安全。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'cooler', 'temperature_control_valve']；方面=['reliability', 'capacity', 'temperature', 'safety', 'pressure', 'flow', 'redundancy', 'control', 'alarm']；可支撑=['system_design', 'equipment_selection', 'parameter_limit', 'calculation', 'test', 'alarm_protection', 'operation']

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

### R001-02 热带海区高温环境适应性
系统应能在热带海区高温环境下保持稳定冷却能力。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'cooler', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['reliability', 'capacity', 'temperature', 'monitoring', 'control', 'alarm', 'maintenance', 'pressure', 'flow']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-COOLER-PRESS-010｜indirect｜primary
  - 来源：S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine｜位置：P111｜部件：cooler｜方面：pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：参考条件为热带条件；空气温度 45 °C；冷却水温度（低温级中冷器前）38 °C；总大气压力 1000 mbar；相对湿度 60%。适用条件：L/V49/60 IMO Tier II – 电力推进/EPROX-AC，1300 kW/cyl.，600 rpm – 电力推进/EPROX-AC，参考条件：热带。

主机冷却型式与设计条件：发动机负荷 100% 时，参考条件为热带，IMO 2008 和 IMO 2028。适用条件：L/V49/60 IMO Tier II – 电力推进/EPROX-AC，1300 kW/cyl.，600 rpm – 电力推进/EPROX-AC，参考条件：热带。

主机冷却型式与设计条件：发动机负荷 85% 时，参考条件为热带，IMO 2008 和 IMO 2028。适用条件：L/V49/60 IMO Tier II – 电力推进/EPROX-AC，1300 kW/cyl.，600 rpm – 电力推进/EPROX-AC，参考条件：热带。

可支撑：cooler 的 pressure temperature 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-LOAD-003｜indirect｜primary
  - 来源：S39 MAN L21/31 Project Guide｜位置：P67｜部件：cooler｜方面：load_reduction, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：环境条件无需降额，前提是不超过以下参考条件（热带条件）；若超过以下数值，需进行特殊计算：涡轮增压器前空气温度 Tx ≤ 318 K（45 °C）/ 333 K（60 °C）；环境压力 ≥ 100 kPa（1 bar）/ 90 kPa；冷却水温度（低温级中冷器进口）≤ 311 K（38 °C）/ 316 K（43 °C）；压缩机前进气压力 ≥ -20 mbar / -40 mbar（1）；涡轮增压器后排气背压 ≤ 30 mbar / 60 mbar（1）。（1）表压。适用条件：Table 3: Available outputs / related reference conditions；POperating: Available output under local conditions and dependent on application；Dependent on local conditions or special application demands, a further load reduction of PApplication, ISO might be needed；De-rating 1: No de-rating due to ambient conditions is needed as long as following conditions are not exceeded；No de-rating up to stated reference conditions (Tropic)；Special calculation needed if following values are exceeded。

可支撑：cooler 的 load_reduction pressure temperature 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-LOAD-005｜indirect｜primary
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P51｜部件：cooler｜方面：load_reduction, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：Derating 定义，P Operating – Liquid fuel mode 相关降额因子；可用功率（输出）取决于当地条件和应用。取决于当地条件或特殊应用要求，可能需要进一步降低 P Application, ISO。  
1. No derating：无需降额，前提是满足所列条件；在规定的参考条件（热带）下无需降额，见下文：  
空气温度（涡轮增压器前）T ≤ 318 K (45 °C)；环境压力 ≥ 100 kPa (1 bar)；冷却水温度（中冷器 LT 级进口）≤ 311 K (38 °C)；压气机前进气压力 ≥ –2 kPa；涡轮增压器后排气背压 ≤ 5 kPa；相对湿度 Φ ≤ 60 %；低于/高于大气压力。适用条件：Table 15: Derating – Limits of ambient conditions。  
2. Derating：联系 MAN Energy Solutions。

可支撑：cooler 的 load_reduction、pressure、temperature 参数应依据来源文件、厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。  
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-LOAD-001｜indirect｜primary
  - 来源：S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine｜位置：P41｜部件：cooler｜方面：load_reduction, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：冷却水温度进气口充气冷却器（LT级）≤ 311 K（38°C）；适用条件：无降额，满足所列条件，环境温度在涡轮增压器前T ≤ 318 K（45°C），环境压力≥ 100 kPa（1 bar），进气压力在压缩机前≥ –2 kPa，排气背压在涡轮增压器后≤ 5 kPa，相对湿度Φ ≤ 60%。

可支撑：cooler 的 load_reduction pressure temperature 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-SYS-COMP-021｜indirect｜primary
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P138｜部件：main_engine_cooling_water_system｜方面：composition, pressure, flow｜可支撑：parameter_limit, equipment_selection, calculation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
淡水侧系统组成：No. of cylinders, config. 6L/7L/8L/9L/10L；LT cooling water air cooler inlet = 38 °C (setpoint 32 °C)；Lube oil engine inlet = 65 °C；Nozzle cooling water engine inlet = 60 °C。适用条件：淡水侧系统组成。
Charge air cooler outlet HP：Air flow rate = 45,376 /h（6L）、52,939 /h（7L）、61,054 /h（8L）、68,054 /h（9L）、76,316 /h（10L）；Mass flow = 49.7 t/h（6L）、57.9 t/h（7L）、66.8 t/h（8L）、74.5 t/h（9L）、83.5 t/h（10L）；Charge air pressure (absolute) = 6.90 bar abs（6L）、6.90 bar abs（7L）、6.75 bar abs（8L）、6.90 bar abs（9L）、6.75 bar abs（10L）；Air required to dissipate heat radiation (engine) = 39,969 /h（6L）、46,630 /h（7L）、53,291 /h（8L）、59,953 /h（9L）、66,614 /h（10L）。适用条件：Charge air cooler outlet HP。
Exhaust gas data：Volume flow (temperature turbocharger outlet) = 90,189 /h（6L）、105,223 /h（7L）、120,407 /h（8L）、135,284 /h（9L）、150,511 /h（10L）；Mass flow = 51.2 t/h（6L）、59.7 t/h（7L）、68.9 t/h（8L）、76.8 t/h（9L）、86.1 t/h（10L）；Exhaust gas temperature at LP turbine outlet = 340 °C（6L）、340 °C（7L）、336 °C（8L）、340 °C（9L）、336 °C（10L）；Heat content (190 °C) = 2,306 kW（6L）、2,690 kW（7L）、3,002 kW（8L）、3,458 kW（9L）、3,753 kW（10L）；Permissible exhaust gas back pressure after turbocharger ≤ 50 mbar。适用条件：Exhaust gas data。
可支撑：main_engine_cooling_water_system 的 composition、pressure、flow 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R001-03 负荷变化工况温度控制
系统应能在主机负荷变化时保持冷却水温度稳定，避免温度失控。

检索画像：部件=['control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['reliability', 'temperature', 'control', 'monitoring', 'pressure', 'flow', 'alarm', 'redundancy']；可支撑=['control', 'monitoring', 'operation', 'alarm_protection', 'parameter_limit']

- E-CTRL-COOL-001｜direct｜primary
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, temperature_control_valve, main_engine_cooling_water_system, alarm_system｜方面：operation, alarm, monitoring, redundancy, test, reliability｜可支撑：operation, alarm, monitoring, redundancy, test｜强度：direct｜适用性：general/class_rule
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

- E-IACS-M35-001｜indirect｜supporting
  - 来源：IACS Unified Requirements M35 Rev.8 Alarms and Safeguards for Main IC Engines in UMS｜位置：UR M35 Rev.8｜部件：alarm_system, main_engine_cooling_water_system, expansion_tank｜方面：alarm_protection, monitoring, safety｜可支撑：alarm_protection, parameter_limit, equipment_selection｜强度：direct｜适用性：yes/class_rule
```text
IACS UR M35 Rev.8 — Mandatory Alarms and Safeguards for Main IC Engines in Unattended Machinery Spaces (UMS):
- High cooling water temperature: mandatory alarm AND automatic slowdown or shutdown trigger
- Low cooling water pressure (HT and LT circuits): mandatory alarm
- Deaerating/expansion tank low level: mandatory alarm
- All parameters that could cause engine damage if unattended must have alarm + automatic protective response
Note: Numerical setpoints for alarms and slowdown/shutdown are engine manufacturer-specific and must be approved by the class society. The UR mandates the alarm exists; the threshold values are defined in the engine manufacturer's project guide and control system.
```

- E-TCV-SHUT-001｜indirect｜supporting
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P91｜部件：temperature_control_valve｜方面：shutdown, temperature, control｜可支撑：parameter_limit, alarm_protection, operation, monitoring｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
温度控制阀配置
• Incorporate deaeration circuit and air vents to eliminate air traps and locks. • A load balancing thermostatic valve must be used to direct coolant through a secondary cooling source to limit jacket water inlet temperature. • Coolant must continually flow through the exhaust heat recovery device when the engine is operating to avoid thermal shock on hot muffler surfaces. This may be accomplished using a low water flow shutdown device. • After engine shutdown, the coolant must continue to flow through the engine until the coolant temperature falls below 94°C (194°F) to avoid steam pockets forming inside the engine. • If the engine thermostats are removed, an external warm-up thermostat is required. • To keep external head within allowable limits for the engine- mounted pump, locate heat recovery mufflers and heat exchangers as near the engine as possible.
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

## R002 主机厂家
主机入口和出口冷却水温度、压力、流量应满足主机厂家技术文件要求。高温冷却水回路和低温冷却水回路的设计参数应与主机技术数据、泵曲线、冷却器选型和热平衡计算保持一致。

### R002-01 主机冷却水进出口参数
主机入口和出口冷却水的温度、压力、流量应满足主机厂家技术文件规定的限值。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'temperature_control_valve']；方面=['temperature', 'pressure', 'flow', 'document_completeness', 'capacity', 'monitoring']；可支撑=['parameter_limit', 'calculation', 'test', 'monitoring', 'equipment_selection']

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
  - 来源：S65 IACS Unified Requirements E10 Machinery Control Systems｜位置：｜部件：control_system, temperature_control_valve, main_engine_cooling_water_system, alarm_system｜方面：operation, alarm, monitoring, redundancy, test, reliability｜可支撑：operation, alarm, monitoring, redundancy, test｜强度：direct｜适用性：general/class_rule
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

- E-SYS-COMP-004｜direct｜primary
  - 来源：S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine｜位置：P135｜部件：main_engine_cooling_water_system｜方面：composition, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
淡水侧系统组成：LT冷却水压力（额定转速下增压空气冷却器进口）≤ 2 bar；PT4145压力传感器测量范围 2 bar 至 8 bar。适用条件：额定转速。

增压空气冷却器（LT级，额定流量）压力损失：6L机型 0.7 bar；7L机型 0.9 bar；8L机型 1.0 bar；9L机型 1.2 bar；10L机型 1.4 bar；12V机型 2.0 bar；14V机型 2.6 bar。适用条件：额定流量。

附设LT冷却水泵（额定转速下）压力升高：6L机型 3.6 bar；7L机型 3.5 bar；8L机型 3.3 bar；9L机型 3.9 bar；10L机型 3.8 bar；12V机型 4.3 bar；14V机型 4.9 bar。适用条件：额定转速。

调节温度：根据功率定义。在较高温度/较低压力下需要降低功率。

可支撑：main_engine_cooling_water_system 的 composition control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-TSENS-PRESS-005｜direct｜primary
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P254｜部件：temperature_sensor｜方面：pressure, temperature, redundancy, reliability｜可支撑：parameter_limit, equipment_selection, calculation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
Internal Cooling Water System 1 (preheating for engines starting on HFO, engines in stand-by position, and engines operating on MDO): temperature ≥ 60°C at the top cover; temperature approximately 25 to 45°C at outlet of the cylinders. 适用条件：preheating is arranged for automatic operation, disconnected when engine is running, connected when engine is in stand-by position.

可支撑：temperature_sensor 的 pressure temperature redundancy 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R002-02 高低温回路设计参数一致性
高温冷却水回路和低温冷却水回路的设计参数（温度、压力、流量）应与主机技术数据、泵曲线、冷却器选型和热平衡计算结果保持一致。

检索画像：部件=['main_engine_cooling_water_system', 'ht_cooling_water_loop', 'lt_cooling_water_loop', 'cooler']；方面=['capacity', 'temperature', 'pressure', 'flow', 'calculation', 'arrangement', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

- E-SYS-COMP-004｜direct｜primary
  - 来源：S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine｜位置：P135｜部件：main_engine_cooling_water_system｜方面：composition, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
淡水侧系统组成：LT冷却水压力（额定转速下增压空气冷却器进口）≤ 2 bar；PT4145压力传感器测量范围 2 bar 至 8 bar。适用条件：额定转速。

增压空气冷却器（LT级，额定流量）压力损失：6L机型 0.7 bar；7L机型 0.9 bar；8L机型 1.0 bar；9L机型 1.2 bar；10L机型 1.4 bar；12V机型 2.0 bar；14V机型 2.6 bar。适用条件：额定流量。

附设LT冷却水泵（额定转速下）压力升高：6L机型 3.6 bar；7L机型 3.5 bar；8L机型 3.3 bar；9L机型 3.9 bar；10L机型 3.8 bar；12V机型 4.3 bar；14V机型 4.9 bar。适用条件：额定转速。

调节温度：根据功率定义。在较高温度/较低压力下需要降低功率。

可支撑：main_engine_cooling_water_system 的 composition control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-LT-COMP-005｜direct｜primary
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P36｜部件：lt_cooling_water_loop｜方面：composition, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
L16/24S;L16/24：Set point HT cooling water engine outlet 79°C nominal (Range of mech. thermostatic element 77-85°C)；Set point LT cooling water engine outlet 35°C nominal (Range of mech. thermostatic element 29-41°C)；Set point lubrication oil inlet engine 66°C nominal (Range of mech. thermostatic element 63-72°C)。适用条件：Reference condition: Tropic Air temperature, 1000 rpm, Air pressure, Relative humidity, Temperature basis。

可支撑：lt_cooling_water_loop 的 composition control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-LT-COMP-006｜direct｜primary
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P38｜部件：lt_cooling_water_loop｜方面：composition, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
L16/24S;L16/24：HT冷却水发动机出口温度设定点 79°C 标称（机械恒温元件范围 77-85°C）；LT冷却水发动机出口温度设定点 35°C 标称（机械恒温元件范围 29-41°C）；润滑油进口温度设定点 66°C 标称（机械恒温元件范围 63-72°C）。适用条件：参考工况为热带空气温度，发动机进水温度来自系统，空气压力、相对湿度按温度基准；HT冷却水先流经HT级增压空气冷却器，再流经水套和气缸盖，发动机出口水温由机械恒温器调节；LT冷却水先流经LT级增压空气冷却器，再流经滑油冷却器，发动机出口水温由机械恒温器调节。

可支撑：lt_cooling_water_loop 的 composition control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-HT-COMP-082｜direct｜primary
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P151｜部件：ht_cooling_water_loop｜方面：composition, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
高温冷却水系统组成：气缸数/配置 6L/7L/8L/9L/10L；扫气压力（绝对） bar abs 5.39/5.41/5.38/5.42/5.38。适用条件：对应气缸数配置。
高温冷却水系统组成：散热所需空气量（发动机） = 10 °C /h 38,847/45,268/51,689/58,110/64,531。适用条件：对应气缸数配置。
高温冷却水系统组成：排气数据体积流量（涡轮增压器出口温度） /h 74,600/87,290/100,020/112,260/124,840。适用条件：对应气缸数配置。
高温冷却水系统组成：排气数据质量流量 t/h 39.8/46.5/53.2/59.8/66.5。适用条件：对应气缸数配置。
高温冷却水系统组成：低压涡轮出口排气温度 °C 380/381/382/381/382。适用条件：对应气缸数配置。
高温冷却水系统组成：热含量（180 °C） kW 2,450/2,872/3,309/3,696/4,134。适用条件：对应气缸数配置。
高温冷却水系统组成：涡轮增压器后允许排气背压 mbar ≤ 50。适用条件：通用。
高温冷却水系统组成：HT冷却水流经：1. HP HT级空冷器 2. 缸套冷却 3. LP HT级空冷器；调节温度。适用条件：相关于厂用系统。

可支撑：ht_cooling_water_loop 的 composition control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-PRESS-060｜indirect｜secondary
  - 来源：S37 MAN L27/38 Propulsion Project Guide｜位置：P158｜部件：cooler｜方面：pressure, temperature, calculation｜可支撑：parameter_limit, equipment_selection, calculation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：空气温度在涡轮增压器前 Tx ≤ 318 K (45 °C) / 333 K (60 °C)；环境压力 ≥ 100 kPa (1 bar) / 90 kPa；冷却水温度在进气冷却器进口（低温级）≤ 311 K (38 °C) / 316 K (43 °C)；压缩机前进气压力 ≥ -20 mbar / -40 mbar；涡轮增压器后排气背压 ≤ 30 mbar / 60 mbar。适用条件：Tier II，No de-rating up to stated reference conditions (Tropic)，Special calculation needed if following values are exceeded。

可支撑：cooler 的 pressure temperature calculation 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R003 系统设计方
主机冷却水系统应明确区分高温冷却水回路、低温冷却水回路、海水侧或中央冷却系统边界。各回路的设备连接、流向、接口和服务对象应在系统原理图中表达清楚。

### R003-01 冷却水回路划分与边界定义
主机冷却水系统应明确划分高温冷却水回路、低温冷却水回路及海水侧或中央冷却系统边界，并在系统原理图中清晰表达各回路的设备连接、流向、接口和服务对象。

检索画像：部件=['main_engine_cooling_water_system', 'central_cooling_system', 'sea_water_cooling_system', 'ht_cooling_water_loop', 'lt_cooling_water_loop']；方面=['temperature', 'drawing_review', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。

## R004 船厂建造方
冷却水系统管路布置应清楚、紧凑并便于施工。管路走向、阀门位置、支架布置、放水点、排气点和设备接口应便于现场焊接、安装、冲洗、压力试验和后续检查。

### R004-01 管路布置施工便利性
冷却水系统管路布置应清晰紧凑，便于现场焊接、安装、冲洗、压力试验和后续检查。

检索画像：部件=['main_engine_cooling_water_system', 'pipe', 'flushing_connection', 'valve', 'support', 'equipment_interface', 'pressure_test_connection']；方面=['pressure', 'installation', 'arrangement', 'flushing', 'pressure_test', 'inspection', 'accessibility']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

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

- E-SUPP-WELD-001｜direct｜primary
  - 来源：S74 IACS Unified Requirements W7 W28 Welding Marine Piping｜位置：｜部件：pipe, main_engine_cooling_water_system, cooler, cooling_water_pump｜方面：test, inspection, installation, class_review｜可支撑：test, inspection, installation, class_review｜强度：direct｜适用性：general/class_rule
```text
IACS Unified Requirements W7 / W28 — Welding Quality Requirements for Marine Cooling Water Piping Systems

Requirements for welding of cooling water pipelines on essential machinery systems:
1. Welder qualification: All butt welds in cooling water piping of essential machinery systems shall be made by welders holding valid certificates to IACS UR W7 or equivalent (ISO 9606-1, ASME IX). Certificates shall cover the applicable material group and joint type.
2. Welding procedure qualification (WPS/PQR): per IACS UR W28 or ISO 15614-1 before production welding commences; WPS records shall be retained for class review.
3. Non-destructive examination (NDE) of completed welds:
   - DN > 100 mm and design pressure > 1.0 MPa: minimum 10% random RT or UT of butt welds
   - Critical locations (expansion loops, penetrations, tee branches): 100% visual + selective PT/MT
   - All completed welds: 100% visual examination per class surveyor's instructions
4. Hydrostatic test: all piping after welding and before insulation, at 1.5× design pressure, hold ≥ 30 min (per IACS UR M72)
5. Weld repairs: defective welds found by NDE shall be repaired and re-examined; results recorded in the welding inspection report submitted to class surveyor.
整理说明：IACS UR W7/W28 对船用冷却水管路焊工资质（ISO 9606-1/ASME IX）、焊接工艺评定、无损检测（DN>100mm高压管路≥10% RT/UT）和水压试验要求提供了规范级依据。
```

- E-SUPP-WELD-002｜direct｜primary
  - 来源：S75 CCS 钢质海船入级规范 第5篇管路焊接与NDT｜位置：｜部件：pipe, main_engine_cooling_water_system｜方面：test, inspection, installation, class_review, document_completeness｜可支撑：test, inspection, installation, class_review, document_completeness｜强度：direct｜适用性：general/class_rule
```text
中国船级社（CCS）钢质海船入级规范 第5篇 — 管路系统焊接与检验要求

冷却水管路系统建造质量验收要求：
1. 焊工资质：冷却水管路焊工应持有CCS或认可机构签发的有效焊工证书，证书覆盖范围应与所焊接材料类别、接头型式和位置一致。
2. 焊接工艺评定（WPS/WPQR）：生产焊接前按CCS要求完成焊接工艺评定，评定文件经CCS审批，保存备查。
3. 无损检测（NDT）要求：
   - 主机冷却水主管路（公称直径≥80mm，设计压力≥1.0 MPa）：随机抽检RT或UT，比例≥10%
   - 关键部位焊缝（弯头、三通、管道贯穿处附近）：增加MT/PT局部检测
   - 全部焊缝：100%外观检验，不合格焊缝须返修复检
4. 管路水压试验：安装完成后，按设计压力1.5倍进行水压试验，保压时间≥30分钟，不得有渗漏或变形。
5. 记录归档：无损检测报告、水压试验记录、返修记录均须存档并提交CCS验船师审核。
整理说明：CCS规范对冷却水管路焊工资质、工艺评定、无损检测要求（≥10% RT/UT）和水压试验的系统性规定，可支撑管路焊接质量、检验记录和安装验收类需求。
```

- E-SUPP-MAINT-001｜direct｜primary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

- E-PIPE-PTEST-001｜direct｜primary
  - 来源：S48 46 CFR 197.462 Pressure vessels and pressure piping｜位置：197.462(d)(4)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-V/part-197/subpart-B/section-197.462｜部件：pipe｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
压力试验人员和设备防护要求
Pressure tests shall be conducted only after suitable precautions are taken to protect personnel and equipment. S49 SOLAS 2024 Chapter II-1 Regulation 26
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

### R004-02 阀门与支架可及性
阀门位置和支架布置应便于操作、维护和检查。

检索画像：部件=['valve', 'support', 'cooler', 'filter', 'cooling_water_pump', 'temperature_control_valve', 'expansion_tank']；方面=['arrangement', 'accessibility', 'maintenance', 'inspection', 'cleaning', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

- E-SUPP-MAINT-001｜direct｜primary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

- E-COOLER-MAINT-004｜indirect｜supporting
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P86｜部件：cooler, equipment_interface, cooling_water_pump｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求：必须考虑有足够的空间用于拉出增压空气冷却器元件、滑油冷却器、滑油滤器滤芯、润滑油泵和水泵。适用条件：L16/24, 2009.05.04 - Tier II。

可支撑：冷却水系统布置应考虑来源文件提出的安装操作或维护可达性原则。具体施工空间、支架、接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。2. 不能替代船厂施工规范、管系布置标准或安装验收程序。3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-COOLER-MAINT-003｜indirect｜supporting
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P63｜部件：cooler, equipment_interface｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
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

- E-PUMP-MAINT-001｜indirect｜supporting
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P116｜部件：cooling_water_pump｜方面：maintenance, cleaning, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
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

### R004-03 放水排气点设置
管路应设置放水点和排气点，便于系统冲洗和压力试验。

检索画像：部件=['pipe', 'drain_point', 'vent_point', 'flushing_connection', 'valve', 'support', 'equipment_interface', 'pressure_test_connection']；方面=['pressure', 'flushing', 'pressure_test', 'installation', 'arrangement', 'accessibility', 'inspection']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-VENT-INSP-001｜indirect｜primary
  - 来源：S51 NASA NTRS 19800002357 Piping Specification｜位置：B-45；source_url=https://ntrs.nasa.gov/api/citations/19800002357/downloads/19800002357.pdf?attachment=true｜部件：vent_point｜方面：inspection, installation, arrangement, configuration｜可支撑：installation, test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
水管路最低点放水和最高点排气要求
Install manual drain valves at every low point of water piping systems and a manual air vent at every high point. S52 BN-G-Y015 Piping Systems Inspection and Testing
整理说明：该证据针对 vent_point 的 inspection / installation / arrangement 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-DRAIN-INSP-001｜indirect｜primary
  - 来源：S51 NASA NTRS 19800002357 Piping Specification｜位置：B-45；source_url=https://ntrs.nasa.gov/api/citations/19800002357/downloads/19800002357.pdf?attachment=true｜部件：drain_point｜方面：inspection, installation, arrangement, configuration｜可支撑：installation, test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
水管路最低点放水和最高点排气要求
Install manual drain valves at every low point of water piping systems and a manual air vent at every high point. S52 BN-G-Y015 Piping Systems Inspection and Testing
整理说明：该证据针对 drain_point 的 inspection / installation / arrangement 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

### R004-04 设备接口可操作性
设备接口应便于现场连接和后续检查。

检索画像：部件=['equipment_interface', 'pipe', 'valve', 'support', 'flushing_connection', 'pressure_test_connection']；方面=['inspection', 'installation', 'arrangement', 'accessibility', 'flushing', 'pressure_test']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

- E-SUPP-MAINT-001｜direct｜primary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

- E-IFACE-MAINT-004｜indirect｜supporting
  - 来源：S39 MAN L21/31 Project Guide｜位置：P91｜部件：equipment_interface｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求：必须考虑有足够的空间用于拉出扫气空气冷却器元件、滑油冷却器、滑油滤器滤芯、滑油泵和水泵。适用条件：L21/31S;L21/31，2014.06.03，IMO Tier II Project Guide MAN Energy Solutions Project Guide MAN L16/24。

可支撑：冷却水系统布置应考虑来源文件提出的安装操作或维护可达性原则。具体施工空间、支架、接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。2. 不能替代船厂施工规范、管系布置标准或安装验收程序。3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-IFACE-MAINT-001｜indirect｜supporting
  - 来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜位置：P92｜部件：equipment_interface｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求
Dismantling space Is must be considered that there is sufficient space for pulling the charge air cooler element, air filter on the turbocharger, lubricating oil cooler, lubricating oil filter cartridge and bracing bolt. Figure 1: Overhaul areas for charge air cooler element, turbocharger filter element, lubricating oil cooler, lubricating oil filter cartridge and bracing bolt 2020-05-11 - en B 10 01 1 MAN Energy Solutions
整理说明：该证据针对 equipment_interface 的 maintenance / accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-COOLER-MAINT-003｜indirect｜supporting
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P63｜部件：cooler, equipment_interface｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
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

- E-COOLER-MAINT-004｜indirect｜supporting
  - 来源：S38 MAN L16/24 GenSet Project Guide｜位置：P86｜部件：cooler, equipment_interface, cooling_water_pump｜方面：maintenance, accessibility, configuration｜可支撑：installation, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统维护空间要求：必须考虑有足够的空间用于拉出增压空气冷却器元件、滑油冷却器、滑油滤器滤芯、润滑油泵和水泵。适用条件：L16/24, 2009.05.04 - Tier II。

可支撑：冷却水系统布置应考虑来源文件提出的安装操作或维护可达性原则。具体施工空间、支架、接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。2. 不能替代船厂施工规范、管系布置标准或安装验收程序。3. 不能直接支撑冷却水温度、压力和流量参数限值。
```
