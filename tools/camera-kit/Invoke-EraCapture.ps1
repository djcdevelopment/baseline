<#
.SYNOPSIS
  Shoot a shot list in a Valheim world on this PC, with receipts (Windows PowerShell 5.1).
.DESCRIPTION
  Thin wrapper over capture_kit.py: finds Python, checks the game folder has BepInEx, and runs
  the capture. Your plugins and config are parked and restored around the run; the game is
  launched directly (never through Steam) so a queued update cannot move it under you.
.EXAMPLE
  .\Invoke-EraCapture.ps1 -World ComfyEra11 -Character MyViking -Shots .\shots\shots-era11.tsv -Out .\out\era11
.EXAMPLE
  .\Invoke-EraCapture.ps1 -World ComfyEra11 -WorldDb D:\downloads\ComfyEra11.db -WorldFwl D:\downloads\ComfyEra11.fwl `
      -Character MyViking -Shots .\shots\shots-era11.tsv -Out .\out\era11 -Width 1920 -Height 1080
#>
[CmdletBinding()]
param(
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim',
    [Parameter(Mandatory)][string]$World,
    [string]$WorldDb,
    [string]$WorldFwl,
    [Parameter(Mandatory)][string]$Character,
    [string]$CharacterFile,
    [Parameter(Mandatory)][string]$Shots,
    [Parameter(Mandatory)][string]$Out,
    [string]$Mods = (Join-Path $PSScriptRoot 'mods'),
    [int]$Width = 3840,
    [int]$Height = 2160,
    [double]$TimeoutMinutes = 0,
    [switch]$KeepWindow
)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required (https://www.python.org/downloads/); install it, then rerun.' }
if (-not (Test-Path (Join-Path $GameRoot 'valheim.exe'))) { throw "valheim.exe not found under $GameRoot" }
if (-not (Test-Path (Join-Path $GameRoot 'BepInEx\core'))) { throw "BepInEx is not installed under $GameRoot (install BepInExPack Valheim from Thunderstore)" }
$arguments = @((Join-Path $PSScriptRoot 'capture_kit.py'), '--game-root', $GameRoot, '--world', $World, '--character', $Character,
               '--shots', $Shots, '--out', $Out, '--mods', $Mods, '--width', $Width, '--height', $Height, '--timeout-minutes', $TimeoutMinutes)
if ($WorldDb) { $arguments += @('--world-db', $WorldDb) }
if ($WorldFwl) { $arguments += @('--world-fwl', $WorldFwl) }
if ($CharacterFile) { $arguments += @('--character-file', $CharacterFile) }
if ($KeepWindow) { $arguments += '--keep-window' }
& $python.Source @arguments
exit $LASTEXITCODE
