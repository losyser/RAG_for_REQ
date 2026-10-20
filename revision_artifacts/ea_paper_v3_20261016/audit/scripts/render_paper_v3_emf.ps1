Add-Type -AssemblyName System.Drawing
$base='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_paper_v3_20261016'
foreach($name in @('scope','alarm','maintenance','temperature')){
 $im=[Drawing.Image]::FromFile((Join-Path $base ('paper\paper_v3_'+$name+'.emf')))
 try{$w=1100;$h=[int]($w*$im.Height/$im.Width);$bmp=New-Object Drawing.Bitmap($w,$h);$g=[Drawing.Graphics]::FromImage($bmp)
 try{$g.Clear([Drawing.Color]::White);$g.DrawImage($im,0,0,$w,$h);$bmp.Save((Join-Path $base ('audit\emf_'+$name+'.png')),[Drawing.Imaging.ImageFormat]::Png)}finally{$g.Dispose();$bmp.Dispose()}
 }finally{$im.Dispose()}
}
