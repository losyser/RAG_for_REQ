# 多粒度证据库审查文件（V2 部件化字段版）

原始证据条目数：2232
Evidence units：2232
Source chunks：1691
Evidence groups：332

## 部件统计
- coolant：408
- expansion_tank：296
- temperature_control_valve：268
- cooling_water_pump：266
- cooler：244
- main_engine_cooling_water_system：158
- pipe：135
- ht_cooling_water_loop：131
- valve：91
- sea_water_cooling_system：65
- jacket_water_cooling_system：39
- lt_cooling_water_loop：30
- alarm_system：21
- temperature_sensor：20
- control_system：16
- central_cooling_system：15
- technical_file：7
- sensor：6
- equipment_interface：5
- level_sensor：4
- pressure_sensor：3
- drain_point：2
- filter：1
- vent_point：1

## 需求方面统计
- temperature：822
- pressure：648
- water_quality：583
- control：496
- installation：438
- flow：345
- cleaning：314
- inspection：313
- corrosion_protection：309
- composition：241
- maintenance：228
- capacity：178
- redundancy：171
- function：128
- drawing_review：126
- arrangement：100
- monitoring：99
- environmental_protection：98
- flushing：81
- alarm：71
- shutdown：53
- calculation：51
- accessibility：37
- material：32
- pressure_test：21
- load_reduction：12
- commissioning：3
- safety：1

## 可支撑类型统计
- parameter_limit：1902
- equipment_selection：1036
- calculation：1036
- operation：542
- installation：526
- maintenance：472
- test：355
- monitoring：328
- inspection：278
- class_review：198
- alarm_protection：121
- document_completeness：110
- system_design：19
- safety：1

## 证据强度统计
- direct：1426
- indirect：760
- background：46

## 适用性等级统计
- manufacturer_specific：2047
- class_rule：139
- background_reference：46

## 过大证据组 Top 30
- G_temperature_control_valve__temperature__detailed_design｜温度控制阀配置｜246 条
- G_coolant__inspection__commissioning｜冷却液水质检测方法｜81 条
- G_ht_cooling_water_loop__composition__detailed_design｜高温冷却水系统组成｜70 条
- G_coolant__water_quality__operation｜冷却液冰点与乙二醇比例｜69 条
- G_cooler__pressure__detailed_design｜冷却水温度与压力参数｜60 条
- G_coolant__water_quality__detailed_design｜冷却液冰点与乙二醇比例｜52 条
- G_cooling_water_pump__capacity__detailed_design｜冷却水流量与泵容量参数｜47 条
- G_expansion_tank__redundancy__detailed_design｜膨胀水箱作用｜47 条
- G_cooling_water_pump__cleaning__detailed_design｜冷却器规格与泵容量参考｜44 条
- G_cooler__installation__detailed_design｜中央冷却器选型要求｜35 条
- G_valve__pressure__detailed_design｜冷却水温度与压力参数｜35 条
- G_coolant__pressure__detailed_design｜冷却水温度与压力参数｜34 条
- G_cooling_water_pump__redundancy__detailed_design｜冷却水泵冗余配置｜28 条
- G_expansion_tank__temperature__detailed_design｜膨胀水箱作用｜26 条
- G_main_engine_cooling_water_system__pressure__detailed_design｜冷却水温度与压力参数｜25 条
- G_pipe__pressure__detailed_design｜冷却水温度与压力参数｜25 条
- G_jacket_water_cooling_system__pressure__detailed_design｜主机冷却型式与设计条件｜24 条
- G_expansion_tank__alarm__detailed_design｜膨胀水箱作用｜23 条
- G_expansion_tank__installation__detailed_design｜膨胀水箱作用｜23 条
- G_main_engine_cooling_water_system__composition__detailed_design｜淡水侧系统组成｜22 条
- G_coolant__cleaning__commissioning｜冷却系统清洗要求｜20 条
- G_main_engine_cooling_water_system__drawing_review__detailed_design｜主机冷却型式与设计条件｜20 条
- G_cooling_water_pump__flow__detailed_design｜冷却水泵配置｜18 条
- G_expansion_tank__flow__detailed_design｜膨胀水箱作用｜18 条
- G_expansion_tank__water_quality__detailed_design｜膨胀水箱作用｜18 条
- G_coolant__water_quality__commissioning｜水质参数要求｜18 条
- G_ht_cooling_water_loop__composition__installation｜高温冷却水系统组成｜18 条
- G_cooling_water_pump__pressure__detailed_design｜冷却水温度与压力参数｜17 条
- G_expansion_tank__inspection__commissioning｜冷却液水质检测方法｜17 条
- G_temperature_sensor__pressure__detailed_design｜冷却水温度与压力参数｜16 条

## 样例 Source Chunks
### CH_S09_MAN_Energy_Solutions_SL2014-584_Cooling_Water_main_engine_cooling_water_system_accessibility_P5
来源：S09 MAN Energy Solutions SL2014-584 Cooling Water System｜P5
部件：main_engine_cooling_water_system
方面：accessibility
证据：E-SYS-ACCESS-001
```text
E-SYS-ACCESS-001 冷却水连接关系
Cooling water system. pages Improved cooling of the O-rings grooves In order to provide improved working conditions for the O-ring, the cooling water access to the O-ring groove has been improved by opening the clearance on the water side of the O-ring, see Fig. 5 below. Fig. 5: Improved cooling water access PrimeServ (PrimeServ-CPH@mandieselturbo.com) will be at your service for assistance for modification of existing components or supply of updated spare parts. S10 MAN L23/30DF Project Guide Internal cooling water system
整理说明：该证据针对 main_engine_cooling_water_system 的 accessibility 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

### CH_S43_ABS_Marine_Vessel_Rules_Part_4_2021_sea_water_cooling_system_alarm_monitoring_P932
来源：S43 ABS Marine Vessel Rules Part 4 2021｜P932
部件：sea_water_cooling_system
方面：alarm, flow, monitoring
证据：E-SW-ALARM-001
```text
E-SW-ALARM-001 传感器与报警配置
13.5.2 Sea Water Main Circulating Pump Where scoop circulation is provided for the main condenser, a low water supply situation is to be alarmed to allow manual starting of the main circulating pump. Alternatively, the pump may be automatically started as vessel speed reduces or as required by the design of the cooling system for satisfactory operation of the propulsion machinery.
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

### CH_S43_ABS_Marine_Vessel_Rules_Part_4_2021_sea_water_cooling_system_alarm_inspection_P867
来源：S43 ABS Marine Vessel Rules Part 4 2021｜P867
部件：sea_water_cooling_system
方面：alarm, inspection, maintenance
证据：E-SW-ALARM-002
```text
E-SW-ALARM-002 冷却系统泄漏检查要求
4-6-5/7.5 for sea chest and 4-6-5/7.7 for two means of circulation. Water-air heat exchangers of rotating propulsion machines for single systems (single generator and single motor), as specified in 4-8-5/5.5.1(b), are to have double wall tubes and be fitted with a leak detector feature to monitor for any water leakage. A visual and audible alarm is to be provided at a normally manned location to indicate detection of such water leakage. 5.17.5(d) Temperature Sensors. Stator windings of AC machines and interpole windings of DC machines, rated above 500 kW, are to be provided with temperature sensors. See 4-9-6/Table 4. 5.17.5(e) Generator Excitation. Excitation current for propulsion generators may be derived from attached rotating exciters, static exciters, excitation motor-generator sets or special purpose
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

### CH_S10_MAN_L23_30DF_Project_Guide_Internal_cooling_wa_main_engine_cooling_water_system_alarm_inspection_P78
来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜P78
部件：main_engine_cooling_water_system
方面：alarm, corrosion_protection, inspection
证据：E-SYS-ALARM-001
```text
E-SYS-ALARM-001 冷却系统泄漏检查要求
Fuel oil leakage is led to a leakage alarm which is heated by means of fuel re- turn oil. The fuel leak oil can be reused and led to the fuel oil tank as it not are mixed with the waste oil. As mentioned above the waste oil is separated from leak oil, and led to the waste oil tank. Internal nozzle cooling system The nozzles of the injection valves on the engines are temperature controlled by means of a circuit containing the engines lubricating oil as media. The system maintains a nozzle surface temperature low enough to prevent formation of carbon trumpets on the nozzle tips during high load operation and high enough to avoid cold corrosion during idling or low-load operation. Lubricating oil system All moving parts of the engine are lubricated with oil circulating under pres- sure.
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

### CH_S36_MAN_L23_30H_GenSet_Project_Guide_main_engine_cooling_water_system_alarm_inspection_P72
来源：S36 MAN L23/30H GenSet Project Guide｜P72
部件：main_engine_cooling_water_system
方面：alarm, corrosion_protection, inspection
证据：E-SYS-ALARM-002
```text
E-SYS-ALARM-002 冷却系统泄漏检查要求
MAN Diesel & Turbo Internal Nozzle Cooling System The nozzles of the injection valves on HFO-engines are temperature controlled by means of a separate circuit containing diesel oil or thermal oil as media. The system maintains a nozzle surface temperature low enough to prevent formation of carbon trumpets on the nozzle tips during high load operation and high enough to avoid cold corrosion during idling or low-load operation. Waste Oil System Waste and leak oil from the comparements, fuel valves is led to a fuel leakage alarm unit. The alarm unit consists of a box with a float switch for level monitoring. In case of a larger than normal leakage, the float switch will initiate alarm. The supply fuel oil to the engine is lead through the unit in order to keep this heated up, thereby ensuring free drain- age passage even for high-viscous waste/leak oil.
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

### CH_S36_MAN_L23_30H_GenSet_Project_Guide_main_engine_cooling_water_system_alarm_inspection_P75
来源：S36 MAN L23/30H GenSet Project Guide｜P75
部件：main_engine_cooling_water_system
方面：alarm, corrosion_protection, inspection
证据：E-SYS-ALARM-003
```text
E-SYS-ALARM-003 冷却系统泄漏检查要求
Internal nozzle cooling system The nozzles of the injection valves on HFO-engines are temperature controlled by means of a circuit from the engines lubricating oil system. The system maintains a nozzle surface temperature low enough to prevent formation of carbon trum- pets on the nozzle tips during high load operation and high enough to avoid cold corrosion during idling or low-load operation. Waste oil system Waste and leak oil from the comparements, fuel valves is led to a fuel leakage alarm unit. The alarm unit consists of a box with a float switch for level monitoring. In case of a larger than normal leakage, the float switch will initiate alarm. The sup- ply fuel oil to the engine is lead through the unit in order to keep this heated up, thereby ensuring free drainage passage even for high-viscous waste/leak oil.
整理说明：原文涉及冷却水相关报警、降负荷、停机或传感器异常处理，可支撑控制保护类需求。阈值和动作逻辑应严格限定在对应厂家、机型和控制系统配置范围内。
可支撑：冷却水温度
压力
液位或传感器异常应按厂家或规则要求设置报警
降负荷或停机保护。
报警阈值和保护动作应受具体厂家
机型和控制系统配置约束。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

### CH_S10_MAN_L23_30DF_Project_Guide_Internal_cooling_wa_main_engine_cooling_water_system_capacity_flow_P191
来源：S10 MAN L23/30DF Project Guide Internal cooling water system｜P191
部件：main_engine_cooling_water_system
方面：capacity, flow, temperature
证据：E-SYS-CAP-001
```text
E-SYS-CAP-001 外部冷却水系统设计原则
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

### CH_S21_Caterpillar_Cooling_Systems_Application_and_In_main_engine_cooling_water_system_capacity_flow_P111
来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜P111
部件：main_engine_cooling_water_system
方面：capacity, composition, flow
证据：E-SYS-CAP-002
```text
E-SYS-CAP-002 冷却水连接关系
ingestion by the pumps. Generally, 110% of the radiator and piping volume is adequate. The tank bottom must be above the engine coolant outlet level. The recommended minimum is 0.6 m (2 ft). The auxiliary pump flow must exceed the engine water pump demand. The recommended minimum is 120% of the nominal engine demand at rated speed. Acceptable venting and deaeration of the engine and external circuit must also be provided.
整理说明：原文给出了冷却水相关参数、阈值或适用条件，可用于对应厂家、机型或规则范围内的参数约束。该证据不应跨系统型式或跨机型直接泛化。
可支撑：main_engine_cooling_water_system 的 capacity
flow
composition 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### CH_S14_Nanni_Marine_Engine_Manual_main_engine_cooling_water_system_capacity_pressure_P68
来源：S14 Nanni Marine Engine Manual｜P68
部件：main_engine_cooling_water_system
方面：capacity, flow, pressure
证据：E-SYS-CAP-003
```text
E-SYS-CAP-003 冷却液更换与加注要求
DRAINING THE COOLANT CIRCUIT 1. Stop the engine and remove the key from the panel. 2. Put a container under the drain plug ( B) to collect coolant. Unscrew the plug and remove the filler cap on top. 3. Drain off all coolant. Empty the recovery container as well as the hoses. 4. Insert a hose into the heat exchanger filler port. Rinse with fresh water until water which flows from the drain port is clean. 5. Reinstall the drain plug, secure it and fill with new coolant as explained on next paragraph.. COOLANT - FILLING Mix the anti-freeze with water in a clean container before filling the heat exchanger. The coolant must be totally free from dust. Fill the exchanger slowly not to introduce air into the coolant system. Refer to the chapter TECHNICAL DATA (Specifications) to know the coolant capacity of the heat exchanger.
整理说明：该证据明确说明泵曲线、额定压力或容量应从厂家 Technical data 或项目指南中确定。它能直接支撑“参数依据”和“选型依据”，但不能直接提供具体压力、容量或流量数值。
可支撑：冷却水泵额定压力
容量或泵曲线应以对应厂家 Technical data 或项目指南为依据。
泵选型和参数确认应结合具体机型技术数据
不应只按通用经验值确定。
不能支撑：1. 不能直接给出具体压力、容量或流量数值。
2. 不能直接支撑泵冗余配置、现场安装空间或停机后冷却持续时间。
3. 不能替代具体机型 Technical data、泵曲线或项目计算书。
```

### CH_S23_CN212654513U_main_engine_cooling_water_system_cleaning_flow_HTML
来源：S23 专利 CN212654513U 船舶主机冷却水系统｜HTML
部件：main_engine_cooling_water_system
方面：cleaning, flow, temperature
证据：E-SYS-CLEAN-002
```text
E-SYS-CLEAN-002 热交换器脉冲清洗装置
请参照图1所示，船舶主机冷却水系统包括热交换器1和脉冲清洗装置，热交换器1的一端分别设有淡水入口2和海水出口3，热交换器1的另一端分别设有淡水出口4和海水入口5，淡水入口2分别连通主机的冷却水出口、辅机的冷却水出口和柴油发电机的冷却水出口，冷却水从船舶的主机、辅机和柴油发动机出来后通过淡水入口2流入热交换器1，淡水出口4通过水管连接有水箱6，水箱6的底部通过水管连接有淡水泵7，淡水泵7的出水口分别连接主机的冷却水入口、辅机的冷却水入口和柴油发电机的冷却水入口，冷却水经过热交换器1降温后从淡水出口4进入水箱6，再由淡水泵7重新供入船舶的主机、辅机以及柴油发动机中对其进行冷却，海水入口5通过水管连接有海水泵8，海水泵8的出水口通过水管延伸到船舶底部并连通海水，海水出口3通过水管连接到船舷外。主机、辅机和柴油发电机中的冷却水分别对主机、辅机和柴油发电机进行冷却后，温度升高，然后从淡水入口2进入热交换器1进行降温后回到水箱6，再被淡水泵7供入主机、辅机和柴油发电机对其进行冷却，循环使用。海水泵8将冷海水从海水入口5供入热交换器1，带走热交换器1的热量，对热交换器1中的淡水进行降温，再从海水出口3出来排回大海中。 脉冲清洗装置包括脉冲喷射设备9、空气压缩设备10和高压水泵11，高压水泵11的抽水口通过水管延伸到船舶底部并连通海水，高压水泵11的出水口通过水管连通空气压缩设备10，空气压缩设备10的出口通过水管连接脉冲喷射设备9的入口，脉冲喷射设备9的喷射口通过水管连通海水入口5，脉冲喷射设备9与海水入口5之间的水管的轴线与海水入口5的轴线重合，使得脉冲喷射设备9喷射出来的气液体混合体能够笔直的进入海水入口5。脉冲喷射设备9与海水入口5之间的水管中设有第一阀门16，海水入口5与海水泵8之间的水管中设有第二阀门17。脉冲喷射设备9将空气压缩设备10和高压水泵11制成的气液混合体通入到热交换器1的海水管道中，利用气水脉冲过程中产生的空穴原理和水锤现象对管内壁进行冲击和振动，实现快速将管壁上的污垢和管内的存积物清洗下来并排出热交换器1之外。
整理说明：原文提供的是方案结构、研究背景或技术原理说明，可用于理解相关组件和可能的工程做法。由于来源不属于通用规范或厂家强制要求，该证据不宜单独转化为工程强制条款。
可支撑：冷却水系统
换热器或相关管路的清洗
冲洗和复查应按来源文件或项目维护程序执行。
清洗后重新投运前应关注残留清洗剂
泄漏
沉积物或换热能力恢复情况。
不能支撑：1. 不能单独作为通用工程强制要求。
2. 不能替代船级社规则、法规、厂家手册或项目设计文件。
3. 不能直接外推到其他厂家、机型或系统型式。
```

### CH_S21_Caterpillar_Cooling_Systems_Application_and_In_sea_water_cooling_system_cleaning_flow_P54
来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜P54
部件：sea_water_cooling_system
方面：cleaning, flow, temperature
证据：E-SW-CLEAN-001
```text
E-SW-CLEAN-001 冷却液污染与沉积风险
will affect the heat transfer of a heat exchanger. Factors for common types of water can be found in Table 4. The fouling factor relationship is: FF = [(1/UCoolant) – (1/UClean Core)] Where: FF = Fouling factor, hr-m 2-°C/kJ (hr- ft2-°F/Btu) UCoolant = Heat Transfer Coefficient of core with coolant, kJ/hr-m2-°C (Btu/hr-ft2 °F) UClean Core = Heat Transfer Coefficient of clean core kJ/hr-m 2-°C (Btu/hr-ft2 °F) Fouling Factor Chart for Water (hr-ft2-°F/Btu) Engine Coolant Temperature < 116°C (240°F) Raw Water Temperature < 52°C (125°F) Raw Water Velocity Water Types ≤0.9 m/s (3 ft/sec) >0.9 m/s (3 ft/sec) Seawater 0.0005 0.0005 Brackish Water 0.002 0.001 Cooling Tower and Artificial Spray Pond: Treated Makeup Spray Pond: Untreated 0.001 0.003 0.001 0.003 City or Well Water (such as Great Lakes) 0.001 0.001 River Water 0.003 0.003 Hard (over 15 grains/gal) 0.003 0.003
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

### CH_S43_ABS_Marine_Vessel_Rules_Part_4_2021_sea_water_cooling_system_cleaning_P615
来源：S43 ABS Marine Vessel Rules Part 4 2021｜P615
部件：sea_water_cooling_system
方面：cleaning
证据：E-SW-CLEAN-002
```text
E-SW-CLEAN-002 冷却水连接关系
7.7.2 Strainers Where sea water is used for direct cooling of the engines, suitable strainers are to be fitted between the sea valve and the pump suction. The strainers are to be either of the duplex type or arranged such that they can be cleaned without interrupting the cooling water supply. This applies also to engines fitted with indirect cooling, where direct sea water cooling is used as an emergency means of cooling.
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

### CH_S21_Caterpillar_Cooling_Systems_Application_and_In_jacket_water_cooling_system_cleaning_capacity_P136
来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜P136
部件：jacket_water_cooling_system
方面：capacity, cleaning, flow
证据：E-JACKET-CLEAN-001
```text
E-JACKET-CLEAN-001 冷却液污染与沉积风险
Jacket Water Cooling Circuit Worksheet Sheet 3 of 3 3. Allowable External Restriction From the graph of External Restriction vs. Coolant Flow for the Jacket Water Circuit, find the maximum allowable restriction for the flow calculated in step 2. Maximum Allowable External Restriction for Jacket Water Cooling Circuit: ____________________ m H2O or ft H2O 4. Jacket Water Circuit Sizing (Radiator, Heat Exchanger or other cooling device) Add an additional external circuit system tolerance to the Total Heat Rejection with Tolerance value calculated in step 1 to account for system fouling or degradation. This additional tolerance should be 1% to 10%, depending on the cooling system used and operating conditions. Total Heat Rejection with Tolerance x (1.01 to 1.10) = Jacket Water Circuit Heat Rejection
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

### CH_S44_PRS_Ship_Machinery_Piping_Systems_sea_water_cooling_system_cleaning_material_P198
来源：S44 PRS Ship Machinery Piping Systems｜P198
部件：sea_water_cooling_system
方面：cleaning, material
证据：E-SW-CLEAN-003
```text
E-SW-CLEAN-003 冷却液污染与沉积风险
11.2.5 Internal seawater cooling systems shall be designed and made of an appropriate material to minimize biofouling and constructed with a minimum of bends, kinks and flanges in seawater piping in accordance with the guidance contained in IMO Resolution MEPC.207(62).
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

### CH_S29_Caterpillar_Know_Your_Cooling_System_main_engine_cooling_water_system_cleaning_corrosion_protection_P55
来源：S29 Caterpillar, Know Your Cooling System｜P55
部件：main_engine_cooling_water_system
方面：cleaning, composition, corrosion_protection
证据：E-SYS-CLEAN-004
```text
E-SYS-CLEAN-004 冷却液污染与沉积风险
Scale or rust in a cooling system can affect heat transfer. The scale and rust can be cleaned out of the cooling system with a two step type heavy duty radiator cleaner. This cleaner consists of an oxalic acid, which cleans the scale and rust, and a neutralizer. Two step type heavy duty cleaners are available from industrial supply outlets or they can be mixed as follows: Acid - Mix 900 g (2 lb) of sodium bisulfate (NaHS0 per 38 liters (10 gal) of water (25 grams per liter). Neutralizer - Mix 225 g (1/2 lb) of sodium carbonate crystals Na2CO3 per 38 liters (10 gal) of water (6 grams per liter). The cooling system may also be cleaned with Caterpillar Cooling System Cleaners. These are designed to clean the system of harmful scale and corrosion without taking the engine out of service. It can be used in all Caterpillar Engines' and other manufacturers' cooling systems in any application.
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

### CH_S32_HY_T_sea_water_cooling_system_cleaning_maintenance_P13
来源：S32 HY/T 海水循环冷却系统运行管理规范｜P13
部件：sea_water_cooling_system
方面：cleaning, corrosion_protection, maintenance
证据：E-SW-CLEAN-005
```text
E-SW-CLEAN-005 热交换器清洁与维护
9.1.1 当海水循环冷却系统采用表面式水冷凝汽器作为换热设备时，凝汽器海水侧的运行管理还应满 足以下要求： a) 冷却管内表面无明显结垢，清洁状态良好； b) 传热端差在设计范围内； c) 水室排气顺畅； d) 管板处无杂物积聚； e) 水室内无海生物生长及附着； f) 水室内壁防腐层应完好。
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

### CH_S36_MAN_L23_30H_GenSet_Project_Guide_central_cooling_system_composition_P183
来源：S36 MAN L23/30H GenSet Project Guide｜P183
部件：central_cooling_system
方面：composition
证据：E-CENTRAL-COMP-003
```text
E-CENTRAL-COMP-003 中央冷却系统总体组成
is closed. Thus the propulsion engine is heated from top and downwards, which is the most eco- nomic solution. MAN Diesel & Turbo B 13 00 0 One string central cooling water system 1624464-1.2 L32/40, L23/30H, L28/32H, L28/32DF 2011.02.21
整理说明：原文说明系统组成、部件功能或连接关系，可用于确定系统边界和组件对象。该类证据通常不能直接支撑参数限值、施工验收或试验判据。
可支撑：可支撑 central_cooling_system 在 composition 方面的系统设计
运行或维护依据。
具体指标和验收条件应结合来源文件适用范围进一步确认。
不能支撑：1. 不能超出来源文件限定的适用对象和工况范围泛化。
2. 不能直接生成原文未给出的具体数值、持续时间或验收判据。
3. 不能替代更高权威等级的规范、厂家技术数据或项目文件。
```

### CH_S36_MAN_L23_30H_GenSet_Project_Guide_central_cooling_system_composition_flow_P185
来源：S36 MAN L23/30H GenSet Project Guide｜P185
部件：central_cooling_system
方面：composition, flow, temperature
证据：E-CENTRAL-COMP-004
```text
E-CENTRAL-COMP-004 中央冷却系统总体组成
circulate the necessary flow of water for the air cooler, the lubricating oil cooler, and the jacket cooler of the auxiliary engines. The auxiliary engine- driven pumps and the integrated loop mentioned above ensure a satisfactory jacket cooling water temperature at the auxiliary engine outlet. The main engine is preheated as described for the jacket water system, fig. 1. MAN Diesel & Turbo B 13 00 0 Central cooling system 1631482-0.0 L23/30H, L28/32H, L28/32DF, L23/30DF
整理说明：原文给出了冷却水相关参数、阈值或适用条件，可用于对应厂家、机型或规则范围内的参数约束。该证据不应跨系统型式或跨机型直接泛化。
可支撑：central_cooling_system 的 composition
flow
temperature 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```

### CH_S36_MAN_L23_30H_GenSet_Project_Guide_central_cooling_system_composition_cleaning_P5
来源：S36 MAN L23/30H GenSet Project Guide｜P5
部件：central_cooling_system
方面：cleaning, composition
证据：E-CENTRAL-COMP-005
```text
E-CENTRAL-COMP-005 中央冷却系统总体组成
Cooling water system cleaning B 13 00 0 010.000.002-04 Water specification for fuel-water emulsions B 13 00 0 010.000.023-16 Internal cooling water system B 13 00 0 1613439-3.2 Internal cooling water system 1 B 13 00 1 1613575-7.4 Internal cooling water system 2 B 13 00 2 1613576-9.3 Design data for external cooling water system B 13 00 0 1613441-5.5 External cooling water system B 13 00 0 1613442-7.0 One string central cooling water system B 13 00 1 1624464-1.2 Central cooling system B 13 00 0 1631482-0.0 Seawater cooling system B 13 00 3 1631480-7.0 Jacket water cooling system B 13 00 0 1631481-9.1
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

### CH_S39_MAN_L21_31_Project_Guide_central_cooling_system_composition_control_P527
来源：S39 MAN L21/31 Project Guide｜P527
部件：central_cooling_system
方面：capacity, composition, control
证据：E-CENTRAL-COMP-007
```text
E-CENTRAL-COMP-007 中央冷却系统总体组成
The second stage of the charge air cooler is placed in the low temperature sys- tem. It will cool the charging air further down before entering the combustion chamber. For special applications i.e. sailing in arctic waters with low air temperatures and direct air intake from deck, a regulating system can be applied to control the water flow to the second stage of the charge air cooler in order to increase the charging air temperature, at low load. Velocity recommendations for freshwater and sea water pipes: Freshwater Suction pipe: 1.0 - 2.0 m/s Delivery pipe: 2.0 - 3.5 m/s Sea water Suction pipe: 1.0 - 1.5 m/s Delivery pipe: 1.5 - 2.5 m/s Central cooling water system Sea water filter, item 3 Design data: Capacity: See sea water pump 2016-09-29 - en
整理说明：原文说明了参数来源、设计依据或相关设备关系，但没有给出可直接采用的具体数值。它适合支撑参数确认路径，而不是直接替代技术数据或计算书。
可支撑：central_cooling_system 的 composition
control
capacity 参数应依据来源文件
厂家技术数据或项目计算文件确定。
若原文给出明确限值
可作为对应适用对象和工况下的参数约束。
不能支撑：1. 不能直接给出可用于设计输入的具体数值。
2. 不能超出来源文件限定的厂家、机型、系统型式或工况范围泛化。
3. 不能直接支撑施工安装、冲洗试压或图纸送审完整性要求。
```
