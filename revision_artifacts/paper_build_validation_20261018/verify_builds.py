"""Read-only PDF/build/protection verification and new diagnostic rendering."""
from pathlib import Path
import hashlib,json,re
import fitz
from PIL import Image,ImageDraw
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[1]
read=lambda p:json.loads(p.read_text('utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'pdfs':{},'protection':{},'dependencies':{}}
for target in ('paper_wiley','paper_cumulative_diff'):
    original=fitz.open(WORK/'delivery'/f'{target}.pdf')
    fresh=fitz.open(WORK/'fresh_extract'/f'{target}.pdf')
    assert len(original)==len(fresh)
    assert [p.get_text() for p in original]==[p.get_text() for p in fresh]
    fonts={f[0]:f for page in fresh for f in page.get_fonts(full=True)}
    unembedded=[f[3] for x,f in fonts.items() if x and not fresh.extract_font(x)[3]]
    assert not unembedded,unembedded
    log=(WORK/'fresh_extract'/f'{target}.log').read_text('utf-8',errors='replace')
    fatal=[line for line in log.splitlines() if re.search(r'undefined|multiply defined|Missing character|Font shape.*not available',line,re.I)]
    assert not fatal,fatal
    fls=(WORK/'fresh_extract'/f'{target}.fls').read_text('utf-8',errors='replace')
    inputs=sorted(set(line[6:] for line in fls.splitlines() if line.startswith('INPUT ')))
    absolute=[p for p in inputs if re.match(r'[A-Za-z]:[/\\]',p)]
    unexpected=[p for p in absolute if not ('texlive/2025/' in p.replace('\\','/').lower() or str(WORK/'fresh_extract').replace('\\','/').lower() in p.replace('\\','/').lower())]
    assert not unexpected,unexpected
    report['dependencies'][target]=inputs
    report['pdfs'][target]={'pages':len(fresh),'fresh_text_equal':True,'embedded_font_count':len(fonts),
        'unembedded_fonts':unembedded,'missing_reference_citation_font_findings':fatal,
        'overfull_hbox_warnings':log.count('Overfull \\hbox'),
        'overfull_vbox_warnings':log.count('Overfull \\vbox'),'unexpected_absolute_input_dependencies':unexpected,
        'delivery_pdf_sha256':sha(WORK/'delivery'/f'{target}.pdf'),'fresh_pdf_sha256':sha(WORK/'fresh_extract'/f'{target}.pdf')}
    thumbs=[]
    for page in fresh:
        pix=page.get_pixmap(matrix=fitz.Matrix(.35,.35));thumbs.append(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
    sheet=Image.new('RGB',(1150,((len(thumbs)+4)//5)*320),'#ddd');draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(thumbs):
        sheet.paste(im,((i%5)*230,(i//5)*320+20));draw.text(((i%5)*230+5,(i//5)*320+3),str(i+1),fill='black')
    sheet.save(WORK/f'{target}_contact.png')
    for page_index in ([0,10,11,12,16] if target=='paper_wiley' else [0,9,11,14,27]):
        if page_index<len(fresh):fresh[page_index].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(WORK/f'{target}_page{page_index+1}.png')
for name,path in [('historical',ROOT/'revision_artifacts/optional_evidence_policies_20261018/protected_before.json'),
                  ('additional',ROOT/'revision_artifacts/followup_integrity_20261018/additional_protected_before.json')]:
    manifest=read(path);changed=[p for p,h in manifest.items() if sha(Path(p))!=h];assert not changed
    report['protection'][name]={'count':len(manifest),'changed':changed}
original_manifest=read(WORK/'ORIGINAL_ZIP_MANIFEST.json')
assert all(sha(WORK/'original_submission'/p)==h for p,h in original_manifest['members'].items())
report['original_zip_members_unchanged']=len(original_manifest['members'])
(WORK/'VALIDATION.json').write_text(json.dumps(report,indent=2),'utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='dependencies'},indent=2))
