"""Add inactive fields from Library page text; distinguish byte/archive verification."""
from pathlib import Path
import json,re
W=Path(__file__).resolve().parent
read=lambda n:json.loads((W/n).read_text('utf8'))
def dump(n,x):(W/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf8')
o=read('source_corrections_candidate.json');r=read('MTU_LIBRARY_PAGE_READ.json')['results']
page=next(x for x in r if x['pages']==[16]);title=next(x for x in r if x['pages']==[1])
txt='\n'.join(x for x in page['content'] if isinstance(x,str));assert '50% by volume' in txt and 'A001065/02E 2020-04' in txt
assert 'Series 1600 PowerPack' in str(title['content'])
source=o['sources'][1]
source.update({'source_id':'MTU-A001065-02E-202004-P16','requested_version':'A001065/02E 2020-04','library_file_id':page['library_file_id'],'library_file_id_version':page['file_id'],'size_bytes':802692,'page_count':57,'sha256':'4fd8866479ffbdb9a51b8f2b61f9d48d7906c72a1930763833a2e1b74cfe3d01','sha256_verification':'parent-reported original-byte hash; not recomputed locally','local_archive_complete':False,'materialization_limitation':'Official helper downloaded but failed Windows os.setxattr; did not install file. Direct requests returned406; Windows curl failed schannel credentials. No access/security changes.','verification':'Library backing-file text read for P1/P16; parent visually verified P16. P16 image not returned by Library in this execution.','model_scope':'Series 1600 PowerPack','project_applicability':'unknown; not a general marine-engine limit','old_KB_edition_match':False,'old_KB_comparison':'E-SYS-WATER-006 P16 starts with matching text but ends mid-word before preservation/dilution/pure-water conditions; overlap is not proof of original file identity.','section':'Coolants / Avoiding damage in the coolant system / Important','source_text':txt,'parameters':[]})
bullets=re.split(r'\n\s*•\s*',txt)[1:]
assert len(bullets)==7
specs=[('initial_fill','=',50,['Initial filling']),('restore_after_loss_or_dilution','=',50,['Topping up after coolant loss OR antifreeze concentration below40% by volume']),('minimum_antifreeze','>=',40,['Lower concentrations inadmissible for corrosion protection']),('maximum_antifreeze','<=',55,['Exceeding55% reduces antifreeze protection and heat dissipation']),('contaminant_exclusion',None,None,['No oil or copper residue, solid or dissolved']),('full_circuit_and_preservation',None,None,['Corrosion inhibition depends on completely filled circuit','After draining without refilling, preserve circuit using approved internal-preservation antifreeze; refer A001070/..']),('residual_dilution_check',None,None,['Residual used coolant/fresh flushing water can dilute new mixture','Check circuit concentration and adjust if necessary'])]
rows=[]
for i,(key,op,value,conds)in enumerate(specs,1):
 span=bullets[i-1]
 if i==7:span=span.split('Important')[0].strip()
 rows.append({'candidate_id':f'MTU02E-P16-{key}','historical_related_ids':['E-SYS-WATER-006'],'source_id':source['source_id'],'page':16,'bullet':i,'parameter':'antifreeze concentration' if value is not None else key,'value':value,'unit':'% by volume' if value is not None else None,'operator':op,'interface':'cooling system/coolant circuit','conditions':conds,'source_span':span,'model_scope':'Series 1600 PowerPack','project_applicability':'unknown','chemistry':'antifreeze; do not relabel as ethylene glycol without product approval evidence','enabled':False})
rows.append({'candidate_id':'MTU02E-P16-pure_water','historical_related_ids':['E-SYS-WATER-006'],'source_id':source['source_id'],'page':16,'bullet':'Important','parameter':'pure water operation','value':None,'unit':None,'operator':'prohibited_without','interface':'engine cooling system','conditions':['No operation with pure water without addition of approved corrosion inhibitor','Do not rewrite as unconditional ban on all water-based coolants'],'source_span':txt.split('Important',1)[1].split('TIM-ID:')[0].strip(),'model_scope':'Series 1600 PowerPack','project_applicability':'unknown','enabled':False})
source['parameters']=[x['candidate_id'] for x in rows]
o['parameters']=[x for x in o['parameters'] if not x['candidate_id'].startswith('MTU02E-')]+rows
dump('source_corrections_candidate.json',o)
d=read('SOURCE_DIFFERENCES.json');d['MTU']=source;d['MTU_field_changes']={'affected_id':'E-SYS-WATER-006','retained_numeric_values':[40,50,55],'new_bindings':['% by volume, not unspecified percent','Initial fill50% versus restore50% conditional on loss OR below40%','Minimum40% and maximum55% are separate constraints','Series1600PowerPack scope, not universal marine','Continuation of truncated source: preservation, residual dilution, pure-water exception'],'not_claimed':['Historical PDF identity','Project applicability','Local complete PDF archive','Comparison of02E with03E/04E']};dump('SOURCE_DIFFERENCES.json',d)
print('Added eight inactive MTU records; Library text verified, local PDF archive still blocked.')
