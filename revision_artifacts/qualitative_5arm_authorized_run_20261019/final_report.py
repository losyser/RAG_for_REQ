"""Local verification/report only. No dispatch and no human judgment generation."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import json,sys
from runner import ROOT,WORK,V2,read,sha,digest,atomic,usage_cost,PROVIDERS

def main():
    summary=read(WORK/'RESULT_SUMMARY.json');pre=read(WORK/'RUN_PREFLIGHT.json')
    changed=[p for p,h in pre['protected_hashes'].items() if sha(p)!=h]
    frozen_changed=[p for p,h in pre['frozen_hashes'].items() if sha(p)!=h]
    assert not changed and not frozen_changed,(changed,frozen_changed)
    phase_data={};identities={}
    for phase,plan in [('generation',read(V2/'REQUESTS_300_PENDING.json')),('review',read(WORK/'QWEN_FROZEN_PLAN.json')['requests'] if (WORK/'QWEN_FROZEN_PLAN.json').exists() else [])]:
        folder=WORK/phase;attempts=sorted(folder.glob('*_attempt.json'));records=[];cost=Decimal(0);risk=Decimal(0);ids=[]
        if (folder/'RUNNING.lock').exists():raise RuntimeError('Cannot finalize while phase active')
        for index,p in enumerate(attempts):
            a=read(p);assert a['slot']==plan[index]['slot'] and a['body_sha256']==digest(plan[index]['body']);assert a['endpoint']==PROVIDERS[phase]['endpoint']
            rp=p.with_name(p.name.replace('_attempt','_response'));r=read(rp) if rp.exists() else {'status':'unresolved'};records.append(r)
            if r['status']=='completed':
                assert usage_cost(r['response'],PROVIDERS[phase])==Decimal(r['usage_cost_CNY']);cost+=Decimal(r['usage_cost_CNY']);ids.append(r['response']['id'])
            else:risk+=Decimal(a['reserved_CNY'])
        assert len(ids)==len(set(ids)),'duplicate response ids'
        phase_data[phase]={'planned':len(plan),'attempted':len(attempts),'completed':sum(r['status']=='completed' for r in records),'failed_or_unresolved':sum(r['status']!='completed' for r in records),'unsent':len(plan)-len(attempts),'usage_estimate_CNY':str(cost),'unresolved_max_risk_CNY':str(risk),'input_tokens_completed':sum(r['response']['usage']['prompt_tokens'] for r in records if r['status']=='completed'),'output_tokens_completed':sum(r['response']['usage']['completion_tokens'] for r in records if r['status']=='completed'),'state':read(folder/'state.json') if (folder/'state.json').exists() else {'status':'not_started'}}
        identities[phase]=[json.loads(s) for s in sorted({json.dumps(r['identity'],sort_keys=True) for r in records if r.get('identity')})]
    reviews=read(WORK/'REVIEW_DIAGNOSTICS.json');raw_support=Counter(r['machine_judgment'].get('support','missing') for r in reviews if r.get('machine_judgment'));raw_app=Counter(r['machine_judgment'].get('applicability','missing') for r in reviews if r.get('machine_judgment'))
    known=Decimal('0.563162')+sum(Decimal(v['usage_estimate_CNY']) for v in phase_data.values());risk=Decimal('4.325376')+sum(Decimal(v['unresolved_max_risk_CNY']) for v in phase_data.values());assert known+risk<=50
    # Verify that the existing API credentials never leaked into local experimental artifacts.
    sys.path.insert(0,str(ROOT));from cooling_rag_mg.config import DeepSeekConfig,QwenConfig
    keys=[DeepSeekConfig().api_key,QwenConfig().api_key];secret_files=[]
    for p in WORK.rglob('*'):
        if p.is_file() and p.suffix not in ['.pyc']:
            data=p.read_bytes()
            if any(k and k.encode() in data for k in keys):secret_files.append(str(p))
    assert not secret_files,'credential leak found; do not distribute'
    pair=read(WORK/'PAIRED_SOURCE_DIFFERENCES.json');pair_summary={}
    for arm in ['semantic','random']:
        rows=[x for x in pair if x['arm']==arm];pair_summary[arm]={'paired_sources':len(rows),'total_Q_count_difference_new_minus_old':sum(x['Q_count_difference_new_minus_old'] for x in rows),'total_TBD_candidate_difference_new_minus_old':sum(x['TBD_candidate_difference_new_minus_old'] for x in rows)}
    audit={'phases':phase_data,'known_usage_estimate_total_CNY':str(known),'unresolved_risk_total_CNY':str(risk),'modeled_total_CNY':str(known+risk),'remaining_to_50_CNY':str(50-known-risk),'billing_verified':False,'model_identities':identities,'protected_files_verified':len(pre['protected_hashes']),'protected_changed':changed,'frozen_changed':frozen_changed,'credential_scan_leaks':0,'paired_source_summary':pair_summary,'raw_machine_support':dict(raw_support),'raw_machine_applicability':dict(raw_app),'human_labels_completed':0,'main_experiment_modified':False}
    atomic(WORK/'FINAL_AUDIT.json',audit)
    lines=['五组定性判据附加实验——执行结果摘要（2026-10-19）','',
      '一、执行状态',f"DeepSeek：计划{phase_data['generation']['planned']}次，已发{phase_data['generation']['attempted']}次，成功{phase_data['generation']['completed']}次，失败/未决{phase_data['generation']['failed_or_unresolved']}次，未发{phase_data['generation']['unsent']}次。",
      f"Qwen：候选{summary['Q_candidates_total']}条，已发{phase_data['review']['attempted']}次，成功{phase_data['review']['completed']}次，失败/未决{phase_data['review']['failed_or_unresolved']}次，未发{phase_data['review']['unsent']}次。",
      '生成终态：'+phase_data['generation']['state']['status'],'评审终态：'+phase_data['review']['state']['status']]
    for phase,data in phase_data.items():
        if data['state'].get('stop_reason'):lines.append(phase+'暂停原因：'+str(data['state']['stop_reason']))
    lines+=['','二、输出分布（机械候选分类，不是工程正确性）']
    for g,s in summary['groups'].items():lines.append(f"{g}：完成{s['completed_sources']}/60源；{s.get('n_rows',0)}条输出；[Q]候选{s.get('q_candidate',0)}条，格式通过{s.get('q_format_pass',0)}条；TBD/混合候选{s.get('tbd_or_mixed_candidate',0)}条；数值候选{s.get('numeric_candidate',0)}条；未标记非数值候选{s.get('unmarked_nonnumeric_candidate',0)}条。")
    lines+=['','三、按源配对与Qwen判断','配对统计：'+json.dumps(pair_summary,ensure_ascii=False),'Qwen原始支持标签：'+json.dumps(dict(raw_support),ensure_ascii=False),'Qwen原始适用性标签：'+json.dumps(dict(raw_app),ensure_ascii=False),'经原句锚点/枚举检查后的抽样分层：'+json.dumps(summary['review_bands'],ensure_ascii=False),
      '机械格式通过、模型语义判断、来源可靠性与目标适用性分别报告。Qwen是跨模型意见，不是人工真值；未评、不确定、不支持及锚点核查失败均保留。不能将[Q]自动加入旧数值A/B。',
      '统计单位为源需求；不把同源shall当独立样本。单次T=0运行不能估计随机方差，也不证明提示词效应超过自然波动。noRAG约束不同，只作工作流比较。',
      '', '四、预算与风险',f"本轮DeepSeek成功usage估价：¥{phase_data['generation']['usage_estimate_CNY']}；Qwen成功usage估价：¥{phase_data['review']['usage_estimate_CNY']}。",f"含历史成功后的usage估价合计：¥{known}；历史及本轮未决风险预留：¥{risk}；累计模型账本：¥{known+risk}；距离¥50上限尚余¥{50-known-risk}。",
      '价格按峰值未缓存费率估算，不计折扣；不是核验后的实付账单。每次发送前使用服务上下文最大费用预留，失败保留全额风险并立即暂停，未自动重试。',
      '', '五、人工抽查与交付',f"已准备{summary['manual_sample_prepared']}条匿名抽查材料及空白判断CSV；人工判断完成0条，未联系或分配专家。抽样按预定组别/机器结果分层，不是总体真值或总体准确率估计。",
      '所有原始请求/响应、usage、返回model/可用指纹、阶段状态及未发队列保存在本目录generation/和review/。匿名包、映射密钥、原句锚点核查、源级计数与配对差异分开保存。',
      f"保护检查：{len(pre['protected_hashes'])}个既有文件哈希未变，冻结文件未变，凭据泄漏扫描0项。未修改KB、主实验、论文或既有人评。",
      '本结果只作为附加实验材料，不自动采用到论文或公开发布。',
      '', '项目交付目录：'+str(WORK), '关键文件：RESULT_SUMMARY.json、FINAL_AUDIT.json、SOURCE_LEVEL_COUNTS.json、SOURCE_LEVEL_REVIEW_COUNTS.json、PAIRED_SOURCE_DIFFERENCES.json、PAIRED_SOURCE_REVIEW_DIFFERENCES.json、REVIEW_DIAGNOSTICS.json、manual_sample/BLANK_HUMAN_JUDGMENTS.csv。']
    (WORK/'中文执行结果摘要_20261019.txt').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':main()
