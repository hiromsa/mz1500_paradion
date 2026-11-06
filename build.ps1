# 魔境騎士パラディオン ビルドスクリプト
# 必要: z88dk (z80asm), Python 3
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

New-Item -ItemType Directory -Path out -Force | Out-Null

# PCG データ再生成 (アート更新時)
python tools\pcggen.py
if ($LASTEXITCODE -ne 0) { exit 1 }

# Side A (ローダ + PCG データ) → 0x2000
z80asm -b -mz80 -l -s -Isrc "-o=out\sidea.bin" src\sidea\loader.asm
if ($LASTEXITCODE -ne 0) { exit 1 }

# Side B (ゲーム本体) → 0x1200
z80asm -b -mz80 -l -s -Isrc "-o=out\sideb.bin" src\sideb\main.asm
if ($LASTEXITCODE -ne 0) { exit 1 }

# MZT パッケージ化
python tools\mkmzt.py --name "PARADION A" --load 2000 --exec 2000 -o out\ParadionA.mzt out\sidea.bin
python tools\mkmzt.py --name "PARADION B" --load 1200 --exec 1200 -o out\ParadionB.mzt out\sideb.bin

Write-Host '--- build done ---'
Get-ChildItem out | Select-Object Name, Length | Format-Table -AutoSize
