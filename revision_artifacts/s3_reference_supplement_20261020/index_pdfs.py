"""Index complete originals without changing PDF bytes. No candidate numbers used."""
import fitz
from preflight import *
KEYWORDS={
'diagram':['cooling water system','cooling system','piping diagram','冷却水系统','冷却水管系'],
'makeup':['expansion tank','make-up','make up','膨胀水箱'],
'thermal':['ambient reference','reference conditions','cooler rating','heat exchanger','cooling water temperature','环境条件','冷却水温度'],
'sensor':['sensor','transmitter','signal','测量范围','传感器'],
'hydrotest':['hydraulic test','hydrostatic','pressure test','水压试验','液压试验'],
'monitor':['monitoring','alarm','监测','报警'],
'standby':['standby pump','stand-by pump','changeover','备用泵','转换'],
'alarm':['alarm','safeguard','acknowledge','报警','安全系统'],
'intake':['seawater intake','intake structure','取水构筑物','校核低水位'],
'flushing':['flushing','cleaning the cooling','冲洗'],
'stability':['temperature control','transient','温度控制'],
'shutdown':['after stopping','after shutdown','stop the engine','stopping the engine','继续运行','停机'],
'quality':['water quality','cooling water treatment','freshwater quality','coolant','hardness','chloride','冷却水水质'],
'valve':['thermostatic','temperature control valve','恒温','温控阀'],
'pump':['pump characteristic','pump capacity','pump head','cooling water pump','冷却水泵','泵的试验'],
'vent':['venting','deaerat','bleed pipe','排气管','膨胀水箱'],
'records':['plans and documents','documentation','提交图纸','图纸和资料'],
'lowload':['low load','low-load','no-load','no load','低负荷']}
def printed(page,text):
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    # Explicit printed labels only; never infer a global PDF offset for modular guides.
    m=re.findall(r'(?m)^\s*(\d{1,4})\s*\(\s*(\d{1,4})\s*\)\s*$',text)
    if m:return m[-1][0]+' ('+m[-1][1]+')（原页标注）'
    m=re.findall(r'(?m)^\s*Page\s+(\d+)\s+of\s+(\d+)\s*$',text,re.I)
    if m:return 'Page '+m[-1][0]+' of '+m[-1][1]
    for line in lines[:4]+lines[-5:]:
        if re.fullmatch(r'\d{1,2}[-–]\d{1,3}',line):return line
    label=page.get_label()
    if label and label!=str(page.number+1):return label+'（PDF内嵌页标签，需对照版面）'
    for line in lines:
        if 'A001' in line and '|' in line:
            m=re.search(r'\|\s*(\d{1,4})\s*$',line) or re.search(r'^\s*(\d{1,4})\s*\|',line)
            if m:return m[1]
    for block in page.get_text('blocks'):
        if block[3] < page.rect.height*.06 or block[1] > page.rect.height*.94:
            value=block[4].strip()
            if re.fullmatch(r'\d{1,4}',value):return value
    return '未自动辨识；以原页版面为准'
def main():
    cache=AUDIT/'pdf_text_cache';cache.mkdir(exist_ok=True)
    outputs=[]
    for p in sorted((PACK/'原版资料').glob('*.pdf')):
        dest=cache/(p.stem+'.json')
        if dest.exists() and json.loads(dest.read_text(encoding='utf8')).get('index_version')==2:continue
        with fitz.open(p) as d:
            pages=[];toc=d.get_toc()
            for n,page in enumerate(d):
                text=page.get_text();lower=text.lower()
                topics={key:[term for term in terms if term in lower] for key,terms in KEYWORDS.items()};topics={k:v for k,v in topics.items() if v}
                pages.append({'pdf_page':n+1,'printed':printed(page,text),'text':text,'topics':topics,'label':page.get_label()})
            dump(dest,{'index_version':2,'file':p.relative_to(PACK).as_posix(),'sha256':sha(p),'page_count':len(d),'toc':toc,'pages':pages})
        outputs.append(p.name);print('Indexed',p.name,len(pages),flush=True)
    print('Newly indexed',len(outputs))
if __name__=='__main__':main()
