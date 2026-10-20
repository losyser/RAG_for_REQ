$ErrorActionPreference='Stop'
$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try {
 $expected='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea'
 if($r.ConnectionString -ne $expected){throw 'Wrong repository'}
 $out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v3_20261016';$audit=Join-Path $out 'audit'
 if(-not(Test-Path (Join-Path $out '111_before_v3.qea'))){throw 'Backup missing'}
 $existing=[xml]$r.SQLQuery("SELECT Package_ID FROM t_package WHERE Name LIKE 'Paper v3 - %'");if($existing.SelectNodes('//Row').Count){throw 'v3 exists: no duplicate creation'}
 function Snapshot($prefix){foreach($table in @('t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref')){$r.SQLQuery("SELECT * FROM $table")|Set-Content (Join-Path $audit ($prefix+'_'+$table+'.xml')) -Encoding UTF8}}
 Snapshot 'immediately_before'
 $spec=Get-Content (Join-Path $audit 'native_spec.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $model=$r.Models.GetAt(0);$project=$r.GetProjectInterface();$records=@()
 foreach($s in $spec){
  if($r.ConnectionString -ne $expected){throw 'Repository changed'}
  $pkg=$model.Packages.AddNew($s.package_name,'');if(-not $pkg.Update()){throw 'Package creation failed'}
  $ids=@{};$map=@{};$connectors=@{};$map[$s.package_xml_id]=$pkg.PackageGUID
  foreach($role in $s.roles){
   $e=$pkg.Elements.AddNew($role.name,'Requirement');$e.Notes=$role.notes;$e.StereotypeEx='SysML1.4::requirement';if(-not $e.Update()){throw 'Element creation failed'}
   $ids[$role.xml_id]=$e.ElementID;$map[$role.xml_id]=$e.ElementGUID
   foreach($prop in $role.tags.PSObject.Properties){
    $t=$null;foreach($existingTag in $e.TaggedValues){if($existingTag.Name -eq $prop.Name){$t=$existingTag;break}}
    if($null -eq $t){$t=$e.TaggedValues.AddNew($prop.Name,'')}
    $v=[string]$prop.Value
    if($v.StartsWith('<memo>#NOTES#')){$t.Value='<memo>';$t.Notes=$v.Substring(13)}else{$t.Value=$v}
    if(-not $t.Update()){throw ('Tag update failed '+$prop.Name)}
   }
  }
  foreach($edge in $s.edges){$e=$r.GetElementByID($ids[$edge.ends[0]]);$c=$e.Connectors.AddNew('','Nesting');$c.SupplierID=$ids[$edge.ends[1]];if(-not $c.Update()){throw 'Connector creation failed'};$connectors[$edge.xml_id]=$c.ConnectorID;$map[$edge.xml_id]=$c.ConnectorGUID}
  $d=$pkg.Diagrams.AddNew($s.diagram_name,'Logical');$d.StyleEx=$s.styleex;$d.ExtendedStyle=$s.eastyle;$d.MetaType='SysML1.4::Requirement';if(-not $d.Update()){throw 'Diagram creation failed'};$map[$s.diagram_xml_id]=$d.DiagramGUID
  foreach($v in $s.view){
   if($ids.ContainsKey($v.subject)){
    $g=@{};foreach($m in [regex]::Matches($v.geometry,'(Left|Right|Top|Bottom)=(-?\d+)')){$g[$m.Groups[1].Value]=[int]$m.Groups[2].Value}
    $obj=$d.DiagramObjects.AddNew(('l='+$g.Left+';r='+$g.Right+';t='+(-$g.Top)+';b='+(-$g.Bottom)+';'),'');$obj.ElementID=$ids[$v.subject];$obj.Style=$v.style;if(-not $obj.Update()){throw 'Diagram object failed'}
   }elseif($connectors.ContainsKey($v.subject)){
    $link=$d.DiagramLinks.AddNew('','');$link.ConnectorID=$connectors[$v.subject];$link.Style=$v.style;$link.IsHidden=$false
    $path=[regex]::Match($v.geometry,'Path=([^;]*);');$link.Path=$path.Groups[1].Value;$link.Geometry=[regex]::Replace($v.geometry,'Path=[^;]*;','');if(-not $link.Update()){throw 'Diagram link failed'}
   }
  }
  $d.DiagramObjects.Refresh();$d.DiagramLinks.Refresh()
  # Direct native render: no OpenDiagram, SaveDiagram, SaveAllDiagrams, CloseDiagram, or ImportPackageXMI.
  foreach($ext in @('png','emf')){$type=if($ext -eq 'emf'){0}else{1};if(-not $project.PutDiagramImageToFile($d.DiagramGUID,(Join-Path $out ('paper\'+$s.file+'.'+$ext)),$type)){throw 'Image export failed'}}
  $records+=@{file=$s.file;diagram_id=$d.DiagramID;package_id=$pkg.PackageID;guid_map=$map}
  $records|ConvertTo-Json -Depth 20|Set-Content (Join-Path $audit 'native_created.json') -Encoding UTF8
  Snapshot ('after_'+$s.file)
  Write-Output ('Created and rendered '+$s.file+' diagram '+$d.DiagramID)
 }
 Snapshot 'final'
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
