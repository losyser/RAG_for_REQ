# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
import time
import warnings
from html import escape
from pathlib import Path
from typing import Any

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=r".*Accessing `__path__`.*")

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_pack import make_batch_dir, save_pack
from cooling_rag_mg.pipeline import make_services, run_requirements_with_services
from cooling_rag_mg.engineering_requirement_agent import (
    generate_engineering_requirements,
    save_engineering_requirements,
)


DEFAULT_REQUIREMENTS = [
    {
        "需求编号": "R001",
        "提出方": "船东代表",
        "需求内容": "主机冷却水系统首先要可靠，不能一到高负荷或者海区温度高的时候就出问题。我们更关心船能不能长期稳定跑，不希望因为冷却水系统影响航行计划。",
        "启用": True,
    },
    {
        "需求编号": "R002",
        "提出方": "船东代表",
        "需求内容": "系统配置不要太省，也不要做得太复杂。希望设备数量、备用能力和后期维护成本之间能平衡一下，不要以后运营起来很麻烦。",
        "启用": True,
    },
    {
        "需求编号": "R003",
        "提出方": "船东代表",
        "需求内容": "主机冷却相关设备最好选成熟可靠的型号，别用太冷门的产品。后期备件、维修和厂家服务都要方便一些。",
        "启用": True,
    },
    {
        "需求编号": "R004",
        "提出方": "船东代表",
        "需求内容": "冷却水系统的能耗也要考虑，尤其是长期航行时水泵一直运行。希望在保证冷却效果的前提下，不要造成明显的能源浪费。",
        "启用": True,
    },
    {
        "需求编号": "R005",
        "提出方": "船东代表",
        "需求内容": "系统出现一般故障时，最好不要马上影响主机运行。至少要给船员一定处理时间，能够切换备用设备或者采取临时措施。",
        "启用": True,
    },
    {
        "需求编号": "R006",
        "提出方": "船东代表",
        "需求内容": "冷却水系统的设计资料、厂家资料和后期交付文件要清楚。船交付以后，船员和管理公司要能看懂系统怎么运行、怎么维护。",
        "启用": True,
    },
    {
        "需求编号": "R007",
        "提出方": "主机厂家",
        "需求内容": "主机进出口冷却水温度、压力和流量不能随便定，必须结合主机型号、负荷范围和厂家技术文件确认。否则可能影响主机性能和寿命。",
        "启用": True,
    },
    {
        "需求编号": "R008",
        "提出方": "主机厂家",
        "需求内容": "高温水和低温水回路的参数要区分清楚，不要把不同冷却用户混在一起考虑。主机本体、增压空气冷却器和滑油冷却器的要求可能不一样。",
        "启用": True,
    },
    {
        "需求编号": "R009",
        "提出方": "主机厂家",
        "需求内容": "主机启动、加速、低负荷和停机后的冷却过程都要考虑。不能只按一个稳定工况算完就认为系统没问题。",
        "启用": True,
    },
    {
        "需求编号": "R010",
        "提出方": "主机厂家",
        "需求内容": "温控阀的设定和动作范围要和主机冷却要求匹配。温度控制太慢或者波动太大，都会影响主机运行状态。",
        "启用": True,
    },
    {
        "需求编号": "R011",
        "提出方": "主机厂家",
        "需求内容": "冷却水水质不能忽视，特别是防腐、防垢和杂质控制。如果水质长期不好，后面可能会影响主机内部冷却通道。",
        "启用": True,
    },
    {
        "需求编号": "R012",
        "提出方": "主机厂家",
        "需求内容": "主机冷却水报警和保护值应与厂家建议保持一致。报警点不能设得太随意，也不能和主机控制系统的保护逻辑冲突。",
        "启用": True,
    },
    {
        "需求编号": "R013",
        "提出方": "系统设计方",
        "需求内容": "冷却水系统的边界要画清楚，哪些属于高温水回路，哪些属于低温水回路，哪些属于海水侧，图纸上应该能看明白。",
        "启用": True,
    },
    {
        "需求编号": "R014",
        "提出方": "系统设计方",
        "需求内容": "系统不能只画管子和设备，还要说明主要流向、控制关系和设备之间的接口。不然后面采购、施工和调试容易理解不一致。",
        "启用": True,
    },
    {
        "需求编号": "R015",
        "提出方": "系统设计方",
        "需求内容": "冷却水泵和冷却器选型要有计算依据。不能只根据以往项目经验直接套用，至少要说明流量、扬程、换热量和裕量是怎么来的。",
        "启用": True,
    },
    {
        "需求编号": "R016",
        "提出方": "系统设计方",
        "需求内容": "管路压力损失要大致核算清楚，特别是长距离管路、阀件较多的位置和冷却器前后。不能等调试时才发现流量不够。",
        "启用": True,
    },
    {
        "需求编号": "R017",
        "提出方": "系统设计方",
        "需求内容": "膨胀水箱的位置、容量和连接方式要合理。系统排气、补水和液位监测都要能正常实现。",
        "启用": True,
    },
    {
        "需求编号": "R018",
        "提出方": "系统设计方",
        "需求内容": "冷却水系统和主机、发电机组、空压机、滑油冷却器等其他设备的接口要统一确认，避免接口尺寸、压力等级或参数对不上。",
        "启用": True,
    },
    {
        "需求编号": "R019",
        "提出方": "系统设计方",
        "需求内容": "备用泵、备用冷却器和旁通管路的设置要结合船级要求和实际运行需求确定。不要只为了图纸完整而设置，也不要缺少必要备用。",
        "启用": True,
    },
    {
        "需求编号": "R020",
        "提出方": "系统设计方",
        "需求内容": "系统图、布置图、设备表和控制说明之间要一致。尤其是阀门编号、传感器位置和设备名称，不能各文件写法不同。",
        "启用": True,
    },
    {
        "需求编号": "R021",
        "提出方": "船厂建造方",
        "需求内容": "冷却水管路布置要考虑现场施工，不能图上看着能走，现场根本不好焊接、吊装或者安装支架。",
        "启用": True,
    },
    {
        "需求编号": "R022",
        "提出方": "船厂建造方",
        "需求内容": "阀门和滤器的位置要尽量放在人员能操作的地方。不要布置在很高、很窄或者被其他设备挡住的位置。",
        "启用": True,
    },
    {
        "需求编号": "R023",
        "提出方": "船厂建造方",
        "需求内容": "冷却器、水泵和膨胀水箱的安装空间要提前考虑。设备不能到货后才发现基础、管口或者检修方向不合适。",
        "启用": True,
    },
    {
        "需求编号": "R024",
        "提出方": "船厂建造方",
        "需求内容": "管路高点和低点要方便排气和放水。现场最怕系统试压、冲洗或者调试时有气排不出去，水又放不干净。",
        "启用": True,
    },
    {
        "需求编号": "R025",
        "提出方": "船厂建造方",
        "需求内容": "管路支架和固定方式要明确，特别是泵进出口、冷却器附近和振动比较明显的位置。不能只靠现场临时处理。",
        "启用": True,
    },
    {
        "需求编号": "R026",
        "提出方": "船厂建造方",
        "需求内容": "设计变更最好及时同步给施工现场。如果冷却水管路已经预制或者已经安装，再改接口和走向会比较麻烦。",
        "启用": True,
    },
    {
        "需求编号": "R027",
        "提出方": "船厂建造方",
        "需求内容": "冷却水系统的管路标识、流向标识和阀门铭牌要清楚。后期试验、交船和船员接收时都要用到。",
        "启用": True,
    },
    {
        "需求编号": "R028",
        "提出方": "船厂建造方",
        "需求内容": "海水侧管路和淡水侧管路材料、连接方式和防腐要求不要混淆。现场施工时需要清楚知道哪些地方要求更严格。",
        "启用": True,
    },
    {
        "需求编号": "R029",
        "提出方": "设备采购方",
        "需求内容": "冷却水泵、冷却器、温控阀、滤器和传感器的采购参数要尽量完整。只写一个设备名称，很难准确询价和比价。",
        "启用": True,
    },
    {
        "需求编号": "R030",
        "提出方": "设备采购方",
        "需求内容": "厂家报价资料要和设计要求对得上，尤其是流量、压力、温度、材料、接口标准和电源要求，不能后面才发现型号不合适。",
        "启用": True,
    },
    {
        "需求编号": "R031",
        "提出方": "设备采购方",
        "需求内容": "关键设备最好明确是否需要船级社认可或者产品证书。如果采购阶段没确认，后面验船时可能会影响交付。",
        "启用": True,
    },
    {
        "需求编号": "R032",
        "提出方": "设备采购方",
        "需求内容": "同类阀门、仪表和备件尽量统一规格和厂家。后期采购、库存和维护都会方便一些。",
        "启用": True,
    },
    {
        "需求编号": "R033",
        "提出方": "设备采购方",
        "需求内容": "设备交货周期要和船厂建造节点匹配。冷却器、水泵和温控阀如果到货太晚，会影响管路安装和系统调试。",
        "启用": True,
    },
    {
        "需求编号": "R034",
        "提出方": "设备采购方",
        "需求内容": "供应商提供的图纸、接口尺寸和技术资料要及时返回设计方确认。不能只等设备到厂后再核对接口。",
        "启用": True,
    },
    {
        "需求编号": "R035",
        "提出方": "轮机长",
        "需求内容": "船员平时看系统状态要方便，温度、压力、液位、泵状态和报警信息最好在集控室能看得比较清楚。",
        "启用": True,
    },
    {
        "需求编号": "R036",
        "提出方": "轮机长",
        "需求内容": "现场的压力表、温度表和液位显示不要太少。只靠远程显示不够，现场巡检时也要能判断系统有没有异常。",
        "启用": True,
    },
    {
        "需求编号": "R037",
        "提出方": "轮机长",
        "需求内容": "泵组切换要方便，最好不要每次切换都要操作很多阀门。紧急情况下，船员需要比较快地恢复冷却能力。",
        "启用": True,
    },
    {
        "需求编号": "R038",
        "提出方": "轮机长",
        "需求内容": "报警不能太乱。温度稍微波动就频繁报警，船员会很难判断到底是不是严重问题。",
        "启用": True,
    },
    {
        "需求编号": "R039",
        "提出方": "轮机长",
        "需求内容": "冷却水系统要便于日常排气、补水、取样和加药。不要每次做这些操作都要拆东西或者进入很难到达的位置。",
        "启用": True,
    },
    {
        "需求编号": "R040",
        "提出方": "轮机长",
        "需求内容": "系统说明书和操作指导要贴近实际。船员更需要知道异常时怎么判断、怎么切换、什么时候需要降负荷或联系岸基支持。",
        "启用": True,
    },
    {
        "需求编号": "R041",
        "提出方": "轮机长",
        "需求内容": "主机冷却水温度变化最好比较平稳。温度忽高忽低会让值班人员不放心，也可能影响主机运行判断。",
        "启用": True,
    },
    {
        "需求编号": "R042",
        "提出方": "轮机长",
        "需求内容": "滤器清洗和冷却器清洗要方便。船上人员有限，不希望每次维护都需要大量拆装管路。",
        "启用": True,
    },
    {
        "需求编号": "R043",
        "提出方": "自动化工程师",
        "需求内容": "冷却水系统的重要温度、压力、液位和泵运行信号应接入监控系统。信号点不能太少，否则后期很难做报警和故障分析。",
        "启用": True,
    },
    {
        "需求编号": "R044",
        "提出方": "自动化工程师",
        "需求内容": "传感器安装位置要能反映真实运行状态。比如温度测点不能离关键设备太远，也不能装在水流不稳定的位置。",
        "启用": True,
    },
    {
        "需求编号": "R045",
        "提出方": "自动化工程师",
        "需求内容": "报警等级要分清楚，普通提示、一般报警和严重报警不要混在一起。否则船员看到报警后不知道优先处理哪个。",
        "启用": True,
    },
    {
        "需求编号": "R046",
        "提出方": "自动化工程师",
        "需求内容": "泵的自动启停、备用切换和故障反馈逻辑要明确。尤其是自动切换失败时，系统应该能给出比较清楚的提示。",
        "启用": True,
    },
    {
        "需求编号": "R047",
        "提出方": "自动化工程师",
        "需求内容": "温控阀开度、控制目标和反馈信号最好能在监控界面显示。只显示一个温度值，不太利于判断控制过程是否正常。",
        "启用": True,
    },
    {
        "需求编号": "R048",
        "提出方": "自动化工程师",
        "需求内容": "冷却水系统的报警和主机控制系统之间要协调。不能一个系统认为需要保护，另一个系统还没有明显提示。",
        "启用": True,
    },
    {
        "需求编号": "R049",
        "提出方": "自动化工程师",
        "需求内容": "监控界面上的系统图要和实际管路基本一致。泵、阀门、冷却器和测点位置如果显示不清楚，船员容易误解。",
        "启用": True,
    },
    {
        "需求编号": "R050",
        "提出方": "自动化工程师",
        "需求内容": "历史数据最好能保存一段时间，至少温度、压力、泵状态和报警记录要能查。这样出现问题后才能回看变化过程。",
        "启用": True,
    },
    {
        "需求编号": "R051",
        "提出方": "安全负责人",
        "需求内容": "高温冷却水管路和设备附近要有必要防护。人员巡检、检修或者放水时，不能因为高温水或蒸汽造成烫伤风险。",
        "启用": True,
    },
    {
        "需求编号": "R052",
        "提出方": "安全负责人",
        "需求内容": "带压部位的阀门、接头和软连接要可靠。冷却水系统虽然不是最高压系统，但泄漏后仍可能影响人员安全和设备运行。",
        "启用": True,
    },
    {
        "需求编号": "R053",
        "提出方": "安全负责人",
        "需求内容": "旋转设备附近要考虑防护和警示。水泵、电机和联轴器附近不应有明显的人员卷入风险。",
        "启用": True,
    },
    {
        "需求编号": "R054",
        "提出方": "安全负责人",
        "需求内容": "冷却水系统发生泄漏时，应尽量能快速隔离。不要因为一个小泄漏导致主机冷却能力大范围下降。",
        "启用": True,
    },
    {
        "需求编号": "R055",
        "提出方": "安全负责人",
        "需求内容": "加药、取样和排放位置要考虑人员操作安全。药剂桶、取样阀和放水点附近最好不要布置得太拥挤。",
        "启用": True,
    },
    {
        "需求编号": "R056",
        "提出方": "安全负责人",
        "需求内容": "重要报警不能被轻易忽略。比如冷却水温度过高、压力过低、膨胀水箱液位低等问题，应能提醒船员及时处理。",
        "启用": True,
    },
    {
        "需求编号": "R057",
        "提出方": "维修人员",
        "需求内容": "水泵、冷却器、滤器和温控阀周围要留出检修空间。不要设备能装进去，但是以后根本拆不出来。",
        "启用": True,
    },
    {
        "需求编号": "R058",
        "提出方": "维修人员",
        "需求内容": "滤器清洗和冷却器拆检要方便，最好能局部隔离。不能为了清一个滤器就要停掉大范围系统。",
        "启用": True,
    },
    {
        "需求编号": "R059",
        "提出方": "维修人员",
        "需求内容": "传感器和仪表更换要方便。温度传感器、压力传感器和液位开关不要装在不好接近的位置。",
        "启用": True,
    },
    {
        "需求编号": "R060",
        "提出方": "维修人员",
        "需求内容": "常用备件最好规格统一一些。阀门、垫片、滤芯和传感器型号太杂，船上备件管理会比较困难。",
        "启用": True,
    },
    {
        "需求编号": "R061",
        "提出方": "维修人员",
        "需求内容": "管路拆装时要考虑残水排放。很多时候维修困难不是设备本身，而是管子里水放不干净，现场处理很麻烦。",
        "启用": True,
    },
    {
        "需求编号": "R062",
        "提出方": "维修人员",
        "需求内容": "设备铭牌、阀门编号和管路标识要能长期看清楚。后期维护时如果标识掉了或者编号混乱，很容易误操作。",
        "启用": True,
    },
    {
        "需求编号": "R063",
        "提出方": "调试人员",
        "需求内容": "系统调试时要能方便验证泵的运行状态、流量变化、压力变化和备用切换情况。不希望调试时缺少测点，只能凭经验判断。",
        "启用": True,
    },
    {
        "需求编号": "R064",
        "提出方": "调试人员",
        "需求内容": "冷却水系统冲洗、排气和注水过程要顺畅。调试阶段如果总是有气堵或者杂质堵塞，会影响后续试验。",
        "启用": True,
    },
    {
        "需求编号": "R065",
        "提出方": "调试人员",
        "需求内容": "温控阀动作要能测试，最好能看到阀门开度或温度变化响应。不然很难判断温控阀到底有没有按设计工作。",
        "启用": True,
    },
    {
        "需求编号": "R066",
        "提出方": "调试人员",
        "需求内容": "报警点和联锁逻辑要有条件进行试验。不能到海试阶段才发现报警值、显示值和实际动作不一致。",
        "启用": True,
    },
    {
        "需求编号": "R067",
        "提出方": "调试人员",
        "需求内容": "调试记录要能反映主要参数变化。比如泵切换前后、主机负荷变化前后、冷却器投入前后，温度和压力都应该有记录。",
        "启用": True,
    },
    {
        "需求编号": "R068",
        "提出方": "调试人员",
        "需求内容": "试验程序要提前和设计、船厂、船东、船级社沟通好。否则现场各方对试验标准理解不同，会影响验收进度。",
        "启用": True,
    },
    {
        "需求编号": "R069",
        "提出方": "船级社验船师",
        "需求内容": "冷却水系统与主机安全运行有关的设备和管路，应满足适用船级社规则要求。送审资料里要能看到相应依据。",
        "启用": True,
    },
    {
        "需求编号": "R070",
        "提出方": "船级社验船师",
        "需求内容": "主冷却水泵、备用泵、冷却器和重要阀件的配置要能说明其可靠性和备用能力。不能只在图纸上简单画出来。",
        "启用": True,
    },
    {
        "需求编号": "R071",
        "提出方": "船级社验船师",
        "需求内容": "材料、压力等级、管路连接和试验压力应符合规则和项目要求。图纸、计算书和设备证书之间不应有明显不一致。",
        "启用": True,
    },
    {
        "需求编号": "R072",
        "提出方": "船级社验船师",
        "需求内容": "与主机保护有关的报警和安全功能要有清楚说明。温度过高、压力过低和液位异常等情况应有适当监测。",
        "启用": True,
    },
    {
        "需求编号": "R073",
        "提出方": "船级社验船师",
        "需求内容": "系统试验和海试项目要能覆盖主要运行工况。不能只做简单启停检查，就认为冷却水系统已经满足要求。",
        "启用": True,
    },
    {
        "需求编号": "R074",
        "提出方": "船级社验船师",
        "需求内容": "如果设计中采用特殊材料、特殊控制方式或者非标准设备，应提供足够说明和证明文件，便于审查和验收。",
        "启用": True,
    },
    {
        "需求编号": "R075",
        "提出方": "环保负责人",
        "需求内容": "冷却液、清洗废液和含药剂水不能随意排放。系统设计和维护文件中应考虑收集、处理和记录问题。",
        "启用": True,
    },
    {
        "需求编号": "R076",
        "提出方": "环保负责人",
        "需求内容": "冷却水系统的泄漏风险要尽量降低，尤其是含防腐剂或清洗剂的液体。泄漏后要有比较方便的收集和处理方式。",
        "启用": True,
    },
    {
        "需求编号": "R077",
        "提出方": "环保负责人",
        "需求内容": "海水侧设备和管路维护时，清洗物、污水和沉积物也要考虑处理。不能只关注系统能不能运行。",
        "启用": True,
    },
    {
        "需求编号": "R078",
        "提出方": "环保负责人",
        "需求内容": "冷却水药剂的使用应有基本管理要求。药剂种类、加注量、存放方式和废液处理最好能在文件里说明。",
        "启用": True,
    },
    {
        "需求编号": "R079",
        "提出方": "材料工程师",
        "需求内容": "海水侧材料要重点考虑腐蚀问题。管路、阀门、冷却器和连接件不能只看强度，还要看长期海水环境下是否合适。",
        "启用": True,
    },
    {
        "需求编号": "R080",
        "提出方": "材料工程师",
        "需求内容": "淡水侧和冷却液侧也要考虑防腐剂、水质和温度影响。不同材料组合在一起时，不要引起明显电化学腐蚀风险。",
        "启用": True,
    },
    {
        "需求编号": "R081",
        "提出方": "材料工程师",
        "需求内容": "冷却器板片、密封件和管路垫片的材料要和介质匹配。不能只按一般淡水系统选材。",
        "启用": True,
    },
    {
        "需求编号": "R082",
        "提出方": "材料工程师",
        "需求内容": "海水滤器、海水阀门和海水管路内壁的防腐措施要明确。海生物附着、结垢和腐蚀都会影响后期使用。",
        "启用": True,
    },
    {
        "需求编号": "R083",
        "提出方": "运维管理人员",
        "需求内容": "冷却水系统运行数据最好能形成记录。温度、压力、液位、泵启停、报警和维护情况都应该便于后期查询。",
        "启用": True,
    },
    {
        "需求编号": "R084",
        "提出方": "运维管理人员",
        "需求内容": "水质检查和冷却液维护周期要比较明确。船员需要知道什么时候取样，什么时候补充药剂，什么时候清洗或更换。",
        "启用": True,
    },
    {
        "需求编号": "R085",
        "提出方": "运维管理人员",
        "需求内容": "系统故障后最好能根据历史数据追踪原因。比如温度慢慢升高、压力逐渐下降或者泵频繁切换，都应该有记录可查。",
        "启用": True,
    },
    {
        "需求编号": "R086",
        "提出方": "运维管理人员",
        "需求内容": "备件清单和维护文件要实用。不要只列设备大类，最好能对应到泵、阀门、滤芯、密封件和传感器等常用部件。",
        "启用": True,
    },
    {
        "需求编号": "R087",
        "提出方": "船厂质量检验人员",
        "需求内容": "安装完成后要检查管路连接、阀门方向、支架、焊缝、设备接口和仪表安装情况。不能只看系统有没有水压试验通过。",
        "启用": True,
    },
    {
        "需求编号": "R088",
        "提出方": "船厂质量检验人员",
        "需求内容": "阀门编号、流向标识、管路颜色和设备铭牌要和图纸一致。现场标识错误会影响后续调试和交船。",
        "启用": True,
    },
    {
        "需求编号": "R089",
        "提出方": "船厂质量检验人员",
        "需求内容": "压力试验、冲洗、密性检查和功能试验都要有记录。记录内容要能说明问题已经检查过，而不是只签一个合格。",
        "启用": True,
    },
    {
        "需求编号": "R090",
        "提出方": "船厂质量检验人员",
        "需求内容": "如果现场施工和设计图纸不一致，应及时形成变更或反馈。不能现场改完以后资料没有同步。",
        "启用": True,
    },
    {
        "需求编号": "R091",
        "提出方": "项目管理方",
        "需求内容": "冷却水系统涉及主机厂家、设计、采购、船厂和船级社，资料传递要及时。不能一方已经改了，其他方还按旧资料执行。",
        "启用": True,
    },
    {
        "需求编号": "R092",
        "提出方": "项目管理方",
        "需求内容": "关键设备和关键图纸要尽量按计划冻结。冷却器、水泵和主机接口如果反复变化，会影响采购和施工进度。",
        "启用": True,
    },
    {
        "需求编号": "R093",
        "提出方": "项目管理方",
        "需求内容": "需求、设计、采购、施工、调试和验收之间最好能追踪关系。后面如果某个参数变化，要知道会影响哪些文件和设备。",
        "启用": True,
    },
    {
        "需求编号": "R094",
        "提出方": "项目管理方",
        "需求内容": "供应商资料提交要有时间要求。冷却器外形图、泵性能曲线和阀门接口资料如果太晚，会影响详细设计。",
        "启用": True,
    },
    {
        "需求编号": "R095",
        "提出方": "项目管理方",
        "需求内容": "调试和验收阶段的问题要能闭合处理。比如温度偏高、压力不稳、报警异常等问题，要能记录原因、责任方和处理结果。",
        "启用": True,
    },
    {
        "需求编号": "R096",
        "提出方": "能源效率负责人",
        "需求内容": "冷却水泵长期运行的能耗需要关注。希望根据实际工况选择合适泵型和控制方式，不要一直按最大负荷方式运行。",
        "启用": True,
    },
    {
        "需求编号": "R097",
        "提出方": "能源效率负责人",
        "需求内容": "冷却器换热能力要有适当裕量，但裕量也不能过大。设备太大可能增加成本和运行负担，太小又会影响高温工况。",
        "启用": True,
    },
    {
        "需求编号": "R098",
        "提出方": "船员培训负责人",
        "需求内容": "冷却水系统交船前最好给船员讲清楚主要运行方式、常见故障和应急处理。只给一堆图纸，船员不一定能很快掌握。",
        "启用": True,
    },
    {
        "需求编号": "R099",
        "提出方": "船员培训负责人",
        "需求内容": "操作说明最好结合实际界面和现场设备来写。比如哪个泵是备用泵，哪个阀门用于隔离，哪个报警需要马上处理，都要说清楚。",
        "启用": True,
    },
    {
        "需求编号": "R100",
        "提出方": "岸基技术支持人员",
        "需求内容": "船舶运行后，如果冷却水系统出现反复报警或温度异常，岸基最好能拿到足够的运行数据和维护记录，方便远程判断问题原因。",
        "启用": True,
    },
]

WORKSPACE_LABELS = {
    "retrieval_workspace": "检索工作台",
    "retrieval_results": "检索结果",
    "engineering_workspace": "工程化需求",
    "experiment_comparison": "实验对比",
    "metrics_analysis": "指标分析",
}

SUPPORT_LABELS = {
    "direct": "直接支撑",
    "indirect": "间接支撑",
    "background": "背景信息",
    "not_applicable": "不适用",
    "": "未审查",
}

SUPPORT_CLASS = {
    "direct": "badge-direct",
    "indirect": "badge-indirect",
    "background": "badge-background",
    "not_applicable": "badge-na",
    "": "badge-na",
}

ENGINEERING_STATUS_LABELS = {
    "verified_by_direct_evidence": "直接证据支撑",
    "supported_by_indirect_evidence": "间接证据支撑",
    "evidence_gap": "证据缺口",
    "need_confirmation": "需确认",
}

ENGINEERING_STATUS_CLASS = {
    "verified_by_direct_evidence": "badge-direct",
    "supported_by_indirect_evidence": "badge-indirect",
    "evidence_gap": "badge-na",
    "need_confirmation": "badge-confirm",
}


def init_state() -> None:
    defaults = {
        "requirements_df": pd.DataFrame(DEFAULT_REQUIREMENTS),
        "results": None,
        "last_output": "",
        "last_runtime": None,
        "engineering_requirements": None,
        "last_engineering_output": "",
        "active_workspace": "retrieval_workspace",
        "top_k": 5,
        "coarse_k": 12,
        "fine_k": 40,
        "is_retrieving": False,
        "is_generating": False,
        "show_result_cta": False,
        # Experiment pages
        "exp_results": {},
        "exp_metrics": None,
        "exp_m6_template": None,
        "exp_running": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f6f8fb;
            --panel: #ffffff;
            --panel-soft: #f9fbfd;
            --line: #dbe3ea;
            --line-strong: #c8d4df;
            --text: #1f2937;
            --muted: #64748b;
            --accent: #2563eb;
            --accent-soft: #eff6ff;
            --success: #15803d;
            --success-bg: #ecfdf3;
            --warning: #a16207;
            --warning-bg: #fffbeb;
            --danger: #b91c1c;
            --danger-bg: #fef2f2;
            --shadow: 0 10px 26px rgba(15, 23, 42, 0.07);
        }
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        .block-container {
            max-width: 1320px;
            padding-top: 1.15rem;
            padding-bottom: 2rem;
        }
        section[data-testid="stSidebar"] {
            width: 15rem !important;
            min-width: 15rem !important;
            background: #ffffff;
            border-right: 1px solid var(--line);
            box-shadow: 8px 0 22px rgba(15, 23, 42, 0.04);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding: 1rem 0.85rem 1.25rem;
        }
        .nav-brand {
            padding: 4px 2px 12px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--line);
        }
        .nav-brand-title {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 760;
            line-height: 1.35;
        }
        .nav-brand-caption {
            color: var(--muted);
            font-size: 0.76rem;
            line-height: 1.55;
            margin-top: 5px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            display: grid;
            gap: 7px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 9px 10px;
            background: #ffffff;
            color: var(--text);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            border-color: #93c5fd;
            background: var(--accent-soft);
            box-shadow: inset 3px 0 0 var(--accent);
        }
        h1, h2, h3,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3 {
            color: var(--text);
            letter-spacing: 0;
        }
        div[data-testid="stMarkdownContainer"] p {
            line-height: 1.65;
        }
        .page-hero {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 18px 20px 16px;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff, #f8fbff);
            box-shadow: var(--shadow);
        }
        .page-kicker {
            color: var(--accent);
            font-size: 0.74rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .page-title {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 780;
            line-height: 1.2;
            margin-bottom: 7px;
        }
        .page-subtitle {
            color: var(--muted);
            max-width: 940px;
            font-size: 0.94rem;
            line-height: 1.65;
            margin-bottom: 12px;
        }
        .section-header {
            margin: 18px 0 10px;
        }
        .section-kicker {
            color: var(--accent);
            font-size: 0.72rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .section-title {
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 760;
            line-height: 1.35;
            margin-bottom: 3px;
        }
        .section-caption, .workflow-note, .muted {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            align-items: center;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 4px 10px;
            background: #ffffff;
            color: var(--muted);
            font-size: 0.8rem;
            font-weight: 650;
        }
        .status-pill strong {
            color: var(--text);
            font-weight: 760;
        }
        .status-pill.success {
            color: var(--success);
            background: var(--success-bg);
            border-color: #bbf7d0;
        }
        .status-pill.warning {
            color: var(--warning);
            background: var(--warning-bg);
            border-color: #fde68a;
        }
        .status-pill.danger {
            color: var(--danger);
            background: var(--danger-bg);
            border-color: #fecaca;
        }
        div[data-testid="stMetric"] {
            background: transparent;
            border: 0;
            padding: 0.1rem 0;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.8rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 720;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: var(--panel);
            box-shadow: none;
            overflow: hidden;
        }
        div[data-testid="stExpander"] details summary {
            background: var(--panel-soft);
            min-height: 42px;
        }
        div[data-testid="stTabs"] button {
            color: var(--muted);
            font-weight: 650;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
            background: var(--panel);
        }
        div[data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid var(--line);
        }
        div[data-testid="stCodeBlock"] {
            border-radius: 10px;
            border: 1px solid var(--line);
        }
        .stButton > button {
            border-radius: 9px;
            min-height: 2.55rem;
            font-weight: 700;
            border: 1px solid var(--line-strong);
            box-shadow: none;
            background: #ffffff;
            color: var(--text);
        }
        .stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: #ffffff;
        }
        .stButton > button:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
        .stButton > button[kind="primary"]:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
            color: #ffffff;
        }
        div[data-testid="stProgress"] > div > div > div > div {
            background: var(--accent);
        }
        .summary-card, .progress-card, .compact-req-card, .evidence-card {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel);
            box-shadow: var(--shadow);
        }
        .summary-card {
            padding: 12px 14px;
            min-height: 72px;
        }
        .summary-label {
            color: var(--muted);
            font-size: 0.8rem;
            margin-bottom: 4px;
        }
        .summary-value {
            color: var(--text);
            font-size: 1.36rem;
            font-weight: 760;
            line-height: 1.2;
        }
        .progress-card {
            padding: 12px 14px;
            margin-top: 6px;
            box-shadow: none;
        }
        .evidence-card {
            border-left: 3px solid #93c5fd;
            padding: 11px 13px;
            margin: 9px 0;
            box-shadow: none;
        }
        .evidence-title {
            color: var(--text);
            font-weight: 740;
            line-height: 1.55;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 0.76rem;
            font-weight: 700;
            margin-right: 6px;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .badge-direct { color: var(--success); background: var(--success-bg); border-color: #bbf7d0; }
        .badge-indirect { color: var(--warning); background: var(--warning-bg); border-color: #fde68a; }
        .badge-background { color: #475569; background: #f1f5f9; border-color: #cbd5e1; }
        .badge-na { color: var(--danger); background: var(--danger-bg); border-color: #fecaca; }
        .badge-confirm { color: #334155; background: #eef2ff; border-color: #c7d2fe; }
        .query-box {
            border-left: 3px solid #93c5fd;
            padding: 9px 11px;
            background: var(--accent-soft);
            border-radius: 8px;
            white-space: pre-wrap;
            font-size: 0.88rem;
            color: var(--text);
            line-height: 1.65;
        }
        .compact-req-card {
            padding: 12px 14px;
            margin: 10px 0;
        }
        .compact-req-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            border-bottom: 1px solid var(--line);
            padding-bottom: 9px;
            margin-bottom: 8px;
        }
        .compact-req-title {
            color: var(--text);
            font-weight: 780;
            font-size: 1rem;
        }
        .compact-sub {
            border-left: 2px solid #93c5fd;
            padding: 7px 0 7px 11px;
            margin: 7px 0;
            background: #f8fbff;
        }
        .compact-sub-title {
            color: var(--text);
            font-weight: 730;
            margin-bottom: 3px;
        }
        .evidence-chip {
            display: inline-block;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 2px 8px;
            margin: 3px 4px 3px 0;
            color: var(--text);
            background: var(--accent-soft);
            font-size: 0.76rem;
        }
        .run-panel {
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 12px 14px;
            background: #ffffff;
            box-shadow: var(--shadow);
            margin: 8px 0 12px;
        }
        .run-title {
            color: var(--text);
            font-weight: 760;
            margin-bottom: 4px;
        }
        .run-detail {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .sysml-canvas {
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
            margin: 12px 0 18px;
            overflow-x: auto;
            overflow-y: hidden;
        }
        /* ── SysML requirement diagram ── */
        .sysml-diagram-section { margin: 10px 0 22px; }
        .sysml-set-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 3px; }
        .sysml-set-id { font-weight: 780; font-size: 1.0rem; color: var(--text); }
        .sysml-set-src { color: var(--muted); font-size: 0.84rem; }
        .sysml-set-summary { color: var(--muted); font-size: 0.83rem; margin-bottom: 10px; line-height: 1.5; }
        .sysml-blocks-wrap {
            display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;
        }
        .sysml-block {
            border: 2px solid #94a3b8; border-top-width: 4px; border-radius: 8px;
            background: #ffffff; min-width: 200px; max-width: 310px;
            flex: 1 1 220px; overflow: hidden; font-size: 0.82rem;
        }
        .sysml-block.sysml-direct   { border-top-color: #15803d; border-color: #86efac; }
        .sysml-block.sysml-indirect { border-top-color: #b45309; border-color: #fcd34d; }
        .sysml-block.sysml-gap      { border-top-color: #b91c1c; border-color: #fca5a5; background: #fff8f8; }
        .sysml-block.sysml-confirm  { border-top-color: #4338ca; border-color: #c7d2fe; background: #f8f8ff; }
        .sysml-block.sysml-unknown  { border-top-color: #94a3b8; }
        .sysml-stereotype {
            font-size: 0.70rem; color: #64748b; font-style: italic;
            text-align: center; padding: 5px 8px 0; letter-spacing: 0.04em;
        }
        .sysml-block-name {
            font-weight: 760; color: var(--text); text-align: center;
            padding: 3px 8px 5px; font-size: 0.87rem; line-height: 1.4;
            border-bottom: 1.5px solid #e2e8f0;
        }
        .sysml-block-body { padding: 8px 10px; }
        .sysml-attr { margin: 3px 0; line-height: 1.55; color: var(--text); }
        .sysml-attr-label { color: #94a3b8; font-style: italic; font-size: 0.72rem; }
        .sysml-text-val { color: #334155; font-size: 0.79rem; }
        .sysml-meta { margin-top: 7px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
        .sysml-verif-chip {
            font-size: 0.69rem; color: #475569; background: #f1f5f9;
            border: 1px solid #e2e8f0; border-radius: 999px; padding: 1px 7px;
        }
        .sysml-evidence-line { width: 100%; color: #94a3b8; font-size: 0.70rem; margin-top: 3px; }
        .sysml-children {
            border-top: 1.5px dashed #e2e8f0; background: #f9fbfd;
            padding: 8px; display: flex; flex-wrap: wrap; gap: 7px;
        }
        .sysml-block.sysml-l2 {
            min-width: 160px; max-width: 270px; flex: 1 1 170px;
            border-top-width: 3px; font-size: 0.79rem;
        }
        .sysml-block.sysml-l2 .sysml-block-name { font-size: 0.82rem; font-weight: 740; }
        @media (max-width: 760px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .page-title { font-size: 1.35rem; }
            .compact-req-head { display: block; }
            .sysml-blocks-wrap { flex-direction: column; }
            .sysml-block, .sysml-block.sysml-l2 { max-width: 100%; min-width: unset; flex: 1 1 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_pill_html(label: str, value: str, tone: str = "neutral") -> str:
    tone_class = "" if tone == "neutral" else f" {tone}"
    return f'<span class="status-pill{tone_class}">{escape(label)}<strong>{escape(value)}</strong></span>'


def render_status_pill(label: str, value: str, tone: str = "neutral") -> None:
    st.markdown(status_pill_html(label, value, tone), unsafe_allow_html=True)


def render_workspace_header(title: str, caption: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="page-hero">
            <div class="page-kicker">{escape(kicker)}</div>
            <div class="page-title">{escape(title)}</div>
            <div class="page-subtitle">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, caption: str = "", kicker: str = "") -> None:
    kicker_html = f'<div class="section-kicker">{escape(kicker)}</div>' if kicker else ""
    caption_html = f'<div class="section-caption">{escape(caption)}</div>' if caption else ""
    st.markdown(
        f"""
        <div class="section-header">
            {kicker_html}
            <div class="section-title">{escape(title)}</div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_df(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for i, row in df.iterrows():
        if not bool(row.get("启用", True)):
            continue
        text = str(row.get("需求内容", "") or "").strip()
        if not text:
            continue
        rid = str(row.get("需求编号", "") or f"R{i+1:03d}").strip()
        stakeholder = str(row.get("提出方", "") or "").strip()
        out.append({"requirement_id": rid, "stakeholder": stakeholder, "requirement_text": text})
    return out


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "待估计"
    seconds = max(0, int(round(seconds)))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}小时{minutes}分{sec}秒"
    if minutes:
        return f"{minutes}分{sec}秒"
    return f"{sec}秒"


def empty_payload() -> dict[str, Any]:
    return {
        "requirements": [],
        "diagnostics": {
            "requirement_count": 0,
            "sub_requirement_count": 0,
            "selected_evidence_count": 0,
            "evidence_gap_count": 0,
        },
    }


def merge_payload(target: dict[str, Any], part: dict[str, Any]) -> None:
    target.setdefault("requirements", []).extend(part.get("requirements", []) or [])
    target_diag = target.setdefault("diagnostics", {})
    part_diag = part.get("diagnostics", {}) or {}
    for key in ["requirement_count", "sub_requirement_count", "selected_evidence_count", "evidence_gap_count"]:
        target_diag[key] = int(target_diag.get(key, 0) or 0) + int(part_diag.get(key, 0) or 0)


def summarize_payload(payload: dict[str, Any]) -> dict[str, int]:
    reqs = payload.get("requirements", []) or []
    sub_count = selected_count = direct_count = indirect_count = background_count = gap_count = 0
    for req in reqs:
        for sub in req.get("sub_requirements", []) or []:
            sub_count += 1
            if sub.get("evidence_gap"):
                gap_count += 1
            for ev in sub.get("selected_results", []) or []:
                selected_count += 1
                support_type = (ev.get("llm_judge", {}) or {}).get("support_type", "")
                if support_type == "direct":
                    direct_count += 1
                elif support_type == "indirect":
                    indirect_count += 1
                elif support_type == "background":
                    background_count += 1
    return {
        "requirements": len(reqs),
        "sub_requirements": sub_count,
        "selected_evidence": selected_count,
        "direct": direct_count,
        "indirect": indirect_count,
        "background": background_count,
        "gaps": gap_count,
    }


def badge_html(support_type: str) -> str:
    cls = SUPPORT_CLASS.get(support_type, "badge-na")
    label = SUPPORT_LABELS.get(support_type, support_type or "未审查")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def engineering_badge_html(status: str) -> str:
    cls = ENGINEERING_STATUS_CLASS.get(status, "badge-confirm")
    label = ENGINEERING_STATUS_LABELS.get(status, status or "未标注")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def format_score(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "无"
    return f"{number:.3f}"


def render_summary_cards(payload: dict[str, Any]) -> None:
    summary = summarize_payload(payload)
    columns = st.columns(6)
    cards = [
        ("需求数", summary["requirements"]),
        ("子需求", summary["sub_requirements"]),
        ("保留证据", summary["selected_evidence"]),
        ("直接支撑", summary["direct"]),
        ("间接支撑", summary["indirect"]),
        ("证据缺口", summary["gaps"]),
    ]
    for col, (label, value) in zip(columns, cards):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-label">{escape(label)}</div>
                    <div class="summary-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_evidence_card(ev: dict[str, Any], idx: int) -> None:
    meta = ev.get("metadata", {}) or {}
    judge = ev.get("llm_judge", {}) or {}
    support_type = judge.get("support_type", "")
    evidence_id = str(ev.get("id", "") or "")
    topic = str(meta.get("topic", "") or "未命名证据")
    source = str(meta.get("source_document", "") or "未知来源")
    location = str(meta.get("location", "") or "未知位置")
    reason = str(judge.get("reason", "") or "无审查说明")
    text = str(ev.get("text", "") or "")

    st.markdown(
        f"""
        <div class="evidence-card">
            <div class="evidence-title">{badge_html(support_type)}{idx}. {escape(evidence_id)}｜{escape(topic)}</div>
            <div class="muted">来源：{escape(source)}｜位置：{escape(location)}</div>
            <div class="muted">判断理由：{escape(reason)}</div>
            <div class="muted">final_score：{format_score(ev.get('final_score'))}｜rrf_score：{format_score(ev.get('rrf_score'))}｜profile_score：{format_score(ev.get('profile_score'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("查看原文和详细字段", expanded=False):
        st.code(text, language="text")
        left, right = st.columns(2)
        with left:
            st.markdown("**LLM Judge**")
            st.json(judge)
        with right:
            st.markdown("**Metadata**")
            st.json(meta)


def sub_support_type(sub: dict[str, Any]) -> str:
    selected = sub.get("selected_results", []) or []
    support_types = [(ev.get("llm_judge", {}) or {}).get("support_type", "") for ev in selected]
    if "direct" in support_types:
        return "direct"
    if "indirect" in support_types:
        return "indirect"
    if "background" in support_types:
        return "background"
    if sub.get("evidence_gap"):
        return "not_applicable"
    return ""


def render_compact_sub_requirement(sub: dict[str, Any]) -> None:
    selected = sub.get("selected_results", []) or []
    support_type = sub_support_type(sub)
    evidence_chips = []
    if selected:
        evidence_chips.append(f'<span class="evidence-chip">保留证据 {len(selected)} 条</span>')
    for ev in selected:
        meta = ev.get("metadata", {}) or {}
        evidence_id = escape(str(ev.get("id", "") or "未编号"))
        source = escape(str(meta.get("source_document", "") or "未知来源"))
        evidence_chips.append(f'<span class="evidence-chip">{evidence_id}｜{source}</span>')
    if not evidence_chips:
        evidence_chips.append('<span class="evidence-chip">暂无保留证据</span>')

    st.markdown(
        f"""
        <div class="compact-sub">
            <div class="compact-sub-title">
                {badge_html(support_type)}
                {escape(str(sub.get('sub_requirement_id', '') or ''))}｜{escape(str(sub.get('requirement_type', '') or ''))}｜{escape(str(sub.get('topic', '') or ''))}
            </div>
            <div class="muted">{escape(str(sub.get('text', '') or ''))}</div>
            <div>{''.join(evidence_chips)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"展开详情：{sub.get('sub_requirement_id', '')}", expanded=False):
        if sub.get("evidence_gap"):
            reason = (sub.get("evidence_gap") or {}).get("reason", "")
            st.warning(f"证据缺口：{reason}")
        tabs = st.tabs(["保留证据", "检索画像", "候选证据", "调试信息"])
        with tabs[0]:
            if not selected:
                st.info("没有保留证据。")
            for idx, ev in enumerate(selected, start=1):
                render_evidence_card(ev, idx)
        with tabs[1]:
            query = sub.get("retrieval_query", "") or ""
            st.markdown("**检索 query**")
            st.markdown(f'<div class="query-box">{escape(query)}</div>', unsafe_allow_html=True)
            st.markdown("**Profile**")
            st.json(sub.get("profile", {}))
        with tabs[2]:
            candidates = sub.get("candidate_results", []) or []
            if candidates:
                table = []
                for item in candidates[:20]:
                    meta = item.get("metadata", {}) or {}
                    table.append({
                        "id": item.get("id"),
                        "topic": meta.get("topic", ""),
                        "source": meta.get("source_document", ""),
                        "score": format_score(item.get("final_score")),
                    })
                st.dataframe(pd.DataFrame(table), width="stretch", hide_index=True)
            else:
                st.info("没有候选证据。")
            with st.expander("查看 rejected_results", expanded=False):
                st.json(sub.get("rejected_results", []))
        with tabs[3]:
            st.markdown("**Stage Diagnostics**")
            st.json(sub.get("stage_diagnostics", {}))
            st.markdown("**Judge Result**")
            st.json(sub.get("judge_result", {}))


def render_compact_results(payload: dict[str, Any]) -> None:
    render_summary_cards(payload)
    requirements = payload.get("requirements", []) or []
    result_count = len(requirements)
    enabled_count = len(normalize_df(st.session_state.requirements_df))
    tone = "success" if result_count == enabled_count else "warning"
    st.markdown(
        f"""
        <div class="status-strip">
            {status_pill_html("结果需求数", str(result_count), tone)}
            {status_pill_html("当前启用需求数", str(enabled_count), "neutral")}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if result_count != enabled_count:
        st.warning("当前启用需求数与已保存检索结果数不一致。通常是检索后又修改了需求表；请重新运行检索以同步结果。")

    if not requirements:
        st.info("当前结果文件中没有需求结果。")
        return

    overview_rows = []
    for req in requirements:
        req_id = str(req.get("requirement_id", "") or "")
        stakeholder = str(req.get("stakeholder", "") or "")
        sub_requirements = req.get("sub_requirements", []) or []
        gap_count = sum(1 for sub in sub_requirements if sub.get("evidence_gap"))
        selected_count = sum(len(sub.get("selected_results", []) or []) for sub in sub_requirements)
        direct_count = sum(
            1
            for sub in sub_requirements
            for ev in sub.get("selected_results", []) or []
            if (ev.get("llm_judge", {}) or {}).get("support_type") == "direct"
        )
        overview_rows.append({
            "需求编号": req_id,
            "提出方": stakeholder,
            "子需求": len(sub_requirements),
            "保留证据": selected_count,
            "直接证据": direct_count,
            "证据缺口": gap_count,
        })

    render_section_header("需求概览", "这里展示本次结果中的全部原始需求；下方选择一条查看详细证据链。", "Overview")
    st.dataframe(pd.DataFrame(overview_rows), width="stretch", hide_index=True)

    options = [str(req.get("requirement_id", "") or f"REQ-{idx + 1}") for idx, req in enumerate(requirements)]
    selected_req_id = st.selectbox(
        "选择要查看的需求",
        options=options,
        format_func=lambda rid: next(
            (
                f"{rid}｜{req.get('stakeholder', '')}｜子需求 {len(req.get('sub_requirements', []) or [])}"
                for req in requirements
                if str(req.get("requirement_id", "") or "") == rid
            ),
            rid,
        ),
    )
    selected_req = next(
        (req for req in requirements if str(req.get("requirement_id", "") or "") == selected_req_id),
        requirements[0],
    )

    req_id = str(selected_req.get("requirement_id", "") or "")
    stakeholder = str(selected_req.get("stakeholder", "") or "")
    raw_text = str(selected_req.get("raw_requirement_text", "") or "")
    sub_requirements = selected_req.get("sub_requirements", []) or []
    gap_count = sum(1 for sub in sub_requirements if sub.get("evidence_gap"))
    selected_count = sum(len(sub.get("selected_results", []) or []) for sub in sub_requirements)

    render_section_header("需求详情", "默认只显示子需求、支撑状态和保留证据摘要；原文和调试字段在展开详情中。", "Detail")
    st.markdown(
        f"""
        <div class="compact-req-card">
            <div class="compact-req-head">
                <div>
                    <div class="compact-req-title">{escape(req_id)}｜{escape(stakeholder)}</div>
                    <div class="muted">{escape(raw_text)}</div>
                </div>
                <div class="status-strip">
                    {status_pill_html('子需求', str(len(sub_requirements)), 'neutral')}
                    {status_pill_html('证据', str(selected_count), 'success' if selected_count else 'warning')}
                    {status_pill_html('缺口', str(gap_count), 'danger' if gap_count else 'success')}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for sub in sub_requirements:
        render_compact_sub_requirement(sub)


def update_progress_ui(
    progress_bar: Any,
    status_box: Any,
    metric_box: Any,
    *,
    fraction: float,
    title: str,
    detail: str,
    completed: int,
    total: int,
    elapsed_seconds: float,
    remaining_seconds: float | None,
) -> None:
    percent = max(0, min(100, int(round(fraction * 100))))
    progress_bar.progress(percent, text=title)
    metric_box.markdown(
        f"""
        <div class="progress-card">
            <div class="summary-label">运行进度</div>
            <div class="summary-value">{completed}/{total}</div>
            <div class="muted">已用：{format_duration(elapsed_seconds)}｜预计剩余：{format_duration(remaining_seconds)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    status_box.info(detail)


def render_run_panel(title: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="run-panel">
            <div class="run-title">{escape(title)}</div>
            <div class="run-detail">{escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_with_progress(
    requirements: list[dict[str, Any]],
    *,
    cfg: Any,
    top_k: int,
    coarse_k: int,
    fine_k: int,
) -> tuple[dict[str, Any], Path, float]:
    total = len(requirements)
    start = time.perf_counter()
    progress_bar = st.progress(0, text="准备检索")
    status_box = st.empty()
    metric_box = st.empty()
    stage_box = st.empty()
    with stage_box.container():
        render_run_panel("多粒度证据检索运行中", "正在执行需求拆分、粗粒度召回、细粒度召回、工程适用性过滤与证据审查。")

    update_progress_ui(
        progress_bar,
        status_box,
        metric_box,
        fraction=0.02,
        title="加载索引和模型",
        detail="正在加载多粒度索引、BM25、FAISS 和 embedding 模型。首次运行会比较慢。",
        completed=0,
        total=total,
        elapsed_seconds=0,
        remaining_seconds=None,
    )

    services = make_services()
    payload = empty_payload()
    load_elapsed = time.perf_counter() - start
    update_progress_ui(
        progress_bar,
        status_box,
        metric_box,
        fraction=0.08,
        title="模型加载完成",
        detail=f"模型和索引已加载。加载耗时：{format_duration(load_elapsed)}。",
        completed=0,
        total=total,
        elapsed_seconds=load_elapsed,
        remaining_seconds=None,
    )

    request_times: list[float] = []
    for index, req in enumerate(requirements, start=1):
        req_id = req.get("requirement_id", f"第{index}条")
        before = time.perf_counter()
        completed_before = index - 1
        fraction_before = 0.08 + (completed_before / total) * 0.88
        avg_seconds = sum(request_times) / len(request_times) if request_times else None
        remaining_before = avg_seconds * (total - completed_before) if avg_seconds is not None else None
        update_progress_ui(
            progress_bar,
            status_box,
            metric_box,
            fraction=fraction_before,
            title=f"正在检索 {index}/{total}：{req_id}",
            detail="当前阶段包括需求拆分、粗检索、细检索、工程适用性过滤和证据审查。",
            completed=completed_before,
            total=total,
            elapsed_seconds=time.perf_counter() - start,
            remaining_seconds=remaining_before,
        )
        part = run_requirements_with_services(
            [req],
            services=services,
            top_k=top_k,
            coarse_k=coarse_k,
            fine_k=fine_k,
        )
        merge_payload(payload, part)
        current_elapsed = time.perf_counter() - before
        request_times.append(current_elapsed)
        completed = index
        avg_seconds = sum(request_times) / len(request_times)
        remaining = avg_seconds * (total - completed)
        fraction_after = 0.08 + (completed / total) * 0.88
        update_progress_ui(
            progress_bar,
            status_box,
            metric_box,
            fraction=fraction_after,
            title=f"已完成 {completed}/{total}：{req_id}",
            detail=f"本条耗时：{format_duration(current_elapsed)}。预计剩余时间按已完成需求的平均耗时计算。",
            completed=completed,
            total=total,
            elapsed_seconds=time.perf_counter() - start,
            remaining_seconds=remaining,
        )

    batch = make_batch_dir(cfg.paths.search_results_dir)
    out_path = save_pack(batch, payload)
    runtime = time.perf_counter() - start
    stage_box.empty()
    progress_bar.progress(100, text="检索完成")
    status_box.success(f"检索完成。结果已保存：{out_path}")
    metric_box.markdown(
        f"""
        <div class="progress-card">
            <div class="summary-label">运行完成</div>
            <div class="summary-value">100%</div>
            <div class="muted">总耗时：{format_duration(runtime)}｜输出：{out_path}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return payload, out_path, runtime


def render_nav_sidebar(cfg: Any) -> str:
    current = st.session_state.get("active_workspace", "retrieval_workspace")
    if current not in WORKSPACE_LABELS:
        current = "retrieval_workspace"
        st.session_state.active_workspace = current
    options = list(WORKSPACE_LABELS.keys())

    with st.sidebar:
        st.markdown(
            """
            <div class="nav-brand">
                <div class="nav-brand-title">冷却水系统 RAG</div>
                <div class="nav-brand-caption">需求检索、证据审查和工程化需求生成</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _core_keys = ["retrieval_workspace", "retrieval_results", "engineering_workspace"]
        _exp_keys  = ["experiment_comparison", "metrics_analysis"]

        for workspace_key in _core_keys:
            selected = workspace_key == current
            button_type = "primary" if selected else "secondary"
            if st.button(WORKSPACE_LABELS[workspace_key], key=f"nav_{workspace_key}", type=button_type, width="stretch"):
                st.session_state.active_workspace = workspace_key
                st.rerun()

        st.markdown('<hr style="margin:10px 0;border-color:#e2e8f0">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:#94a3b8;font-weight:660;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px">实验与评估</div>', unsafe_allow_html=True)

        for workspace_key in _exp_keys:
            selected = workspace_key == current
            button_type = "primary" if selected else "secondary"
            if st.button(WORKSPACE_LABELS[workspace_key], key=f"nav_{workspace_key}", type=button_type, width="stretch"):
                st.session_state.active_workspace = workspace_key
                st.rerun()

        selected = st.session_state.get("active_workspace", current)
        has_results = st.session_state.results is not None
        has_engineering = st.session_state.engineering_requirements is not None

        st.markdown('<div class="nav-meta">', unsafe_allow_html=True)
        render_status_pill("DeepSeek", "已配置" if cfg.deepseek.enabled else "未配置", "success" if cfg.deepseek.enabled else "danger")
        render_status_pill("检索", "已有结果" if has_results else "待运行", "success" if has_results else "warning")
        render_status_pill("工程化", "已生成" if has_engineering else "待生成", "success" if has_engineering else "warning")
        if st.session_state.last_runtime is not None:
            render_status_pill("耗时", format_duration(st.session_state.last_runtime), "neutral")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("运行路径", expanded=False):
            st.caption("检索输出目录")
            st.code(str(cfg.paths.search_results_dir), language="text")
            if st.session_state.last_output:
                st.caption("最近检索输出")
                st.code(st.session_state.last_output, language="text")
            if st.session_state.last_engineering_output:
                st.caption("最近工程化输出")
                st.code(st.session_state.last_engineering_output, language="text")

    return selected



def render_retrieval_workspace(cfg: Any) -> None:
    render_workspace_header(
        "检索工作台",
        "调整检索参数和原始需求。启动后系统会执行多粒度召回、工程适用性过滤与证据审查。",
        "Retrieval Console",
    )
    with st.expander("检索参数", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            top_k = st.number_input("每个子需求保留证据数", min_value=1, max_value=10, value=int(st.session_state.top_k), step=1, key="top_k_input")
        with cols[1]:
            coarse_k = st.number_input("大颗粒度候选数", min_value=5, max_value=50, value=int(st.session_state.coarse_k), step=1, key="coarse_k_input")
        with cols[2]:
            fine_k = st.number_input("小颗粒度候选数", min_value=10, max_value=100, value=int(st.session_state.fine_k), step=5, key="fine_k_input")
    st.session_state.top_k = int(top_k)
    st.session_state.coarse_k = int(coarse_k)
    st.session_state.fine_k = int(fine_k)

    render_section_header("原始需求", "只保留启用且需求内容非空的行进入检索。", "Input")
    edited_df = st.data_editor(
        st.session_state.requirements_df,
        key="requirements_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "需求编号": st.column_config.TextColumn("需求编号", width="small"),
            "提出方": st.column_config.TextColumn("提出方", width="medium"),
            "需求内容": st.column_config.TextColumn("需求内容", width="large"),
            "启用": st.column_config.CheckboxColumn("启用", width="small"),
        },
    )
    enabled_count = len(normalize_df(pd.DataFrame(edited_df)))
    action_col, info_col, clear_col = st.columns([1.05, 3.6, 1.05])
    with action_col:
        start_clicked = st.button("开始检索", type="primary", width="stretch", disabled=bool(st.session_state.is_retrieving))
    with info_col:
        st.markdown(f'<div class="workflow-note">当前启用需求 {enabled_count} 条。检索完成后会停留在本页，避免长任务结束后强制刷新导致页面失去响应。</div>', unsafe_allow_html=True)
    with clear_col:
        clear_clicked = st.button("清空结果", width="stretch", disabled=bool(st.session_state.is_retrieving))

    if clear_clicked:
        st.session_state.results = None
        st.session_state.engineering_requirements = None
        st.session_state.last_output = ""
        st.session_state.last_engineering_output = ""
        st.session_state.last_runtime = None
        st.session_state.show_result_cta = False
        st.rerun()

    if start_clicked:
        st.session_state.requirements_df = pd.DataFrame(edited_df)
        reqs = normalize_df(edited_df)
        if not reqs:
            st.warning("没有可检索的需求。")
            return
        st.session_state.is_retrieving = True
        try:
            payload, out_path, runtime = run_with_progress(
                reqs,
                cfg=cfg,
                top_k=int(top_k),
                coarse_k=int(coarse_k),
                fine_k=int(fine_k),
            )
            st.session_state.results = payload
            st.session_state.last_output = str(out_path)
            st.session_state.last_runtime = runtime
            st.session_state.show_result_cta = True
        finally:
            st.session_state.is_retrieving = False

    if st.session_state.results and st.session_state.show_result_cta:
        st.success("检索已完成。请进入检索结果页查看全部需求概览。")
        if st.button("查看检索结果", type="primary", width="stretch"):
            st.session_state.active_workspace = "retrieval_results"
            st.session_state.show_result_cta = False
            st.rerun()


def render_retrieval_results_workspace() -> None:
    render_workspace_header(
        "检索结果",
        "结果区只呈现最直接的信息。需求原文、候选证据、拒绝结果和调试字段放入折叠详情中。",
        "Evidence View",
    )
    if not st.session_state.results:
        st.info("尚未完成检索。请先进入“检索工作台”运行检索。")
        if st.button("进入检索工作台", type="primary"):
            st.session_state.active_workspace = "retrieval_workspace"
            st.rerun()
        return
    render_compact_results(st.session_state.results)


def render_engineering_requirement_overview(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    total_items = sum(len(x.get("engineering_requirements", []) or []) for x in req_sets)
    direct_items = sum(
        1
        for req_set in req_sets
        for item in req_set.get("engineering_requirements", []) or []
        if item.get("support_status") == "verified_by_direct_evidence"
    )
    gap_items = sum(
        1
        for req_set in req_sets
        for item in req_set.get("engineering_requirements", []) or []
        if item.get("support_status") == "evidence_gap"
    )
    cols = st.columns(3)
    for col, label, value, caption in [
        (cols[0], "需求集", len(req_sets), ""),
        (cols[1], "工程需求", total_items, ""),
        (cols[2], "证据缺口", gap_items, f"直接证据支撑 {direct_items} 条"),
    ]:
        with col:
            extra = f'<div class="muted">{escape(caption)}</div>' if caption else ""
            st.markdown(f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{value}</div>{extra}</div>', unsafe_allow_html=True)


def render_sysml_requirement_table(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    rows = []
    for req_set in req_sets:
        for item in req_set.get("engineering_requirements", []) or []:
            rows.append({
                "需求集": req_set.get("requirement_set_id", ""),
                "来源需求": req_set.get("source_requirement_id", ""),
                "ID": item.get("id", ""),
                "父级": item.get("parent_id", ""),
                "层级": item.get("level", ""),
                "类型": item.get("requirement_type", ""),
                "主题": item.get("topic", ""),
                "工程化需求": item.get("shall_statement", ""),
                "验证方式": item.get("verification_method", ""),
                "支撑状态": ENGINEERING_STATUS_LABELS.get(item.get("support_status", ""), item.get("support_status", "")),
                "证据": ", ".join([str(x) for x in item.get("evidence_ids", []) or []]),
            })
    if not rows:
        st.info("没有可展示的工程化需求表。")
        return
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    for req_set in req_sets:
        set_id = req_set.get("requirement_set_id", "")
        source_id = req_set.get("source_requirement_id", "")
        with st.expander(f"{set_id}｜来源 {source_id}｜完整验收判据与风险", expanded=False):
            st.markdown(f"**工程化摘要**  {req_set.get('professional_summary', '')}")
            for item in req_set.get("engineering_requirements", []) or []:
                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <div class="evidence-title">{engineering_badge_html(item.get('support_status', ''))}{escape(str(item.get('id', '') or ''))}｜{escape(str(item.get('topic', '') or ''))}</div>
                        <div>{escape(str(item.get('shall_statement', '') or ''))}</div>
                        <div class="muted">验证方式：{escape(str(item.get('verification_method', '') or ''))}｜证据：{escape(', '.join([str(x) for x in item.get('evidence_ids', []) or []]) or '无')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                criteria = item.get("acceptance_criteria", []) or []
                if criteria:
                    st.markdown("**验收判据**")
                    for criterion in criteria:
                        st.write(f"- {criterion}")
                st.markdown("**未满足风险**")
                st.write(item.get("risk_if_unmet", "无"))


def render_relationships(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    rows = []
    for req_set in req_sets:
        for rel in req_set.get("relationships", []) or []:
            rows.append({
                "需求集": req_set.get("requirement_set_id", ""),
                "source": rel.get("source", ""),
                "type": rel.get("type", ""),
                "target": rel.get("target", ""),
                "description": rel.get("description", ""),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("没有关系数据。")


def _build_req_tree(items: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    result = []
    for item in items:
        if item.get("parent_id") == parent_id:
            node = dict(item)
            node["_children"] = _build_req_tree(items, node.get("id", ""))
            result.append(node)
    return result


def _sysml_block_html(item: dict[str, Any], depth: int = 0) -> str:
    status = item.get("support_status", "")
    status_class = {
        "verified_by_direct_evidence": "sysml-direct",
        "supported_by_indirect_evidence": "sysml-indirect",
        "evidence_gap": "sysml-gap",
        "need_confirmation": "sysml-confirm",
    }.get(status, "sysml-unknown")
    status_label = ENGINEERING_STATUS_LABELS.get(status, status)
    badge_class = ENGINEERING_STATUS_CLASS.get(status, "badge-na")
    req_id = escape(str(item.get("id", "") or ""))
    topic = escape(str(item.get("topic", "") or ""))
    shall_raw = str(item.get("shall_statement", "") or "")
    shall_display = escape(shall_raw[:130] + ("…" if len(shall_raw) > 130 else ""))
    verif = escape(str(item.get("verification_method", "") or ""))
    ev_list = [str(x) for x in (item.get("evidence_ids") or [])]
    evidence = escape(", ".join(ev_list) if ev_list else "—")
    depth_class = "sysml-l1" if depth == 0 else "sysml-l2"
    children = item.get("_children", [])
    children_html = ""
    if children:
        inner = "".join(_sysml_block_html(c, depth + 1) for c in children)
        children_html = f'<div class="sysml-children">{inner}</div>'
    return (
        f'<div class="sysml-block {status_class} {depth_class}">'
        f'<div class="sysml-stereotype">«requirement»</div>'
        f'<div class="sysml-block-name">{topic}</div>'
        f'<div class="sysml-block-body">'
        f'<div class="sysml-attr"><span class="sysml-attr-label">id : </span>{req_id}</div>'
        f'<div class="sysml-attr"><span class="sysml-attr-label">text : </span>'
        f'<span class="sysml-text-val">{shall_display}</span></div>'
        f'<div class="sysml-meta">'
        f'<span class="badge {badge_class}">{escape(status_label)}</span>'
        f'<span class="sysml-verif-chip">{verif}</span>'
        f'<div class="sysml-evidence-line">证据：{evidence}</div>'
        f'</div></div>'
        f'{children_html}'
        f'</div>'
    )


def render_sysml_requirement_diagram(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    if not req_sets:
        st.info("没有可展示的工程化需求。")
        return
    for req_set in req_sets:
        set_id = req_set.get("requirement_set_id", "")
        source_id = req_set.get("source_requirement_id", "")
        stakeholder = req_set.get("stakeholder", "")
        summary = req_set.get("professional_summary", "")
        items = req_set.get("engineering_requirements", []) or []
        roots = _build_req_tree(items, set_id)
        # Orphan safety: items not reached by tree (e.g. parent points to unknown id)
        reached = set()
        def _collect(nodes: list) -> None:
            for n in nodes:
                reached.add(n.get("id", ""))
                _collect(n.get("_children", []))
        _collect(roots)
        for item in items:
            if item.get("id", "") not in reached:
                node = dict(item)
                node["_children"] = []
                roots.append(node)
        blocks_html = "".join(_sysml_block_html(r, 0) for r in roots)
        st.markdown(
            f'<div class="sysml-diagram-section">'
            f'<div class="sysml-set-header">'
            f'<span class="sysml-set-id">{escape(set_id)}</span>'
            f'<span class="sysml-set-src">来源 {escape(source_id)} ｜ {escape(stakeholder)}</span>'
            f'</div>'
            f'<div class="sysml-set-summary">{escape(summary)}</div>'
            f'<div class="sysml-blocks-wrap">{blocks_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"{set_id} — 完整验收判据与风险", expanded=False):
            for item in items:
                st.markdown(
                    f'<div class="evidence-card">'
                    f'<div class="evidence-title">'
                    f'{engineering_badge_html(item.get("support_status", ""))}'
                    f'{escape(str(item.get("id", "") or ""))} ｜ {escape(str(item.get("topic", "") or ""))}'
                    f'</div>'
                    f'<div>{escape(str(item.get("shall_statement", "") or ""))}</div>'
                    f'<div class="muted">验证方式：{escape(str(item.get("verification_method", "") or ""))} ｜ '
                    f'证据：{escape(", ".join([str(x) for x in item.get("evidence_ids", []) or []]) or "无")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                criteria = item.get("acceptance_criteria", []) or []
                if criteria:
                    st.markdown("**验收判据**")
                    for c in criteria:
                        st.write(f"- {c}")
                risk = item.get("risk_if_unmet", "")
                if risk:
                    st.markdown("**未满足风险**")
                    st.write(risk)


def render_engineering_workspace(cfg: Any) -> None:
    render_workspace_header(
        "工程化需求",
        "基于原始需求和有支撑证据生成工程化需求，以 SysML 需求图方式呈现层级结构与支撑状态。",
        "SysML Requirement",
    )
    has_results = st.session_state.results is not None
    control_col, note_col = st.columns([1.1, 4])
    with control_col:
        generate_clicked = st.button(
            "生成工程化需求",
            type="primary",
            width="stretch",
            disabled=(not has_results) or bool(st.session_state.is_generating),
        )
    with note_col:
        if has_results:
            st.markdown('<div class="workflow-note">已检测到检索结果，可以调用工程化需求智能体。生成过程结束后会自动刷新。</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="workflow-note">请先完成检索。没有检索结果时不能生成工程化需求。</div>', unsafe_allow_html=True)

    if generate_clicked:
        current_requirements = normalize_df(st.session_state.requirements_df)
        if not cfg.deepseek.enabled:
            st.error("DeepSeek 未配置，无法运行工程化需求智能体。")
        elif not current_requirements:
            st.warning("没有启用的原始需求。")
        elif not st.session_state.results:
            st.warning("没有检索结果。请先运行检索。")
        else:
            st.session_state.is_generating = True
            try:
                with st.spinner("正在通过 LangGraph 调用 DeepSeek 生成工程化需求。"):
                    engineering_payload = generate_engineering_requirements(current_requirements, st.session_state.results)
                    if st.session_state.last_output:
                        retrieval_dir = Path(st.session_state.last_output).parent
                        out_path = save_engineering_requirements(retrieval_dir, engineering_payload)
                    else:
                        out_path = save_engineering_requirements(cfg.paths.search_results_dir, engineering_payload)
                    st.session_state.engineering_requirements = engineering_payload
                    st.session_state.last_engineering_output = str(out_path)
                st.success(f"工程化需求已生成：{out_path}")
            finally:
                st.session_state.is_generating = False
            st.rerun()

    if st.session_state.last_engineering_output:
        st.success("最近工程化需求输出已保存。")
        with st.expander("查看输出路径", expanded=False):
            st.code(st.session_state.last_engineering_output, language="text")

    payload = st.session_state.engineering_requirements
    if not payload:
        st.info("尚未生成工程化需求。点击上方按钮后可在需求图中查看层级结构和支撑状态。")
        return
    render_engineering_requirement_overview(payload)
    diagram_tab, table_tab, gap_tab, raw_tab = st.tabs(["需求图", "SysML 需求表", "证据缺口", "原始 JSON"])
    with diagram_tab:
        render_sysml_requirement_diagram(payload)
    with table_tab:
        render_sysml_requirement_table(payload)
    with gap_tab:
        gaps = []
        for req_set in payload.get("requirement_sets", []) or []:
            for gap in req_set.get("evidence_gaps", []) or []:
                gaps.append({
                    "需求集": req_set.get("requirement_set_id", ""),
                    "related_requirement_id": gap.get("related_requirement_id", ""),
                    "gap_type": gap.get("gap_type", ""),
                    "description": gap.get("description", ""),
                    "suggested_document_update": gap.get("suggested_document_update", ""),
                })
        if gaps:
            st.dataframe(pd.DataFrame(gaps), width="stretch", hide_index=True)
        else:
            st.success("没有单独列出的证据缺口。")
    with raw_tab:
        st.json(payload)


def render_app_shell(cfg: Any) -> None:
    from apps.experiment_ui import render_experiment_workspace, render_metrics_workspace
    render_nav_sidebar(cfg)
    active_workspace = st.session_state.active_workspace
    if active_workspace == "retrieval_workspace":
        render_retrieval_workspace(cfg)
    elif active_workspace == "retrieval_results":
        render_retrieval_results_workspace()
    elif active_workspace == "engineering_workspace":
        render_engineering_workspace(cfg)
    elif active_workspace == "experiment_comparison":
        render_experiment_workspace(cfg)
    elif active_workspace == "metrics_analysis":
        render_metrics_workspace(cfg)
    else:
        st.session_state.active_workspace = "retrieval_workspace"
        render_retrieval_workspace(cfg)


def main() -> None:
    st.set_page_config(page_title="多粒度需求证据检索", layout="wide", initial_sidebar_state="expanded")
    init_state()
    inject_css()
    cfg = get_config()
    render_app_shell(cfg)


if __name__ == "__main__":
    main()
