# Genera assets/icon-256.png: cuadrado redondeado azul noche con flecha ámbar
# cayendo sobre una bandeja cobalto (marca Expoal). Ejecutar desde la raíz del repo.
Add-Type -AssemblyName System.Drawing

$size = 256
$bmp = New-Object System.Drawing.Bitmap($size, $size)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.Color]::Transparent)

function RoundRectPath([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = 2 * $r
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}

# Fondo: cuadrado redondeado azul noche
$bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 13, 19, 38))
$bgPath = RoundRectPath 8 8 240 240 56
$g.FillPath($bgBrush, $bgPath)

# Glow ámbar suave detrás de la flecha (elipses concéntricas con poca alpha)
for ($i = 92; $i -ge 30; $i -= 8) {
    $glowBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(7, 232, 184, 75))
    $g.FillEllipse($glowBrush, 128 - $i, 116 - $i, 2 * $i, 2 * $i)
    $glowBrush.Dispose()
}

# Bandeja: barra redondeada cobalto
$trayBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 91, 123, 214))
$trayPath = RoundRectPath 66 186 124 16 8
$g.FillPath($trayBrush, $trayPath)

# Flecha ámbar: fuste + punta
$arrowBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 232, 184, 75))
$g.FillRectangle($arrowBrush, 114, 54, 28, 62)
$pts = @(
    (New-Object System.Drawing.PointF(88, 112)),
    (New-Object System.Drawing.PointF(168, 112)),
    (New-Object System.Drawing.PointF(128, 168))
)
$g.FillPolygon($arrowBrush, $pts)

$g.Dispose()
New-Item -ItemType Directory -Force "$PSScriptRoot\..\assets" | Out-Null
$out = Join-Path (Resolve-Path "$PSScriptRoot\..\assets") "icon-256.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "Icono generado: $out"
