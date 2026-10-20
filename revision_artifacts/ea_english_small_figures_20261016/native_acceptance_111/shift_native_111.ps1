$ErrorActionPreference='Stop'
$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try {
 if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea'){throw 'Wrong repository'}
 $out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_english_small_figures_20261016\native_acceptance_111\final'
 $project=$r.GetProjectInterface()
 foreach($id in @(2,3,4,5,6)) {
  $d=$r.GetDiagramByID($id)
  if($d.Name -notmatch '^REQ_english_(full|scope|alarm|maintenance|temperature)$'){throw 'Unexpected diagram'}
  $pkg=$r.GetPackageByID($d.PackageID);if($pkg.Name -ne ('Presentation_'+$d.Name.Substring(4))){throw 'Wrong package'}
  foreach($obj in $d.DiagramObjects){$obj.top=[int]$obj.top-40;$obj.bottom=[int]$obj.bottom-40;$obj.Update()|Out-Null}
  foreach($link in $d.DiagramLinks){
   $link.Path=[regex]::Replace([string]$link.Path,'(-?\d+):(-?\d+);',{param($m) $m.Groups[1].Value+':'+([int]$m.Groups[2].Value-40)+';'})
   $link.Update()|Out-Null
  }
  $d.Update()|Out-Null;$r.ReloadDiagram($id);$r.OpenDiagram($id)
  foreach($ext in @('png','emf')){$target=Join-Path $out ($d.Name.Substring(4)+'.'+$ext);if(Test-Path $target){throw 'Output exists'};$type=if($ext -eq 'emf'){0}else{1};if(-not $project.PutDiagramImageToFile($d.DiagramGUID,$target,$type)){throw 'Export failed'}}
 }
 foreach($pair in @(@('objects','SELECT Object_ID,Name,Object_Type,Stereotype,ea_guid FROM t_object'),@('properties','SELECT Object_ID,Property,Value,Notes FROM t_objectproperties'),@('connectors','SELECT Connector_ID,Start_Object_ID,End_Object_ID,Connector_Type FROM t_connector'),@('diagramobjects','SELECT Diagram_ID,Object_ID,RectTop,RectBottom,RectLeft,RectRight,ObjectStyle FROM t_diagramobjects'),@('diagramlinks','SELECT DiagramID,ConnectorID,Geometry,Style FROM t_diagramlinks'),@('diagrams','SELECT Diagram_ID,Name,ea_guid,StyleEx FROM t_diagram'),@('xref','SELECT Name,Type,Client,Description FROM t_xref'))) {
 $r.SQLQuery($pair[1])|Set-Content (Join-Path $out ($pair[0]+'.xml')) -Encoding UTF8
 }
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
