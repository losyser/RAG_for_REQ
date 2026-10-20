$ErrorActionPreference='Continue'
$out='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\audit_20261015\ea\readonly_diagnostic.txt'
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('Read-only EA diagnostic: '+(Get-Date -Format o))
$lines.Add('Host64Bit: '+[Environment]::Is64BitProcess)
foreach($view in @([Microsoft.Win32.RegistryView]::Registry32,[Microsoft.Win32.RegistryView]::Registry64)) {
 $base=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,$view)
 $prog=$base.OpenSubKey('EA.Repository\CLSID')
 $cls=if($prog){$prog.GetValue('')}else{'MISSING'}
 $server=$base.OpenSubKey("CLSID\$cls\LocalServer32")
 $lines.Add("$view ProgID=$cls LocalServer32=$(if($server){$server.GetValue('')}else{'MISSING'})")
 $base.Dispose()
}
$exe='D:\Program Files\Sparx Systems\EA Trial\EA.exe'
$bytes=[IO.File]::ReadAllBytes($exe);$offset=[BitConverter]::ToInt32($bytes,60)
$lines.Add(('EA PE machine: 0x{0:X4}' -f [BitConverter]::ToUInt16($bytes,$offset+4)))
$lines.Add('EA file version: '+(Get-Item -LiteralPath $exe).VersionInfo.FileVersion)
$lines.Add((Get-CimInstance Win32_Process -Filter "name = 'EA.exe'" | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | Format-List | Out-String))
$lines.Add((Get-Process EA -ErrorAction SilentlyContinue | Select-Object Id,Responding,MainWindowHandle,MainWindowTitle | Format-List | Out-String))
try {
 $active=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App')
 $lines.Add('ROT EA.App available; repository path (read only): '+$active.Repository.ConnectionString)
 [void][Runtime.InteropServices.Marshal]::ReleaseComObject($active)
} catch {$lines.Add('ROT EA.App: '+$_.Exception.Message)}
try {
 $events=Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-DistributedCOM';StartTime=(Get-Date).AddHours(-4)} -MaxEvents 100 -ErrorAction Stop | Where-Object { $_.Message -match '67F4E0FA-46A7-4255-B084-69A9433D08C3' }
 foreach($event in $events){$lines.Add("DCOM event ID=$($event.Id) Time=$($event.TimeCreated) $($event.Message)")}
} catch {$lines.Add('DCOM log unavailable: '+$_.Exception.Message)}
$lines.Add('No registry writes, registration, security changes, process termination or user model open performed.')
$lines | Set-Content -LiteralPath $out -Encoding utf8
$lines
