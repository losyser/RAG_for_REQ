import json,re
from preflight import *
for p in (AUDIT/'pdf_text_cache').glob('*.json'):
    d=json.loads(p.read_text(encoding='utf8'))
    toc=[t for t in d['toc'] if re.search('cool|water|pump|alarm|thermo|ambient|load|fluids',t[1],re.I)]
    print(json.dumps({'file':p.stem,'toc':toc[:90],'quality_pages':[(r['pdf_page'],r['printed'],r['text'][:90].replace('\n',' ')) for r in d['pages'] if len(r['topics'].get('quality',[]))>=2][:12]},ensure_ascii=False))
