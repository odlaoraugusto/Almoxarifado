<#
Backup diario do banco Postgres do Almoxarifado.

Le usuario/senha/host/porta/banco direto de backend\.env (DATABASE_URL)
- nao duplica a senha num segundo lugar, nem fica em texto plano dentro
deste script.

NOTA DE CODIFICACAO: este arquivo e' escrito só com caracteres ASCII de
proposito (sem acento/travessao) porque o Windows PowerShell 5.1, sem um
BOM UTF-8 no arquivo, le .ps1 usando a codepage do sistema em vez de
UTF-8 - qualquer acentuacao quebra o parsing com um erro de sintaxe
confuso ("Token inesperado"), sem indicar a causa real. Testado e
confirmado neste projeto antes de finalizar o script.

Agendar via Task Scheduler (ver docs/GUIA_IMPLANTACAO_SERVIDOR.md,
secao 6). Rodar manualmente pra testar:

    powershell -ExecutionPolicy Bypass -File backup_diario.ps1
#>

$ErrorActionPreference = "Stop"

# ---- ajustar estes dois caminhos pra realidade desta maquina ----
$pgDumpExe = "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
$backupDir = "D:\Backups\Almoxarifado"   # disco/pasta SEPARADA do servidor principal
# -------------------------------------------------------------------

$envPath = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envPath)) {
    throw "Arquivo .env nao encontrado em $envPath - rode a partir de backend\scripts\, ou ajuste o caminho."
}

$linhaUrl = Get-Content $envPath | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
if (-not $linhaUrl) {
    throw "DATABASE_URL nao encontrada em $envPath"
}

# Formato esperado: postgresql+psycopg2://usuario:senha@host:porta/banco
# Grupo da senha e' guloso (.+) de proposito - a senha pode conter "@";
# so o ULTIMO "@" antes de host:porta/banco e' o separador de verdade.
if ($linhaUrl -notmatch 'postgresql\+psycopg2://([^:]+):(.+)@([^@:/]+):(\d+)/(.+)$') {
    throw "Nao consegui interpretar DATABASE_URL (formato inesperado): $linhaUrl"
}
$dbUser = $Matches[1]
$dbSenha = $Matches[2]
$dbHost = $Matches[3]
$dbPorta = $Matches[4]
$dbNome = $Matches[5].Trim()

if (-not (Test-Path $pgDumpExe)) {
    throw "pg_dump.exe nao encontrado em $pgDumpExe - ajuste a variavel `$pgDumpExe no topo deste script."
}

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$dataHoje = Get-Date -Format "yyyy-MM-dd"
$arquivoSaida = Join-Path $backupDir "almoxarifado_$dataHoje.dump"

$env:PGPASSWORD = $dbSenha
try {
    & $pgDumpExe -Fc -h $dbHost -p $dbPorta -U $dbUser -d $dbNome -f $arquivoSaida
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump terminou com codigo de erro $LASTEXITCODE"
    }
    Write-Output "Backup criado: $arquivoSaida"
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# Mantem so os ultimos 30 dias - ajustar se quiser reter mais tempo.
Get-ChildItem $backupDir -Filter "almoxarifado_*.dump" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

Write-Output "Backups com mais de 30 dias removidos (se houver)."
