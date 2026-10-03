<#
.SYNOPSIS
    Rota la contraseña del usuario de MongoDB Atlas que usa spark para escribir derivados.

.DESCRIPTION
    Resuelve el hallazgo del 2026-10-02: en spark/.env, MONGO_PASSWORD (usuario de
    lectura del core) y ANALYTICS_MONGO_PASSWORD (usuario de escritura de derivados)
    eran la MISMA contraseña, así que repartir la credencial de lectura entregaba
    también la de escritura.

    Este script NO puede cambiar la contraseña en Atlas: eso requiere el plano de
    control (consola web, Atlas CLI con API key, o Admin API), y ninguno de los dos
    usuarios de base de datos tiene privilegio para cambiarla (verificado: ni
    changeOwnPassword ni changeAnyPassword).

    Lo que sí hace, después de que cambies la contraseña en Atlas:
      1. Comprueba la contraseña nueva contra Atlas ANTES de escribir nada.
      2. Respalda .env con marca de tiempo.
      3. Sustituye solo la línea ANALYTICS_MONGO_PASSWORD, sin tocar el resto.
      4. Si algo falla al escribir, restaura el respaldo.

    La contraseña se pide de forma interactiva y nunca se imprime, ni viaja por la
    línea de comandos ni por el historial.

.PARAMETER RutaEnv
    Ruta del .env a modificar. Por defecto, el de la raíz de spark.

.PARAMETER OmitirVerificacion
    No comprueba la credencial contra Atlas. Solo para pruebas sin red.

.PARAMETER NuevaPassword
    Contraseña nueva como SecureString. Si se indica, no se pide por consola (útil
    para automatizar). Si se omite, se solicita de forma interactiva.

.EXAMPLE
    # 1. En Atlas: Database Access -> el usuario de spark -> Edit -> Edit Password
    # 2. Luego:
    .\scripts\rotar_password_analytics.ps1
#>
[CmdletBinding()]
param(
    [string]$RutaEnv = (Join-Path $PSScriptRoot '..\.env'),
    [switch]$OmitirVerificacion,
    [SecureString]$NuevaPassword
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-PlainText {
    param([Parameter(Mandatory)][SecureString]$Value)
    $puntero = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($puntero)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($puntero)
    }
}

function Leer-Valor {
    param(
        # AllowEmptyString es obligatorio aqui: el .env termina en salto de linea,
        # asi que -split deja un ultimo elemento vacio, y un parametro Mandatory
        # con [string[]] rechaza el array entero por contener una cadena vacia.
        [Parameter(Mandatory)][AllowEmptyString()][string[]]$Lineas,
        [Parameter(Mandatory)][string]$Clave
    )
    $prefijo = "$Clave="
    foreach ($linea in $Lineas) {
        if ($linea.StartsWith($prefijo)) {
            return $linea.Substring($prefijo.Length).Trim()
        }
    }
    return $null
}

$RutaEnv = (Resolve-Path -LiteralPath $RutaEnv).Path
if (-not (Test-Path -LiteralPath $RutaEnv -PathType Leaf)) {
    throw "No existe el archivo .env: $RutaEnv"
}

# Se lee y se escribe como UTF-8 sin BOM, conservando los finales de línea.
$contenido = [System.IO.File]::ReadAllText($RutaEnv)
$lineas = $contenido -split "`n"

$clave = 'ANALYTICS_MONGO_PASSWORD'
$usuario = Leer-Valor -Lineas $lineas -Clave 'ANALYTICS_MONGO_USER'
$cluster = Leer-Valor -Lineas $lineas -Clave 'ANALYTICS_MONGO_CLUSTER'
$passwordActual = Leer-Valor -Lineas $lineas -Clave $clave
$passwordCore = Leer-Valor -Lineas $lineas -Clave 'MONGO_PASSWORD'

if (-not $passwordActual) {
    throw "No se encontro la linea $clave= en $RutaEnv"
}
if (-not $usuario -or -not $cluster) {
    throw "Faltan ANALYTICS_MONGO_USER o ANALYTICS_MONGO_CLUSTER en $RutaEnv"
}

Write-Output "Archivo: $RutaEnv"
Write-Output "Usuario: $usuario"

if ($NuevaPassword) {
    $textoNueva = ConvertTo-PlainText -Value $NuevaPassword
}
else {
    $nueva = Read-Host -AsSecureString -Prompt 'Nueva contrasena del usuario de ANALYTICS (no se muestra)'
    $repetir = Read-Host -AsSecureString -Prompt 'Repitela para confirmar'
    $textoNueva = ConvertTo-PlainText -Value $nueva
    $textoRepetir = ConvertTo-PlainText -Value $repetir
    if ($textoNueva -cne $textoRepetir) {
        throw 'Las contrasenas no coinciden. No se cambio nada.'
    }
}

if ($textoNueva.Length -lt 16) {
    throw "La contrasena debe tener al menos 16 caracteres (tiene $($textoNueva.Length)). No se cambio nada."
}
if ($passwordCore -and $textoNueva -ceq $passwordCore) {
    throw 'Esa es la contrasena del usuario de LECTURA del core. El objetivo de esta rotacion es justamente que sean distintas. No se cambio nada.'
}
if ($textoNueva -ceq $passwordActual) {
    throw 'Es la misma contrasena que ya estaba. No se cambio nada.'
}

if (-not $OmitirVerificacion) {
    Write-Output 'Comprobando la contrasena nueva contra Atlas antes de escribir el .env...'
    $verificador = Join-Path $PSScriptRoot 'verificar_credencial_analytics.py'
    if (-not (Test-Path -LiteralPath $verificador -PathType Leaf)) {
        throw "No se encontro el verificador: $verificador"
    }
    # La contrasena viaja por variable de entorno, nunca por argumentos de proceso.
    $env:UB_ANALYTICS_PASSWORD = $textoNueva
    try {
        & python $verificador
        if ($LASTEXITCODE -ne 0) {
            throw 'La contrasena nueva no autentico contra Atlas. No se cambio el .env.'
        }
    }
    finally {
        Remove-Item Env:UB_ANALYTICS_PASSWORD -ErrorAction SilentlyContinue
    }
}
else {
    Write-Warning 'Verificacion omitida: se escribira una contrasena sin comprobar contra Atlas.'
}

$indice = -1
for ($i = 0; $i -lt $lineas.Count; $i++) {
    if ($lineas[$i].StartsWith("$clave=")) { $indice = $i; break }
}
if ($indice -lt 0) {
    throw "No se encontro la linea $clave= para reemplazar. No se cambio nada."
}

$marca = Get-Date -Format 'yyyyMMddHHmmss'
$respaldo = "$RutaEnv.bak.$marca"
Copy-Item -LiteralPath $RutaEnv -Destination $respaldo
Write-Output "Respaldo: $respaldo"

$lineas[$indice] = "$clave=$textoNueva"

try {
    $nuevoContenido = $lineas -join "`n"
    [System.IO.File]::WriteAllText($RutaEnv, $nuevoContenido, (New-Object System.Text.UTF8Encoding($false)))
}
catch {
    Copy-Item -LiteralPath $respaldo -Destination $RutaEnv -Force
    throw "Fallo al escribir; se restauro el respaldo. Error: $($_.Exception.Message)"
}

# El respaldo solo debia existir por si fallaba la escritura.
Remove-Item -LiteralPath $respaldo -Force

Write-Output ''
Write-Output 'Contrasena rotada en el .env.'
Write-Output "Linea reemplazada: ${clave}=<oculta>"
Write-Output ''
Write-Output 'Siguientes pasos:'
Write-Output '  1. Verificar:  python scripts/verificar_credencial_analytics.py'
Write-Output '  2. Probar el exportador:  spark-submit unidades/unidad_5_visualizacion/exportar_insights_dashboard.py'
Write-Output '  3. Avisar a quien tenga otra copia del .env: su ANALYTICS_MONGO_PASSWORD quedo obsoleta.'
Write-Output '     (barber NO se ve afectado: usa su propio usuario laravel_analytics_reader.)'
