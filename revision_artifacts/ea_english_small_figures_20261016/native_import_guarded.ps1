$ErrorActionPreference='Stop'
$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try {
 if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea'){throw 'Wrong repository'}
 $out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_english_small_figures_20261016'
 $p=$r.GetProjectInterface();$model=$r.Models.GetAt(0)
 $r.SQLQuery('SELECT Diagram_ID,Name,ea_guid FROM t_diagram')|Set-Content (Join-Path $out 'before_diagrams.xml') -Encoding UTF8
 foreach($case in @('english_full','english_scope','english_alarm','english_maintenance','english_temperature')) {
  $target=Join-Path $out ('native_'+$case)
  if(Test-Path $target){throw 'Refusing overwrite'}
  New-Item -ItemType Directory -Path $target|Out-Null
  if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea'){throw 'Repository changed'}
  $p.ImportPackageXMI($model.PackageGUID,(Join-Path $out ($case+'.xml')),1,0)|Set-Content (Join-Path $target 'import_response.txt') -Encoding UTF8
  foreach($pair in @(@('objects','SELECT Object_ID,Name,Object_Type,Stereotype,ea_guid FROM t_object'),@('properties','SELECT Object_ID,Property,Value,Notes FROM t_objectproperties'),@('connectors','SELECT Connector_ID,Start_Object_ID,End_Object_ID,Connector_Type FROM t_connector'),@('diagramobjects','SELECT Diagram_ID,Object_ID,RectTop,RectBottom,RectLeft,RectRight,ObjectStyle FROM t_diagramobjects'),@('diagrams','SELECT Diagram_ID,Name,ea_guid,StyleEx FROM t_diagram'),@('xref','SELECT Name,Type,Client,Description FROM t_xref'))) {
   $r.SQLQuery($pair[1])|Set-Content (Join-Path $target ($pair[0]+'.xml')) -Encoding UTF8
  }
  $ds=[xml]$r.SQLQuery("SELECT Diagram_ID,Name,ea_guid FROM t_diagram WHERE Name='REQ_$case'")
  $rows=@($ds.SelectNodes('//Row'));if($rows.Count -ne 1){throw 'Expected exactly one new diagram'}
  $row=$rows[0];$r.OpenDiagram([int]$row.Diagram_ID)
  foreach($ext in @('png','emf')) {
   $file=Join-Path $out ($case+'.'+$ext);if(Test-Path $file){throw 'Refusing image overwrite'}
   $type=if($ext -eq 'emf'){0}else{1}
   if(-not $p.PutDiagramImageToFile([string]$row.ea_guid,$file,$type)){throw 'Image export failed'}
  }
  Write-Output ('Verified import/export '+$case+' diagram '+$row.Diagram_ID)
 }
} finally {[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
