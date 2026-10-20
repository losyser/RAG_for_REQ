"""Explicitly authorized Windows fallback; raw bytes plus honest identity sidecar."""
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
transfer=json.loads((HERE/'private_transfer/transfer.json').read_text(encoding='utf8'))
target=HERE/'original'/transfer['file_name']
if target.exists():raise RuntimeError('Never overwrite original')
request=urllib.request.Request(transfer['download_url'],headers=transfer.get('headers',{}),method=transfer.get('method','GET'))
with urllib.request.urlopen(request,timeout=60) as response:
    data=response.read();status=response.status;content_type=response.headers.get('Content-Type')
if len(data)!=transfer['size_bytes']:raise ValueError('size_mismatch')
with target.open('xb') as stream:stream.write(data)
digest=hashlib.sha256(data).hexdigest()
meta={k:transfer[k] for k in ['library_file_id','file_id','file_name','current_version_number','size_bytes','xattrs']}
meta.update(sha256=digest,downloaded_at_utc=datetime.now(timezone.utc).isoformat(),http_status=status,content_type=content_type,local_original=str(target),original_bytes_modified=False,windows_extended_attributes_applied=False,metadata_preservation='Sidecar JSON explicitly authorized after original helper failed because Windows Python has no os.setxattr. Returned xattrs are recorded only, not claimed to be installed.',download_route='Exact Library prepare_materialize authorized URL; URL omitted from durable metadata')
(HERE/'ORIGINAL_PROVENANCE.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'bytes':len(data),'sha256':digest,'version':transfer['current_version_number'],'xattrs_applied':False}))
