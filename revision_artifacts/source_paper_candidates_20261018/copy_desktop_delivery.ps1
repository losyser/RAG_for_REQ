$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$desktopRoot = [Environment]::GetFolderPath('Desktop')
$targetPath = [IO.Path]::GetFullPath((Join-Path $desktopRoot '论文项目夜间优化_20261019'))
if ([IO.Path]::GetDirectoryName($targetPath) -ne $desktopRoot) { throw 'Destination escaped Desktop' }
if (Test-Path -LiteralPath $targetPath) { throw 'Destination already exists; no files overwritten' }
$files = @(
    @{ Source = 'minor_revision_candidate.zip'; Name = '作者审阅候选包.zip' },
    @{ Source = 'DESKTOP_README.txt'; Name = '先读说明.txt' },
    @{ Source = 'minor_revision_candidate\paper_wiley.pdf'; Name = '论文候选_clean.pdf' },
    @{ Source = 'minor_revision_candidate\paper_cumulative_diff.pdf'; Name = '论文候选_累计diff.pdf' }
)
foreach ($entry in $files) {
    $sourcePath = Join-Path $sourceRoot $entry.Source
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing delivery: $($entry.Source)" }
}
[IO.Directory]::CreateDirectory($targetPath) | Out-Null
$verified = @()
foreach ($entry in $files) {
    $sourcePath = Join-Path $sourceRoot $entry.Source
    $destinationPath = Join-Path $targetPath $entry.Name
    [IO.File]::Copy($sourcePath, $destinationPath, $false)
    $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath $destinationPath -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) { throw 'Copy hash mismatch' }
    $verified += @{ source = $sourcePath; destination = $destinationPath; sha256 = $sourceHash; matched = $true }
}
@{ directory = $targetPath; overwritten = $false; files = $verified } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sourceRoot 'DESKTOP_DELIVERY.json') -Encoding utf8
Write-Output $targetPath
