# 需求证据包（V2 工程字段版）

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

- E-PIPE-PTEST-AUTH-001｜direct｜primary
  - 来源：46 CFR 56.97-40 Installation tests｜位置：§56.97-40｜部件：pipe｜方面：pressure_test, inspection, reliability｜可支撑：test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能证明冷却水系统换热能力或主机运行参数满足要求。
2. 不能替代项目船级社规则、试验大纲或具体管系等级确认。
3. 不能直接支撑泵冗余、温控阀控制逻辑或停机后冷却要求。
```text
Installation tests
hydrostatic leak test of 1 1/2 times the maximum allowable working pressure; conducted in the presence of a marine inspector.
整理说明：该条款可作为管系安装后水压泄漏试验和验船师见证要求的法规级依据。用于主机冷却水系统时，必须先确认该系统是否落入 Part 56 适用范围。
可支撑：管系安装后泄漏试验应按适用法规或船级社要求确定试验压力和见证要求。
对属于 46 CFR Part 56 范围的管系
可将 1.5 倍最大允许工作压力作为法规核验依据。
不能支撑：1. 不能证明冷却水系统换热能力或主机运行参数满足要求。
2. 不能替代项目船级社规则、试验大纲或具体管系等级确认。
3. 不能直接支撑泵冗余、温控阀控制逻辑或停机后冷却要求。
```

- E-PIPE-PTEST-012｜direct｜primary
  - 来源：S47 46 CFR 58.20-25 Tests｜位置：58.20-25(a)；source_url=https://www.ecfr.gov/current/title-46/chapter-I/subchapter-F/part-58/subpart-58.20/section-58.20-25｜部件：pipe｜方面：pressure_test, inspection, reliability｜可支撑：parameter_limit, equipment_selection, calculation, test｜强度：direct｜适用性：limited/class_rule
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

- E-PIPE-PTEST-AUTH-002｜direct｜primary
  - 来源：46 CFR 56.97-30 Hydrostatic tests｜位置：§56.97-30｜部件：pipe｜方面：pressure_test, inspection｜可支撑：test, inspection, class_review｜强度：direct｜适用性：limited/class_rule
  - 不能支撑：1. 不能直接支撑冷却水流量、压力运行值或换热能力。
2. 不能替代项目试验程序中的安全隔离、盲板、排气和记录要求。
3. 不能外推为所有非 USCG 船舶的强制条款。
```text
Hydrostatic tests
hydrostatic test pressure must be maintained for a minimum of 10 minutes.
整理说明：该条款为管系水压试验保持时间提供法规级依据，可补充试压章节的证据强度。它仍需与具体管系类别、材料和项目要求结合使用。
可支撑：管系水压试验应按适用法规或项目程序规定保持足够时间。
若适用 Part 56
可将 10 分钟作为法规核验点之一。
不能支撑：1. 不能直接支撑冷却水流量、压力运行值或换热能力。
2. 不能替代项目试验程序中的安全隔离、盲板、排气和记录要求。
3. 不能外推为所有非 USCG 船舶的强制条款。
```

### R029-02 支架与阀门安装
冷却水系统支架应固定牢固，阀门方向应正确。

检索画像：部件=['main_engine_cooling_water_system', 'valve', 'support', 'pipe', 'equipment_interface', 'flushing_connection', 'pressure_test_connection']；方面=['installation', 'arrangement', 'accessibility', 'flushing', 'pressure_test', 'inspection']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

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

- E-SUPP-MAINT-001｜indirect｜secondary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
Marine Machinery Installation — Maintenance Access and Clearance Requirements
(Based on DNV Rules for Classification: Ships, Pt.4 Ch.1, IACS UR M3, ISO 14122-3, and standard marine engineering practice)

Maintenance and accessibility requirements for cooling water system components:
1. All major cooling water equipment (pumps, heat exchangers, temperature control valves, strainers) shall have sufficient clearance for routine maintenance and component removal without disturbing adjacent equipment.
2. Recommended minimum clearances:
   - Pump: axial clearance ≥ 1.5× pump casing length for impeller/shaft removal; radial clearance ≥ shaft diameter + 100 mm
   - Plate heat exchanger / tube bundle: full plate/tube bundle pull-out length on one side
   - Valve handwheel/actuator: minimum 600 mm operating side clearance
3. Walkway minimum clear width: 600 mm where personnel pass through; 500 mm where inspection only
4. Overhead lifting provisions (pad eye or monorail) shall be provided for equipment with removal mass > 25 kg
5. All equipment requiring periodic maintenance shall have clear nameplates with maintenance interval and tag number
整理说明：冷却水系统设备维护间距要求（DNV/IACS/ISO 14122-3）：泵轴向间距≥1.5倍泵长，板式换热器需留全板束抽出空间；通道宽度≥600mm；>25kg设备须有吊装点；设备须有维护标牌。
```

### R029-03 传感器与设备接口安装
冷却水系统传感器安装应正确，设备接口应连接可靠。

检索画像：部件=['main_engine_cooling_water_system', 'equipment_interface', 'pipe', 'valve', 'support', 'flushing_connection', 'pressure_test_connection']；方面=['reliability', 'installation', 'arrangement', 'accessibility', 'flushing', 'pressure_test', 'inspection']；可支撑=['installation', 'arrangement', 'inspection', 'test', 'flushing', 'pressure_test']

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

- E-SUPP-MAINT-001｜indirect｜secondary
  - 来源：S72 DNV Rules Pt4 Ch1 Machinery Space Access Requirements｜位置：｜部件：cooling_water_pump, cooler, temperature_control_valve, main_engine_cooling_water_system｜方面：installation, maintenance, arrangement, inspection｜可支撑：installation, maintenance, arrangement, inspection｜强度：direct｜适用性：general/class_rule
```text
Marine Machinery Installation — Maintenance Access and Clearance Requirements
(Based on DNV Rules for Classification: Ships, Pt.4 Ch.1, IACS UR M3, ISO 14122-3, and standard marine engineering practice)

Maintenance and accessibility requirements for cooling water system components:
1. All major cooling water equipment (pumps, heat exchangers, temperature control valves, strainers) shall have sufficient clearance for routine maintenance and component removal without disturbing adjacent equipment.
2. Recommended minimum clearances:
   - Pump: axial clearance ≥ 1.5× pump casing length for impeller/shaft removal; radial clearance ≥ shaft diameter + 100 mm
   - Plate heat exchanger / tube bundle: full plate/tube bundle pull-out length on one side
   - Valve handwheel/actuator: minimum 600 mm operating side clearance
3. Walkway minimum clear width: 600 mm where personnel pass through; 500 mm where inspection only
4. Overhead lifting provisions (pad eye or monorail) shall be provided for equipment with removal mass > 25 kg
5. All equipment requiring periodic maintenance shall have clear nameplates with maintenance interval and tag number
整理说明：冷却水系统设备维护间距要求（DNV/IACS/ISO 14122-3）：泵轴向间距≥1.5倍泵长，板式换热器需留全板束抽出空间；通道宽度≥600mm；>25kg设备须有吊装点；设备须有维护标牌。
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

- E-SYS-CLEAN-001｜indirect｜secondary
  - 来源：S21 Caterpillar Cooling Systems Application and Installation Guide｜位置：P116｜部件：main_engine_cooling_water_system｜方面：cleaning, installation, monitoring, configuration｜可支撑：installation, maintenance, test, inspection｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却液污染与沉积风险
accurate set-up and performance documentation of the cooling system during the commissioning procedure. Future system problems or component deterioration (such as fouling) are easier to identify if basic data is available. It also provides information for relating field conditions to original factory tests. Temperature and pressure measurement locations should give accurate reading of fluid stream conditions. Preferred locations are in straight lengths of piping reasonably close to each system component. Avoid pressure measurements in bends, piping transition pieces or turbulent regions. Plan to install monitoring ports during the design and construction of the cooling system. If the ports are installed later, ensure the pipes are cleaned of drill chips and weld slag after the pressure ports are installed.
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

- E-PIPE-INST-003｜indirect｜secondary
  - 来源：S28 Wärtsilä 32 Product Guide, Cooling Water System｜位置：P39｜部件：pipe｜方面：installation, material, configuration｜可支撑：installation｜强度：direct｜适用性：limited/manufacturer_specific
  - 不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```text
冷却水系统材料限制
5. Piping Design, Treatment and Installation This chapter provides general guidelines for the design, construction and planning of piping systems, however, not excludingother solutionsof at least equal standard. Installationrelated instructionsare included in the project specific instructions delivered for each installation. Fuel, lubricating oil, fresh water and compressed air piping is usually made in seamless carbon steel (DIN 2448) and seamless precision tubes in carbon or stainless steel (DIN 2391), exhaust gas piping in welded pipes of corten or carbon steel (DIN 2458). Sea-water piping should be in Cunifer or hot dip galvanized steel. NOTE! The pipes in the freshwater side of the cooling water system must not be galvanized! Attention must be paid to fire risk aspects.
整理说明：该证据针对 pipe 的 installation / material 方面提供原文依据，可支撑相应的设计、运行、维护或审查判断；其支撑范围应受来源类型、适用对象和原文明确条件限制。
可支撑：冷却水系统布置应考虑来源文件提出的安装
操作或维护可达性原则。
具体施工空间
支架
接口和验收要求仍应由项目安装规范确认。
不能支撑：1. 不能直接给出焊接空间、操作空间、支架间距、冲洗接口或试压接口的具体要求。
2. 不能替代船厂施工规范、管系布置标准或安装验收程序。
3. 不能直接支撑冷却水温度、压力和流量参数限值。
```

### R029-04 标识与试验记录验证
冷却水系统标识应完整，试验记录应齐全，发现问题应在交船前整改并闭环。

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

- E-SUPP-COMM-001｜direct｜primary
  - 来源：S82 Marine Cooling System Pre-Commissioning Checklist CCS DNV IACS｜位置：｜部件：main_engine_cooling_water_system, cooling_water_pump, expansion_tank, temperature_control_valve, alarm_system, pipe, temperature_sensor, pressure_sensor, level_sensor｜方面：commissioning_check, inspection, test, operation, document_completeness, reliability｜可支撑：commissioning_check, inspection, test, operation, document_completeness｜强度：direct｜适用性：general/general
```text
Marine Cooling Water System — Pre-Commissioning Checklist and Acceptance Criteria
(Consolidated from CCS 调试要求, DNV Rules Pt.4 Ch.3, IACS UR M51, and standard shipyard commissioning practice)

Pre-commissioning verification (must be signed off before first engine start):
□ All cooling water pipelines installed per approved drawings; all weld NDE and pressure test records complete and accepted by class surveyor
□ All cooling water isolating valves installed with correct flow direction; valve position indicators fitted and correct
□ Expansion tank filled to correct operating level (50–75%); vent valve opened; filling connection capped; low-level alarm tested
□ Coolant: concentration tested and within specification; inhibitor added per manufacturer; pH within range; chloride below limit
□ System fully vented; no air pockets at high points; vent cocks closed
□ Pump rotation correct; mechanical seals not leaking; pump bearings lubricated
□ All temperature, pressure, and level transmitters calibrated; readings match independent reference gauges
□ All high-temperature, low-pressure, low-level alarms tested at correct set-points; alarms annunciated at engine control room AND bridge
□ TCV: position sensor calibrated; valve opens/closes correctly on temperature signal; manual override tested
□ Standby pump automatic start tested: pump starts on duty pump failure signal
□ Post-flush: strainer baskets inspected clean; temporary flushing connections removed
□ Insulation applied to all hot pipes; safety warning signs affixed

Post-commissioning documents required:
- Signed commissioning c
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

## R030 项目管理方
冷却水系统的需求、设计、采购、施工、调试和验收资料应保持一致。若主机厂家文件、船级社意见或现场施工条件发生变化，应能追踪受影响的设备、管路、控制逻辑和验证文件。

### R030-01 冷却水系统全生命周期资料一致性
冷却水系统的需求、设计、采购、施工、调试和验收资料应保持一致，确保各阶段文档可追溯。

检索画像：部件=['main_engine_cooling_water_system']；方面=['installation', 'commissioning', 'document_completeness', 'arrangement', 'capacity', 'flow', 'control', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。

### R030-02 变更影响追踪
当主机厂家文件、船级社意见或现场施工条件发生变化时，应能追踪受影响的设备、管路、控制逻辑和验证文件。

检索画像：部件=['pipe']；方面=['control', 'installation', 'document_completeness', 'class_approval', 'arrangement', 'capacity', 'flow', 'redundancy', 'reliability']；可支撑=['system_design', 'equipment_selection', 'arrangement', 'redundancy']

> 证据缺口：有候选证据，但均未达到直接或间接支撑标准。
> 建议补充：补充更直接的标准条款、厂家手册、试验记录或设计说明。
