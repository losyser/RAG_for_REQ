$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$logRoot = Join-Path $appRoot 'local_records'
$address = 'http://127.0.0.1:8769'
$launchMutex = [System.Threading.Mutex]::new($false, 'Local\CoolingMappingReviewLauncherV1')
$ownsMutex = $false
function Test-ReviewServer {
    try {
        $health = Invoke-RestMethod -Uri "$address/api/health" -TimeoutSec 2
        return ($health.app -eq 'expert-mapping-review' -and $health.version -eq 1 -and $health.mode -eq 'production')
    } catch { return $false }
}
try {
    $ownsMutex = $launchMutex.WaitOne(0)
    if (-not $ownsMutex) { exit 0 }
    if (-not (Test-ReviewServer)) {
        $candidates = @('D:\Program Files\Python314\python.exe', 'D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe')
        $pythonExe = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $pythonExe) { $pythonExe = (Get-Command python.exe -ErrorAction Stop).Source }
        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
        $process = Start-Process -FilePath $pythonExe -ArgumentList @('-I', ('"' + (Join-Path $appRoot 'server.py') + '"')) -WorkingDirectory $appRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'server.stdout.log') -RedirectStandardError (Join-Path $logRoot 'server.stderr.log')
        $ready = $false
        for ($attempt = 0; $attempt -lt 25; $attempt++) {
            Start-Sleep -Milliseconds 400
            if (Test-ReviewServer) { $ready = $true; break }
            if ($process.HasExited) { break }
        }
        if (-not $ready) { throw '本地审核服务未启动。端口 8769 可能被占用，请查看 local_records\server.stderr.log。原审查记录未更改。' }
    }
    Start-Process $address
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, '需求映射审核启动失败') | Out-Null
    exit 1
} finally {
    if ($ownsMutex) { $launchMutex.ReleaseMutex() }
    $launchMutex.Dispose()
}

