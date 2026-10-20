$ErrorActionPreference='Stop';$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try {
 if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea'){throw 'Wrong model'}
 $out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_status_alignment_v2_20261016\final';New-Item -ItemType Directory -Path $out -Force|Out-Null
 $p=$r.GetProjectInterface()
 foreach($id in @(7,8,9,10)) {
  $d=$r.GetDiagramByID($id);if($d.Name -notmatch '^REQ_status_v2_'){throw 'Wrong diagram'}
  $r.OpenDiagram($id);$d.DiagramObjects.Refresh()
  for($i=$d.DiagramObjects.Count-1;$i -ge 0;$i--){$o=$d.DiagramObjects.GetAt($i);$e=$r.GetElementByID($o.ElementID);if($e.Type -eq 'Package'){$d.DiagramObjects.DeleteAt($i,$false)}};$d.DiagramObjects.Refresh()
  $r.ReloadDiagram($id)
  foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};if(-not $p.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $out ($d.Name.Substring(4)+'.'+$ext)),$type)){throw 'Export failed'}}
  Write-Output ('Repaired '+$d.Name)
 }
 foreach($pair in @(@('objects','SELECT * FROM t_object'),@('properties','SELECT * FROM t_objectproperties'),@('connectors','SELECT * FROM t_connector'),@('diagramobjects','SELECT * FROM t_diagramobjects'),@('diagrams','SELECT * FROM t_diagram'),@('xref','SELECT * FROM t_xref'))) {$r.SQLQuery($pair[1])|Set-Content (Join-Path $out ($pair[0]+'.xml')) -Encoding UTF8}
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
