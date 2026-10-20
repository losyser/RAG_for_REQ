$ErrorActionPreference='Stop'
$out='C:\Users\yando\Documents\Codex\2026-10-16\task\native_attempt'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$log=Join-Path $out 'attempt.log'
function Record($message) { $line=([DateTime]::UtcNow.ToString('o')+' '+$message); $line | Add-Content -LiteralPath $log -Encoding UTF8; Write-Output $line }
$repo=$null; $owned=$false
try {
 $app=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App')
 $existing=$app.Repository
 $existingSession=$existing.InstanceGUID
 $existingPath=$existing.ConnectionString
 Record ('Existing session='+$existingSession+' connection='+$existingPath)
 Record 'Attempting exactly one independent EA.Repository COM activation'
 $repo=New-Object -ComObject EA.Repository
 Record ('New session='+$repo.InstanceGUID+' initial connection='+$repo.ConnectionString)
 if($repo.InstanceGUID -eq $existingSession -or $repo.ConnectionString) {throw 'New repository is not demonstrably independent and empty; refusing model operations'}
 $owned=$true
 $model=Join-Path $out 'structure_minimal_test.qea'
 if(Test-Path -LiteralPath $model) {throw 'Test file exists; refusing overwrite'}
 Copy-Item -LiteralPath 'D:\Program Files\Sparx Systems\EA Trial\EABase.qea' -Destination $model
 if(-not $repo.OpenFile($model)){throw 'OpenFile failed'}
 if($repo.ConnectionString -ne $model){throw 'Unexpected model connection'}
 Record ('Opened independent test model '+$repo.ConnectionString)
 if($repo.Models.Count -eq 0){$root=$repo.Models.AddNew('Structure validation','Package');[void]$root.Update();$repo.Models.Refresh()}
 $root=$repo.Models.GetAt(0)
 $project=$repo.GetProjectInterface()
 $input='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_structure_20261016\ea_native_OR041_minimal_structure.xml'
 $message=$project.ImportPackageXMI($root.PackageGUID,$input,1,0)
 Record ('Import response='+$message)
 foreach($query in @(
  @('objects','SELECT Object_ID, Name, Object_Type, Stereotype, ea_guid FROM t_object'),
  @('properties','SELECT Object_ID, Property, Value, Notes FROM t_objectproperties'),
  @('xref','SELECT XrefID, Name, Type, Client, Description FROM t_xref'),
  @('diagramobjects','SELECT Diagram_ID, Object_ID, RectTop, RectLeft, RectRight, RectBottom, ObjectStyle FROM t_diagramobjects'),
  @('diagrams','SELECT Diagram_ID, Name, ea_guid, StyleEx FROM t_diagram')
 )){$repo.SQLQuery($query[1]) | Set-Content -LiteralPath (Join-Path $out ($query[0]+'.xml')) -Encoding UTF8}
 $diagrams=[xml]$repo.SQLQuery('SELECT Diagram_ID, Name, ea_guid FROM t_diagram')
 foreach($row in $diagrams.SelectNodes('//Row')){
  $repo.OpenDiagram([int]$row.Diagram_ID)
  Record ('PNG export '+$project.PutDiagramImageToFile([string]$row.ea_guid,(Join-Path $out ('diagram_'+$row.Diagram_ID+'.png')),1))
 }
 Record 'Minimal import/readback/export completed; requires content and image verification'
} catch {
 Record ('FAILED: '+$_.Exception.ToString())
 $_ | Out-String | Add-Content -LiteralPath $log -Encoding UTF8
} finally {
 if($owned -and $repo){$repo.CloseFile();$repo.Exit()}
 if($repo){[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($repo)}
 if($existing){Record ('Existing model after attempt='+$existing.ConnectionString);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($existing)}
 if($app){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
