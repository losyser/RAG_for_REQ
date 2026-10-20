$ErrorActionPreference='Stop';$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try{
if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea'){throw 'Wrong model'}
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_folded_paper_20261016';$p=$r.GetProjectInterface()
foreach($id in @(8,9,10,11)){
 $d=$r.GetDiagramByID($id);if($d.Name -notmatch '^REQ_(folded_all|paper_overview|detail_b|detail_c)$'){throw 'Wrong diagram'}
 $name=$d.Name.Substring(4);$r.OpenDiagram($id)
 foreach($ext in @('emf','png')){$target=Join-Path $out ($name+'.'+$ext);if(Test-Path $target){throw 'Refusing overwrite'};$type=if($ext -eq 'emf'){0}else{1};Write-Output ($name+' '+$ext+': '+$p.PutDiagramImageToFile($d.DiagramGUID,$target,$type))}
}
foreach($pair in @(@('final_objects','SELECT Object_ID,Name,Note,ea_guid FROM t_object'),@('final_properties','SELECT Object_ID,Property,Value,Notes FROM t_objectproperties'),@('final_diagramobjects','SELECT Diagram_ID,Object_ID,RectTop,RectBottom,RectLeft,RectRight,ObjectStyle FROM t_diagramobjects'),@('final_diagramlinks','SELECT DiagramID,ConnectorID,Geometry,Style FROM t_diagramlinks'))){$r.SQLQuery($pair[1])|Set-Content (Join-Path $out ($pair[0]+'.xml')) -Encoding UTF8}
$r.OpenDiagram(9)
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
