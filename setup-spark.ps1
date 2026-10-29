<#
.SYNOPSIS
Prepara un entorno virtual del checkout actual sin clonar, migrar o desplegar servicios.
#>
param(
    [string]$PythonExe = "python",
    [ValidateSet("ci", "dashboard", "full")][string]$Profile = "ci",
    [switch]$Install
)
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& $PythonExe -c "import sys; assert (3, 11) <= sys.version_info < (3, 13), 'Usa Python 3.11 o 3.12; runtime verificado 3.12.'"
if ($LASTEXITCODE -ne 0) { throw "Selecciona Python compatible con -PythonExe. No se modificó el entorno." }
$requirements = switch ($Profile) {
    "ci" { "requirements-ci.txt" }
    "dashboard" { "requirements-dashboard.txt" }
    "full" { "requirements.txt" }
}
if (-not $Install) {
    Write-Host "Checkout: $projectRoot"
    Write-Host "Perfil: $Profile. Usa -Install para crear .venv e instalar sus dependencias."
    Write-Host "No se ejecutan pruebas, conexiones a bases, clonado ni despliegues automáticamente."
    exit 0
}
& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "No se pudo preparar el entorno virtual." }
$venvPython = Join-Path $projectRoot ".venv/Scripts/python.exe"
& $venvPython -m pip install --index-url https://pypi.org/simple -r $requirements
if ($LASTEXITCODE -ne 0) { throw "Falló la instalación; no se ejecutaron operaciones de datos." }
Write-Host "Entorno preparado. Consulta docs/desarrollo.md para validar y ejecutar."
