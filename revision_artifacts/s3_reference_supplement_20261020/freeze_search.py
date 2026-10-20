"""Fix per-card search assignments before substantive document selection."""
from preflight import *
TOPICS={
'diagram':('系统图与边界','marine engine cooling system piping diagram documentation'),
'makeup':('膨胀水箱与补水','marine engine cooling expansion tank make up water level'),
'thermal':('冷却器与环境条件','marine engine cooling water heat exchanger ambient reference conditions'),
'sensor':('仪表量程与接口','marine cooling water temperature pressure sensor measurement range signal installation'),
'hydrotest':('水压试验','marine machinery cooling water piping turbocharger hydrostatic testing'),
'monitor':('温压液位监测','marine engine cooling water temperature pressure level monitoring alarm'),
'standby':('备用泵与切换','marine engine cooling water standby pump automatic manual changeover'),
'alarm':('报警与保护','marine engine cooling water alarm safety self monitoring acknowledgement'),
'intake':('海水取水与事故工况','海水循环冷却系统 取水构筑物 事故 输水管道 运行管理 标准'),
'flushing':('冲洗与清洁','marine diesel engine cooling system flushing cleaning operating instructions'),
'stability':('运行稳定性与控制','marine engine cooling water temperature control transient performance design'),
'shutdown':('停机与余热冷却','marine diesel engine high temperature cooling pump shutdown standby operation'),
'quality':('冷却水与添加剂','marine engine coolant fresh water quality additives hardness chloride pH'),
'valve':('温控阀','marine engine cooling water thermostatic valve pressure drop temperature control'),
'pump':('泵性能与调试','marine cooling water pump commissioning flow head performance acceptance'),
'vent':('排气与膨胀水箱','marine engine cooling water vent expansion tank deaeration'),
'records':('设计依据与文件控制','marine machinery design documentation sensor alarm settings technical file approval'),
'lowload':('低负荷与零负荷','dual fuel marine engine no load low load cooling water operating restrictions')}
ASSIGN=[('K211115','diagram',''),('K627088','makeup',''),('K591793','thermal','49/60DF'),('K783304','sensor',''),('K522557','hydrotest',''),('K849074','monitor','49/60'),('K168579','standby',''),('K636170','thermal','49/60'),('K748946','alarm','Scania DI16 EMS S6'),('K288080','monitor','L21/31 L16/24 L23/30H'),('K732549','diagram','49/60 L21/31'),('K452269','intake',''),('K997682','thermal',''),('K661062','alarm',''),('K330617','standby',''),('K901284','flushing',''),('K646321','stability',''),('K737574','shutdown',''),('K866911','shutdown',''),('K692349','quality',''),('K965410','quality',''),('K221247','alarm','Scania DI16 EMS S6'),('K817906','thermal',''),('K538764','monitor',''),('K573282','sensor',''),('K189805','thermal','L49/60DF'),('K124367','valve',''),('K395496','pump',''),('K323039','alarm','Scania DI16 EMS S6'),('K612522','quality','L23/30DF 49/60DF L16/24'),('K754421','monitor',''),('K620579','pump',''),('K692264','quality',''),('K823041','monitor',''),('K867382','makeup',''),('K204711','monitor','49/60'),('K464919','records',''),('K299956','vent','49/60DF'),('K814606','valve','L23/30DF'),('K797131','alarm',''),('K187408','thermal','L27/38'),('K807026','diagram',''),('K836062','flushing',''),('K244601','stability',''),('K849466','hydrotest','IACS turbocharger'),('K445671','alarm','Scania DI16 EMS S6'),('K972248','standby',''),('K746254','shutdown',''),('K227030','lowload',''),('K831135','valve','L16/24S L16/24')]
def main():
    assert not (AUDIT/'SEARCH_PROTOCOL_FROZEN.json').exists()
    visible=json.loads((AUDIT/'REVIEWER_VISIBLE_INPUT.json').read_text(encoding='utf8'));assert {r[0] for r in ASSIGN}==set(visible)
    queries={};cards=[]
    for code,topic,model in ASSIGN:
        title,terms=TOPICS[topic]
        q1=terms+' rules manual';d1=['iacs.org.uk','ccs.org.cn'] if topic not in ['intake','quality','flushing','shutdown','lowload'] else (['std.samr.gov.cn','openstd.samr.gov.cn','gov.cn'] if topic=='intake' else ['everllence.com','man-es.com','scania.com','mtu-solutions.com','wartsila.com'])
        if model.startswith('Scania'):q2='"Scania" "DI16" "S6" coolant operator manual';d2=['scania.com']
        elif model.startswith('IACS'):q2='IACS turbocharger water cooled casing hydraulic testing machinery requirements';d2=['iacs.org.uk']
        elif model:q2='"'+model.split()[0]+'" project guide cooling water system';d2=['everllence.com','man-es.com']
        else:q2=terms+' installation design guide';d2=['everllence.com','man-es.com','scania.com','mtu-solutions.com','wartsila.com','ccs.org.cn','iacs.org.uk'] if topic!='intake' else d1
        keys=[]
        for q,ds in [(q1,d1),(q2,d2)]:
            key=hashlib.sha256(json.dumps([q,ds],ensure_ascii=False).encode()).hexdigest()[:12];queries[key]={'q':q,'domains':ds};keys.append(key)
        cards.append({'blind_id':code,'topic':topic,'topic_title':title,'visible_model':model or '未明确型号；不得自行套用其他型号','queries':keys,'query_budget':2,'local_passes':1,'max_results_screened_per_query':5,'max_new_full_documents_per_query':2,'navigation_budget':'同一来源同一主题定位全部相关章节，正文与前后完整页、表头脚注及限制一起索引；不以候选数值检索或排序。'})
    policy={'version':'reference-procedure-v1','frozen_utc':datetime.now(timezone.utc).isoformat(),'procedure_amendment_after_sampling':True,'not_preregistered':True,'input':'Only reviewer-facing complete original sheet; no answer key, arm, grade or original evidence IDs used','query_rule':'Two slots per blind card: subject rules/manual and visible model cooling guide (or subject installation guide if no model). No candidate numeric thresholds included. Model numbers permitted. Identical query keys share a cached result, charged to every requesting card.','selection':'Local complete original first, then official public original. Screen first five official results in returned order. Prefer explicit model match over family; identifiable complete published version over extract; if version conflicts retain both within two-document/query cap. No ranking by numerical agreement. Exact model unknown is retained as gap.','stop':'One local catalog/text pass per card; two public search slots, maximum five result links screened and two complete documents selected per query. Each selected document URL may be fetched once plus one official redirect/retry. Login/payment/denial stops that URL. Do not broaden searches based on apparent correctness. Shared complete documents may serve all cards, including limiting information.','access':'No uploads, APIs, reviewer contact, login bypass or purchases. Restricted standards access recorded only. Local provenance unverified documents not presented as verified official downloads.','scope':'Document existence/topic match is not project applicability or a truth label. Include unresolved model/configuration/version/acceptance criteria gaps. No support/opposition labels.','existing_edits':'Desktop identity fields already edited; no scores in inspected cells. Preserve originals and record provision date. Do not require refilling or combine ratings under differing information conditions. External copies unknown.','connectivity_preflight':'Two Scania connectivity searches occurred before protocol freeze; not used as evidence-based source selection. The frozen Scania slot is executed/cached under the same limits.'}
    dump(AUDIT/'SEARCH_PROTOCOL_FROZEN.json',policy);dump(AUDIT/'QUERY_PLAN.json',queries);dump(AUDIT/'CARD_SEARCH_PLAN.json',cards)
    print(json.dumps({'cards':len(cards),'query_slots':sum(c['query_budget'] for c in cards),'unique_queries':len(queries)},ensure_ascii=False))
if __name__=='__main__':main()
