<#
.SYNOPSIS
    Run one unattended interior-capture session: plan, arm, launch, wait, collect.

.DESCRIPTION
    The interior sibling of Invoke-OrbitCapture.ps1. plan_interiors.py composes
    cameras inside each structure (hall, top room, seat, gate, courtyard) from
    scan_features.py's output, and every row carries mode=interior so the mod
    keeps the camera at eye height instead of clamping it 2 m off the ground.

    Both runners stage into the same BepInEx\config\shotplan.tsv on purpose:
    the mod reads one fixed name, and only one capture session can own the game
    at a time anyway. Whichever runner armed last is what shoots.

.EXAMPLE
    .\Invoke-InteriorCapture.ps1 -ClusterIds "439,71,407"          # pilot
    .\Invoke-InteriorCapture.ps1 -Top 25 -TimeoutMinutes 300       # full band
#>
[CmdletBinding()]
param(
    [string] $ClusterIds = '',
    [int] $Top = 25,
    [string] $World = 'ComfyEra16',
    [string] $Character = 'tugcorp',
    [int] $TimeoutMinutes = 90,
    [switch] $SkipPlan,
    [string] $ValheimRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim',
    [string] $SteamExe = 'C:\Program Files (x86)\Steam\steam.exe'
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg = Join-Path $ValheimRoot 'BepInEx\config'
$receipts = Join-Path $cfg 'shotplan-receipts.jsonl'

if (Get-Process valheim -ErrorAction SilentlyContinue) {
    throw 'Valheim is already running. Close it first -- the DLL and plan are read at startup.'
}

if (-not $SkipPlan) {
    Write-Host '[1/5] planning interior shots'
    if ($ClusterIds) {
        & python (Join-Path $here 'plan_interiors.py') --cluster-ids $ClusterIds
    } else {
        & python (Join-Path $here 'plan_interiors.py') --top $Top
    }
    if ($LASTEXITCODE -ne 0) { throw 'plan_interiors.py failed' }
}

Write-Host '[2/5] arming the mod'
Copy-Item (Join-Path $here 'out\interiorplan.tsv') (Join-Path $cfg 'shotplan.tsv') -Force
$req = @{ world = $World; character = $Character; quit_when_done = $true } | ConvertTo-Json
$req | Out-File -LiteralPath (Join-Path $cfg 'orbit-request.json') -Encoding utf8

# ComfyNetworkSense joins a server when this exists, and would fight for the menu.
$autojoin = Join-Path $cfg 'comfy-network-sense\native-autotest-request.json'
if (Test-Path -LiteralPath $autojoin) {
    Move-Item -LiteralPath $autojoin -Destination "$autojoin.disabled-for-orbit" -Force
    Write-Host '      parked the server auto-join request'
}

$before = 0
if (Test-Path -LiteralPath $receipts) {
    $before = (Get-Content -LiteralPath $receipts | Measure-Object -Line).Lines
}
$planned = (Get-Content -LiteralPath (Join-Path $cfg 'shotplan.tsv') |
            Where-Object { $_ -notmatch '^#' -and $_.Trim() }).Count
Write-Host "      $planned shot(s) planned; $before receipt(s) already on file"

Write-Host '[3/5] launching Valheim'
Start-Process -FilePath $SteamExe -ArgumentList '-applaunch', '892970', '-console'

Write-Host '[4/5] waiting (the mod quits the game when the plan is done)'
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$seen = $before
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 15
    if (Test-Path -LiteralPath $receipts) {
        $now = (Get-Content -LiteralPath $receipts | Measure-Object -Line).Lines
        if ($now -ne $seen) {
            $seen = $now
            Write-Host ("      {0}/{1} shots" -f ($seen - $before), $planned)
        }
    }
    # The mod calls Application.Quit when finished, so the process going away IS
    # the completion signal -- but only once it has actually started.
    if (-not (Get-Process valheim -ErrorAction SilentlyContinue) -and $seen -gt $before) {
        Write-Host '      game exited'
        break
    }
}

$captured = $seen - $before
if ($captured -lt $planned) {
    Write-Warning "only $captured of $planned shots were captured -- check BepInEx/LogOutput.log"
}

Write-Host '[5/5] building the gallery index'
& python (Join-Path $here 'build_valheim_index.py') --thumbs
Write-Host ''
Write-Host "done: $captured shot(s) this run"
Write-Host 'next: review receipts + thumbnails; retunes supersede automatically per (cluster, variant)'
