"""Offline provenance inventory. Lexical tokens are NOT semantic support labels."""
from pathlib import Path
import hashlib,json,re,socket
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
def blocked(*a,**k): raise RuntimeError('Network disabled')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
def read(p): return json.loads(p.read_text('utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
kbpath=ROOT/'data/processed/evidence_units_v3_audited.jsonl'
kb={x['id']:x for x in map(json.loads,kbpath.read_text('utf-8').splitlines())}
# Keep every numeric token, even model/page identifiers, for inspection. Do not
# interpret these as quantities automatically or sort reversed range endpoints.
num=re.compile(r'(?P<operator><=|>=|≤|≥|<|>|=)?\s*(?P<first>[+−-]?\d+(?:\.\d+)?)(?:\s*(?P<separator>至|到|to|–|—|~|-)\s*(?P<second>[+−-]?\d+(?:\.\d+)?))?\s*(?P<unit>°\s*C|℃|dGH|mg/l|mg/L|kW/cyl|bar|MPa|kPa|kW|分钟|min|mm|%|台|年|h|s)?',re.I)
def tokens(s):
 return [dict(m.groupdict(),raw=m.group(0),start=m.start(),end=m.end(),context=s[max(0,m.start()-45):m.end()+45],bound_semantics='unresolved',unit_missing=m['unit'] is None) for m in num.finditer(s)]
def strings(v,path=''):
 if isinstance(v,str): yield path,v
 elif isinstance(v,dict):
  for k,x in v.items(): yield from strings(x,path+'.'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v): yield from strings(x,path+f'[{i}]')
def evidence_objects(v):
 if isinstance(v,dict):
  if v.get('id') and isinstance(v.get('text'),str): yield v
  for x in v.values(): yield from evidence_objects(x)
 elif isinstance(v,list):
  for x in v: yield from evidence_objects(x)
def parse(s):
 s=re.sub(r'^```(?:json)?\s*|\s*```$','',s.strip())
 return json.loads(s)
roots=[('original12',ROOT/'revision_artifacts/optional_evidence_policies_20261018/authorized_flash_run'),('original12',ROOT/'revision_artifacts/optional_evidence_policies_20261018/authorized_flash_slot12'),('quarantine4',ROOT/'revision_artifacts/quarantine_flash_comparison_20261018')]
records=[]; manifest={str(kbpath):sha(kbpath)}
for batch,folder in roots:
 for reqfile in sorted(folder.glob('[0-9][0-9]_*_request.json')):
  req=read(reqfile);respfile=reqfile.with_name(reqfile.name.replace('_request.json','_response.json'));resp=read(respfile)
  manifest[str(reqfile)]=sha(reqfile);manifest[str(respfile)]=sha(respfile)
  messages=req['request']['messages'];prompt='\n'.join(m['content'] for m in messages);passages={}
  for m in messages:
   s=m['content']
   try:
    for e in evidence_objects(json.loads(s)): passages.setdefault(e['id'],[]).append(e)
   except (ValueError,TypeError): pass
   matches=list(re.finditer(r'^\[([^\]]+)\]\s+层级:',s,re.M))
   for i,h in enumerate(matches):
    block=s[h.start():matches[i+1].start() if i+1<len(matches) else len(s)].split('\n## ')[0]
    passages.setdefault(h[1],[]).append({'exact_prompt_block':block})
  selected=req.get('selected_ids',[]);sources=[]
  for ident in dict.fromkeys(selected+list(passages)):
   source=kb.get(ident);blocks=passages.get(ident,[])
   text=json.dumps(blocks,ensure_ascii=False)
   sources.append({'id':ident,'selected':ident in selected,'present_in_prompt_passage':bool(blocks),'exact_passages':blocks,'prompt_tokens':tokens(text),'active_kb_record':source,'source_tokens':tokens(source.get('text','')) if source else [],'original_page_verification':'unresolved; metadata/prompt presence does not verify original page','edition':source.get('edition') if source else None,'applicability':'unknown pending model/condition comparison'})
  body=(resp.get('response') or {}).get('choices') or [];rows=[];parse_error=None
  if body:
   try:
    output=parse(body[0]['message']['content']);rows=output.get('shalls',output.get('engineering_requirements',[]))
   except (ValueError,TypeError,AttributeError) as e: parse_error=type(e).__name__
  audited=[]
  for i,row in enumerate(rows,1):
   citations=row.get('evidence_citations',[]) or [];checks=[]
   for cite in citations:
    ident=cite.get('kb_id',cite.get('id')) if isinstance(cite,dict) else cite
    checks.append({'id':ident,'active_kb_exists':ident in kb,'prompt_passage_exists':ident in passages,'selected':ident in selected,'semantic_support':'unresolved','model_condition_applicability':'unknown'})
   fields=[]
   for path,s in strings(row):
    if any(k in path for k in ['shall_statement','measurable_criterion','acceptance_criteria','applicable_condition']):
     fields.append({'field':path,'exact_text':s,'numeric_tokens':tokens(s)})
   audited.append({'row':i,'raw_row':row,'citations':checks,'fields':fields,'independent_semantic_judgment':'not performed; tokens preserve signs/operators/range endpoints but not entailment'})
  records.append({'batch':batch,'request_file':str(reqfile.relative_to(ROOT)),'response_file':str(respfile.relative_to(ROOT)),'case':req['case'],'arm':req['arm'],'request_sha256':req.get('request_sha256'),'model':req['request']['model'],'status':resp.get('status'),'http_status':resp.get('http_status'),'usage':(resp.get('response') or {}).get('usage'),'sources':sources,'rows':audited,'parse_error':parse_error,'raw_rows':len(rows),'preprompt_selected_without_passage':[x for x in selected if x not in passages],'preprompt_exclusion_cause':'not inferred from absence; consult frozen policy/registry','exposure':'development cases; not blind tests'})
assert len(records)==16,len(records)
dump('CHAIN_AUDIT.json',{'status':'PROVENANCE_AND_LEXICAL_INVENTORY_NOT_ENTAILMENT_VALIDATION','batches':{b:[r for r in records if r['batch']==b] for b in ['original12','quarantine4']},'limitations':['Original pages and applicability remain unresolved.','Numeric tokenizer retains model/page digits and may miss worded quantities; no accuracy score derived.','Same numeric token is not semantic support.','No new generation, repair, scoring replacement, or human labels.']})
dump('CHAIN_INPUT_HASHES.json',manifest)
for b in ['original12','quarantine4']:
 r=[x for x in records if x['batch']==b];print(b,'attempts',len(r),'raw_rows',sum(x['raw_rows'] for x in r),'parse_errors',[x['case'] for x in r if x['parse_error']],'statuses',[x['status'] for x in r])
assert all(sha(Path(p))==h for p,h in manifest.items())
