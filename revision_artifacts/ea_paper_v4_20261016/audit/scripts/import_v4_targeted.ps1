$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
Add-Type -TypeDefinition @"
using System;using System.Runtime.InteropServices;using System.Runtime.InteropServices.ComTypes;
public static class EATargetROT {
 [DllImport("ole32.dll")]static extern int GetRunningObjectTable(int r,out IRunningObjectTable t);
 [DllImport("ole32.dll")]static extern int CreateBindCtx(int r,out IBindCtx b);
 public static object Get(string wanted){IRunningObjectTable t;IBindCtx b;GetRunningObjectTable(0,out t);CreateBindCtx(0,out b);IEnumMoniker en;t.EnumRunning(out en);var m=new IMoniker[1];while(en.Next(1,m,IntPtr.Zero)==0){string n;m[0].GetDisplayName(b,null,out n);if(n==wanted){object o;t.GetObject(m[0],out o);return o;}}throw new Exception("Exact EA instance not found: "+wanted);}
}
"@
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v4_20261016'
$test=Join-Path $out 'v4_independent_import.qea'
$old=[EATargetROT]::Get('!Sparx.EA.App:2880').Repository
$repo=[EATargetROT]::Get('!Sparx.EA.App:3688').Repository
if($old.ConnectionString -ne 'C:\Users\yando\Desktop\4x.qea' -or $repo.ConnectionString -ne $test -or $repo.InstanceGUID -eq $old.InstanceGUID){throw 'Repository guard failed'}
Write-Output ('Protected '+$old.ConnectionString+'; importing into '+$repo.ConnectionString)
$render=Join-Path $out 'audit\native_render';New-Item -ItemType Directory -Path $render -Force|Out-Null
if($repo.Models.Count -eq 0){$model=$repo.Models.AddNew('V4 Import Validation','Package');$model.Update()|Out-Null;$repo.Models.Refresh()}
$model=$repo.Models.GetAt(0);$project=$repo.GetProjectInterface()
Write-Output 'Starting one actual combined XMI import'
$response=$project.ImportPackageXMI($model.PackageGUID,(Join-Path $out 'candidate\paper_v4_combined.xml'),1,0)
$response|Set-Content (Join-Path $out 'audit\combined_import_response.txt') -Encoding UTF8
Write-Output ('Import returned '+$response)
foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$repo.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $out ('audit\imported_'+$table+'.xml')) -Encoding UTF8}
$ds=[xml]$repo.SQLQuery('SELECT Diagram_ID,Name,ea_guid FROM t_diagram')
foreach($row in $ds.SelectNodes('//Row')){
 if($row.Name -notlike 'Paper v4*'){continue}
 $id=[int]$row.Diagram_ID;$repo.OpenDiagram($id);$d=$repo.GetDiagramByID($id)
 $slug=if($row.Name -like '*Reliability*'){'reliability'}elseif($row.Name -like '*Parameters*'){'parameters'}elseif($row.Name -like '*Installation*'){'installation'}else{throw 'Unexpected diagram'}
 foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $render ('paper_v4_'+$slug+'.'+$ext)),$type)){throw ('Export failed '+$slug)}}
 Write-Output ('Imported and rendered '+$row.Name)
}
if($old.ConnectionString -ne 'C:\Users\yando\Desktop\4x.qea'){throw 'Protected connection changed'}
Write-Output 'Finished; both repositories remain open'
