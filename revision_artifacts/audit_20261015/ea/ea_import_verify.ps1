$ErrorActionPreference = 'Stop'
$outDir = 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\audit_20261015\ea'
$model = Join-Path $outDir 'audit_import.qea'
if (Test-Path -LiteralPath $model) { throw 'Independent test model already exists; refusing overwrite' }
Copy-Item -LiteralPath 'D:\Program Files\Sparx Systems\EA Trial\EABase.qea' -Destination $model
Write-Output 'Created independent copy of vendor EABase.qea'
$repo = New-Object -ComObject EA.Repository
if ($repo.ConnectionString) { throw 'Unexpected attached model; refusing to modify it' }
try {
    if (-not $repo.OpenFile($model)) { throw 'EA OpenFile returned false' }
    Write-Output ('EA opened test model: ' + $repo.ConnectionString)
    if ($repo.Models.Count -eq 0) {
        $modelRoot = $repo.Models.AddNew('Revision Audit', 'Package')
        [void]$modelRoot.Update()
        $repo.Models.Refresh()
    }
    $parent = $repo.Models.GetAt(0)
    $project = $repo.GetProjectInterface()
    $result = $project.ImportPackageXMI($parent.PackageGUID, (Join-Path $outDir 'ea_native_sel.xml'), 1, 0)
    Write-Output ('Import result: ' + $result)
    $result | Set-Content -LiteralPath (Join-Path $outDir 'ea_import_message.txt') -Encoding utf8
    $objects = $repo.SQLQuery('SELECT Object_ID, Name, Object_Type, Stereotype, ea_guid FROM t_object')
    $objects | Set-Content -LiteralPath (Join-Path $outDir 'ea_imported_objects.xml') -Encoding utf8
    $repo.SQLQuery('SELECT Connector_ID, Start_Object_ID, End_Object_ID, Connector_Type, Stereotype FROM t_connector') | Set-Content -LiteralPath (Join-Path $outDir 'ea_imported_connectors.xml') -Encoding utf8
    $repo.SQLQuery('SELECT Object_ID, Property, Value, Notes FROM t_objectproperties') | Set-Content -LiteralPath (Join-Path $outDir 'ea_imported_properties.xml') -Encoding utf8
    $diagrams = [xml]$repo.SQLQuery('SELECT Diagram_ID, Name, ea_guid FROM t_diagram')
    $diagrams.OuterXml | Set-Content -LiteralPath (Join-Path $outDir 'ea_imported_diagrams.xml') -Encoding utf8
    foreach ($row in $diagrams.SelectNodes('//Row')) {
        if ($row.Name -eq 'REQ_Selected_Requirements') {
            $repo.OpenDiagram([int]$row.Diagram_ID)
            $ok = $project.PutDiagramImageToFile([string]$row.ea_guid, (Join-Path $outDir 'ea_merged.png'), 1)
            Write-Output ('Merged PNG export: ' + $ok)
        }
    }
    Write-Output 'EA import/readback completed'
} finally {
    $repo.CloseFile()
    $repo.Exit()
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($repo)
}
