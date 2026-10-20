$ErrorActionPreference = 'Stop'
$outputRoot = Join-Path $PSScriptRoot 'outputs\pilot_excel'
$templatePath = Join-Path $outputRoot '需求映射专家试做_OR002_OR001.xlsx'
$copyPath = Join-Path $outputRoot ('isolated_native_test_' + [guid]::NewGuid().ToString('N') + '.xlsx')
if (Test-Path -LiteralPath $copyPath) { throw 'Test copy already exists' }
Copy-Item -LiteralPath $templatePath -Destination $copyPath
$excel = $null
$book = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $book = $excel.Workbooks.Open($copyPath, 0, $false)
    if ($book.Worksheets.Count -ne 5) { throw 'Sheet count mismatch' }
    $candidateSheet = $book.Worksheets.Item('2候选判断')
    $firstSheet = $book.Worksheets.Item('1独立首判')
    $homeSheet = $book.Worksheets.Item('0规则与计时')
    $validationType = $candidateSheet.Range('E9').Validation.Type
    $validationFormula = $candidateSheet.Range('E9').Validation.Formula1
    if ($validationType -ne 3 -or $validationFormula -notlike '*不确定*' -or $validationFormula -notlike '*未答*') { throw 'Candidate dropdown missing' }
    $candidateSheet.Range('E9').Value2 = '不确定'
    if (-not $candidateSheet.Range('E9').Validation.Value) { throw 'Valid dropdown choice rejected' }
    $candidateSheet.Range('E9').Value2 = 'INVALID_TEST'
    if ($candidateSheet.Range('E9').Validation.Value) { throw 'Invalid dropdown choice accepted' }
    $candidateSheet.Range('E9').Value2 = '不确定'
    $candidateSheet.Range('F9').Value2 = "本机Excel隔离验证，非专家判断`n原中文第二行"
    $firstSheet.Range('A9').Value2 = 'OR002'
    $firstSheet.Range('B9').Value2 = 'alarm_system:alarm_response'
    $firstSheet.Range('E9').Value2 = '不确定'
    $firstSheet.Range('F9').Value2 = '隔离测试首判'
    if (-not $firstSheet.Range('B9').Validation.Value) { throw 'Named taxonomy dropdown failed' }
    $homeSheet.Range('B6').Value2 = '本机Excel测试，非专家'
    $homeSheet.Range('B19').Value2 = '是'
    $homeSheet.Range('B20').Value2 = '首判完成后查看'
    $homeSheet.Range('B21').Value2 = '2026-10-17 16:00'
    $homeSheet.Range('B28').Value2 = '2026-10-17 15:30'
    $homeSheet.Range('B24').Value2 = 12.5
    $homeSheet.Range('B25').Value2 = 0
    $excel.CalculateFullRebuild()
    if ($firstSheet.Range('C9').Value2 -ne '报警与保护系统') { throw 'Native lookup did not recalculate' }
    $book.Save()
    $book.Close($false)
    $book = $excel.Workbooks.Open($copyPath, 0, $true)
    if ($book.Worksheets.Item('2候选判断').Range('E9').Value2 -ne '不确定') { throw 'Saved choice not retained' }
    if ($book.Worksheets.Item('1独立首判').Range('C9').Value2 -ne '报警与保护系统') { throw 'Lookup after reopen failed' }
    [ordered]@{
        native_excel_open=$true
        dropdown_valid_and_invalid_choices_checked=$true
        named_taxonomy_dropdown_checked=$true
        formula_recalculation_checked=$true
        save_reopen_checked=$true
        isolated_copy=$copyPath
        original_template_edited=$false
        excel_version=$excel.Version
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputRoot 'native_excel_verification.json') -Encoding utf8
    Write-Output 'Native Excel validation passed'
} finally {
    if ($book) { $book.Close($false) }
    if ($excel) { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel) }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
