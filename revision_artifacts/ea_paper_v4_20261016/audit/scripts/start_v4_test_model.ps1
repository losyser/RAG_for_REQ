$ErrorActionPreference='Stop'
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v4_20261016'
$test=Join-Path $out 'v4_independent_import.qea'
$app=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$old=$app.Repository
$oldPath=$old.ConnectionString;$oldInstance=$old.InstanceGUID
if($oldPath -ne 'C:\Users\yando\Desktop\4x.qea'){throw ('Unexpected active path '+$oldPath)}
if(Test-Path -LiteralPath $test){throw 'Test file exists; not overwriting'}
Copy-Item -LiteralPath 'D:\Program Files\Sparx Systems\EA Trial\EABase.qea' -Destination $test
$process=Start-Process -FilePath 'D:\Program Files\Sparx Systems\EA Trial\EA.exe' -ArgumentList ('"'+$test+'"') -WindowStyle Hidden -PassThru
$record=[ordered]@{test_path=$test;launched_pid=$process.Id;protected_path=$oldPath;protected_instance=$oldInstance}
$record|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'audit\test_model_launch.json') -Encoding UTF8
$record|ConvertTo-Json
for($i=0;$i -lt 15;$i++){
 Start-Sleep -Seconds 2
 if($old.ConnectionString -ne $oldPath){throw 'Protected connection changed; stop'}
 try{$active=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App').Repository;Write-Output ('ACTIVE '+$active.InstanceGUID+' '+$active.ConnectionString)}catch{Write-Output $_.Exception.Message}
}
