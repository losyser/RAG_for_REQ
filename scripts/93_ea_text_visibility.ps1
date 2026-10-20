param([Parameter(Mandatory=$true)][string]$RepositoryPath,[ValidateSet('Expand','Collapse')][string]$Mode='Expand',[string[]]$Ids=@(),[switch]$All)
$ErrorActionPreference='Stop'
if(-not $All -and $Ids.Count -eq 0){throw 'Specify -Ids business IDs or -All'}
$a=[Runtime.InteropServices.Marshal]::GetActiveObject('EA.App');$r=$a.Repository
try {
 if($r.ConnectionString -ne $RepositoryPath){throw 'The open repository does not match -RepositoryPath; no model is opened or switched.'}
 $d=$r.GetCurrentDiagram();if($null -eq $d){throw 'Open a presentation diagram first'}
 $pkg=$r.GetPackageByID($d.PackageID);if(-not $pkg.Name.StartsWith('Presentation_')){throw 'Only Presentation_ export packages are supported; existing user diagrams are protected.'}
 $nodes=@{};$children=@{};$parent=@{};$legend=@();$found=@()
 foreach($o in $d.DiagramObjects){
  $e=$r.GetElementByID($o.ElementID)
  if($e.Stereotype -ne 'requirement'){$legend+=,$o;continue}
  $id=$e.TaggedValues.GetByName('id').Value;$text=$e.TaggedValues.GetByName('text').Notes
  if($null -eq $e.TaggedValues.GetByName('original_documentation')){throw 'Missing presentation projection marker'}
  if($text -ne $e.Notes){throw ('Text and display Notes differ for '+$id+'. Re-export to refresh the projection; no canonical text is overwritten.')}
  $nodes[[int]$e.ElementID]=@{Object=$o;Element=$e;Id=$id};$children[[int]$e.ElementID]=@()
  if($All -or $Ids -contains $id){$found+=$id}
 }
 foreach($id in $Ids){if($found -notcontains $id){throw ('ID not visible in current diagram: '+$id)}}
 foreach($n in $nodes.Values){if($All -or $Ids -contains $n.Id){$n.Object.ShowNotes=($Mode -eq 'Expand');if(-not $n.Object.Update()){throw 'Visibility update failed'}}}
 foreach($l in $d.DiagramLinks){$c=$r.GetConnectorByID($l.ConnectorID);if($nodes.ContainsKey([int]$c.ClientID) -and $nodes.ContainsKey([int]$c.SupplierID)){$children[[int]$c.ClientID]+=[int]$c.SupplierID;$parent[[int]$c.SupplierID]=[int]$c.ClientID}}
 foreach($key in @($children.Keys)){$children[$key]=@($children[$key] | Sort-Object {$nodes[$_].Object.Sequence})}
 function Place([int]$id,[int]$x,[int]$y){
  $n=$nodes[$id];$o=$n.Object;$h=76+15*[Math]::Max(0,[Math]::Ceiling($n.Element.Name.Length/32)-1)
  if($o.ShowNotes){$weighted=$n.Element.Notes.Length+@($n.Element.Notes.ToCharArray() | Where-Object {[int]$_ -ge 0x2e80}).Count;$h+=32+17*[Math]::Ceiling($weighted/34)}
  $cy=$y;foreach($child in $children[$id]){$cy=(Place $child ($x+304) $cy)+24}
  $span=[Math]::Max($h,($cy-$y-24));$top=$y+[int](($span-$h)/2)
  $o.Left=[int]$x;$o.Right=[int]($x+240);$o.Top=[int](-$top);$o.Bottom=[int](-($top+$h));if(-not $o.Update()){throw 'Geometry update failed'}
  return [int]($y+$span)
 }
 $cursor=20
 foreach($id in @($nodes.Keys | Sort-Object)){if(-not $parent.ContainsKey($id)){$cursor=(Place $id 20 $cursor)+40}}
 foreach($o in $legend){$o.Top=-$cursor;$o.Bottom=-($cursor+55);$o.Update()|Out-Null}
 foreach($l in $d.DiagramLinks){$c=$r.GetConnectorByID($l.ConnectorID);$src=$nodes[[int]$c.ClientID].Object;$dst=$nodes[[int]$c.SupplierID].Object;$x=[int](($src.Right+$dst.Left)/2);$sy=[int](($src.Top+$src.Bottom)/2);$ty=[int](($dst.Top+$dst.Bottom)/2);$l.Path=('{0}:{1};{0}:{2};' -f $x,$sy,$ty);$l.LineStyle=5;$l.Update()|Out-Null}
 $r.ReloadDiagram($d.DiagramID)
 Write-Output ($Mode+': '+($found -join ', ')+'; diagram '+$d.DiagramID+' / '+$d.Name)
} finally {[void][Runtime.InteropServices.Marshal]::ReleaseComObject($r);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
