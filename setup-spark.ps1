<#
.SYNOPSIS
    Clona y configura el proyecto UrbanBlade Analytics (Spark) en Windows + WSL.

.DESCRIPTION
    Este proyecto corre dentro de WSL (Ubuntu) con un entorno Miniconda, porque PySpark
    necesita Java y un entorno Linux para funcionar de forma estable en Windows.

    Este script:
      1. Verifica que WSL2 + Ubuntu estén instalados (si no, te dice cómo instalarlos).
      2. Clona el repositorio en tu carpeta de Windows (o lo actualiza si ya existe).
      3. Dentro de WSL: instala Java (OpenJDK 11) si falta.
      4. Dentro de WSL: instala Miniconda si falta.
      5. Crea el entorno conda 'spark_env' (Python 3.11) e instala requirements.txt.
      6. Verifica que exista un archivo .env (te lo pasa el responsable del proyecto,
         este script NO genera uno falso ni sobreescribe uno existente).
      7. Imprime los comandos para correr los scripts y el dashboard.

.PARAMETER RepoUrl
    URL del repositorio a clonar.

.PARAMETER Branch
    Rama a clonar/actualizar.

.PARAMETER TargetDir
    Carpeta donde se clonará el proyecto (relativa al directorio actual).

.EXAMPLE
    .\setup-spark.ps1
#>

param(
    [string]$RepoUrl   = "https://github.com/KikeGonRam/spark.git",
    [string]$Branch    = "urbanblade-analytics",
    [string]$TargetDir = "spark",
    [string]$CondaEnv  = "spark_env"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    AVISO: $msg" -ForegroundColor Yellow }
function Fail($msg)       { Write-Host ""; Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# Convierte una ruta absoluta de Windows (C:\Users\x\...) a su equivalente en WSL (/mnt/c/Users/x/...)
function ToWslPath($winPath) {
    $p = $winPath -replace '\\', '/'
    $drive = $p.Substring(0,1).ToLower()
    $rest = $p.Substring(2)
    return "/mnt/$drive$rest"
}

# ── 1. Verificar WSL + Ubuntu ──────────────────────────────────────────────────
Write-Step "Verificando WSL2 y Ubuntu"

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Fail "WSL no está instalado. Abre PowerShell como Administrador y corre: wsl --install -d Ubuntu`nLuego reinicia tu PC y vuelve a ejecutar este script."
}

$distros = wsl.exe -l -q 2>$null
if (-not ($distros -match "Ubuntu")) {
    Fail "No se encontró la distribución 'Ubuntu' en WSL. Instálala con: wsl --install -d Ubuntu`nLuego vuelve a ejecutar este script."
}
Write-Ok "WSL + Ubuntu disponibles"

# ── 2. Clonar o actualizar el repositorio ──────────────────────────────────────
Write-Step "Preparando el código fuente"

if (Test-Path $TargetDir) {
    Write-Warn "La carpeta '$TargetDir' ya existe. Actualizando en vez de clonar de nuevo..."
    Push-Location $TargetDir
    git fetch origin
    git checkout $Branch
    git pull origin $Branch
    Pop-Location
} else {
    git clone --branch $Branch $RepoUrl $TargetDir
    Write-Ok "Repositorio clonado en .\$TargetDir"
}

$fullPath = (Resolve-Path $TargetDir).Path
$wslPath  = ToWslPath $fullPath
Write-Ok "Ruta en WSL: $wslPath"

# ── 3. Java (OpenJDK 11) dentro de WSL ──────────────────────────────────────────
Write-Step "Verificando Java (OpenJDK 11) dentro de WSL"

$javaCheck = wsl.exe -d Ubuntu -e bash -lc "command -v java && java -version 2>&1 | head -1" 2>&1
if ($LASTEXITCODE -ne 0 -or -not $javaCheck) {
    Write-Warn "Java no encontrado. Instalando OpenJDK 11 (te pedirá tu contraseña de sudo en WSL)..."
    wsl.exe -d Ubuntu -e bash -lc "sudo apt-get update -y && sudo apt-get install -y openjdk-11-jdk"
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo instalar Java. Instálalo manualmente: sudo apt install openjdk-11-jdk" }
}
Write-Ok "Java disponible en WSL"

# ── 4. Miniconda dentro de WSL ──────────────────────────────────────────────────
Write-Step "Verificando Miniconda dentro de WSL"

$condaCheck = wsl.exe -d Ubuntu -e bash -lc "test -d ~/miniconda3 && echo SI || echo NO" 2>&1
if ($condaCheck -match "NO") {
    Write-Warn "Miniconda no encontrado. Instalando en ~/miniconda3 dentro de WSL..."
    wsl.exe -d Ubuntu -e bash -lc @"
cd ~ &&
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh &&
bash miniconda.sh -b -p `$HOME/miniconda3 &&
rm miniconda.sh &&
`$HOME/miniconda3/bin/conda init bash
"@
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo instalar Miniconda. Instálalo manualmente desde https://docs.conda.io/en/latest/miniconda.html" }
    Write-Ok "Miniconda instalado (abre una nueva terminal de WSL para que tome efecto el PATH)"
} else {
    Write-Ok "Miniconda ya está instalado"
}

# ── 5. Entorno conda 'spark_env' + dependencias ────────────────────────────────
Write-Step "Configurando el entorno conda '$CondaEnv' e instalando dependencias"

$envCheck = wsl.exe -d Ubuntu -e bash -lc "source ~/miniconda3/etc/profile.d/conda.sh && conda env list | grep -qw $CondaEnv && echo SI || echo NO" 2>&1
if ($envCheck -match "NO") {
    Write-Warn "Creando el entorno '$CondaEnv' (Python 3.11)..."
    wsl.exe -d Ubuntu -e bash -lc "source ~/miniconda3/etc/profile.d/conda.sh && conda create -y -n $CondaEnv python=3.11"
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo crear el entorno conda." }
}

Write-Host "    Instalando paquetes de requirements.txt (puede tardar varios minutos)..." -ForegroundColor DarkGray
wsl.exe -d Ubuntu -e bash -lc "source ~/miniconda3/etc/profile.d/conda.sh && conda activate $CondaEnv && cd '$wslPath' && pip install -q -r requirements.txt"
if ($LASTEXITCODE -ne 0) { Fail "Falló la instalación de dependencias. Revisa requirements.txt y tu conexión a internet." }
Write-Ok "Entorno '$CondaEnv' listo con todas las dependencias"

# ── 6. Verificar archivo .env ───────────────────────────────────────────────────
Write-Step "Verificando archivo .env"

$envFile = Join-Path $fullPath ".env"
if (-not (Test-Path $envFile)) {
    Write-Host ""
    Write-Host "    No existe un archivo .env en este proyecto." -ForegroundColor Yellow
    Write-Host "    1. Pide el archivo .env al responsable del proyecto (credenciales" -ForegroundColor Yellow
    Write-Host "       reales de MongoDB Atlas, no debe subirse a git)." -ForegroundColor Yellow
    Write-Host "    2. Colócalo en: $envFile" -ForegroundColor Yellow
    Write-Host "    3. Vuelve a ejecutar este script para validar la conexión." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    Variables esperadas: MONGO_USER, MONGO_PASSWORD, MONGO_CLUSTER, MONGO_DB" -ForegroundColor DarkGray
    exit 1
}
Write-Ok "Archivo .env encontrado"

# ── 7. Prueba de conexión a MongoDB Atlas ───────────────────────────────────────
Write-Step "Probando conexión a MongoDB Atlas"
wsl.exe -d Ubuntu -e bash -lc "source ~/miniconda3/etc/profile.d/conda.sh && conda activate $CondaEnv && cd '$wslPath' && python config/mongo_spark_conexion_sinnulos.py 2>&1 | head -10"

# ── 8. Resumen final ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " Proyecto listo" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Carpeta:        .\$TargetDir"
Write-Host "  Ruta en WSL:    $wslPath"
Write-Host "  Entorno conda:  $CondaEnv"
Write-Host ""
Write-Host "  Para trabajar, abre una terminal de WSL (Ubuntu) y corre:"
Write-Host "    conda activate $CondaEnv"
Write-Host "    cd $wslPath"
Write-Host ""
Write-Host "  Comandos de ejemplo (ver unidades/COMANDOS.txt para la lista completa):"
Write-Host "    spark-submit unidades/unidad_3_supervisado/01_regresion.py"
Write-Host "    streamlit run unidades/unidad_5_visualizacion/main_dashboard.py"
Write-Host "========================================================" -ForegroundColor Green
