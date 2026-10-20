"""Strict fixed-subset scorer. Blocks incomplete/uncertain references; never chooses rows by score."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('server.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

def strict_json(path):
    def unique(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key/ID: '+key)
            result[key]=value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)

def coverage_report(package,records):
    reports=[]
    for record in records:
        answers=record.get('web_answer_fields',{});rows=[]
        for source in package['sources']:
            a=answers.get(source['id'],{}) if isinstance(answers,dict) else {}
            a=a if isinstance(a,dict) else {}
            states=a.get('candidates',{});states=states if isinstance(states,dict) else {}
            fixed=[p['id'] for p in source['candidates']]
            counts={state:sum(states.get(pid,'unanswered')==state for pid in fixed) for state in review.STATES}
            rows.append({'source_id':source['id'],'candidate_count':len(fixed),'candidate_states':counts,
                         'first_pass_done':a.get('first_pass_done',False),'coverage_reviewed':a.get('coverage_reviewed',False),
                         'review_details':a.get('review_details',{}),'source_note':a.get('note',''),
                         'initial_pairs':a.get('initial_pairs',[]),'missing_pairs':a.get('missing_pairs',[])})
        n=sum(r['candidate_count'] for r in rows)
        definitive=sum(r['candidate_states']['relevant']+r['candidate_states']['irrelevant'] for r in rows)
        complete=sum(r['coverage_reviewed'] is True for r in rows)
        reports.append({'reviewer':record.get('reviewer'),'collection_mode':record.get('collection_mode'),
                        'stage_order':record.get('stage_order','per-source-first-pass-before-candidates; verify declarations'),
                        'candidate_denominator':n,'definitive_candidate_count':definitive,
                        'definitive_candidate_fraction':definitive/n if n else None,
                        'taxonomy_reviewed_source_count':complete,'source_denominator':len(rows),
                        'taxonomy_reviewed_source_fraction':complete/len(rows),'per_source':rows,
                        'coverage_is_self_reported_not_proof_of_gold':True})
    return reports

def normalize_record(data,package):
    if data.get('format')=='mapping-review-backup-v1':
        if data.get('sha256')!=review.digest({k:v for k,v in data.items() if k!='sha256'}):raise ValueError('Web backup checksum mismatch')
        task=data['task'];review.validate_package(task['package'])
        if task['package']!=package:raise ValueError('Web package differs from frozen package')
        return {'kind':task['package']['kind'],'package_version':task['package']['version'],'reviewer':task['reviewer'],
                'collection_mode':'web','web_answer_fields':task['answers'],'pending_pair_rows':[],'issues':[]}
    if data.get('format')=='mapping-review-excel-import-v1':
        rows=data.get('candidate_rows',[])
        ids=[(r['source_id'],r['pair_id']) for r in rows]
        expected={(s['id'],p['id']) for s in package['sources'] for p in s['candidates']}
        if len(ids)!=len(set(ids)) or set(ids)!=expected:raise ValueError('Excel candidate row IDs duplicated or incomplete')
        for row in rows:
            if row['verdict']!=data['web_answer_fields'][row['source_id']]['candidates'][row['pair_id']]:raise ValueError('Excel row and answer mismatch')
        return data
    raise ValueError('Unsupported record; use web JSON backup or validated Excel readback')

def score(package,manifest,predictions,records,expected_reviewers):
    review.validate_package(package)
    ids=[s['id'] for s in package['sources']]
    if package['kind']!='formal' or package['version']!=manifest['package_version'] or ids!=manifest['selected_source_ids'] or len(ids)!=manifest['n']:
        raise ValueError('Frozen source/version mismatch')
    if set(predictions)!={'deepseek','qwen','bm25','embed'}:raise ValueError('Four fixed methods required')
    legal={(c,i) for c,intents in package['taxonomy'].items() for i in intents}
    selected_predictions={}
    for method,data in predictions.items():
        selected_predictions[method]={}
        for sid in ids:
            items=data[sid];p={tuple(x) for x in items}
            if len(p)!=len(items) or not p<=legal:raise ValueError('Invalid/duplicate prediction pairs')
            selected_predictions[method][sid]=p
    for source in package['sources']:
        union=set().union(*(m[source['id']] for m in selected_predictions.values()))
        if union!={(p['component'],p['intent']) for p in source['candidates']}:raise ValueError('Frozen candidate pool differs from four-method union')
    reasons=[];gold_sets=[];reviewers=[]
    if expected_reviewers not in (1,2) or len(records)!=expected_reviewers:reasons.append('Expected reviewer count not met; no automatic single-expert fallback')
    for number,record in enumerate(records,1):
        who=record.get('reviewer','');reviewers.append(who.strip() if isinstance(who,str) else '')
        prefix=f'reviewer {number}'
        if not isinstance(who,str) or not who.strip():reasons.append(prefix+': reviewer identity missing')
        if record.get('kind')!='formal' or record.get('package_version')!=package['version']:reasons.append(prefix+': wrong phase/version');continue
        if record.get('collection_mode') not in ('web','excel'):reasons.append(prefix+': unknown collection mode')
        reasons.extend(prefix+': '+str(issue) for issue in record.get('issues',[]))
        if record.get('pending_pair_rows'):reasons.append(prefix+': incomplete additional pair rows preserved')
        answers=record.get('web_answer_fields',{})
        try:review.validate_answers(package,answers)
        except (review.ReviewError,KeyError,TypeError,AttributeError) as error:reasons.append(prefix+': invalid/incomplete answer structure '+str(error));continue
        gold={}
        for sid in ids:
            a=answers[sid];tag=prefix+' '+sid
            if not a['first_pass_done'] or not a['coverage_reviewed']:reasons.append(tag+': first pass or full-taxonomy coverage incomplete')
            if any(v in ('unanswered','uncertain') for v in a['candidates'].values()):reasons.append(tag+': unanswered/uncertain candidate; cannot coerce or drop')
            if any(p['verdict']=='uncertain' for p in a['missing_pairs']):reasons.append(tag+': uncertain missing pair')
            d=a.get('review_details',{})
            if d.get('complete')!='yes' or d.get('total_minutes') is None or d.get('interruption_minutes') is None:reasons.append(tag+': completion/timing declaration missing')
            if d.get('exposure')!='after_first_pass' or not d.get('first_pass_at') or not d.get('first_candidate_at'):reasons.append(tag+': independent-first-pass/exposure declaration unresolved')
            if d.get('questions','').strip():reasons.append(tag+': questions/stopping notes require explicit resolution before scoring')
            final={pid:state for pid,state in a['candidates'].items()}
            final.update({review.pair_id(p['component'],p['intent']):p['verdict'] for p in a['missing_pairs']})
            for p in a['initial_pairs']:
                pid=review.pair_id(p['component'],p['intent'])
                if final.get(pid) not in ('relevant','irrelevant'):reasons.append(tag+': first-pass pair lacks definitive final disposition '+pid)
                elif p['verdict']=='relevant' and final[pid]=='irrelevant' and not a['note'].strip():reasons.append(tag+': reversed positive first pass needs a retained explanation '+pid)
            gold[sid]={tuple(pid.split(':')) for pid,state in final.items() if state=='relevant'}
        gold_sets.append(gold)
    if len(set(reviewers))!=len(reviewers):reasons.append('Reviewer identities are not distinct')
    if len(gold_sets)==2:
        for sid in ids:
            if gold_sets[0][sid]!=gold_sets[1][sid]:reasons.append(sid+': independent reviewers disagree; preserve originals and resolve before shared reference scoring')
    result={'status':'blocked' if reasons else 'scored','scores':None,'reasons':reasons,'source_ids':ids,'source_count':len(ids),
            'package_version':package['version'],'reference_reviewers':reviewers,'expected_reviewers':expected_reviewers,
            'reference_mode':('single-reviewer-reference' if expected_reviewers==1 else 'two-reviewer-shared-reference') if not reasons else 'reference-not-ready',
            'review_status':'ready' if not reasons else 'incomplete-invalid-or-unresolved',
            'coverage':coverage_report(package,records),
            'inter_reviewer_agreement':None,
            'agreement_note':'No dual-reviewer agreement statistic reported; one reviewer is not an agreement study.' if expected_reviewers==1 else 'Exact final positive-pair sets must agree; no kappa is computed. Disagreement blocks common-reference scores.',
            'method_provenance':{'predictions_sha256':manifest.get('predictions_sha256'),
                'package_prediction_scope':package['provenance']['prediction_scope'],
                'deepseek':'Saved historical Stage 1 predictions matching v3 pairs; reused upstream by v4, not a new v4 mapping run.',
                'qwen':'Saved Qwen predictions in the same frozen e1_predictions.json; no new call.',
                'bm25':'Saved BM25 predictions in the same frozen e1_predictions.json; no rerun.',
                'embed':'Saved embedding predictions in the same frozen e1_predictions.json; no rerun.'},
            'reference_limitations':['Candidate pooling can prime final labels even after independent first pass.',
                'Excel first-pass order and exposure are self-reported, not enforced blinding; web legacy records may lack timing/exposure metadata.',
                'No independence claim beyond recorded declarations; missing declarations block scores and require separately documented clarification, never invented metadata.',
                'Unanswered and uncertain labels are never negatives. No incomplete-source exclusion or complete-case subset score.',
                'If reviewers disagree, preserve original records; adjudication is not implemented by this scorer.'],
            'scope':'Only the frozen 8 sources from the remaining 58-source frame; not full-60, external-domain or new-model-run performance',
            'undefined_metric_policy':'zero denominator => null; never drop sources from macro average',
            'statistical_limit':'8 source units, not 75 independent pairs; no adequacy/power guarantee or confidence interval asserted'}
    if reasons:return result
    if len(gold_sets)!=expected_reviewers:raise ValueError('No complete reference')
    gold=gold_sets[0];scores={}
    for method,pred in selected_predictions.items():
        per=[]
        for sid in ids:
            p,g=pred[sid],gold[sid];tp=len(p&g);fp=len(p-g);fn=len(g-p)
            per.append({'source_id':sid,'tp':tp,'fp':fp,'fn':fn,'prediction_count':len(p),'gold_count':len(g),
                        'precision':tp/len(p) if p else None,'recall':tp/len(g) if g else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None})
        tp=sum(r['tp'] for r in per);fp=sum(r['fp'] for r in per);fn=sum(r['fn'] for r in per)
        scores[method]={'micro':{'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None},
                        'macro_f1':sum(r['f1'] for r in per)/len(ids) if all(r['f1'] is not None for r in per) else None,'per_source':per}
    result['scores']=scores
    result['gold_pairs_by_source']={sid:[list(p) for p in sorted(pairs)] for sid,pairs in gold.items()}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--predictions',type=Path,required=True);p.add_argument('--records',type=Path,nargs='+',required=True)
    p.add_argument('--expected-reviewers',type=int,choices=[1,2],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.exit(2,'Output exists; refusing overwrite\n')
    package=strict_json(a.package);manifest=strict_json(a.manifest)
    if hashlib.sha256(a.predictions.read_bytes()).hexdigest()!=manifest['predictions_sha256']:p.exit(2,'Frozen prediction hash mismatch\n')
    records=[]
    for path in a.records:
        if path.suffix.lower()=='.xlsx':
            reader_spec=importlib.util.spec_from_file_location('excel_pilot',Path(__file__).with_name('excel_pilot.py'))
            excel_pilot=importlib.util.module_from_spec(reader_spec);reader_spec.loader.exec_module(excel_pilot)
            records.append(normalize_record(excel_pilot.read_workbook(path,a.package),package))
        else:records.append(normalize_record(strict_json(path),package))
    result=score(package,manifest,strict_json(a.predictions),records,a.expected_reviewers)
    result['input_files_sha256']={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
        [('package',a.package),('manifest',a.manifest),('predictions',a.predictions)]}
    result['input_record_sha256']=[hashlib.sha256(path.read_bytes()).hexdigest() for path in a.records]
    with a.output.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':result['status'],'blockers':len(result['reasons']),'output':str(a.output)}))
