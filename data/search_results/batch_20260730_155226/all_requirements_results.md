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

## R023 船级社验船师
冷却水系统应满足适用船级社规则对备用冷却水供应、泵组配置、重要设备冷却、报警监测和试验验证的要求。涉及主机安全运行的关键设备和保护功能应具备可审查的设计依据。

### R023-01 备用冷却水供应与泵组配置
冷却水系统应配置备用冷却水泵，确保单泵故障时仍能向主机提供冷却水。

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

### R023-02 重要设备冷却报警监测
冷却水系统应对主机及关键设备冷却参数（如温度、压力、流量）进行监测，并在异常时发出报警。

检索画像：部件=['main_engine_cooling_water_system', 'control_system', 'alarm_system', 'temperature_sensor', 'pressure_sensor', 'flow_sensor', 'level_sensor']；方面=['temperature', 'pressure', 'flow', 'monitoring', 'alarm', 'shutdown', 'load_reduction']；可支撑=['alarm_protection', 'monitoring', 'operation', 'test', 'parameter_limit']

- E-ISO8861-002｜direct｜primary
  - 来源：S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements｜位置：｜部件：alarm_system, expansion_tank, temperature_sensor, pressure_sensor, level_sensor, main_engine_cooling_water_system｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/international_standard
```text
ISO 8861:1998 Shipbuilding and Marine Structures — Cooling System Monitoring Requirements
Section 8 — Monitoring and Alarm:
The following parameters shall be monitored and alarmed for main engine cooling water systems:
a) High temperature of HT cooling water at engine outlet: alarm set-point to be within manufacturer's limits (typically 85–95°C for large 4-stroke engines);
b) Low pressure of cooling water at engine inlet: alarm set-point as specified by manufacturer;
c) Low level in expansion tank: alarm when level falls below minimum operating level;
d) High temperature of LT cooling water: alarm set-point as per central cooler design.
All alarms shall be indicated in the engine control room and navigating bridge.
整理说明：ISO 8861:1998 规定了主机冷却水系统的监测参数、报警设定和报警位置，为冷却水监测、报警配置和控制系统设计提供了国际标准依据。
```

- E-IACS-M35-001｜direct｜primary
  - 来源：IACS Unified Requirements M35 Rev.8 Alarms and Safeguards for Main IC Engines in UMS｜位置：UR M35 Rev.8｜部件：alarm_system, main_engine_cooling_water_system, expansion_tank｜方面：alarm_protection, monitoring, safety｜可支撑：alarm_protection, parameter_limit, equipment_selection｜强度：direct｜适用性：yes/class_rule
```text
IACS UR M35 Rev.8 — Mandatory Alarms and Safeguards for Main IC Engines in Unattended Machinery Spaces (UMS):
- High cooling water temperature: mandatory alarm AND automatic slowdown or shutdown trigger
- Low cooling water pressure (HT and LT circuits): mandatory alarm
- Deaerating/expansion tank low level: mandatory alarm
- All parameters that could cause engine damage if unattended must have alarm + automatic protective response
Note: Numerical setpoints for alarms and slowdown/shutdown are engine manufacturer-specific and must be approved by the class society. The UR mandates the alarm exists; the threshold values are defined in the engine manufacturer's project guide and control system.
```

- E-ALARM-ALARM-010｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P947｜部件：alarm_system｜方面：alarm, pressure, temperature, configuration｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水温度与压力参数
Systems Monitored Parameters A D Auto slow down Auto Start Auto shut down Notes: [ A = Alarm. D = Display. x = apply. ] Turbocharger C1 Lube oil inlet, pressure - x Unless provided with a self- contained lubricating oil system integrated with the turbocharger C2 Lube oil outlet (each bearing), temp. - high x Where outlet temperature from each bearing cannot be monitored due to the engine/turbocharger design, alternative arrangements may be accepted. Continuous monitoring of inlet pressure and inlet temperature in combination with specific intervals for bearing inspection in accordance with the turbocharger manufacturer’s instructions may be accepted as an alternative. C3 Speed x x Alarm Activation for High Speed only required for turbochargers of categories B and C Piston cooling D1 Coolant inlet, pressure - x x x The slow down is not required if the coolant is oil taken from the
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

- E-ALARM-ALARM-009｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P774｜部件：alarm_system｜方面：alarm, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, alarm_protection｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水温度与压力参数
until such a time that the lesser ambient temperature may be achieved. iv) Audible and visual alarms are provided, at a continually-manned control station, to indicate any malfunction of the cooling systems. 1.17.2(b) Rating of Cables. In accepting a lesser ambient temperature than 45°C, it is to be ensured that electrical cables for their entire length are adequately rated for the maximum ambient temperature to which they are exposed along their length. 1.17.2(c) Ambient Temperature Control Equipment. The equipment used for cooling and maintaining the lesser ambient temperature is to be classified as a secondary essential service, in accordance with 4-8-1/7.3, and the capability of cooling is to be witnessed by the Surveyor at sea trial.
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

- E-ALARM-ALARM-002｜indirect｜supporting
  - 来源：S06 Scania DI16 船用发动机车主手册（中文）｜位置：P21｜部件：alarm_system｜方面：alarm, temperature, control｜可支撑：parameter_limit, alarm_protection, operation, monitoring｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液温度报警重置条件
冷却液温度， EMS/S6 控制系统拥有下述警报级别： 对于较低级别，基本温度值为 95°C，对于较高级别，基本温度值为 105°C。 出现警报后，应将认可值记录 2 秒以上，以重置警报。
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

### R023-03 系统试验验证与设计依据
冷却水系统应提供可审查的设计依据，并通过试验验证其满足船级社规则要求。

检索画像：部件=['main_engine_cooling_water_system']；方面=['class_approval', 'inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review', 'document_completeness']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

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

- E-DNV-COOL-003｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, temperature_control_valve, alarm_system｜方面：test, commissioning_check, operation, reliability｜可支撑：test, commissioning_check, operation｜强度：direct｜适用性：general/class_rule
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

- E-SYS-PTEST-001｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P176｜部件：main_engine_cooling_water_system｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
冷却水温度与压力参数
13.1.3 Pressure Tests Turbine casings are to be subjected to pressure test of 1.5 times the highest pressure in the casing during normal operation. Turbine casings may be divided by temporary diaphragms to allow for an even distribution of the test pressures. Where hydrostatic tests are not practicable, alternative tests to determine soundness and workmanship are to be submitted for consideration and approval in each case. Intercoolers and heat exchangers are to be hydrostatically tested on both sides to 1.5 times the design pressure.
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

### R023-04 主机安全运行关键设备保护
冷却水系统应确保主机安全运行，关键设备（如缸套、增压器）的冷却保护功能可靠。

检索画像：部件=['main_engine_cooling_water_system']；方面=['reliability', 'safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-IACS-M35-001｜direct｜primary
  - 来源：IACS Unified Requirements M35 Rev.8 Alarms and Safeguards for Main IC Engines in UMS｜位置：UR M35 Rev.8｜部件：alarm_system, main_engine_cooling_water_system, expansion_tank｜方面：alarm_protection, monitoring, safety｜可支撑：alarm_protection, parameter_limit, equipment_selection｜强度：direct｜适用性：yes/class_rule
```text
IACS UR M35 Rev.8 — Mandatory Alarms and Safeguards for Main IC Engines in Unattended Machinery Spaces (UMS):
- High cooling water temperature: mandatory alarm AND automatic slowdown or shutdown trigger
- Low cooling water pressure (HT and LT circuits): mandatory alarm
- Deaerating/expansion tank low level: mandatory alarm
- All parameters that could cause engine damage if unattended must have alarm + automatic protective response
Note: Numerical setpoints for alarms and slowdown/shutdown are engine manufacturer-specific and must be approved by the class society. The UR mandates the alarm exists; the threshold values are defined in the engine manufacturer's project guide and control system.
```

- E-SUPP-MAINT-001｜indirect｜supporting
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

- E-SUPP-MAINT-002｜indirect｜supporting
  - 来源：S73 Marine Cooling System Modular Maintenance Design Practice｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system, filter｜方面：maintenance, installation, equipment_selection, inspection, reliability｜可支撑：maintenance, installation, equipment_selection, inspection｜强度：direct｜适用性：general/general
```text
Marine Engineering Best Practice — Modular Design and Quick-Exchange Requirements for Cooling System Equipment
(Consolidated from DNV Rules, class society guidance, and international shipbuilding practice)

Design requirements to minimise downtime during maintenance and component exchange:
1. Cooling water pumps: shall be designed for in-situ impeller/mechanical seal replacement without removing the pump casing from the pipeline (back-pull-out design), OR shall have flanged connections permitting removal as a complete unit within the maintenance clearance.
2. Heat exchangers: shall be of removable-bundle or gasketed plate-frame type where practical, allowing cleaning/inspection without full removal from the cooling circuit.
3. Temperature control valves: shall be fitted with upstream and downstream isolating valves, permitting in-situ actuator and trim replacement while maintaining other cooling circuits in service.
4. All equipment shall use standardised flanged or threaded connections compatible with ship-standard pipe dimensions, to permit rapid exchange with equivalent spare units.
5. Spare parts for critical components (pump mechanical seals, TCV actuators, strainer baskets, heat exchanger gaskets) shall be listed in the Class-approved spare parts list with manufacturer part numbers.
整理说明：冷却水系统模块化快拆设计要求：泵采用背抽式设计支持就地更换密封，板式换热器须可拆芯清洗，温控阀两侧须有截止阀支持在线更换，备品配件须入级认可备件清单。
```

- E-SYS-INSP-005｜indirect｜supporting
  - 来源：S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine｜位置：P271｜部件：main_engine_cooling_water_system｜方面：inspection, water_quality, corrosion_protection｜可支撑：parameter_limit, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液水质检测方法
Treated coolant can become contaminated during operation and the additive can lose some of its effectiveness. It is therefore advisable to check the cool- ing system and the condition of the coolant regularly. To detect leaks in the lubricating oil system, regular checking of the water in the expansion tank is recommended. Signs of oil in the water include discoloration or a visible oil film on the surface of the water sample. Check the additive concentration using the test kits provided by the additive manufacturer at least once per week. The results must be recorded. Note: The chemical additive concentrations shall not be less than the minimum con- centrations specified. See paragraph Permitted coolant additives, Page 272. Excessively low concentrations lead to corrosion and must be avoided. Con- centrations that are somewhat higher do not cause damage.
整理说明：原文涉及冷却液、水质、防腐剂、pH、硬度、氯离子或污染沉积风险，可支撑水质处理和维护检测类需求；具体限值和检测周期须按来源文件适用条件使用。
可支撑：main_engine_cooling_water_system 的 inspection
water_quality
corrosion_protection 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R024 设备采购方
冷却器、冷却水泵、温控阀、传感器和主要阀门的采购资料应完整，包括型号、容量、压力等级、材料、接口尺寸、适用介质、工作条件和厂家技术文件。采购设备应与系统设计参数保持一致。

### R024-01 冷却器采购资料完整性
冷却器采购资料应包含型号、容量、压力等级、材料、接口尺寸、适用介质、工作条件和厂家技术文件，且与系统设计参数一致。

检索画像：部件=['cooler']；方面=['capacity', 'pressure', 'document_completeness', 'material', 'arrangement', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-COOLER-ARR-003｜indirect｜secondary
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P338｜部件：cooler｜方面：arrangement, pressure, composition, configuration｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
中央冷却器选型要求
There are many possible concepts for the arrangement of cooling water sys- tems and the best solution always depends on the specific application of the engine and ship. The table below shows the main characteristics and schemes of two main concepts. For further information contact MAN Energy Solutions. Concept Mixing CW system Conventional CW system Arrangement Physically and thermodynamically connected LT and HT circuit Physically and thermodynamically separated LT and HT circuit Features One central seawater cooler sufficient Reduced piping No transfer of pressure peaks and pollutants between LT and HT circuits Central cooler possible with HT-cooler recooled by LT-cooling water 2022-12-20 - 3.1
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooler 的 arrangement
pressure
composition 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-INST-007｜indirect｜secondary
  - 来源：S39 MAN L21/31 Project Guide｜位置：P525｜部件：cooler｜方面：installation, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
中央冷却器选型要求：适用对象为L21/31、L27/38机型，柴油-电力推进船舶；海水温度推荐使用25°C或32°C，取决于船舶运营区域；当船舶在MCR工况下航速低于3节（如拖船、挖泥船等）时，冷却器设计需考虑航速影响。适用条件：中央冷却器选型，L21/31、L27/38机型，柴油-电力推进船舶。

可支撑：cooler的installation pressure temperature参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-INST-008｜indirect｜secondary
  - 来源：S39 MAN L21/31 Project Guide｜位置：P541｜部件：cooler｜方面：installation, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
中央冷却器选型要求：海水温度 25°C 或 32°C，取决于船舶运行区域。适用条件：L27/38;L21/31 机型，柴电推进船舶，2016.09.28 版本。

可支撑：cooler 的 installation pressure temperature 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-ARR-005｜indirect｜secondary
  - 来源：S37 MAN L27/38 Propulsion Project Guide｜位置：P118｜部件：cooler｜方面：arrangement, control, pressure, configuration｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件：HT冷却水首先流经HT级增压空气冷却器，然后流经水套和气缸盖，发动机出口水温由机械式恒温器调节；LT冷却水首先流经LT级增压空气冷却器，然后流经滑油冷却器，发动机出口水温由机械式恒温器调节。适用条件：参考条件。  
冷却器额定值：公差 +10%；热回收：公差 -15%。适用条件：冷却器布置基本值。  
冷却水流量：公差 ±5%；冷却水温度：公差 ±20°C。适用条件：涡轮出口温度及压力按上述参考条件。  

可支撑：cooler的arrangement、control、pressure参数应依据来源文件、厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。  
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。  
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLER-INST-006｜indirect｜secondary
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P80｜部件：cooler｜方面：installation, pressure, material｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
中央冷却器配置：冷却器类型包括管壳式和板框式。适用条件：淡水热交换器。

管壳式热交换器建议材料：壳体材料为钢；端盖材料为铁；管子材料为90/10 CuNi；管板材料为90/10 CuNi；折流板材料为钢。适用条件：表7。

板框式热交换器建议材料：框架材料为低碳钢（涂漆）；海水板片材料为钛或铝黄铜；淡水板片材料为不锈钢；海水接口材料为钢（涂层）；淡水接口材料为钢（涂层）；垫片材料为丁腈橡胶。适用条件：表8。

可支撑：cooler的installation pressure material参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R024-02 冷却水泵采购资料完整性
冷却水泵采购资料应包含型号、容量、压力等级、材料、接口尺寸、适用介质、工作条件和厂家技术文件，且与系统设计参数一致。

检索画像：部件=['cooling_water_pump']；方面=['capacity', 'pressure', 'document_completeness', 'material', 'arrangement', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

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

- E-PUMP-CAP-011｜indirect｜supporting
  - 来源：S32 HY/T 海水循环冷却系统运行管理规范｜位置：P13｜部件：cooling_water_pump｜方面：capacity, flow, pressure｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却水流量与泵容量参数
8.1.1 循环水泵及循环水管道提供的循环冷却水流量和压力应满足换热器的换热需要，同时在满足各 工况流量和压力的前提下，节省电能消耗。
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：cooling_water_pump 的 capacity
flow
pressure 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-PUMP-RED-025｜indirect｜supporting
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

### R024-03 温控阀采购资料完整性
温控阀采购资料应包含型号、容量、压力等级、材料、接口尺寸、适用介质、工作条件和厂家技术文件，且与系统设计参数一致。

检索画像：部件=['temperature_control_valve']；方面=['capacity', 'pressure', 'document_completeness', 'material', 'arrangement', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

- E-TCV-TEMP-051｜direct｜primary
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P26｜部件：temperature_control_valve｜方面：temperature, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
温度控制阀配置：Capacities 5-8L23/30H 130 kW/Cyl., 720 rpm 或 135 kW/Cyl., 750 rpm。适用条件：Reference condition: Tropic Air temperature LT water temperature inlet engine (from system) Air pressure Relative humidity Temperature basis 2) Setpoint HT cooling water engine outlet Set point lube oil inlet engine 82°C (engine equipped with HT thermostatic valve) 60°C (SAE30), 66°C (SAE40) Number of cylinders Engine output Speed Heat to be dissipated 1) Cooling water (CW) cylinder Charge air cooler; cooling water HT (1 stage cooler: no HT-stage) Charge air cooler; cooling water LT Lube oil (LO) cooler Heat radiation engine Air data Temp. of charge air at charge air cooler outlet, max. Air flow rate Charge air pressure Air required to dissipate heat radiation (eng.) (t2-t1=10°C) m3/h 4) kg/kWh m3/h 7.39 3.08 7.39 3.08 7.39 3.08 7.39 3.08 Exhaust gas data 5) Volume flow (temperature turbocharger outlet) Mass flow。

可支撑：temperature_control_valve 的 temperature control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-TCV-TEMP-059｜direct｜primary
  - 来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜位置：P189｜部件：temperature_control_valve｜方面：temperature, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
温度控制阀：外部管路最大水流速，淡水：3.0 m/s；海水：3.0 m/s。适用条件：外部管路连接。
发动机：HT系统压降约为0.5 bar。适用条件：不包括泵和恒温阀。
润滑油冷却器：冷却水压降约为0.3 bar。适用条件：内置式润滑油冷却器；实际压降可能因冷却器设计不同而异。
恒温阀：压降约为0.5 bar。适用条件：内置式恒温阀。
增压空气冷却器：冷却水压降 ∆P = V² × K [Bar]；V为冷却水流量，单位m³/h；K为常数，参见B 15 00 0，增压空气冷却器。适用条件：冷却水流经增压空气冷却器。
冷却水泵：应为离心式。适用条件：冷却水系统。

可支撑：temperature_control_valve 的 temperature control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-TCV-TEMP-021｜indirect｜secondary
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P178｜部件：temperature_control_valve｜方面：temperature, control, pressure｜可支撑：parameter_limit, equipment_selection, calculation, operation｜强度：indirect｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
温度控制阀：外部管道流速，淡水最大流速 3.0 m/s；海水最大流速 3.0 m/s。适用条件：外部管道连接。  
发动机：高压系统压降，约（未给出具体数值）。适用条件：不含泵和恒温阀。  

可支撑：temperature_control_valve 的 temperature control pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。  
不能支撑：1. 不能直接给出可用于设计输入的具体数值。2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-TCV-TEMP-011｜indirect｜secondary
  - 来源：S37 MAN L27/38 Propulsion Project Guide｜位置：P136｜部件：temperature_control_valve｜方面：temperature, control, installation｜可支撑：parameter_limit, installation, operation, monitoring｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
MAN Diesel & Turbo L27/38 冷却水系统：预热器可为电加热型；若中央供暖容量足够，可安装板式换热器；必须确保主机冷却系统中使用的阻蚀淡水不与中央供暖系统的水混合。适用条件：MAN Diesel & Turbo L27/38 机型。

MAN Diesel & Turbo L27/38 冷却水系统：热回收低于发动机缸套水热排量的25%时，热回收设备（项目35）可与HT淡水冷却器串联连接；若利用HT冷却水段超过25%的热量，应安装额外的恒温阀（项目34）用于旁通HT淡水冷却器，以避免热回收设备（项目35）后的不必要冷却。适用条件：MAN Diesel & Turbo L27/38 机型，热回收比例阈值25%。

可支撑：temperature_control_valve 的 temperature control installation 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R024-04 传感器和主要阀门采购资料完整性
传感器和主要阀门采购资料应包含型号、容量、压力等级、材料、接口尺寸、适用介质、工作条件和厂家技术文件，且与系统设计参数一致。

检索画像：部件=['valve']；方面=['capacity', 'pressure', 'document_completeness', 'material', 'arrangement', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。

## R025 维修人员
冷却水系统应支持故障隔离和局部检修。主要设备、滤器、冷却器和关键阀件应具备合理的隔离条件，避免单个部件维护时对整个冷却系统造成不必要影响。

### R025-01 设备隔离维护
主机冷却水系统的主要设备、滤器、冷却器和关键阀件应配置隔离阀，以便在单个部件维护时不影响系统其他部分运行。

检索画像：部件=['main_engine_cooling_water_system', 'cooler', 'filter', 'cooling_water_pump', 'temperature_control_valve', 'expansion_tank']；方面=['maintenance', 'accessibility', 'cleaning', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

- E-PUMP-MAINT-001｜direct｜primary
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

- E-SUPP-MAINT-001｜indirect｜supporting
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

## R026 安全负责人
冷却水系统应降低高温介质、旋转设备、带压管路和化学处理液对人员造成伤害的风险。高温表面、旋转部件、放水排放点和化学品加注点应根据现场条件设置必要防护和警示标识。

### R026-01 高温表面防护与警示
冷却水系统的高温表面应设置隔热防护或警示标识，防止人员烫伤。

检索画像：部件=['main_engine_cooling_water_system']；方面=['temperature', 'safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-SUPP-SAFE-001｜direct｜primary
  - 来源：S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements｜位置：｜部件：pipe, main_engine_cooling_water_system, ht_cooling_water_loop, cooling_water_pump｜方面：installation, safety, inspection｜可支撑：installation, safety, inspection｜强度：direct｜适用性：general/class_rule
```text
高温冷却水管路：表面温度 > 60°C；绝热后表面温度 < 55°C。适用条件：HT回路典型温度 70–95°C，环境温度 25°C，典型船级社要求。
高温冷却水管路、阀门及设备：绝热材料最高工作温度 ≥ 150°C；绝热材料为矿物棉（岩棉/玻璃棉）或等效材料；机械防护包覆材料为铝或不锈钢包覆层。适用条件：暴露于溅水或人员通行的区域。
高温冷却水管路法兰、阀门、仪表连接件及需定期检查的部件：不得施加固定绝热层；应配备可拆卸绝热罩。
无法完全绝热的高温表面（如阀盖、泵壳）：应张贴符合ISO 11684的“热表面”警告标识；标识间距 ≤ 2 m。适用条件：可触及区域。
冷却水管路：按ISO 14726（或船厂特定标准）进行色标标识；HT冷却水为绿色加字母代码；海水为绿色加特定条纹；淡水为绿色。
主要冷却系统设备：应配备铭牌，包含标签号、系统名称及维护间隔。
```

### R026-02 旋转部件防护与警示
冷却水系统的旋转部件应设置防护罩或警示标识，防止人员卷入。

检索画像：部件=['main_engine_cooling_water_system']；方面=['safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-SUPP-SAFE-001｜direct｜primary
  - 来源：S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements｜位置：｜部件：pipe, main_engine_cooling_water_system, ht_cooling_water_loop, cooling_water_pump｜方面：installation, safety, inspection｜可支撑：installation, safety, inspection｜强度：direct｜适用性：general/class_rule
```text
高温冷却水管路：表面温度 > 60°C；绝热后表面温度 < 55°C。适用条件：HT回路典型温度 70–95°C，环境温度 25°C，典型船级社要求。
高温冷却水管路、阀门及设备：绝热材料最高工作温度 ≥ 150°C；绝热材料为矿物棉（岩棉/玻璃棉）或等效材料；机械防护包覆材料为铝或不锈钢包覆层。适用条件：暴露于溅水或人员通行的区域。
高温冷却水管路法兰、阀门、仪表连接件及需定期检查的部件：不得施加固定绝热层；应配备可拆卸绝热罩。
无法完全绝热的高温表面（如阀盖、泵壳）：应张贴符合ISO 11684的“热表面”警告标识；标识间距 ≤ 2 m。适用条件：可触及区域。
冷却水管路：按ISO 14726（或船厂特定标准）进行色标标识；HT冷却水为绿色加字母代码；海水为绿色加特定条纹；淡水为绿色。
主要冷却系统设备：应配备铭牌，包含标签号、系统名称及维护间隔。
```

### R026-03 带压管路防护与警示
冷却水系统的带压管路应设置防护或警示标识，防止高压流体喷射伤人。

检索画像：部件=['main_engine_cooling_water_system', 'pipe']；方面=['safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-SUPP-SAFE-001｜direct｜primary
  - 来源：S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements｜位置：｜部件：pipe, main_engine_cooling_water_system, ht_cooling_water_loop, cooling_water_pump｜方面：installation, safety, inspection｜可支撑：installation, safety, inspection｜强度：direct｜适用性：general/class_rule
```text
高温冷却水管路：表面温度 > 60°C；绝热后表面温度 < 55°C。适用条件：HT回路典型温度 70–95°C，环境温度 25°C，典型船级社要求。
高温冷却水管路、阀门及设备：绝热材料最高工作温度 ≥ 150°C；绝热材料为矿物棉（岩棉/玻璃棉）或等效材料；机械防护包覆材料为铝或不锈钢包覆层。适用条件：暴露于溅水或人员通行的区域。
高温冷却水管路法兰、阀门、仪表连接件及需定期检查的部件：不得施加固定绝热层；应配备可拆卸绝热罩。
无法完全绝热的高温表面（如阀盖、泵壳）：应张贴符合ISO 11684的“热表面”警告标识；标识间距 ≤ 2 m。适用条件：可触及区域。
冷却水管路：按ISO 14726（或船厂特定标准）进行色标标识；HT冷却水为绿色加字母代码；海水为绿色加特定条纹；淡水为绿色。
主要冷却系统设备：应配备铭牌，包含标签号、系统名称及维护间隔。
```

### R026-04 化学处理液防护与警示
冷却水系统的化学处理液加注点应设置防护和警示标识，防止化学品伤害。

检索画像：部件=['main_engine_cooling_water_system']；方面=['safety', 'corrosion_protection', 'environmental_protection', 'alarm', 'maintenance']；可支撑=['safety', 'environment', 'maintenance', 'alarm_protection', 'inspection']

- E-SUPP-SAFE-001｜direct｜primary
  - 来源：S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements｜位置：｜部件：pipe, main_engine_cooling_water_system, ht_cooling_water_loop, cooling_water_pump｜方面：installation, safety, inspection｜可支撑：installation, safety, inspection｜强度：direct｜适用性：general/class_rule
```text
高温冷却水管路：表面温度 > 60°C；绝热后表面温度 < 55°C。适用条件：HT回路典型温度 70–95°C，环境温度 25°C，典型船级社要求。
高温冷却水管路、阀门及设备：绝热材料最高工作温度 ≥ 150°C；绝热材料为矿物棉（岩棉/玻璃棉）或等效材料；机械防护包覆材料为铝或不锈钢包覆层。适用条件：暴露于溅水或人员通行的区域。
高温冷却水管路法兰、阀门、仪表连接件及需定期检查的部件：不得施加固定绝热层；应配备可拆卸绝热罩。
无法完全绝热的高温表面（如阀盖、泵壳）：应张贴符合ISO 11684的“热表面”警告标识；标识间距 ≤ 2 m。适用条件：可触及区域。
冷却水管路：按ISO 14726（或船厂特定标准）进行色标标识；HT冷却水为绿色加字母代码；海水为绿色加特定条纹；淡水为绿色。
主要冷却系统设备：应配备铭牌，包含标签号、系统名称及维护间隔。
```

## R027 材料工程师
海水侧管路、阀门、冷却器和相关附件应考虑海水腐蚀、海生物附着和材料相容性。淡水侧和冷却液侧部件应考虑防腐剂、冷却液浓度、水质条件和温度压力对材料的影响。

### R027-01 海水侧材料耐腐蚀与防污
海水侧管路、阀门、冷却器和附件应选用耐海水腐蚀、抗海生物附着的材料，并考虑材料相容性。

检索画像：部件=['sea_water_cooling_system', 'cooler', 'pipe', 'valve']；方面=['material', 'corrosion_protection', 'reliability', 'capacity', 'temperature', 'pressure', 'flow']；可支撑=['system_design', 'equipment_selection', 'parameter_limit', 'calculation']

- E-SUPP-MAT-001｜direct｜primary
  - 来源：S77 DNV Rules Pt4 Ch6 Material Selection Seawater Systems｜位置：｜部件：sea_water_cooling_system, cooler, pipe, valve, cooling_water_pump｜方面：equipment_selection, installation｜可支撑：equipment_selection, installation｜强度：direct｜适用性：general/class_rule
```text
Marine Cooling Water System — Material Selection for Seawater-Exposed Components
(Based on DNV Rules Pt.4 Ch.6, IACS UR, ASTM B111, and ISO 6509)

Material requirements by circuit:

Seawater circuit (sea chests, strainers, seawater pump casings, cooler seawater side, overboard piping):
- ACCEPTABLE: Gunmetal / red brass (CuSn), Nickel-aluminium bronze (CuAlNi), Duplex stainless steel (22Cr or 25Cr), Titanium Grade 2 (preferred for polluted ports and biofouling risk), Glass Reinforced Epoxy (GRE) for piping
- NOT ACCEPTABLE for seawater wetted surfaces: plain carbon steel, grey cast iron
- Heat exchanger tubes in tropical/polluted seawater: CuNi 70/30 (ASTM B111 C71500) or titanium Grade 2 (most resistant to erosion-corrosion and biofouling)

Freshwater circuit (HT/LT loops, expansion tank, internal piping):
- Carbon steel (seamless or ERW): acceptable with inhibited coolant treatment
- Copper alloys: compatible with treated freshwater; avoid direct galvanic contact with aluminium engine components
- Stainless steel 316L: suitable for all freshwater cooling service

Bimetallic (galvanic) corrosion prevention:
Where dissimilar metals join (e.g. steel pipe to bronze valve), insulating flanges, isolating sleeves, or cathodic protection shall be applied per DNV RP-0198.
整理说明：冷却水系统材料选型规范：海水侧须用铜镍合金/双相不锈钢/钛合金/GRE管（禁用碳钢/灰铸铁）；热带污染海域换热管推荐CuNi 70/30或钛合金；淡水侧可用碳钢（加抑制剂）；异种金属连接须防电化学腐蚀（绝缘法兰或阴极保护）。
```

- E-SW-CORR-004｜indirect｜supporting
  - 来源：S26 MTU, Fluids and Lubricants Specifications, A001065｜位置：P30｜部件：sea_water_cooling_system｜方面：corrosion_protection, material｜可支撑：system_design｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```text
材料与防腐要求
• Copper-based alloys with the exception of CuNi10 and CuNi30 (e.g. seawater cooler) • Tin, also as surface protection • Magnesium-based alloys Non-metallic materials • Elastomers: Nitrile butadiene rubber, natural rubber, chloroprene rubber, butyl rubber, EPDM • Silicone elastomer • Fluorosilicone elastomer • Polyurethane • Polyvinyl Information: In case of doubt about the use of materials on the engine / add-on components in coolant circuits, consulta- tion with the respective MTU specialist department must be held. S28 Wärtsilä 32 Product Guide, Cooling Water System
整理说明：该证据针对 sea_water_cooling_system 的 corrosion_protection / material 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：可支撑 sea_water_cooling_system 在 corrosion_protection
material 方面的系统设计
运行或维护依据。
具体指标和验收条件应结合来源文件适用范围进一步确认。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

- E-SW-CORR-010｜indirect｜supporting
  - 来源：S42 MAN 49/60DF Project Guide｜位置：P284｜部件：sea_water_cooling_system｜方面：corrosion_protection, cleaning, water_quality｜可支撑：parameter_limit, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却系统腐蚀与气蚀风险
Every 2 to 6 months, a coolant sample must be sent to an independent labor- atory or to the engine manufacturer for an integrated analysis. If chemical additives or antifreeze agents are used, coolant should be re- placed after 3 years at the latest. If there is a high concentration of solids (rust) in the system, the water must be completely replaced and entire system carefully cleaned. Deposits in the cooling system may be caused by fluids that enter the coolant or by emulsion break-up, corrosion in the system, and limescale deposits if the water is very hard. If the concentration of chloride ions has increased, this generally indicates that seawater has entered the system. The maximum spe- cified concentration of 50 mg chloride ions per kg must not be exceeded as otherwise the risk of corrosion is too high.
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

- E-COOLANT-CLEAN-029｜indirect｜supporting
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P198｜部件：coolant｜方面：cleaning, water_quality, material｜可支撑：parameter_limit, maintenance, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液污染与沉积风险
11.2.5 Internal seawater cooling systems shall be designed and made of an appropriate material to minimize biofouling and constructed with a minimum of bends, kinks and flanges in seawater piping in accordance with the guidance contained in IMO Resolution MEPC.207(62).
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

### R027-02 淡水侧材料耐介质与工况
淡水侧和冷却液侧部件应选用与防腐剂、冷却液浓度、水质条件及温度压力相容的材料。

检索画像：部件=['coolant']；方面=['temperature', 'pressure', 'material', 'water_quality', 'corrosion_protection', 'reliability', 'capacity', 'flow']；可支撑=['system_design', 'equipment_selection', 'parameter_limit', 'calculation']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-COOLANT-WATER-149｜indirect｜secondary
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P54｜部件：coolant｜方面：water_quality, pressure, temperature｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
主机冷却型式与设计条件
13.5.3 Ambient Reference Conditions (2020) The following ambient reference conditions are to be applied by the engine manufacturer for the purpose of determining the rated power of diesel engines used on vessels with unrestricted service. However, the engine manufacturer is not expected to provide simulated ambient reference conditions at any test. Barometric pressure: 1 bar (1 kgf/cm2, 15 psi) Air temperature: 45°C (113°F) Relative air humidity: 60% Seawater Temperature (Charging air coolant inlet): 32°C (90°F)
整理说明：原文涉及冷却液、水质、防腐剂、pH、硬度、氯离子或污染沉积风险，可支撑水质处理和维护检测类需求；具体限值和检测周期须按来源文件适用条件使用。
可支撑：coolant 的 water_quality
pressure
temperature 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLANT-WATER-148｜indirect｜secondary
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P409｜部件：coolant｜方面：water_quality, corrosion_protection, pressure｜可支撑：parameter_limit, equipment_selection, calculation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
防腐剂安全防护：压力容器类别a)（有毒和腐蚀性物质的压力容器和热交换器）：压力 >1.0 bar / >1.0 kgf/cm² / >15 psi；温度 所有；容积 所有；适用条件：依据4-4-1/1.9，ABS型式认可等级5。
压力容器类别b)（除a)以外的压力容器、热交换器和加热器）：压力 >6.9 bar / >7 kgf/cm² / >100 psi；温度 所有；容积 所有；适用条件：依据4-4-1/1.9，ABS型式认可等级4/5。
压力容器类别c)（除a)和b)以外的压力容器、热交换器和加热器）：压力 >1.0 bar / >1.0 kgf/cm² / >15 psi；温度 >149°C(1) / >66°C(2) / >90°C(3) 或 >300°F(1) / >150°F(2) / >200°F(3)；容积 >0.14 m³ / >5 ft³；适用条件：依据4-4-1/1.11.2和4-4-1/1.5，ABS型式认可等级4/5。

可支撑：coolant 的 water_quality corrosion_protection pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLANT-WATER-004｜indirect｜secondary
  - 来源：S06 Scania DI16 船用发动机车主手册（中文）｜位置：P35｜部件：coolant｜方面：water_quality, corrosion_protection, inspection｜可支撑：parameter_limit, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液防腐剂比例
检查防腐剂 冷却液中必须始终有足够的防腐剂，以便为冷却系统提供防腐保护。 如果不存在结冰危险，则仅应在冷却液中使用 Scania Corrosion Inhibitor （Scania 防腐剂）。 Scania Corrosion Inhibitor （Scania 防腐剂）中的抑制剂不含亚硝酸盐。 防腐剂的正确体积比为 8-12%。
整理说明：原文涉及冷却液、水质、防腐剂、pH、硬度、氯离子或污染沉积风险，可支撑水质处理和维护检测类需求；具体限值和检测周期须按来源文件适用条件使用。
可支撑：coolant 的 water_quality
corrosion_protection
inspection 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLANT-WATER-005｜indirect｜secondary
  - 来源：S06 Scania DI16 船用发动机车主手册（中文）｜位置：P35｜部件：coolant｜方面：water_quality, corrosion_protection｜可支撑：parameter_limit｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液防腐剂比例
- 切勿仅用水或防腐剂加注至正确的液位！ 必须始终用预混合冷却液进行补足： 水 + 10% Scania Corrosion Inhibitor （Scania 防腐剂） （体积比）。
整理说明：原文涉及冷却液、水质、防腐剂、pH、硬度、氯离子或污染沉积风险，可支撑水质处理和维护检测类需求；具体限值和检测周期须按来源文件适用条件使用。
可支撑：coolant 的 water_quality
corrosion_protection 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-COOLANT-INSP-006｜indirect｜secondary
  - 来源：S08 MAN Energy Solutions SL2016-623 Cooling water treatment｜位置：P3｜部件：coolant｜方面：inspection, water_quality, pressure｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液水质检测方法：总硬度 ≤10 °dGH；pH值 6.5 - 8 at 20 °C；氯离子含量 ≤50 mg/l。适用条件：Water for filling and refilling (without additive)，水类型为淡水，无杂质。

冷却液水质检测方法：总硬度 ≤10 °dGH；pH值 ≥7.5 at 20 °C；氯离子含量 ≤50 mg/l。适用条件：Circulating water (with additive)，水类型为处理过的冷却水。

冷却液水质检测方法：硬度单位换算 1 mg/l = 1 p；钙离子浓度 7.9 mg/l CaCO3 / 0.179 mmol/l。适用条件：水质检测通用。

可支撑：coolant 的 inspection，water_quality，pressure 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。

不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

## R028 运维管理人员
冷却水系统应便于建立运行维护记录。冷却水温度、压力、液位、泵运行状态、报警事件、冷却液补充、更换、取样和清洗情况应能够形成可追溯的运行维护数据。

### R028-01 运行参数监测与记录
冷却水系统应具备温度、压力、液位、泵运行状态及报警事件的实时监测与记录功能，数据可追溯。

检索画像：部件=['main_engine_cooling_water_system', 'cooling_water_pump', 'temperature_control_valve', 'cooler', 'temperature_sensor', 'pressure_sensor', 'flow_sensor']；方面=['temperature', 'pressure', 'monitoring', 'alarm', 'control', 'reliability', 'maintenance', 'flow', 'capacity']；可支撑=['operation', 'monitoring', 'alarm_protection', 'maintenance', 'parameter_limit', 'operation_parameter', 'commissioning', 'system_design', 'calculation']

- E-ISO8861-002｜direct｜primary
  - 来源：S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements｜位置：｜部件：alarm_system, expansion_tank, temperature_sensor, pressure_sensor, level_sensor, main_engine_cooling_water_system｜方面：monitoring, alarm, parameter_limit｜可支撑：monitoring, alarm, parameter_limit｜强度：direct｜适用性：general/international_standard
```text
ISO 8861:1998 Shipbuilding and Marine Structures — Cooling System Monitoring Requirements
Section 8 — Monitoring and Alarm:
The following parameters shall be monitored and alarmed for main engine cooling water systems:
a) High temperature of HT cooling water at engine outlet: alarm set-point to be within manufacturer's limits (typically 85–95°C for large 4-stroke engines);
b) Low pressure of cooling water at engine inlet: alarm set-point as specified by manufacturer;
c) Low level in expansion tank: alarm when level falls below minimum operating level;
d) High temperature of LT cooling water: alarm set-point as per central cooler design.
All alarms shall be indicated in the engine control room and navigating bridge.
整理说明：ISO 8861:1998 规定了主机冷却水系统的监测参数、报警设定和报警位置，为冷却水监测、报警配置和控制系统设计提供了国际标准依据。
```

- E-DNV-COOL-001｜indirect｜supporting
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, temperature_control_valve, central_cooling_system｜方面：parameter_limit, capacity, system_design｜可支撑：parameter_limit, capacity, system_design｜强度：direct｜适用性：general/class_rule
```text
DNV Rules for Classification: Ships, Pt.4 Ch.3 — Cooling Water Systems
The cooling water system for main propulsion engines shall be designed so that the cooling water temperatures at the engine inlet are maintained within the limits specified by the engine manufacturer. For high-temperature (HT) fresh water circuits, the maximum inlet temperature to the engine shall not exceed 36°C above the thermostat opening temperature under worst-case ambient conditions. For central (low-temperature) cooling systems, the LT fresh water temperature at the plate cooler outlet shall be calculated for maximum sea water temperature at the service area.
整理说明：DNV船级社规则对主机冷却水进机温度范围、温控阀调节范围及中央冷却系统低温回路设计提供了规范级依据。可支撑温度参数限制、系统设计及温控阀配置类需求。
```

- E-WAR46DF-PARAM-001｜indirect｜supporting
  - 来源：S28 Wärtsilä 32 Product Guide, Cooling Water System｜位置：｜部件：ht_cooling_water_loop, lt_cooling_water_loop, cooling_water_pump, temperature_control_valve, main_engine_cooling_water_system｜方面：parameter_limit, operation, alarm, commissioning_check, reliability, configuration｜可支撑：parameter_limit, operation, alarm, commissioning_check｜强度：direct｜适用性：limited/manufacturer_specific
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

### R028-02 维护操作记录与追溯
冷却液补充、更换、取样和清洗等维护操作应能形成可追溯的记录。

检索画像：部件=['coolant', 'cooler', 'filter', 'cooling_water_pump', 'temperature_control_valve', 'expansion_tank']；方面=['maintenance', 'cleaning', 'accessibility', 'inspection', 'flushing']；可支撑=['maintenance', 'inspection', 'operation', 'cleaning']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-COOLANT-CLEAN-001｜indirect｜secondary
  - 来源：S09 MAN Energy Solutions SL2014-584 Cooling Water System｜位置：P3｜部件：coolant｜方面：cleaning, inspection, water_quality｜可支撑：parameter_limit, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却系统清洗要求
flushed, refilled and recharged with the inhibitor. Every four-five years and after long out-of-operation periods Based on the regular checks, clean the cooling water system for oil sludge, rust and lime. During cleaning, cool - ing jackets should be removed from the cylinder liner and cylinder cover, and the exhaust valve should be removed from the cylinder cover. This is necessary in order to per - form thorough cleaning of the entire cooling water system. Finally, refill the system and add the inhibitor. Partly cleaning of the system during piston overhaul is also recommended (removal of the cooling jacket on the cylin - der cover, clean and re-fit with new O-rings) as the cylinder cover is the most sensitive area of the cooling water system. A clear record of all measuring results should be kept, so that the actual condition and trend of the system may be
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

- E-COOLANT-CLEAN-016｜indirect｜secondary
  - 来源：S36 MAN L23/30H GenSet Project Guide｜位置：P160｜部件：coolant｜方面：cleaning, water_quality, corrosion_protection｜可支撑：parameter_limit, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却系统清洗要求
Excessively low concentrations can promote corrosion and must be avoided. If the concentration is slightly above the recommended concentration this will not result in damage. Concentrations that are more than twice the recom- mended concentration should be avoided. Every 2 to 6 months send a cooling water sample to an independent labora- tory or to the engine manufacturer for integrated analysis. Emulsifiable anticorrosive agents must generally be replaced after abt. 12 months according to the supplier's instructions. When carrying this out, the entire cooling system must be flushed and, if necessary, cleaned. Once filled into the system, fresh water must be treated immediately. If chemical additives or anti-freeze solutions are used, cooling water should be replaced after 3 years at the latest.
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

- E-COOLANT-MAINT-003｜indirect｜secondary
  - 来源：S26 MTU, Fluids and Lubricants Specifications, A001065｜位置：P19｜部件：coolant｜方面：maintenance, water_quality, function｜可支撑：parameter_limit, maintenance｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
冷却液更换与合规要求：氯离子含量 ≤ 25 mg/l。适用条件：Table 11 冷却液要求；冷却液必须在不满足上述规格时更换。注意：对于冷却液功能的整体评估，除上述限值外，还必须考虑各自冷却液的特有特性数据以及所用淡水水质。

可支撑：coolant 的 maintenance；water_quality；function 参数应依据来源文件厂家技术数据或项目计算文件确定。若原文给出明确限值，可作为对应适用对象和工况下的参数约束。

不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R028-03 数据记录系统配置
系统应配置数据记录功能，支持运行维护数据的存储与查询。

检索画像：部件=['main_engine_cooling_water_system']；方面=['maintenance', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。

## R029 船厂质量检验人员
冷却水系统安装和试验完成后，应检查管路密性、支架固定、阀门方向、传感器安装、设备接口、标识完整性和试验记录。发现的问题应在交船前完成整改并形成闭环记录。

### R029-01 管路安装与密性检查
冷却水系统管路安装后应进行密性检查，确保无泄漏。

检索画像：部件=['main_engine_cooling_water_system', 'pipe', 'valve', 'support', 'equipment_interface', 'flushing_connection', 'pressure_test_connection']；方面=['installation', 'inspection', 'arrangement', 'accessibility', 'flushing', 'pressure_test']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

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

- E-PIPE-PTEST-007｜direct｜primary
  - 来源：S46 46 CFR 56.97-40 Installation tests｜位置：56.97-40(a)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-56/subpart-56.97/section-56.97-40｜部件：pipe｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
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

- E-PIPE-PTEST-012｜direct｜primary
  - 来源：S47 46 CFR 58.20-25 Tests｜位置：58.20-25(a)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-58/subpart-58.20/section-58.20-25｜部件：pipe｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
All pressure vessels, compressors, piping, and direct expansion cooling coils: 设计压力泄漏试验要求；试验压力等于设计压力。适用条件：安装后，依据 S48 46 CFR 197.462。

可支撑：管系安装后应按适用法规、船级社或项目试验程序进行水压或泄漏试验。试验压力、持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

- E-PIPE-PTEST-001｜indirect｜secondary
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

- E-PIPE-PTEST-004｜indirect｜secondary
  - 来源：S52 BN-G-Y015 Piping Systems Inspection and Testing｜位置：3.1 General；source_url=https://red-bag.com/general-guides/186-bn-g-y015-piping-systems-inspection-and-testing.html｜部件：pipe｜方面：pressure_test, inspection, pressure, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
水压试验前焊缝和机械接头可检验性要求
Insulation or painting shall not be applied over welds, flanges and/or other mechanical joints prior to hydrotesting.
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

### R029-02 支架与阀门安装检查
冷却水系统支架应固定牢固，阀门方向应正确。

检索画像：部件=['main_engine_cooling_water_system', 'valve', 'support', 'pipe', 'equipment_interface', 'flushing_connection', 'pressure_test_connection']；方面=['installation', 'inspection', 'arrangement', 'accessibility', 'flushing', 'pressure_test']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-VALVE-INSP-010｜indirect｜secondary
  - 来源：S51 NASA NTRS 19800002357 Piping Specification｜位置：B-45；source_url=https://ntrs.nasa.gov/api/citations/19800002357/downloads/19800002357.pdf?attachment=true｜部件：valve｜方面：inspection, installation, arrangement, configuration｜可支撑：installation, test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
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

- E-VALVE-ARR-001｜indirect｜secondary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P198｜部件：valve｜方面：arrangement, configuration｜可支撑：installation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水连接关系
11.2.2 Sea-water supply to the cooling system shall be provided by means of at least two inlet valves, one of which shall be located at the bottom, the other one on the side of the ship. These valves shall be interconnected and the cooling water shall be taken from the connecting sea-water main.
整理说明：该证据针对 valve 的 arrangement 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-VALVE-ACCESS-004｜indirect｜secondary
  - 来源：S44 PRS Ship Machinery Piping Systems｜位置：P144｜部件：valve｜方面：accessibility, configuration｜可支撑：installation, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水连接关系
6.1.2 Where exhaust gas lines with water injection are led through the shell plating, near or below the load waterline, means shall be provided to prevent the sea -water from entering the engine. The pipes shall be looped or fitted with a suitable device such as a riser to prevent the return of water to the engine. Water for cooling exhaust gas shall be injected in a manner that minimizes the possibility of cooling water entering the engine through the exhaust manifold. Where a shut -off valve is fitted at the over board discharge, means shall be provided to prevent the engine from being started when the valve is not fully open. Moreover this valve is to be readily operable from accessible position.
整理说明：该证据针对 valve 的 accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-SUPP-MAINT-001｜indirect｜secondary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

### R029-03 传感器与设备接口检查
冷却水系统传感器安装应正确，设备接口应连接可靠。

检索画像：部件=['main_engine_cooling_water_system', 'equipment_interface', 'pipe', 'valve', 'support', 'flushing_connection', 'pressure_test_connection']；方面=['reliability', 'installation', 'inspection', 'arrangement', 'accessibility', 'flushing', 'pressure_test']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

> 证据缺口：只有间接证据，尚无直接证据形成工程化需求依据。
> 建议补充：补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。

- E-SUPP-MAINT-001｜indirect｜secondary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
冷却水系统设备（泵）：轴向间隙 ≥ 1.5 × 泵壳长度，用于叶轮/轴拆卸；径向间隙 ≥ 轴直径 + 100 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（板式换热器/管束）：全板束/管束抽出长度在一侧。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（阀手轮/执行器）：操作侧间隙 ≥ 600 mm。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统通道：最小净宽度 ≥ 600 mm，人员通过处；≥ 500 mm，仅检查处。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（移除质量 > 25 kg）：应设置顶部吊装设施（吊眼或单轨）。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
冷却水系统设备（需定期维护）：应具有清晰的铭牌，标明维护间隔和标签号。适用条件：基于DNV规范Pt.4 Ch.1、IACS UR M3、ISO 14122-3及标准船舶工程实践。
```

- E-IFACE-INST-001｜indirect｜secondary
  - 来源：S45 46 CFR 56.01-10 Plan approval｜位置：56.01-10(f)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-56/subpart-56.01/section-56.01-10｜部件：equipment_interface｜方面：installation, pressure, drawing_review｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
穿舱和防火边界管路贯穿详图提交要求
Where piping passes through watertight bulkheads and/or fire boundaries, plans of typical details of piping penetrations must be submitted. S46 46 CFR 56.97-40 Installation tests
整理说明：该证据说明管系图纸或送审资料中需要体现材料、管径、设计压力、泵额定容量和关断扬程等信息，可支撑审图和文件完整性要求；具体图纸深度仍需按项目和审查机构要求确认。
可支撑：管系图纸
材料信息
设计压力和泵额定参数应在送审文件中清楚标注。
图纸审查应覆盖与冷却水管系相关的接口
材料
压力等级和泵参数。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

- E-SUPP-SAFE-001｜indirect｜secondary
  - 来源：S83 SOLAS ISO13702 ISO14726 Insulation Safety Labeling Requirements｜位置：｜部件：pipe, main_engine_cooling_water_system, ht_cooling_water_loop, cooling_water_pump｜方面：installation, safety, inspection｜可支撑：installation, safety, inspection｜强度：direct｜适用性：general/class_rule
```text
高温冷却水管路：表面温度 > 60°C；绝热后表面温度 < 55°C。适用条件：HT回路典型温度 70–95°C，环境温度 25°C，典型船级社要求。
高温冷却水管路、阀门及设备：绝热材料最高工作温度 ≥ 150°C；绝热材料为矿物棉（岩棉/玻璃棉）或等效材料；机械防护包覆材料为铝或不锈钢包覆层。适用条件：暴露于溅水或人员通行的区域。
高温冷却水管路法兰、阀门、仪表连接件及需定期检查的部件：不得施加固定绝热层；应配备可拆卸绝热罩。
无法完全绝热的高温表面（如阀盖、泵壳）：应张贴符合ISO 11684的“热表面”警告标识；标识间距 ≤ 2 m。适用条件：可触及区域。
冷却水管路：按ISO 14726（或船厂特定标准）进行色标标识；HT冷却水为绿色加字母代码；海水为绿色加特定条纹；淡水为绿色。
主要冷却系统设备：应配备铭牌，包含标签号、系统名称及维护间隔。
```

- E-SYS-CORR-001｜indirect｜secondary
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P67｜部件：main_engine_cooling_water_system｜方面：corrosion_protection, installation, material, configuration｜可支撑：installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水连接关系
cooler systems require the installation of strainers between the cooler and the pump inlet. Material, such as weld slag and corrosion products, must be removed from the system to prevent wear and plugging of cooling system components. Use a continuous bypass filter to remove smaller particles and sediment.
整理说明：该证据针对 main_engine_cooling_water_system 的 corrosion_protection / installation / material 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

- E-SYS-COMP-019｜indirect｜secondary
  - 来源：S41 Everllence 49/60DF Project Guide｜位置：P377｜部件：main_engine_cooling_water_system｜方面：composition, installation, pressure｜可支撑：parameter_limit, equipment_selection, calculation, installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```text
淡水侧系统组成
Y-type strainers with magnetic inserts and a mesh size of 1–2 mm depending on the pipe diameter. The strainers have to be installed in horizontal pipes or pipes with flow direc- tion downwards. We recommend to install shut off-flaps upstream and downstream of the strainer. HE-005/Nozzle cooling wa- ter cooler The nozzle cooling water system is a separate and closed cooling circuit. It is cooled down by LT cooling water via the nozzle cooling water cooler (HE-005). Heat data, flow rates and tolerances are indicated in section Planning data, described before in paragraph Cooler dimensioning, general, Page 374. For plants with two main engines only one nozzle cooling water cooler (HE-005) is required. As an option a compact nozzle cooling water module (MOD-005) can be delivered, see section Nozzle cooling water module, Page 389.
整理说明：原文给出了冷却水相关参数、阈值或适用条件，可用于对应厂家、机型或规则范围内的参数约束。该证据不应跨系统型式或跨机型直接泛化。
可支撑：main_engine_cooling_water_system 的 composition
installation
pressure 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### R029-04 标识与试验记录闭环
冷却水系统标识应完整，试验记录应齐全，发现问题应在交船前整改并形成闭环记录。

检索画像：部件=['main_engine_cooling_water_system']；方面=['inspection', 'commissioning', 'pressure_test', 'calculation', 'drawing_review', 'document_completeness', 'class_approval']；可支撑=['test', 'inspection', 'class_review', 'document_completeness', 'calculation', 'pressure_test']

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

- E-DNV-COOL-003｜direct｜primary
  - 来源：S61 DNV Rules for Classification Ships Pt4 Ch3 Machinery｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, temperature_control_valve, alarm_system｜方面：test, commissioning_check, operation, reliability｜可支撑：test, commissioning_check, operation｜强度：direct｜适用性：general/class_rule
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

- E-SYS-PTEST-001｜indirect｜supporting
  - 来源：S43 ABS Marine Vessel Rules Part 4 2021｜位置：P176｜部件：main_engine_cooling_water_system｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```text
冷却水温度与压力参数
13.1.3 Pressure Tests Turbine casings are to be subjected to pressure test of 1.5 times the highest pressure in the casing during normal operation. Turbine casings may be divided by temporary diaphragms to allow for an even distribution of the test pressures. Where hydrostatic tests are not practicable, alternative tests to determine soundness and workmanship are to be submitted for consideration and approval in each case. Intercoolers and heat exchangers are to be hydrostatically tested on both sides to 1.5 times the design pressure.
整理说明：该证据涉及管系安装后的水压、泄漏或检验要求，可支撑试压和检验类需求。使用时必须保持条款适用范围，不能将其扩展为冷却性能、泵冗余或主机运行参数要求。
可支撑：管系安装后应按适用法规
船级社或项目试验程序进行水压或泄漏试验。
试验压力
持续时间和见证要求应按适用条款或项目文件确认。
不能支撑：1. 不能证明冷却能力、换热能力或正常运行参数满足主机厂家要求。
2. 不能替代项目试验大纲、船级社验船师意见或具体管系等级要求。
3. 不能直接支撑泵冗余、温控逻辑或停机后冷却要求。
```

## R030 项目管理方
冷却水系统的需求、设计、采购、施工、调试和验收资料应保持一致。若主机厂家文件、船级社意见或现场施工条件发生变化，应能追踪受影响的设备、管路、控制逻辑和验证文件。

### R030-01 系统资料一致性管理
冷却水系统的需求、设计、采购、施工、调试和验收资料应保持一致，并建立变更追踪机制。

检索画像：部件=['main_engine_cooling_water_system']；方面=['installation', 'commissioning', 'document_completeness', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。

### R030-02 变更影响追踪
当主机厂家文件、船级社意见或现场施工条件发生变化时，应能追踪受影响的设备、管路、控制逻辑和验证文件。

检索画像：部件=['pipe']；方面=['control', 'installation', 'document_completeness', 'class_approval', 'arrangement', 'capacity', 'flow', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。
