# Script para reorganizar el proyecto WayGPS
# Estructura objetivo:
# wayGps/
# â”œâ”€â”€ app/ (Backend Django - queda igual)
# â”œâ”€â”€ Frontend/ (contenido directo de react-frontend)
# â”œâ”€â”€ frontend-vanilla/ (archivos vanilla directos)
# â”œâ”€â”€ docs/
# â””â”€â”€ BAT/

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REORGANIZACIÃ“N DEL PROYECTO WAYGPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Detectar directorio base (wayGps/)
# Si el script estÃ¡ en app/, el base es el padre
# Si el script estÃ¡ en wayGps/, el base es el mismo
if ($PSScriptRoot -like "*\app") {
    $basePath = Split-Path -Parent $PSScriptRoot
} else {
    $basePath = $PSScriptRoot
}

# Si no encontramos app/ en el padre, buscar en el directorio actual
if (-not (Test-Path "$basePath\app")) {
    Write-Host "âš  No se encontrÃ³ la carpeta 'app'. Buscando en el directorio actual..." -ForegroundColor Yellow
    $basePath = Get-Location
    if (-not (Test-Path "$basePath\app")) {
        Write-Host "âŒ ERROR: No se encontrÃ³ la carpeta 'app'." -ForegroundColor Red
        Write-Host "   Ejecuta este script desde wayGps/ o desde app/" -ForegroundColor Yellow
        exit 1
    }
}

$appPath = $basePath + "\app"
$frontendPath = $basePath + "\Frontend"
$frontendVanillaPath = $basePath + "\frontend-vanilla"
$docsPath = $basePath + "\docs"
$batPath = $basePath + "\BAT"

# Cambiar al directorio base
Set-Location $basePath

Write-Host "Directorio base: $basePath" -ForegroundColor Yellow
Write-Host "Directorio app: $appPath" -ForegroundColor Yellow
Write-Host ""

# Crear carpetas necesarias
Write-Host "1. Creando estructura de carpetas..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $frontendPath | Out-Null
New-Item -ItemType Directory -Force -Path $frontendVanillaPath | Out-Null
New-Item -ItemType Directory -Force -Path $docsPath | Out-Null
New-Item -ItemType Directory -Force -Path $batPath | Out-Null
Write-Host "   âœ“ Carpetas creadas" -ForegroundColor Green
Write-Host ""

# 2. Mover contenido de react-frontend DIRECTAMENTE a Frontend/ (SIN crear subcarpeta react-frontend)
# Ejemplo: app/react-frontend/src/ â†’ Frontend/src/ (NO Frontend/react-frontend/src/)
Write-Host "2. Moviendo contenido de react-frontend directamente a Frontend/..." -ForegroundColor Green
if (Test-Path "$appPath\react-frontend") {
    # Si Frontend/ ya existe y tiene contenido, eliminarlo primero
    if (Test-Path "$frontendPath" -and (Get-ChildItem -Path $frontendPath -Force | Measure-Object).Count -gt 0) {
        Write-Host "   âš  Frontend/ ya existe con contenido, eliminando..." -ForegroundColor Yellow
        Remove-Item "$frontendPath\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Mover TODOS los archivos y carpetas del contenido de react-frontend directamente a Frontend/
    # Esto mueve: src/, public/, package.json, vite.config.js, etc. directamente a Frontend/
    # NO crea una subcarpeta react-frontend dentro de Frontend/
    Get-ChildItem -Path "$appPath\react-frontend" -Force | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $frontendPath -Force
    }
    
    # Eliminar la carpeta react-frontend vacÃ­a despuÃ©s de mover todo su contenido
    if (Test-Path "$appPath\react-frontend") {
        Remove-Item "$appPath\react-frontend" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "   âœ“ Contenido movido directamente a Frontend/ (src/, package.json, vite.config.js, etc.)" -ForegroundColor Green
} else {
    Write-Host "   âš  react-frontend no encontrado en app/" -ForegroundColor Yellow
}
Write-Host ""

# 3. Mover archivos vanilla a frontend-vanilla/
Write-Host "3. Moviendo archivos vanilla a frontend-vanilla/..." -ForegroundColor Green
$vanillaFiles = @("index.html", "app.js", "config.js", "styles.css", "demoSTT.html")
foreach ($file in $vanillaFiles) {
    if (Test-Path "$appPath\$file") {
        Move-Item -Path "$appPath\$file" -Destination "$frontendVanillaPath\$file" -Force
        Write-Host "   âœ“ $file movido a frontend-vanilla/" -ForegroundColor Green
    }
}

# NOTA: Los templates/ y static/ de app/ son de Django y deben quedarse ahÃ­
# Solo movemos archivos vanilla del raÃ­z de app/
Write-Host "   âœ“ Archivos vanilla movidos" -ForegroundColor Green
Write-Host "   â„¹ Templates y static de Django quedan en app/ (no se mueven)" -ForegroundColor Cyan
Write-Host ""

# 4. Mover archivos .md y .txt a docs/
Write-Host "4. Moviendo documentaciÃ³n (.md y .txt)..." -ForegroundColor Green
$excludeFiles = @("REORGANIZAR_PROYECTO.ps1", "INSTRUCCIONES_POST_REORGANIZACION.md")
$mdFiles = Get-ChildItem -Path $appPath -Filter "*.md" -File -ErrorAction SilentlyContinue | Where-Object { $excludeFiles -notcontains $_.Name }
$txtFiles = Get-ChildItem -Path $appPath -Filter "*.txt" -File -ErrorAction SilentlyContinue | Where-Object { $excludeFiles -notcontains $_.Name }

foreach ($file in $mdFiles) {
    $dest = "$docsPath\$($file.Name)"
    if (Test-Path $dest) {
        Write-Host "   âš  $($file.Name) ya existe en docs/, renombrando..." -ForegroundColor Yellow
        $dest = "$docsPath\$($file.BaseName)_$(Get-Date -Format 'yyyyMMdd_HHmmss')$($file.Extension)"
    }
    Move-Item -Path $file.FullName -Destination $dest -Force
    Write-Host "   âœ“ $($file.Name) movido a docs/" -ForegroundColor Green
}

foreach ($file in $txtFiles) {
    $dest = "$docsPath\$($file.Name)"
    if (Test-Path $dest) {
        Write-Host "   âš  $($file.Name) ya existe en docs/, renombrando..." -ForegroundColor Yellow
        $dest = "$docsPath\$($file.BaseName)_$(Get-Date -Format 'yyyyMMdd_HHmmss')$($file.Extension)"
    }
    Move-Item -Path $file.FullName -Destination $dest -Force
    Write-Host "   âœ“ $($file.Name) movido a docs/" -ForegroundColor Green
}
Write-Host ""

# 5. Mover archivos .bat a BAT/
Write-Host "5. Moviendo scripts (.bat)..." -ForegroundColor Green
$batFiles = Get-ChildItem -Path $appPath -Filter "*.bat" -File -ErrorAction SilentlyContinue

foreach ($file in $batFiles) {
    $dest = "$batPath\$($file.Name)"
    if (Test-Path $dest) {
        Write-Host "   âš  $($file.Name) ya existe en BAT/, renombrando..." -ForegroundColor Yellow
        $dest = "$batPath\$($file.BaseName)_$(Get-Date -Format 'yyyyMMdd_HHmmss')$($file.Extension)"
    }
    Move-Item -Path $file.FullName -Destination $dest -Force
    Write-Host "   âœ“ $($file.Name) movido a BAT/" -ForegroundColor Green
}
Write-Host ""

# 6. Mover archivos .ps1 relacionados con activaciÃ³n (si estÃ¡n en raÃ­z de app)
Write-Host "6. Moviendo scripts PowerShell relacionados (.ps1)..." -ForegroundColor Green
$excludePs1 = @("REORGANIZAR_PROYECTO.ps1")
$ps1Files = Get-ChildItem -Path $appPath -Filter "*.ps1" -File -ErrorAction SilentlyContinue | Where-Object { 
    ($_.Name -like "*activar*" -or $_.Name -like "*analizar*") -and ($excludePs1 -notcontains $_.Name)
}

foreach ($file in $ps1Files) {
    $dest = "$batPath\$($file.Name)"
    if (Test-Path $dest) {
        Write-Host "   âš  $($file.Name) ya existe en BAT/, renombrando..." -ForegroundColor Yellow
        $dest = "$batPath\$($file.BaseName)_$(Get-Date -Format 'yyyyMMdd_HHmmss')$($file.Extension)"
    }
    Move-Item -Path $file.FullName -Destination $dest -Force
    Write-Host "   âœ“ $($file.Name) movido a BAT/" -ForegroundColor Green
}
Write-Host ""

# 7. Copiar instrucciones a docs/
Write-Host "7. Copiando instrucciones..." -ForegroundColor Green
if (Test-Path "$basePath\INSTRUCCIONES_POST_REORGANIZACION.md") {
    Copy-Item -Path "$basePath\INSTRUCCIONES_POST_REORGANIZACION.md" -Destination "$docsPath\INSTRUCCIONES_POST_REORGANIZACION.md" -Force
    Write-Host "   âœ“ Instrucciones copiadas a docs/" -ForegroundColor Green
}
Write-Host ""

# 8. Resumen
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REORGANIZACIÃ“N COMPLETADA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nueva estructura:" -ForegroundColor Yellow
Write-Host "  wayGps/" -ForegroundColor White
Write-Host "  â”œâ”€â”€ app/                    (Backend Django - sin cambios)" -ForegroundColor White
Write-Host "  â”œâ”€â”€ Frontend/               (Frontend React - contenido directo)" -ForegroundColor White
Write-Host "  â”‚   â”œâ”€â”€ src/" -ForegroundColor White
Write-Host "  â”‚   â”‚   â””â”€â”€ pages/" -ForegroundColor White
Write-Host "  â”‚   â”‚       â”œâ”€â”€ Moviles.jsx" -ForegroundColor White
Write-Host "  â”‚   â”‚       â”œâ”€â”€ Equipos.jsx" -ForegroundColor White
Write-Host "  â”‚   â”‚       â”œâ”€â”€ Sofia.jsx" -ForegroundColor White
Write-Host "  â”‚   â”‚       â”œâ”€â”€ Recorridos.jsx" -ForegroundColor White
Write-Host "  â”‚   â”‚       â””â”€â”€ ..." -ForegroundColor White
Write-Host "  â”‚   â”œâ”€â”€ package.json" -ForegroundColor White
Write-Host "  â”‚   â””â”€â”€ vite.config.js" -ForegroundColor White
Write-Host "  â”œâ”€â”€ frontend-vanilla/       (Frontend Vanilla HTML/JS/CSS)" -ForegroundColor White
Write-Host "  â”‚   â”œâ”€â”€ index.html" -ForegroundColor White
Write-Host "  â”‚   â”œâ”€â”€ app.js" -ForegroundColor White
Write-Host "  â”‚   â””â”€â”€ ..." -ForegroundColor White
Write-Host "  â”œâ”€â”€ docs/                   (DocumentaciÃ³n .md y .txt)" -ForegroundColor White
Write-Host "  â””â”€â”€ BAT/                    (Scripts .bat y .ps1)" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor Red
Write-Host "  - Frontend/ contiene DIRECTAMENTE src/, package.json, vite.config.js, etc." -ForegroundColor Yellow
Write-Host "    (NO existe Frontend/react-frontend/, el contenido estÃ¡ en la raÃ­z de Frontend/)" -ForegroundColor Yellow
Write-Host "  - frontend-vanilla/ contiene DIRECTAMENTE index.html, app.js, config.js, etc." -ForegroundColor Yellow
Write-Host "    (NO existe frontend-vanilla/vanilla/, los archivos estÃ¡n en la raÃ­z)" -ForegroundColor Yellow
Write-Host "  - Ejemplo: Frontend/src/pages/Moviles.jsx (NO Frontend/react-frontend/src/...)" -ForegroundColor Yellow
Write-Host "  - Verifica que las rutas en React apunten correctamente" -ForegroundColor Yellow
Write-Host "  - Verifica que las rutas en Vanilla funcionen correctamente" -ForegroundColor Yellow
Write-Host "  - Los templates y static de Django quedan en app/templates y app/static" -ForegroundColor Yellow
Write-Host ""

