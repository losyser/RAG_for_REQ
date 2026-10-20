$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
Add-Type -TypeDefinition @"
using System;using System.Runtime.InteropServices;using System.Runtime.InteropServices.ComTypes;
public static class EATargetROT {
 [DllImport("ole32.dll")]static extern int GetRunningObjectTable(int r,out IRunningObjectTable t);
 [DllImport("ole32.dll")]static extern int CreateBindCtx(int r,out IBindCtx b);
 public static object Get(string wanted){IRunningObjectTable t;IBindCtx b;GetRunningObjectTable(0,out t);CreateBindCtx(0,out b);IEnumMoniker en;t.EnumRunning(out en);var m=new IMoniker[1];while(en.Next(1,m,IntPtr.Zero)==0){string n;m[0].GetDisplayName(b,null,out n);if(n==wanted){object o;t.GetObject(m[0],out o);return o;}}throw new Exception("Exact EA instance not found: "+wanted);}
}
"@
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_notes_detail_20261016'
$repo=[EATargetROT]::Get('!Sparx.EA.App:23884').Repository
$old=[EATargetROT]::Get('!Sparx.EA.App:2880').Repository
$test=Join-Path $out 'notes_import_validation.qea'
if($repo.ConnectionString -ne $test -or $old.ConnectionString -ne 'C:\Users\yando\Desktop\4x.qea'){throw 'Exact repository guard failed'}
if($repo.Models.Count -eq 0){$m=$repo.Models.AddNew('Notes validation','Package');$m.Update()|Out-Null;$repo.Models.Refresh()}
$project=$repo.GetProjectInterface();$model=$repo.Models.GetAt(0)
$response=$project.ImportPackageXMI($model.PackageGUID,(Join-Path $out 'paper\reliability_selected_notes.xml'),1,0)
$response|Set-Content (Join-Path $out 'audit\import_response.txt') -Encoding UTF8
$rows=[xml]$repo.SQLQuery('SELECT Diagram_ID FROM t_diagram')
foreach($row in $rows.SelectNodes('//Row')){
 $d=$repo.GetDiagramByID([int]$row.Diagram_ID);$repo.OpenDiagram($d.DiagramID)
 foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $out ('paper\reliability_selected_notes.'+$ext)),$type)){throw 'Export failed'}}
}
foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$repo.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $out ('audit\imported_'+$table+'.xml')) -Encoding UTF8}
Write-Output ('Actual XML import and native exports completed in '+$test)