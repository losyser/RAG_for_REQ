"""Acquire only frozen search-result URLs or existing complete originals; no model calls."""
import concurrent.futures,requests,fitz,sys
from urllib.parse import urlparse
from preflight import *
# Result ranks selected for subject/document/model relevance, without numerical agreement tests.
PICKS={
'0197632a86f2':[], '0e141b22e787':[1,2], '12bfce042a08':[], '1893cda6636a':[1],
'20c89bc83acc':[1,3], '275f317bef40':[1,2], '295311242ddb':[1,2], '3868f0ced50f':[],
'39ff590b1091':[1,2], '40e37b24bce0':[1,2], '444a411525b5':[1,2], '44a2fda44ea8':[],
'485feee280d1':[], '4ae9bf4faf7f':[1,3], '54fcd461985b':[1,2], '5a189e6ce278':[1,3],
'65b35bfea389':[3,4], '6694f0068021':[], '6c2a28e27b61':[1,2], '732382747cbc':[],
'7d273f8f15d7':[], '802327fd5227':[1,2], '86c378e86412':[1,2], '87124117f950':[1,2],
'96b5b7a7dc78':[1,2], '970deb27234e':[], '987b761a81b4':[], '9a5d21269e8d':[1,2],
'9b134b81641c':[1,2], 'a25361ff9c95':[1,2], 'a65d9beab3d4':[1,2], 'ab16ba040969':[],
'aba1e177a9f5':[2,5], 'b906f6e8dcd0':[2,4], 'baa2bb394ffe':[1,2], 'c576e009c27b':[1,3],
'c7c2e71b45eb':[1,2], 'cde2f2e7a5ed':[1,2], 'd0a8aa54351a':[2,3], 'd1e84be5c768':[1,2],
'e20814e25510':[1,2], 'e41e7f496177':[1,2], 'e8af85fc3fa1':[3,4], 'f396a936014a':[1,2]}
WHY={
'65b35bfea389':'Visible condition explicitly says propulsion; propulsion-specific complete guides ranked above GenSet variants.',
'b906f6e8dcd0':'Exact diesel 49/60 Tier II and Tier III guides; DF is a different variant and retained elsewhere, not substituted.',
'5a189e6ce278':'Complete dual-fuel project guides; general technology brochure not a complete installation/operation reference.',
'aba1e177a9f5':'Complete marine cooling manual and full project guide; isolated chapter PDFs omitted in favor of complete publications.',
'd0a8aa54351a':'Complete marine cooling manual and project guide; isolated chapter PDFs omitted.',
'e8af85fc3fa1':'Complete project guides; isolated component chapters omitted.',
'44a2fda44ea8':'Complete local CCS 2024/2025 rules available; no need to substitute older web rules or green-ship scope.',
'485feee280d1':'No results. No new query added. Related L16/24 guide may be found through shared subject searches; S variant remains explicit gap.'}
def inspect(p):
    with fitz.open(p) as d:
        if d.needs_pass:raise ValueError('Password restricted; no bypass')
        return {'pages':len(d),'metadata':d.metadata,'first_page':d[0].get_text()[:2200],'last_page':d[-1].get_text()[-1200:],'toc_entries':len(d.get_toc()),'sha256':sha(p),'bytes':p.stat().st_size,'pdf_header':p.read_bytes()[:5].decode('ascii'),'encrypted':d.is_encrypted}
def worker(url,dest):
    resp=requests.get(url,timeout=(12,30),headers={'User-Agent':'Mozilla/5.0'},allow_redirects=True)
    record={'url':url,'status':resp.status_code,'final_url':resp.url,'content_type':resp.headers.get('Content-Type')}
    resp.raise_for_status()
    if not resp.content.startswith(b'%PDF-'):raise ValueError('Response is not PDF')
    Path(dest).write_bytes(resp.content);print(json.dumps(record))
def main():
    logs=[];urls={}
    for p in sorted((AUDIT/'search_results').glob('*.json')):
        r=json.loads(p.read_text(encoding='utf8'));rows=re.findall(r'^([^\n]+) \((https?://[^\n]+)\)$',r['result'],re.M)[:5]
        selected=PICKS[p.stem];assert len(selected)<=2
        screened=[]
        for rank,(title,url) in enumerate(rows,1):
            official=any(urlparse(url).hostname==domain or urlparse(url).hostname.endswith('.'+domain) for domain in r['query']['domains'])
            take=rank in selected;assert not take or official
            screened.append({'rank':rank,'title':title,'url':url,'official_domain':official,'selected_for_full_document':take,'reason':WHY.get(p.stem,'完整原版及主题/机型匹配优先；相同主题本地完整规范共同可用。') if take or not selected else '未选：超出同查询两份完整资料上限，或并非完整/同类用途资料；保留网址记录。'})
            if take:urls.setdefault(url,{'url':url,'search_title':title,'query_ids':[]})['query_ids'].append(p.stem)
        logs.append({'query_id':p.stem,'query':r['query'],'screened':screened,'screened_count':len(rows),'selected_count':len(selected),'stop_reason':WHY.get(p.stem,'达到固定查询/来源上限；不以数值结果追加搜索。') if selected else WHY.get(p.stem,'前五结果无可直接采用的同类完整原版，或本地完整通用规范已覆盖主题；保留主题与型号缺口。')})
    dump(AUDIT/'SOURCE_SELECTION_LOG.json',logs)
    target=PACK/'原版资料';target.mkdir(exist_ok=True)
    def fetch(r):
        key=hashlib.sha256(r['url'].encode()).hexdigest()[:10];dest=target/('official_'+key+'.pdf')
        result={**r,'file':dest.relative_to(PACK).as_posix(),'retrieved_utc':datetime.now(timezone.utc).isoformat(),'method':'official_public_get','attempts':[]}
        try:
            if dest.exists():
                result['attempts'].append({'url':r['url'],'status':'recovered_complete_file_from_first_download_run','transport_metadata':'First run interrupted for nonterminating servers; complete files preserved, no new request'})
            else:
                result['attempts'].append({'url':r['url'],'status':'bounded_attempt_after_interrupted_or_unstarted_first_run','total_timeout_seconds':75})
                proc=subprocess.run([sys.executable,'-E','-B','-X','utf8',__file__,'--fetch',r['url'],str(dest)],capture_output=True,text=True,encoding='utf8',timeout=75)
                if proc.returncode:raise ValueError(proc.stderr[-700:])
                result['attempts'].append(json.loads(proc.stdout))
            result.update(inspect(dest));result['status']='downloaded_pdf'
        except Exception as e:result['status']='unavailable';result['error']=str(e)
        return result
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures=[ex.submit(fetch,r) for r in urls.values()]
        for future in concurrent.futures.as_completed(futures):
            result=future.result()
            records.append(result);dump(AUDIT/'ACQUISITION_LOG.json',records);print(result['status'],result['file'],flush=True)
    # Complete local publications are uniformly available across all topics. Never edit bytes.
    local=[
      (ROOT.parent/'standards/CCS_Rules_Sea_Going_Steel_Ships_2024_full.pdf','CCS_SeaGoingSteelShips_2024_English_full.pdf','CCS2024'),
      (ROOT/'data/raw/ccs_rules/ccs_2025.pdf','CCS_SeaGoingSteelShips_2025_Chinese_full.pdf','CCS2025'),
      (ROOT.parent/'IACS_URM_Machinery_Requirements.pdf','IACS_Machinery_Requirements_local_full.pdf','IACS_M'),
      (ROOT/'revision_artifacts/source_paper_candidates_20261018/MAN4960_official.pdf','MAN_4960_local_complete.pdf','MAN4960_LOCAL')]
    for origin,name,code in local:
        dest=target/name;shutil.copy2(origin,dest)
        records.append({'local_code':code,'file':dest.relative_to(PACK).as_posix(),'original_path':str(origin),'method':'local_complete_original_copy','status':'local_pdf','source_url_status':'原始下载URL需核对；不得假称本次官方下载','retrieved_utc':datetime.now(timezone.utc).isoformat(),**inspect(dest)})
    dump(AUDIT/'ACQUISITION_LOG.json',records)
    print('Completed',len(records),'records; failures retained.')
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--fetch':worker(sys.argv[2],sys.argv[3])
    else:main()
