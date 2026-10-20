param([string]$Case='minimal')
$ErrorActionPreference='Stop'
$expected='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea'
$base='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016'
$out=Join-Path 'C:\Users\yando\Documents\Codex\2026-10-16\task' ('native_verified_'+$Case)
if(Test-Path -LiteralPath $out){throw 'Output directory already exists'}
New-Item -ItemType Directory -Path $out | Out-Null
$app=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App')
$repo=$app.Repository
try {
 if($repo.ConnectionString -ne $expected){throw ('Wrong repository: '+$repo.ConnectionString)}
 $repo.ConnectionString | Set-Content (Join-Path $out 'connection.txt')
 $before=$repo.SQLQuery('SELECT Object_ID,Name,Object_Type FROM t_object')
 $before | Set-Content (Join-Path $out 'before_objects.xml') -Encoding UTF8
 $file=if($Case -eq 'minimal'){'ea_native_OR041_minimal_core_tags_CANDIDATE.xml'}else{'ea_native_sel_core_tags_CANDIDATE.xml'}
 $root=$repo.Models.GetAt(0)
 $project=$repo.GetProjectInterface()
 $response=$project.ImportPackageXMI($root.PackageGUID,(Join-Path $base $file),1,0)
 $response | Set-Content (Join-Path $out 'import_response.txt') -Encoding UTF8
 foreach($pair in @(
 @('objects','SELECT Object_ID,Name,Object_Type,Stereotype,ea_guid FROM t_object'),
 @('properties','SELECT Object_ID,Property,Value,Notes FROM t_objectproperties'),
 @('xref','SELECT Name,Type,Client,Description FROM t_xref'),
 @('diagramobjects','SELECT Diagram_ID,Object_ID,RectTop,RectLeft,RectRight,RectBottom,ObjectStyle FROM t_diagramobjects'),
 @('diagrams','SELECT Diagram_ID,Name,ea_guid,StyleEx FROM t_diagram'),
 @('connectors','SELECT Connector_ID,Start_Object_ID,End_Object_ID,Connector_Type FROM t_connector')
 )){$repo.SQLQuery($pair[1]) | Set-Content (Join-Path $out ($pair[0]+'.xml')) -Encoding UTF8}
 $diagrams=[xml]$repo.SQLQuery('SELECT Diagram_ID,Name,ea_guid FROM t_diagram')
 foreach($row in $diagrams.SelectNodes('//Row')){
  if($row.Name -like '*CoreTags_CANDIDATE*'){
   $repo.OpenDiagram([int]$row.Diagram_ID)
   $ok=$project.PutDiagramImageToFile([string]$row.ea_guid,(Join-Path $out ('diagram_'+$row.Diagram_ID+'.png')),1)
   Write-Output ('Native PNG '+$row.Name+': '+$ok)
  }
 }
 Write-Output ('Readback saved: '+$out)
}finally{
 [void][Runtime.InteropServices.Marshal]::ReleaseComObject($repo)
 [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
