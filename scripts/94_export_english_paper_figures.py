"""Offline, explicit mapping export; refuses to overwrite an output directory."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cooling_rag_mg.ea_paper_figures import mapping_template,paper_bundle
def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--mapping',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();xml=a.source.read_text(encoding='utf-8')
    if a.output.exists():p.error('Output already exists; use a new directory')
    files=paper_bundle(xml,json.loads(a.mapping.read_text(encoding='utf-8'))) if a.mapping else {'english_figure_mapping.json':json.dumps(mapping_template(xml),ensure_ascii=False,indent=2).encode('utf-8')}
    a.output.mkdir(parents=True)
    for name,data in files.items():(a.output/name).write_bytes(data)
if __name__=='__main__':main()
