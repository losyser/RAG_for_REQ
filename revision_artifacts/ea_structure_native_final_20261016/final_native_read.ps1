$ErrorActionPreference='Stop'
$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try{
if($r.ConnectionString -ne 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea'){throw 'Wrong model'}
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_structure_native_final_20261016\native_verified'
$r.SQLQuery('SELECT ConnectorID,DiagramID,Geometry,Style FROM t_diagramlinks WHERE DiagramID=5') | Set-Content (Join-Path $out 'diagramlinks.xml') -Encoding UTF8
$r.SQLQuery('SELECT Object_ID,Note,ea_guid FROM t_object') | Set-Content (Join-Path $out 'documentation.xml') -Encoding UTF8
$d=$r.GetDiagramByID(5);$p=$r.GetProjectInterface();$pkg=$r.GetPackageByID($d.PackageID)
$p.ExportPackageXMI($pkg.PackageGUID,0,1,-1,1,0,(Join-Path $out 'native_roundtrip.xml'))
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
