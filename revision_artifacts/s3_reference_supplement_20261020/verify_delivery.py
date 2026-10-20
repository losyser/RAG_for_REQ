"""Offline integrity, equal-budget, navigation and protection checks; never read answer keys."""
from preflight import *
import fitz, urllib.parse
from html.parser import HTMLParser
from PIL import Image, ImageDraw

def read(p):return json.loads(p.read_text(encoding='utf8'))
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.extend(v for k,v in attrs if k=='href')

def main():
    docs=read(PACK/'来源与版本清单.json');cards=read(PACK/'逐条资料导航.json')
    assert len(cards)==50 and len({n['blind_id'] for n in cards})==50
    queries=read(AUDIT/'QUERY_PLAN.json')
    assert len(queries)==44 and sum(n['query_budget'] for n in cards)==100
    assert all((AUDIT/'search_results'/f'{q}.json').exists() for q in queries)
    assert all(n['local_passes']==1 for n in cards)
    assert all(len(n['per_model_coverage'])>1 for n in cards if n['blind_id'] in ['K288080','K732549','K612522','K831135'])
    assert all(d['version']!='of entry into service' for d in docs)
    structural=[];thumbs=[];qa=AUDIT/'visual_checks';qa.mkdir(exist_ok=True)
    for d in docs:
        p=PACK/d['file'];raw=p.read_bytes();assert sha(p)==d['sha256']
        assert raw.startswith(b'%PDF-') and b'%%EOF' in raw[-4096:]
        with fitz.open(p) as pdf:
            assert not pdf.needs_pass and len(pdf)==d['pages']
            for page in pdf:assert page.rect.width>0 and page.rect.height>0
            for topic,sections in d['topics'].items():
                for sec in sections:assert 1<=sec['start']<=sec['end']<=len(pdf),(d['file'],sec)
            for number in [1,len(pdf)]:
                pix=pdf[number-1].get_pixmap(matrix=fitz.Matrix(.45,.45),alpha=False)
                im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((220,300))
                tile=Image.new('RGB',(240,330),'white');tile.paste(im,((240-im.width)//2,20));ImageDraw.Draw(tile).text((5,310),d['catalog_id']+' PDF '+str(number),fill='black');thumbs.append(tile)
            structural.append({'file':d['file'],'pages':len(pdf),'sha256':d['sha256'],'all_page_objects_load':True,'header_eof_present':True,'first_last_rendered':True,'limitation':'Structural and endpoint checks do not prove publisher pagination completeness or applicability.'})
    for batch in range(0,len(thumbs),12):
        canvas=Image.new('RGB',(960,990),'#cccccc')
        for k,tile in enumerate(thumbs[batch:batch+12]):canvas.paste(tile,((k%4)*240,(k//4)*330))
        canvas.save(qa/f'endpoints_{batch//12+1}.png')
    local_links=0
    for p in PACK.glob('*.html'):
        parser=Links();parser.feed(p.read_text(encoding='utf8'))
        for href in parser.links:
            u=urllib.parse.urlsplit(href)
            if u.scheme:continue
            target=p.parent/urllib.parse.unquote(u.path) if u.path else p
            assert target.is_file(),href
            if u.fragment.startswith('page='):
                with fitz.open(target) as doc:assert 1<=int(u.fragment[5:])<=len(doc)
            elif u.fragment:assert 'id="'+u.fragment+'"' in target.read_text(encoding='utf8'),href
            local_links+=1
    protected=read(AUDIT/'PROTECTED_BEFORE.json');changed=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h];assert not changed,changed
    dump(AUDIT/'PDF_INTEGRITY.json',structural)
    dump(AUDIT/'LOCAL_SEARCH_LOG.json',[{'blind_id':n['blind_id'],'passes':1,'corpus':'same four complete local originals, shared full-text index','topic':n['topic'],'visible_model':n['visible_model'],'result_catalog_ids':[r['catalog_id'] for r in n['references']],'per_model_coverage':n['per_model_coverage'],'candidate_thresholds_used':False} for n in cards])
    report={'utc':datetime.now(timezone.utc).isoformat(),'protected_files':len(protected),'changed_protected_files':changed,'unique_pdf_checks':len(docs),'local_links_checked':local_links,'cards':50,'query_logs':44,'query_slots':100,'model_api_calls':0,'scores_written':0,'checks_passed':True}
    dump(AUDIT/'VERIFICATION.json',report)
    dump(PACK/'文件哈希清单.json',{p.relative_to(PACK).as_posix():sha(p) for p in sorted(PACK.rglob('*')) if p.is_file() and p.name!='文件哈希清单.json'})
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
