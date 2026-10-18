from pathlib import Path
import hashlib,json,re,zipfile
import fitz
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'minor_revision_candidate';S=W.parent/'paper_build_validation_20261018/delivery'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'pdfs':{},'protection':{},'unchanged_scientific_inputs':{}}
for target in ['paper_wiley','paper_cumulative_diff','supplementary_ea_notes','mapping_review_supplement','response_to_reviewers']:
 doc=fitz.open(D/(target+'.pdf'));log=(D/(target+'.log')).read_text('utf8',errors='replace')
 bad=[l for l in log.splitlines() if re.search('undefined|multiply defined|Missing character|Font shape.*not available',l,re.I)]
 fonts={f[0]:f for page in doc for f in page.get_fonts(full=True)}
 unembedded=[f[3] for x,f in fonts.items() if x and not doc.extract_font(x)[3]]
 assert not bad and not unembedded,(target,bad,unembedded)
 report['pdfs'][target]={'pages':len(doc),'errors':bad,'unembedded':unembedded,'embedded_fonts':len(fonts),'overfull_hbox':log.count('Overfull \\hbox'),'overfull_vbox':log.count('Overfull \\vbox'),'sha256':sha(D/(target+'.pdf'))}
 sheet=Image.new('RGB',(1250,((len(doc)+4)//5)*360),'#ddd');dr=ImageDraw.Draw(sheet)
 for i,pg in enumerate(doc):
  px=pg.get_pixmap(matrix=fitz.Matrix(.4,.4));im=Image.frombytes('RGB',(px.width,px.height),px.samples);sheet.paste(im,((i%5)*250,(i//5)*360+18));dr.text(((i%5)*250+4,(i//5)*360),str(i+1),fill='black')
 sheet.save(W/(target+'_contact.png'))
 for index in ([0,13,14,17] if target=='paper_wiley' else ([0] if target in ['supplementary_ea_notes','mapping_review_supplement'] else [])):
  doc[index].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(W/f'{target}_page{index+1}.png')
for p in list(S.glob('table*.tex'))+[S/'revision_numbers.tex',S/'appendix_sensitivity.tex',S/'appendix_prompts.tex',S/'paper_bibliography.bib']:
 assert sha(p)==sha(D/p.name),p
 report['unchanged_scientific_inputs'][p.name]=sha(p)
for name,path in [('historical',ROOT/'revision_artifacts/optional_evidence_policies_20261018/protected_before.json'),('additional',ROOT/'revision_artifacts/followup_integrity_20261018/additional_protected_before.json'),('unrelated_dirty',ROOT/'revision_artifacts/optional_evidence_policies_20261018/dirty_before.json')]:
 m=json.loads(path.read_text('utf8'));changed=[p for p,h in m.items() if sha(ROOT/p)!=h];assert not changed
 report['protection'][name]={'count':len(m),'changed':changed}
assets=json.loads((W/'FIGURE_ASSET_PRESERVATION.json').read_text('utf8'));assert all(sha(D/p)==h for p,h in assets.items());report['preserved_assets']=len(assets)
(W/'BUILD_VALIDATION.json').write_text(json.dumps(report,indent=2),'utf8')
with zipfile.ZipFile(W/'minor_revision_candidate.zip','w',zipfile.ZIP_DEFLATED)as z:
 for p in D.rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.tex','.sty','.cls','.bst','.bib','.bbl','.pdf','.svg','.eps','.png','.otf','.ttf','.py','.md','.zip','.json']:z.write(p,p.relative_to(D))
 for n in ['PAPER_CHANGE_LEDGER.json','candidate_vs_current.diff','BUILD_VALIDATION.json','FIGURE_ASSET_PRESERVATION.json']:z.write(W/n,n)
print(json.dumps({k:v for k,v in report.items() if k!='unchanged_scientific_inputs'},indent=2))
