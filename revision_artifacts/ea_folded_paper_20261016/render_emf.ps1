Add-Type -AssemblyName System.Drawing
$base='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_folded_paper_20261016'
foreach($name in @('paper_overview','detail_b','detail_c')){
 $im=[Drawing.Image]::FromFile((Join-Path $base ($name+'.emf')))
 try{$w=1069;$h=[int]($w*$im.Height/$im.Width);$bmp=New-Object Drawing.Bitmap($w,$h);$g=[Drawing.Graphics]::FromImage($bmp)
 try{$g.Clear([Drawing.Color]::White);$g.DrawImage($im,0,0,$w,$h);$bmp.Save((Join-Path $base ($name+'_emf_render.png')),[Drawing.Imaging.ImageFormat]::Png)}finally{$g.Dispose();$bmp.Dispose()}
 }finally{$im.Dispose()}
}
