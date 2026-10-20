$ErrorActionPreference='Continue'
$lines=[Collections.Generic.List[string]]::new()
$lines.Add('Framework PowerShell host64Bit='+[Environment]::Is64BitProcess)
foreach($prog in @('EA.App','EA.Repository')) {
 try {
  $obj=[Runtime.InteropServices.Marshal]::GetActiveObject($prog)
  $lines.Add("$prog ROT attachment succeeded (no model opened/changed)")
  if($prog -eq 'EA.App') {$lines.Add('Existing repository: '+$obj.Repository.ConnectionString)}
  else {$lines.Add('Existing repository: '+$obj.ConnectionString)}
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($obj)
 } catch {$lines.Add("$prog ROT attachment failed: $($_.Exception.Message)")}
}
foreach($path in @('D:\Program Files (x86)\Sparx Systems\EA Trial\EA.exe','D:\Program Files\Sparx Systems\EA Trial\EA.exe')) {
 if(Test-Path -LiteralPath $path){$b=[IO.File]::ReadAllBytes($path);$off=[BitConverter]::ToInt32($b,60);$lines.Add(('{0}: machine=0x{1:X4}' -f $path,[BitConverter]::ToUInt16($b,$off+4)))}else{$lines.Add($path+': absent')}
}
$suffix=if([Environment]::Is64BitProcess){'64'}else{'32'}
$lines | Set-Content -LiteralPath "D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\audit_20261015\ea\rot_diagnostic_$suffix.txt" -Encoding utf8
$lines
