# Cierra SOLO los Expoal que arrancó esta carpeta de desarrollo.
#
# Existe porque un `Get-Process -Name expoal | Stop-Process` cerró también el
# Expoal que el usuario tenía abierto, instalado en otra ruta. El nombre del
# proceso es el mismo para el instalado y para el de desarrollo, así que el
# nombre NO sirve para distinguirlos: lo que distingue es la RUTA del ejecutable.
#
#   Ver:  powershell -NoProfile -File scripts\stop_dev_server.ps1
#   Matar: powershell -NoProfile -File scripts\stop_dev_server.ps1 -Apply
#
# Simula por defecto, igual que los demás scripts de la casa.
param(
    [switch]$Apply,
    # Solo se toca lo que vive bajo esta carpeta. Cualquier otra copia de Expoal
    # es de quien la abrió, y no es nuestra para cerrarla.
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$raiz = (Resolve-Path $Root).Path
$todos = @(Get-Process -Name Expoal, expoal -ErrorAction SilentlyContinue)

$mios = @($todos | Where-Object { $_.Path -and $_.Path.StartsWith($raiz, 'OrdinalIgnoreCase') })
$ajenos = @($todos | Where-Object { $_ -notin $mios })

if ($ajenos.Count -gt 0) {
    Write-Host "NO se tocan (no son de esta carpeta):" -ForegroundColor Yellow
    $ajenos | ForEach-Object { Write-Host "  $($_.Id)  $($_.Path)" }
}

if ($mios.Count -eq 0) {
    Write-Host "No hay ningun servidor de desarrollo abierto." -ForegroundColor Green
    exit 0
}

Write-Host "De esta carpeta ($raiz):"
$mios | ForEach-Object { Write-Host "  $($_.Id)  $($_.Path)" }

if (-not $Apply) {
    Write-Host "`nSimulacro. Vuelve a lanzarlo con -Apply para cerrarlos." -ForegroundColor Cyan
    exit 0
}

foreach ($p in $mios) {
    Stop-Process -Id $p.Id -Force -Confirm:$false
    Write-Host "cerrado: $($p.Id)"
}
