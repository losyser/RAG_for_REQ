"""Neutral navigation from shared complete publications; no judgments or experimental keys."""
import html,collections,urllib.parse
import fitz
from preflight import *
from freeze_search import TOPICS
from index_pdfs import KEYWORDS
esc=html.escape
COMMON_LIMIT='来源与主题相符不等于适用于项目。须核对发动机/控制系统版本、用途、船级/合同日期、工况及项目批准文件。候选声明不是事实，本页不提供正确性或支持/反对判定。'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def clean(s):return re.sub(r'\s+',' ',s).strip()
def describe(r,pages):
    url=r.get('url','');first='\n'.join(p['text'] for p in pages[:2]);file=r['file'];code=r.get('local_code')
    scope='按出版物封面和适用范围；项目适用性未核实。';models=[];kind='制造商资料';version='见封面及各章节修订日期，不能由下载日期推断'
    if code=='CCS2024':title='CCS Rules for Classification of Sea-Going Steel Ships 2024（英文完整版）';kind='通用船级规范';scope='2024版，2024-07-01生效；须核对船舶入级、建造合同和适用修订。';version='R001-2024'
    elif code=='CCS2025':title='中国船级社《钢质海船入级规范》2025（中文完整版）';kind='通用船级规范';scope='2025版，2025-07-01生效；2024与2025不可无条件互换。';version='R001-2025'
    elif code=='IACS_M':title='IACS Requirements concerning Machinery Installations（本地完整汇编）';kind='通用船级要求';scope='汇编内各UR分别注明版本和实施日期；汇编总体发布日期未确认。';version='各UR各自版本，见完整页眉/脚注'
    elif code=='MAN4960_LOCAL':title='Everllence 49/60 Project Guide — IMO Tier II（本地完整原件）';models=['49/60'];scope='49/60柴油机；不得自动替代49/60DF或未指定型号。'
    elif 'Cooling-System_Issue-7' in url:title='Scania Cooling system — Marine engines DI09, DI13, DI16';models=['Scania DI16'];version='02:05 Issue 7.0 en-GB，©2015';scope='船用DI09/DI13/DI16；不同回路/龙骨冷却/换热器配置需区分。'
    elif 'opm_0000460' in url:title='Scania Operator’s Manual DI16 EMS with S6/PDE';models=['Scania DI16 EMS S6'];version='©2011，文号见原件';scope='DI16船用、EMS S6/PDE；控制功能激活与配置条件必须同时核对。'
    elif 'Electrical-Systems' in url:title='Scania Installation manual — Electrical system';models=['Scania DI16 EMS S6'];scope='区分S6、S8、PDE、XPI和SCR系统；网址issue编号不替代正文版本。'
    elif '4960DF' in url or '49-60df' in url:title='49/60DF Project Guide — Marine';models=['49/60DF','L49/60DF'];scope='49/60DF双燃料；区分燃气/液体模式、推进方式与排放等级。'
    elif '_4960.pdf' in url:title='49/60 Project Guide — Marine';models=['49/60'];scope='49/60柴油机；Tier II与Tier III版本分别保留，不替代DF。'
    elif 'L2330DF' in url:title='L23/30DF Project Guide — Marine';models=['L23/30DF'];scope='L23/30DF；分项章节可能列其他型号，须按各章节标题核对。'
    elif 'L2738' in url:title='L27/38 Project Guide — '+('Propulsion' if 'Propulsion' in url else 'GenSet');models=['L27/38'];scope='须区分推进用途与发电机组用途；模块内各页有独立文号/修订日期。'
    elif 'L2131' in url:title='L21/31 Project Guide';models=['L21/31'];scope='L21/31及封面规定用途/排放等级；不得推定L16/24或L23/30H同样适用。'
    elif 'L1624' in url:title='L16/24 Project Guide — Marine';models=['L16/24'];scope='L16/24；L16/24S变体需另核对，不能仅据名称相近等同。'
    elif 'V2833' in url:title='V28/33D STC Project Guide';models=['V28/33D STC'];scope='V28/33D STC用途与排放等级限定；只供未指定型号条目查方法和限制。'
    elif '3240' in url:title='32/40CD Project Guide';models=['32/40CD'];scope='32/40CD及TCF/NR变体限定，不推定适用于其他发动机。'
    elif '175D' in url:title='175D Project Guide';models=['175D']
    elif 'MS15029' in url:title='MTU Operating Instructions — Series 1600 marine diesel';models=['MTU Series 1600'];scope='按封面发动机变体；冲洗程序不得直接推广到所有主机。'
    elif 'A0010' in url:
        number=re.search(r'A001\d+_\d+E',url)[0];title='MTU Fluids and Lubricants Specifications — '+number;version=number
        scope=clean(first[:550])+'；注意燃气/柴油/发电机组及轻金属回路区别，不跨系列套用。'
    elif 'sl2016-623' in url:title='MAN Service Letter SL2016-623 — Cooling water treatment';version='SL2016-623';scope='按服务信函Action Code和所列发动机系列；不是所有柴油机的统一水质标准。'
    elif 'efficiency-improvements' in url:title='MAN Efficiency improvements — Main engine auxiliary systems';scope='设计方法与效率讨论；不替代项目批准的控制阈值。'
    elif 'G95ME' in url:title='G95ME-C10.7 Project Guide';models=['G95ME-C10.7'];scope='二冲程G95ME系列；不能直接套用于四冲程主机。'
    elif any(x in url for x in ['G60ME','S50ME','S60ME']):title=urllib.parse.unquote(url.split('/')[-1]).replace('.pdf','')+' Project Guide';models=[title.split()[0]];scope='二冲程机型专用，未指定型号时仅作方法背景。'
    elif 'E-13' in first:title='CCS E-13 Monitoring and Alarm (Display) System';kind='报警产品检验指南';version='Guideline E-13（201510）';scope='监测报警产品认可与检验，不能推定为项目数值设定表。'
    elif 'M-02' in first:title='CCS M-02 Turbochargers';kind='增压器检验指南';version=clean(first)[0:90];scope='增压器产品及类别限定；水冷腔试验与整船冷却管系试验对象不同。'
    elif 'INTELLIGENT MACHINERY' in first:
        year=re.search(r'20\d{2}',first)[0];title='CCS Guidelines for Surveys of Intelligent Machinery of Ships '+year;kind='智能机舱指南';version=year;scope='智能机舱监测及相应附加标志范围；不是通用报警定值依据。'
    else:title=clean(first[:180]) or r.get('search_title',Path(file).stem)
    dates=re.findall(r'(?:Revision|Date)\s*\.*\s*([0-9][^\n]+)',first)
    if dates:version='；'.join(clean(x) for x in dates[:2])
    if 'opm_0000460' in url:version='©2011；opm_d16mar_en-GB；2 291 675'
    if 'Electrical-Systems' in url:version='Issue 11 en-GB；©2018（原件版本与URL标号不同）'
    if Path(file).stem=='official_260b8e1a27':title='L23/30DF Project Guide — GenSet';scope+=' 本版本为GenSet用途。'
    publisher='CCS' if kind!='制造商资料' and code!='IACS_M' else ('IACS' if code=='IACS_M' else ('Scania' if 'Scania' in title else ('MTU / Rolls-Royce Power Systems' if 'MTU' in title else 'MAN Energy Solutions / Everllence')))
    return {'title':title,'kind':kind,'models':models,'version':version,'scope':scope,'publisher':publisher}
def sections(index,topic):
    """Use lexical section headings, not candidate values. Full contiguous sections retained."""
    toc=index['toc'];found=[];n=index['page_count'];terms=KEYWORDS[topic];name=Path(index['file']).stem
    curated=None
    if name.startswith('CCS_SeaGoingSteelShips_'):
        modern='2025' in name
        general=(1381,1385,'轮机一般规定与环境条件') if modern else (1474,1478,'Machinery general provisions and environment')
        plans=(1386,1387,'泵与管系一般规定、提交图纸') if modern else (1479,1480,'Pumping and piping general provisions, plans')
        pumps=(1401,1403,'泵阀附件、试验与布置') if modern else (1493,1495,'Pumps, fittings, tests and arrangement')
        cooling=(1445,1446,'第3篇第4章第5节 冷却水管系及相邻页') if modern else (1541,1543,'Part 3 Chapter 4 Section 5 Cooling water systems and adjacent page')
        control=(1913,1916,'自动化基本要求、控制/安全/报警系统') if modern else (2004,2007,'Automation control, safety and alarm systems')
        sensors=(1924,1925,'传感器及遥控装置') if modern else (2017,2018,'Sensors and remote control')
        alarms=(1933,1945,'AUT-0自动化监视完整表、表头与备注；附加标志范围') if modern else (2028,2038,'AUT-0 complete monitoring tables, headings and notes; notation-specific')
        curated={'diagram':[plans,cooling],'makeup':[cooling],'thermal':[general,cooling],'sensor':[sensors,control],'hydrotest':[pumps],'monitor':[control,alarms],'standby':[cooling,control],'alarm':[control,alarms],'stability':[control,general],'valve':[cooling,pumps],'pump':[pumps,cooling],'vent':[cooling],'records':[plans,control]}.get(topic,[])
    elif name=='IACS_Machinery_Requirements_local_full':
        curated={'thermal':[(41,41,'UR M28 Ambient reference conditions, including note')],'monitor':[(49,55,'UR M35 complete 7-page requirement, tables and all notes')],'alarm':[(42,44,'UR M29/M30 alarm and safety systems'),(49,55,'UR M35 complete tables and all notes')],'hydrotest':[(257,263,'UR M73 Turbochargers, full requirement and categories')]}.get(topic,[])
    elif name=='MAN_4960_local_complete':
        curated={'monitor':[(133,139,'2.17 Operating/service temperatures and pressures; full tables and notes'),(225,237,'3.10 Engine-located measuring and control devices')],'sensor':[(225,237,'3.10 Engine-located measuring and control devices')],'diagram':[(318,343,'5.6 Cooling water system, all subsections')],'shutdown':[(318,343,'5.6 Cooling water system; operating and preheating conditions')],'standby':[(318,343,'5.6 Cooling water system; pumps and operating conditions')],'vent':[(318,343,'5.6 Cooling water system; venting and expansion arrangements')]}.get(topic)
    elif name=='official_0fe226fb52':
        curated={'alarm':[(19,22,'Running, coolant-temperature protection and alarm reset; complete context')],'monitor':[(19,22,'Running and coolant temperature'),(45,45,'Checking coolant level monitor')],'quality':[(31,35,'Cooling system, checking and changing coolant')],'flushing':[(36,38,'Cleaning cooling system including external/internal cleaning and cooler')],'shutdown':[(22,24,'Engine stopping and checks after running')]}.get(topic)
    mechanical=['diagram','makeup','thermal','valve','pump','standby','vent','shutdown','stability']
    if name in ['official_f01490a644','official_260b8e1a27']:
        offset=14 if name=='official_260b8e1a27' else 0
        ranges={t:[(171,218,'B13 Cooling water system, complete chapter including tables, notes and operating limits')] for t in mechanical}
        ranges.update(quality=[(177,188,'Coolant specification, inspection and cleaning')],flushing=[(185,188,'Cleaning cooling water system')])
        if topic in ranges:curated=[(s+offset,e+offset,t) for s,e,t in ranges[topic]]
    if name in ['official_fae10eb604','official_31144db92f']:
        if topic in mechanical:curated=[(209,232,'B13 complete cooling water chapter, including specification and inspection')]
        if topic=='thermal':curated.append((51,54,'D10 List of capacities, complete tables'))
        if topic=='quality':curated=[(221,232,'Coolant specification, cleaning and inspection')]
        if topic=='flushing':curated=[(227,230,'Cleaning cooling water system'),(461,462,'P69 Flushing cooling water system')]
    if name=='MAN_4960_local_complete' and topic=='thermal':curated=[(100,139,'Operating conditions, cooler data and operating/service tables with notes'),(318,343,'5.6 Complete cooling water system')]
    mtu={'official_27ea4a4b13':{'quality':[(11,13,'Coolants'),(28,29,'Approved additives')],'flushing':[(31,36,'Flushing and cleaning')]},'official_1d61e5181a':{'quality':[(17,35,'Coolant requirements'),(96,116,'Approved coolants and applicability')],'flushing':[(117,122,'Flushing and cleaning')]},'official_06d8c82268':{'quality':[(29,66,'Coolant requirements and applicability')],'flushing':[(100,109,'Flushing and cleaning')]}}
    if name in mtu and topic in mtu[name]:curated=mtu[name][topic]
    if name=='official_0ab7312201':curated=[]
    if curated is not None:
        return [{'start':s,'end':e,'title':t,'printed_start':index['pages'][s-1]['printed'],'printed_end':index['pages'][e-1]['printed']} for s,e,t in curated]
    for i,(level,title,start) in enumerate(toc):
        if any(t in title.lower() for t in terms):
            end=n
            for nextlevel,_,nextpage in toc[i+1:]:
                if nextlevel<=level and nextpage>start:end=nextpage-1;break
            if end-start>60:end=min(n,start+12) # navigation window; full publication still supplied
            found.append((start,end,title))
    if not found:
        # Topic occurrences excluding contents/index lists; include surrounding complete pages.
        for p in index['pages']:
            text=p['text'];lower=text.lower()
            if len(text)<250 or 'table of contents' in lower or 'contents\n' in lower or '目\n录' in text:continue
            hits=p['topics'].get(topic,[])
            if hits:
                # Avoid a generic word alone for topics with precise vocabulary.
                if topic in ['sensor','alarm','monitor'] and not any(x in lower for x in ['cool','engine','冷却','柴油机','报警系统','alarm system','monitoring and alarm']):continue
                title=clean(text.splitlines()[0])[:90]
                found.append((max(1,p['pdf_page']-1),min(n,p['pdf_page']+1),title))
    merged=[]
    for start,end,title in sorted(found):
        if merged and start<=merged[-1][1]+1:
            prev=merged[-1];merged[-1]=(prev[0],max(prev[1],end),prev[2])
        else:merged.append((start,end,title))
    return [{'start':s,'end':e,'title':t,'printed_start':index['pages'][s-1]['printed'],'printed_end':index['pages'][e-1]['printed']} for s,e,t in merged]
def main():
    acquisition=read(AUDIT/'ACQUISITION_LOG.json');indices={p.stem:read(p) for p in (AUDIT/'pdf_text_cache').glob('*.json')};docs=[];hash_seen={};duplicate=[]
    for r in acquisition:
        if r['status']=='unavailable':continue
        if r['sha256'] in hash_seen:
            hash_seen[r['sha256']]['alternate_urls'].append(r.get('url',''));duplicate.append(r['file']);continue
        idx=indices[Path(r['file']).stem];d={**describe(r,idx['pages']),'file':r['file'],'sha256':r['sha256'],'pages':r['pages'],'url':r.get('url',''),'alternate_urls':[],'acquisition':r['method'],'query_ids':r.get('query_ids',[]),'pdf_integrity':'可打开、未加密、首尾页及页数已检查；保留原字节。完整性仍须以出版物目录/页尾和版本对照。','local_url_limit':r.get('source_url_status',''),'topics':{t:sections(idx,t) for t in TOPICS},'first_pages':[1,min(2,r['pages'])]}
        if r.get('local_code'):d['local_code']=r['local_code']
        docs.append(d);hash_seen[r['sha256']]=d
    docs.sort(key=lambda d:(d['publisher'],d['title'],d['version'],d['file']))
    # Assign neutral catalog handles independent of all experimental identities.
    for i,d in enumerate(docs,1):d['catalog_id']='doc'+str(i)
    cards=read(AUDIT/'CARD_SEARCH_PLAN.json');visible=read(AUDIT/'REVIEWER_VISIBLE_INPUT.json');selections=read(AUDIT/'SOURCE_SELECTION_LOG.json');qlogs={q['query_id']:q for q in selections}
    navigation=[]
    for card in cards:
        topic=card['topic'];model=card['visible_model'];specified=not model.startswith('未明确');v=visible[card['blind_id']]
        candidates=[]
        for d in docs:
            sect=d['topics'][topic]
            if not sect:continue
            if topic=='intake':continue # Fixed intake queries returned no applicable land-based original; marine intake is a different object.
            exact=specified and any(m.lower() in model.lower() for m in d['models'])
            # DF and S suffixes are never silently equated to base models.
            if ('DF' in model and all('DF' not in m for m in d['models'])):exact=False
            if 'Scania' in model and topic=='alarm' and 'EMS S6' not in ' '.join(d['models']):exact=False
            local_rule=d.get('local_code') in ['CCS2024','CCS2025','IACS_M']
            query_match=bool(set(card['queries'])&set(d['query_ids']))
            if specified and not exact and not local_rule and not query_match:continue
            rank=(0 if exact else 1 if local_rule else 2 if query_match else 3,d['title'],d['version'])
            candidates.append((rank,d,exact,sect))
        candidates.sort(key=lambda t:t[0]);chosen=candidates[:3];refs=[]
        for rank,d,exact,sects in chosen:
            refs.append({'catalog_id':d['catalog_id'],'file':d['file'],'title':d['title'],'relation':'可见型号相符，仍须核对变体/条件' if exact else ('通用规范背景，不是项目数值设定表' if d.get('local_code') in ['CCS2024','CCS2025','IACS_M'] else '主题参考；不可推定适用未指定或不同型号'),'model_match':exact,'sections':sects[:3],'additional_sections_in_catalog':max(0,len(sects)-3)})
        gaps=['项目批准的设计基准、设备清单、实际控制配置与制造商项目专用定值未提供；不能由通用手册补造。']
        if not specified:gaps.append('候选未明确型号；通用或其他型号资料仅用于理解方法与查找限制。')
        elif not any(r['model_match'] for r in refs):gaps.append('本次固定检索额度内未取得可确认匹配的完整指定型号原版；相关型号不能自动代替。')
        if 'L16/24S' in model:gaps.append('L16/24S与L16/24变体范围须逐章节确认；未取得单独S型完整指南。')
        if topic=='intake':gaps=['固定查询未找到海水循环冷却系统取水构筑物及陆上事故输水管道的完整同类标准；船用海水吸入管系资料不替代陆上构筑物规范。需合法取得相应标准及项目设计条件。']
        model_items=model.split() if specified and not model.startswith(('Scania','IACS')) else ([model] if specified else [])
        per_model=[]
        for item in model_items:
            matched=[d['catalog_id'] for d in docs if item in d['models'] and d['topics'][topic]]
            per_model.append({'model':item,'topic_catalog_ids':matched,'status':'有名称相符的主题导航；变体/工况未核实' if matched else '本次固定检索未取得可确认的型号主题导航'})
        for item in per_model:gaps.append('逐型号：'+item['model']+' — '+item['status'])
        if len(model_items)>1:gaps.append('冻结的型号查询仅使用首个型号，其他型号仅检查共享资料库；未临时增补查询。一个型号有资料不代表本条全部型号有据。')
        nav={**card,'per_model_coverage':per_model,'condition_as_candidate_claim':v.get('适用条件',''),'parameters_as_candidate_claim':v.get('数值判据',''),'references':refs,'topic_navigation_available':bool(refs),'explicit_model_navigation_available':any(r['model_match'] for r in refs),'gaps':gaps,'query_results':[{'query_id':q,'screened':qlogs[q]['screened_count'],'selected':qlogs[q]['selected_count'],'stop_reason':qlogs[q]['stop_reason']} for q in card['queries']]};navigation.append(nav)
    dump(PACK/'来源与版本清单.json',docs);dump(PACK/'逐条资料导航.json',navigation)
    summary={'cards':50,'topic_navigation_available':sum(n['topic_navigation_available'] for n in navigation),'topic_navigation_missing':sum(not n['topic_navigation_available'] for n in navigation),'explicit_model_cards':sum(not n['visible_model'].startswith('未明确') for n in navigation),'explicit_model_navigation_available':sum(n['explicit_model_navigation_available'] for n in navigation),'unique_complete_pdf_bytesets':len(docs),'downloaded_url_failures':sum(r['status']=='unavailable' for r in acquisition),'query_slots':100,'unique_queries':44,'ratings_produced':0,'coverage_definition':'Only a relevant complete-document navigation exists, not factual correctness, numerical coverage, model applicability or evidence sufficiency.','duplicate_identical_files':duplicate}
    dump(AUDIT/'COVERAGE.json',summary)
    (PACK/'使用说明.txt').write_text('中性查证资料包 reference-procedure-v1，编制日期2026-10-20。\n先打开“阅读入口.html”，按盲编号或设备主题查找，再打开完整PDF。PDF页码从1开始；印刷页码可能按章节重置，需连同章节标题/文号记录。\n务必同读完整章节、表头、脚注、相邻页、适用范围和限制。本包不提供判定，候选声明不是事实；找到资料不代表适用于项目。不同型号、版本、用途不得自动互换。找不到时记录缺口，不推导真值。\n本包为冻结抽样后的评审程序补充，不是预注册程序。原评分表已有身份栏编辑，已保护；不要求重填，不覆盖任何原件。协调者应记录实际资料发放/查阅日期、评审开始/完成情况；不同资料条件的评分分开保留，不混合分析，不以补充资料自动重判。编制日期不等于已发放日期。\n统一规则：每条1次本地目录/全文检索、2个公开查询槽，每查询最多筛前5项、选择最多2份完整原版。相同查询共享结果，逐条记录同等预算；不使用候选数值搜索，不查答案键。\n本包未代替项目专用设计文件，未核实外部评审资格或资料实际接触情况；仅供本次本地评审查阅，保留原出版物版权标识，不公开转载或绕过付费/受限访问。\n',encoding='utf8')
    style='body{font:16px/1.65 "Microsoft YaHei",sans-serif;color:#243547;background:#f3f5f8;margin:0}main{max-width:1120px;margin:auto;padding:30px}h1{font-size:29px}h2{font-size:22px}h3{font-size:18px}article,section{background:white;border:1px solid #d9e1ea;border-radius:8px;padding:22px;margin:20px 0}a{color:#205d91}li{margin:8px 0}.muted{color:#526476}.notice{background:#fff4d8;padding:16px;border-left:5px solid #aa7a20}nav{line-height:2.1}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}code{overflow-wrap:anywhere}details{margin:12px 0}.tag{font-size:13px;background:#e7eef6;padding:4px 8px}'
    def page_link(d,n,label):return '<a href="'+esc(urllib.parse.quote(d['file'])+'#page='+str(n))+'">'+esc(label)+'</a>'
    sourcehtml=['<!doctype html><meta charset="utf-8"><title>来源与双页码导航</title><style>'+style+'</style><main><h1>完整原文与版本索引</h1><p><a href="阅读入口.html">返回盲编号导航</a></p><p class="notice">'+COMMON_LIMIT+' 印刷页码须与章节标题同时使用；不根据固定偏移猜页码。保留全部原PDF，可直接查看跨页表格与脚注。</p>']
    for d in docs:
        sourcehtml.append('<article id="'+d['catalog_id']+'"><h2>'+esc(d['title'])+'</h2><p>'+esc(d['publisher']+'｜'+d['version'])+'</p><p>'+esc(d['scope'])+'</p><p>'+page_link(d,1,'完整原版PDF（'+str(d['pages'])+'页）')+' · '+page_link(d,d['pages'],'末页')+'</p>')
        if d['url']:sourcehtml.append('<p>官方来源：<a href="'+esc(d['url'])+'">出版者原下载链接</a>（网络可用性可能变化；本地完整PDF不依赖联网）</p>')
        else:sourcehtml.append('<p>本地已有原版。原始下载直链未确认；出版机构门户：<a href="'+('https://iacs.org.uk/' if d['publisher']=='IACS' else 'https://www.ccs.org.cn/' if d['publisher']=='CCS' else 'https://www.everllence.com/')+'">官方网站</a>。门户不是原文件直链，来源链不完整已记录。</p>')
        sourcehtml.append('<p class="muted">SHA256：<code>'+d['sha256']+'</code></p>')
        for topic,sects in d['topics'].items():
            if not sects:continue
            sourcehtml.append('<details><summary>'+esc(TOPICS[topic][0])+'：'+str(len(sects))+'处章节／完整页窗口</summary><ul>')
            for sec in sects:
                label=f"PDF {sec['start']}–{sec['end']}；印刷 {sec['printed_start']} → {sec['printed_end']}；{sec['title']}"
                sourcehtml.append('<li>'+page_link(d,sec['start'],label)+'（请连续读到终页，含表头、脚注及限制）</li>')
            sourcehtml.append('</ul></details>')
        sourcehtml.append('</article>')
    (PACK/'来源与页码索引.html').write_text(''.join(sourcehtml)+'</main>',encoding='utf8')
    content=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>独立数值评审 · 中性查证资料</title><style>'+style+'</style><main><h1>独立数值评审 · 中性查证资料</h1><p>评审程序补充 reference-procedure-v1 · 编制于2026-10-20 · 只读导航，不保存答案</p><p class="notice">'+COMMON_LIMIT+'</p><p><a href="使用说明.txt">中文使用说明与程序补充</a> · <a href="来源与页码索引.html">完整原文、版本与双页码索引</a> · <a href="检索与缺口日志.html">统一检索与缺口日志</a></p><p>本次提供主题导航 '+str(summary['topic_navigation_available'])+'/50；这不是数值核实率或正确率。原评分表不在本目录，已有记录不覆盖、不要求重填。资料实际发放日期由协调者另记。</p><nav>']
    content.append(' · '.join('<a href="#'+n['blind_id']+'">'+n['blind_id']+'</a>' for n in navigation));content.append('</nav>')
    for n in navigation:
        content.append('<article id="'+n['blind_id']+'"><span class="tag">'+esc(n['topic_title'])+'</span><h2>'+n['blind_id']+'</h2><p><b>可见设备／型号：</b>'+esc(n['visible_model'])+'</p><p><b>候选声称的工况（未核实）：</b>'+esc(n['condition_as_candidate_claim'])+'</p><p><b>待查参数：</b>'+esc(n['parameters_as_candidate_claim'])+'（候选数值非事实或答案）</p><h3>同格式原文导航</h3><ul>')
        for ref in n['references']:
            content.append('<li><a href="来源与页码索引.html#'+ref['catalog_id']+'">'+esc(ref['title'])+'</a> — '+esc(ref['relation'])+'<ul>')
            for sec in ref['sections']:content.append('<li>'+page_link(ref,sec['start'],f"PDF {sec['start']}–{sec['end']}；印刷 {sec['printed_start']} → {sec['printed_end']}")+'；'+esc(sec['title'])+'</li>')
            content.append('</ul>须同读表头、脚注和范围；其余相关章节在完整来源索引中。</li>')
        if not n['references']:content.append('<li>本次未找到可采用的同主题完整原版。保留缺口，不以异类资料代替。</li>')
        content.append('</ul><h3>缺口与查证边界</h3><ul>'+''.join('<li>'+esc(g)+'</li>' for g in n['gaps'])+'</ul><p class="muted">检索机会：本地1次；公开查询2槽；前5项/槽；最多2份完整资料/槽。相同查询共享结果。</p></article>')
    (PACK/'阅读入口.html').write_text(''.join(content)+'</main></html>',encoding='utf8')
    logs=['<!doctype html><meta charset="utf-8"><title>检索与缺口日志</title><style>'+style+'</style><main><h1>检索规则与访问记录</h1><p><a href="阅读入口.html">返回阅读入口</a></p><p>冻结抽样后的程序补充；两类查询按设备/型号/参数/工况生成，不用候选具体数值。相同查询共享结果，任何条目均可查阅本包全部原版。未进行实验臂差异择优补充。</p><p>每条2查询槽，44个不同查询共服务100槽；无结果与超时均保留。下载发生一次长响应中断，完整已下载文件保留；剩余请求采用75秒总超时，未新增查询或按数值方向改变来源。</p>']
    for n in navigation:
        logs.append('<section><h2>'+n['blind_id']+'</h2>')
        for key in n['queries']:
            q=qlogs[key];logs.append('<p>'+esc(q['query']['q'])+'</p><p>筛查 '+str(q['screened_count'])+' 项；选择 '+str(q['selected_count'])+' 份；'+esc(q['stop_reason'])+'</p>')
        logs.append('</section>')
    logs.append('<h2>原文件下载失败／访问需求</h2><ul>')
    for r in acquisition:
        if r['status']=='unavailable':logs.append('<li><a href="'+esc(r['url'])+'">'+esc(r.get('search_title','官方资料'))+'</a>：本次未取得完整原件（超时或访问失败）；不绕过权限，需出版者可访问原版。</li>')
    logs.append('</ul><p>海水取水构筑物标准：固定查询未取得完整标准及明确版本；需合法获取相应国家/行业标准和项目条件，不能从候选数值反推标准。受限/收费资料仅记录访问需求。</p></main>')
    (PACK/'检索与缺口日志.html').write_text(''.join(logs),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
