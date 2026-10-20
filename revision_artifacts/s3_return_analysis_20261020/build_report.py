"""Descriptive completeness only; no inferential or arm comparison results."""
from validate_return import *
import csv

def main():
    report=read(H/'VALIDATION_REPORT.json');d=H/'交付_返表核验与待补';d.mkdir(exist_ok=True)
    w=openpyxl.load_workbook(H/'raw/数值候选独立评分.xlsx',read_only=True);ws=w['评分50'];labels=Counter(ws.cell(i,2).value for i in range(6,56))
    errors=[{'blind_id':ws.cell(i,1).value,'cell':f'评分50!D{i}'} for i in range(6,56) if ws.cell(i,2).value=='错误'];w.close()
    dump(H/'DESCRIPTIVE_COMPLETENESS.json',{'correctness_labels_unstratified':dict(labels),'error_locator_missing':errors,'formal_statistics_computed':False,'agreement_computed':False,'note':'These are submitted labels and filling counts, not verified truth or independent-expert conclusions.'})
    rows=[]
    for x in report['missing_required_ratings']+report['missing_required_basis']:rows.append(['冻结验证必填',x['blind_id'],x['cell'],x['field']])
    for cell,label in [('B7','按真实情况说明作者关系，学历不能代替作者关系选项'),('B8','相关专业与工程经验'),('B10','既往接触输出或审核的情况'),('B11','如实确认是否独立完成且未交换答案；不得为通过验证改写事实'),('B12','实际记录阶段'),('B13','实际开始时间，含时区；不推算或编造'),('B14','实际完成时间，含时区；不推算或编造')]:rows.append(['冻结验证必填','身份/过程','身份与说明!'+cell,label])
    for x in errors:rows.append(['建议核实；不是现有脚本非空门槛',x['blind_id'],x['cell'],'错误判断的冲突位置、来源及页码；不要求改分'])
    rows.append(['待澄清；不自动改判','K849466','评分50!B50:C50','当前正确且工况不明：说明已核实范围与未知条件，保留原始两轴回答'])
    with (d/'最小补填与澄清清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['类别','盲ID或事项','原表位置','需要由评审本人提供']);writer.writerows(rows)
    text='''# S3返表核验：正式统计暂阻塞

收到附件35725字节，SHA256：`87f3153b7ddb329efd528a45621135a812298c0ca812d42eb59caae6a03a173f`。原件已原样保存，未修改评分、候选或论文。

50个盲ID唯一且匹配冻结样本，全部固定内容、定义和候选文本未改变。提交的正确性标签为：正确10、可接受2、错误9、无法判断29。这只是填写分布，不是核实后的正确率，也不是独立专家结论。

冻结脚本以退出码2返回blocked，未计算主次指标、配对差、未知界限、bootstrap、显著性或一致性。未生成正式统计结果。

需要补充：

- 12条“正确/可接受”的具体依据均为空。请本人提供真实来源、版本和页码，或明确实践判断依据；逐条ID及单元格见CSV。
- K522557的适用性C10和信心E10未填。
- 身份B7填的是学历背景，尚未回答作者关系；B8专业经验、B10既往接触、B12记录阶段、B13/B14含时区起止时间未填。B11“独立完成”未完整回答是否未交换答案。仅按真实过程补充，不能为了通过验证填写不实声明。
- 9条“错误”缺冲突位置，建议补充以便追溯；这是依据充分性待核实事项，不冒称现有脚本的必填门槛。备注可选，50个备注空白本身不构成阻塞。
- K849466“正确＋工况不明”需要说明核实范围，二者不自动视为互相矛盾，也不自动改判。
- 评审者是谁、是否作者以及是否使用AI逐条辅助判断，待作者/评审说明；不能据上下文推断造假，也不能声称独立外部专家评审已完成。资料接触版本和日期亦待确认。

验证器另报四张表“行列范围改变”。已定位为范围元数据兼容性问题：冻结模板没有dimension标签，契约记录为null；返表含明确dimension。两份文件实际范围完全一致（22×2、22×2、55×6、355×3），固定单元格也一致。不能据此认定用户改表。没有改冻结脚本或去掉该检查；后续若修复兼容性，须单独版本化和记录，不能趁机更改统计方案。

即使日后解决结构兼容性，现有依据及过程声明缺失仍会阻塞。当前不自补答案、不推断时间、不伪造第二评审或共识。保留此次原件；任何补填应另存新版本并说明变化。
'''
    (d/'返表核验摘要.md').write_text(text,encoding='utf8')
    for name in ['VALIDATION_REPORT.json','FROZEN_ANALYSIS_STDOUT.json','DIMENSION_DIAGNOSTIC.json','DESCRIPTIVE_COMPLETENESS.json']:shutil_copy(H/name,d/name)
    dump(H/'DELIVERY_MANIFEST.json',{p.relative_to(H).as_posix():sha(p) for p in d.iterdir() if p.is_file()})
    print('Descriptive completeness and blocked report generated; no outcome statistics.')

def shutil_copy(a,b):
    import shutil
    shutil.copy2(a,b)
if __name__=='__main__':main()
