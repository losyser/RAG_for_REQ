$ErrorActionPreference='Stop';$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try{
 if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea'){throw 'Wrong repository'}
 $out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v3_20261016';$audit=Join-Path $out 'audit';$records=Get-Content (Join-Path $audit 'native_created.json') -Raw -Encoding UTF8|ConvertFrom-Json;$record=$records|Where-Object file -eq 'paper_v3_temperature';$d=$r.GetDiagramByID($record.diagram_id);$pkg=$r.GetPackageByID($d.PackageID);if($pkg.Name -ne 'Paper v3 - Temperature Control'){throw 'Wrong package'}
 $saved=@();$links=@();$project=$r.GetProjectInterface()
 foreach($obj in $d.DiagramObjects){$e=$r.GetElementByID($obj.ElementID);if($e.Type -ne 'Requirement'){continue};$saved+=@{Object=$obj;Left=$obj.Left;Right=$obj.Right;Top=$obj.Top;Bottom=$obj.Bottom;Style=$obj.Style;ShowNotes=$obj.ShowNotes};$id=$e.TaggedValues.GetByName('id').Value
  if($id -eq 'OR008'){$obj.ShowNotes=$true;$obj.Left=20;$obj.Right=420;$obj.Top=-200;$obj.Bottom=-600}
  elseif($id -eq 'OR008.1'){$obj.ShowNotes=$true;$obj.Left=500;$obj.Right=1000;$obj.Top=-60;$obj.Bottom=-390}
  elseif($id -eq 'OR008.5'){$obj.Left=500;$obj.Right=1000;$obj.Top=-420;$obj.Bottom=-510}
  elseif($id -eq 'OR008.8'){$obj.Left=500;$obj.Right=1000;$obj.Top=-550;$obj.Bottom=-640}
  $obj.Update()|Out-Null
 }
 try{
  if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $audit 'root_child_notes_expanded.png'),1)){throw 'Expanded render failed'}
 }finally{foreach($s in $saved){$o=$s.Object;$o.Style=$s.Style;$o.ShowNotes=$s.ShowNotes;$o.Left=$s.Left;$o.Right=$s.Right;$o.Top=$s.Top;$o.Bottom=$s.Bottom;$o.Update()|Out-Null}}
 if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $audit 'root_child_notes_refolded.png'),1)){throw 'Refolded render failed'}
 foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$r.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $audit ('final_'+$table+'.xml')) -Encoding UTF8}
 Write-Output 'Root and child Notes expanded and restored in new diagram only.'
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
