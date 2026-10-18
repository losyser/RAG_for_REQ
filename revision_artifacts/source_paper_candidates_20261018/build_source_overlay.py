"""Build a non-active, edition-specific candidate from a verified table grid."""
from pathlib import Path
import json,hashlib,re
W=Path(__file__).resolve().parent
def read(n):return json.loads((W/n).read_text('utf8'))
def dump(n,x):(W/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf8')
def cell(raw):
    if raw is None or raw.strip() in ('','-','–','—'):
        return {'raw':raw,'value':None,'unit':None,'meaning':'not_stated'}
    m=re.fullmatch(r'(-?\d+(?:\.\d+)?)\s*(°C|bar)(?:\s*(nominal)?(?:([123])\))?)?',raw.replace('\n',' '))
    if not m:return {'raw':raw,'value':None,'unit':None,'meaning':'structured_by_variant_required'}
    return {'raw':raw,'value':float(m[1]),'unit':m[2],'meaning':'nominal' if m[3] else 'column_bound','footnote':m[4]}
def build():
    grid=read('MAN_table74_cells.json');rows=grid['rows'];assert rows[0][2:]==['Min.','Max.']
    sha=hashlib.sha256((W/'MAN4960_official.pdf').read_bytes()).hexdigest()
    assert sha=='29da4ba210bc2bba9b3f00d6f4f0aee15c6c7847568d5dd69355b3028692ffc1'
    source={'source_id':'MAN4960-IMOII-202512-v3-P134','url':'https://man-es.com/applications/projectguides/4stroke/Propulsion/PG_P-II_4960.pdf','sha256':sha,'version':'Revision 12.2025/3.0','date':'2025-12-03','pdf_page_1based':134,'printed_page':134,'section':'2.17 Operating/service temperatures and pressures','table':'74 HT cooling water – Engine','page_count':508,'model_scope':'49/60 IMO Tier II marine four-stroke diesel engine','project_applicability':'unknown','disclaimer':'Guide data are non-binding and require project-specific assessment.','old_KB_edition_match':False,'verification':'PDF header, table cells and footnotes visually inspected; newly verified edition, not proof of historical source'}
    conditions={1:['Attached HT pump optional; HP TC charge-air-cooler inlet'],2:['HP TC charge-air-cooler outlet'],3:['Regulated jacket-outlet temperature; SaCoS may lower set point to avoid maximum engine-outlet temperature','Flow order: HP HT charge-air cooler, jacket cooling, LP HT charge-air cooler'],4:['Operation at alarm level; last charge-air-cooler outlet'],5:['Engine inlet preheated before start'],6:['Engine inlet at nominal speed; nominal pressure 4 bar'],7:['Total engine pressure loss at nominal flow rate'],8:['Attached HT cooling-water pump pressure rise at nominal speed']}
    result=[]
    for i,raw in enumerate(rows[1:9],1):
        lo,hi=cell(raw[2]),cell(raw[3]);nom=lo if lo['meaning']=='nominal' else None
        variants=[]
        if i in (7,8):
            for line in raw[2].splitlines():
                models,val=line.split(':');value,unit=val.strip().split()
                variants.append({'models':[m.strip() for m in models.split(',')],'value':float(value),'unit':unit,'source_column':'Min.','bound_semantics':'not inferred for variant design values'})
        result.append({'candidate_id':f'MAN4960-202512-T74-R{i}','historical_related_ids':['E-HT-COMP-036'] if i<=5 else [],'source_id':source['source_id'],'table_row':i,'raw_cells':raw,'parameter':raw[0].replace('\n',' '),'interface':None if raw[1]=='-' else raw[1],'unit':lo['unit'] or hi['unit'] or 'bar','min':None if nom or variants else lo['value'],'max':hi['value'],'nominal':nom['value'] if nom else (4.0 if i==6 else None),'operators':{'min':'>=' if lo['value'] is not None and not nom else None,'max':'<=' if hi['value'] is not None else None,'nominal':'nominal' if nom or i==6 else None},'min_cell':lo,'max_cell':hi,'variants':variants,'conditions':conditions[i],'all_table_footnotes':rows[9][0],'model_scope':source['model_scope'],'project_applicability':'unknown','enabled':False})
    originals=read('affected_original_records.json');mtu=[x for x in originals if 'A001065' in x.get('source_document','')]
    pending={'source_id':'MTU-A001065-02E-P16-PENDING','requested_version':'A001065/02E','printed_page':16,'url':'https://www.mtu-solutions.com/content/dam/mtu/download/technical-info/betriebsstoffvorschrift_en/A001065_02E.pdf/_jcr_content/renditions/original./A001065_02E.pdf','sha256':None,'parameters':[],'model_scope':None,'project_applicability':'unknown','verification':'not verified in this execution environment: exact official URL returned HTTP406; PDF/hash/layout not locally verified. Parent-transferred text retained separately; no active parameters inferred.','enabled':False,'related_historical_ids_by_document':[x['id']for x in mtu],'primary_candidate_id':'E-SYS-WATER-006','document_level_match_is_not_page_verification':True}
    overlay={'schema_version':'source-corrections-candidate-v1','active':False,'main_KB_mutation':False,'sources':[source,pending],'parameters':result,'quarantine_retained':['E-HT-COMP-036'],'unknown_retained':[x['id']for x in mtu],'activation_requirement':'Separate author decision, trusted edition mapping and project applicability review; never auto-merge historical evidence.'}
    dump('source_corrections_candidate.json',overlay)
    dump('SOURCE_DIFFERENCES.json',{'new_source_not_historical_proof':True,'MAN_related_id':'E-HT-COMP-036','differences':[{'historical':'HP TC outlet / TE3145 / 60–80°C','candidate':'pump/HP TC inlet / 3121 (3102), TE3145 / 60–80°C'},{'historical':'jacket outlet / TE3170 / 60–92°C','candidate':'HP TC outlet / TE3170 / 60–92°C'},{'historical':'LP TC outlet / TE3180 / nominal90°C','candidate':'jacket outlet / TE3180 / nominal90°C with SaCoS footnote'},{'historical':'engine inlet preheat / 3111, TE3190 / −100°C','candidate':'LP TC outlet / 3111, TE3190 / maximum100°C at alarm; separate preheat row / 3121 (3102), TE3145 / 60–80°C'}],'MTU':pending,'original_record_file':'affected_original_records.json'})
    return overlay
if __name__=='__main__':build()
