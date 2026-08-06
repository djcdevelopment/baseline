<#
.SYNOPSIS
    Run one unattended orbit-capture session: plan, arm, launch, wait, collect.

.DESCRIPTION
    The camera mod cannot be driven by console commands, because nothing in this
    repository can type into Valheim's console. It arms itself from a file instead:
    orbit-request.json tells it which world and character to open, and shotplan.tsv
    tells it where to point. This script writes both, starts the game, and waits.

    Deliberately NOT using fieldlab/scripts/Invoke-NativeValheimClient.ps1: that
    harness writes a request that makes ComfyNetworkSense auto-join a *server*, which
    races this mod for the main menu. It also has no path for loading a local world.
    Single-player is both simpler and faster here -- ZDOs stream off disk with no
    network in the way.

.EXAMPLE
    .\Invoke-OrbitCapture.ps1 -Top 3
    .\Invoke-OrbitCapture.ps1 -Top 40 -TimeoutMinutes 240
#>
[CmdletBinding()]
param(
    [int] $Top = 3,
    [ValidateSet('all', 'in-world', 'outland')]
    [string] $Region = 'in-world',
    [string] $World = 'ComfyEra16',
    [string] $Character = 'tugcorp',
    [double] $MaxDistance = 120,
    [double] $Elevation = 40,
    [int] $TimeoutMinutes = 60,
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
    Write-Host '[1/5] planning shots'
    & python (Join-Path $here 'plan_shots.py') --top $Top --region $Region `
        --max-distance $MaxDistance --elevation $Elevation
    if ($LASTEXITCODE -ne 0) { throw 'plan_shots.py failed' }
}

Write-Host '[2/5] arming the mod'
Copy-Item (Join-Path $here 'out\shotplan.tsv') (Join-Path $cfg 'shotplan.tsv') -Force
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
Write-Host 'next: name_structures.py for any new structures, then deploy'
