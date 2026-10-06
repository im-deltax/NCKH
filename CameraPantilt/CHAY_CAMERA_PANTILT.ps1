param(
    [string]$Port = 'COM13',
    [int]$Cam = 1,
    [string]$Iff = 'COM18',
    [string]$The = 'COM15'
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Chua co moi truong Python. Hay chay CAI_DAT.ps1 tai thu muc goc kho ma.'
}
Set-Location $PSScriptRoot
if (-not (Test-Path -LiteralPath 'canh_bao_bi_mat.json')) {
    Write-Host 'Chua co canh_bao_bi_mat.json: he thong van chay nhung KHONG gui canh bao Telegram.' -ForegroundColor Yellow
    Write-Host 'Xem README.md (muc canh bao Telegram) de cai dat.' -ForegroundColor Yellow
}
& $python -X utf8 -m pantilt.track `
    --port $Port `
    --cam $Cam `
    --che-do PRED `
    --lidar 'http://127.0.0.1:8770/stream' `
    --iff $Iff `
    --the $The `
    --canh-bao `
    --ten CHAY_HE_THONG
