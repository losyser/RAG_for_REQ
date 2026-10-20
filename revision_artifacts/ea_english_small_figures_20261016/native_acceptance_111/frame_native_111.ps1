$ErrorActionPreference='Stop';$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try{
if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea'){throw 'Wrong model'}
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_english_small_figures_20261016\native_acceptance_111\release';if(Test-Path $out){throw 'Output exists'};New-Item -ItemType Directory -Path $out|Out-Null
$p=$r.GetProjectInterface()
foreach($id in @(2,3,4,5,6)){
 $d=$r.GetDiagramByID($id);if($d.Name -notmatch '^REQ_english_'){throw 'Unexpected diagram'}
 $r.OpenDiagram($id);$d.DiagramObjects.Refresh()
 foreach($o in $d.DiagramObjects){$e=$r.GetElementByID($o.ElementID);if($e.Type -eq 'Package'){$o.top=-10;$o.Update()|Out-Null}}
 $r.ReloadDiagram($id)
 foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};$p.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $out ($d.Name.Substring(4)+'.'+$ext)),$type)|Out-Null}
}
$r.SQLQuery('SELECT d.Diagram_ID,d.RectTop,d.RectBottom,d.RectLeft,d.RectRight,d.ObjectStyle,o.ea_guid,o.Object_Type FROM t_diagramobjects d INNER JOIN t_object o ON d.Object_ID=o.Object_ID')|Set-Content (Join-Path $out 'native_geometry.xml') -Encoding UTF8
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
