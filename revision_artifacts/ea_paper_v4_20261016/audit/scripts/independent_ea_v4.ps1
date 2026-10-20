$ErrorActionPreference='Stop';$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v4_20261016';$log=Join-Path $out 'audit\independent_ea.log';$owned=$false;$repo=$null
function Log($s){([DateTime]::UtcNow.ToString('o')+' '+$s)|Add-Content -LiteralPath $log -Encoding UTF8;Write-Output $s}
try{
 $app=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$old=$app.Repository;$oldPath=$old.ConnectionString;$oldGuid=$old.InstanceGUID;Log ('Protected existing repository: '+$oldPath+' instance '+$oldGuid)
 if($oldPath -ne 'C:\Users\yando\Desktop\4x.qea'){throw 'Existing repository mismatch; no changes'}
 Log 'Activating one independent EA.Repository';$repo=New-Object -ComObject EA.Repository
 if($repo.InstanceGUID -eq $oldGuid -or $repo.ConnectionString){throw 'Independent empty repository not established'};$owned=$true;Log ('Independent instance '+$repo.InstanceGUID)
 $test=Join-Path $out 'audit\independent_combined.qea';if(Test-Path $test){throw 'Test repository already exists'};Copy-Item -LiteralPath 'D:\Program Files\Sparx Systems\EA Trial\EABase.qea' -Destination $test
 if(-not $repo.OpenFile($test)){throw 'Independent OpenFile failed'};Log ('Opened '+$repo.ConnectionString)
 if($repo.Models.Count -eq 0){$model=$repo.Models.AddNew('Paper import validation','Package');$model.Update()|Out-Null;$repo.Models.Refresh()};$model=$repo.Models.GetAt(0);$project=$repo.GetProjectInterface()
 $input=Join-Path $out 'paper\paper_v4_combined.xml';$ready=Join-Path $out 'audit\ready_for_import.txt';$deadline=[DateTime]::UtcNow.AddMinutes(25)
 Log 'Ready for final combined XML'
 while(-not(Test-Path $ready)){if([DateTime]::UtcNow -gt $deadline){throw 'No ready marker before deadline'};Start-Sleep -Seconds 1}
 if($old.ConnectionString -ne $oldPath -or $repo.ConnectionString -ne $test){throw 'Repository identity changed'}
 $project.ImportPackageXMI($model.PackageGUID,$input,1,0)|Set-Content (Join-Path $out 'audit\combined_import_response.txt') -Encoding UTF8
 foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$repo.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $out ('audit\imported_'+$table+'.xml')) -Encoding UTF8}
 $ds=[xml]$repo.SQLQuery('SELECT Diagram_ID,Name,ea_guid FROM t_diagram')
 foreach($row in $ds.SelectNodes('//Row')){
  if($row.Name -notlike 'Paper v4*'){continue}
  $id=[int]$row.Diagram_ID;$repo.OpenDiagram($id);$d=$repo.GetDiagramByID($id)
  $slug=if($row.Name -like '*Reliability*'){'reliability'}elseif($row.Name -like '*Parameters*'){'parameters'}elseif($row.Name -like '*Installation*'){'installation'}else{throw 'Unexpected diagram'}
  foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $out ('paper\paper_v4_'+$slug+'.'+$ext)),$type)){throw 'Export failed'}}
  Log ('Imported and rendered '+$row.Name)
 }
 foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$repo.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $out ('audit\rendered_'+$table+'.xml')) -Encoding UTF8}
 if($old.ConnectionString -ne $oldPath){throw 'Original connection changed'}
 Log 'Combined import complete; original connection unchanged'
}catch{Log ('BLOCKED: '+$_.Exception.ToString());exit 1}
finally{if($owned -and $null -ne $repo){$repo.CloseFile();$repo.Exit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($repo)};if($null -ne $old){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($old)};if($null -ne $app){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}}
