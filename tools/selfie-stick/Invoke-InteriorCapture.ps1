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

    Era isolation is the same contract the orbit runner keeps: -Clusters,
    -Features, -PlanOut, -GalleryDest and -RunManifest all point into one era's
    namespace, and the gallery is rebuilt from only the runs that era recorded.
    Cluster ids come from union-find ordering and are NOT stable across eras, so
    joining an Era 17 capture to Era 16 clusters silently mislabels every frame.

.EXAMPLE
    .\Invoke-InteriorCapture.ps1 -ClusterIds "439,71,407"          # pilot
    .\Invoke-InteriorCapture.ps1 -Top 25 -TimeoutMinutes 300       # full band
#>
[CmdletBinding()]
param(
    [string] $ClusterIds = '',
    [int] $Top = 25,
    [string] $Vantages = '',
    [ValidateSet('all', 'in-world', 'outland')]
    [string] $Region = 'in-world',
    [string] $World = 'ComfyEra16',
    [string] $Character = 'tugcorp',
    [int] $TimeoutMinutes = 90,
    [switch] $SkipPlan,
    [string] $Features = '',
    [string] $Clusters = '',
    [string] $PlanOut = '',
    [string] $GalleryDest = '',
    [string] $RunManifest = '',
    [int] $DisplayIndex = 0,
    [int] $CaptureWidth = 3840,
    [int] $CaptureHeight = 2160,
    [string] $ValheimRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim',
    [string] $SteamExe = 'C:\Program Files (x86)\Steam\steam.exe'
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $PlanOut) { $PlanOut = Join-Path (Join-Path $here 'out') 'interiorplan.json' }
$eraOut = Split-Path -Parent $PlanOut
if (-not $Clusters) { $Clusters = Join-Path $eraOut 'clusters.json' }
if (-not $Features) { $Features = Join-Path $eraOut 'features.json' }
if (-not $GalleryDest) { $GalleryDest = Join-Path $eraOut 'gallery' }
if (-not $RunManifest) { $RunManifest = Join-Path $eraOut 'capture-runs.json' }
$names = Join-Path $eraOut 'cluster-names.json'
$cfg = Join-Path $ValheimRoot 'BepInEx\config'
$receipts = Join-Path $cfg 'shotplan-receipts.jsonl'
$logOutput = Join-Path $ValheimRoot 'BepInEx\LogOutput.log'
$networkSenseDll = Join-Path $ValheimRoot 'BepInEx\plugins\ComfyNetworkSense.dll'
$networkSenseConfig = Join-Path $cfg 'djcdevelopment.valheim.comfynetworksense.cfg'

if (Get-Process valheim -ErrorAction SilentlyContinue) {
    throw 'Valheim is already running. Close it first -- the DLL and plan are read at startup.'
}

# Same preflight as the orbit runner, and for the same reason: this client is
# also the single-player host, so a missing portal-connection cache pins its
# main thread while an era-scale portal network is matched.
if (-not (Test-Path -LiteralPath $networkSenseDll)) {
    throw "ComfyNetworkSense is missing: $networkSenseDll"
}
$networkSenseVersionText = (Get-Item -LiteralPath $networkSenseDll).VersionInfo.FileVersion
try { $networkSenseVersion = [version] $networkSenseVersionText } catch {
    throw "Cannot parse ComfyNetworkSense version '$networkSenseVersionText'."
}
if ($networkSenseVersion -lt [version] '0.4.8') {
    throw "ComfyNetworkSense $networkSenseVersion lacks the portal connection cache (need 0.4.8+)."
}
if (-not (Test-Path -LiteralPath $networkSenseConfig)) {
    throw "ComfyNetworkSense config is missing: $networkSenseConfig"
}
$networkSenseConfigBytes = [IO.File]::ReadAllBytes($networkSenseConfig)
$networkSenseConfigText = [Text.Encoding]::UTF8.GetString($networkSenseConfigBytes)
if ($networkSenseConfigText -notmatch '(?m)^\s*portalConnectionCacheEnabled\s*=\s*true\s*$') {
    throw 'ComfyNetworkSense portalConnectionCacheEnabled must be true for interior capture.'
}
Write-Host "      portal cache preflight passed (ComfyNetworkSense $networkSenseVersion)"

if (-not $SkipPlan) {
    Write-Host '[1/5] planning interior shots'
    $planArgs = @((Join-Path $here 'plan_interiors.py'),
                  '--features', $Features, '--clusters', $Clusters,
                  '--names', $names, '--out', $PlanOut, '--region', $Region)
    if ($ClusterIds) { $planArgs += @('--cluster-ids', $ClusterIds) }
    else { $planArgs += @('--top', "$Top") }
    if ($Vantages) { $planArgs += @('--vantages', $Vantages) }
    & python $planArgs
    if ($LASTEXITCODE -ne 0) { throw 'plan_interiors.py failed' }
}

Write-Host '[2/5] arming the mod'
$planTsv = [IO.Path]::ChangeExtension($PlanOut, '.tsv')
Copy-Item $planTsv (Join-Path $cfg 'shotplan.tsv') -Force
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
$monitorNumber = $DisplayIndex + 1
$quietNetworkSenseConfig = [regex]::Replace(
    $networkSenseConfigText,
    '(?m)^(\s*showHudOnStart\s*=\s*)true\s*$',
    '${1}false')
try {
    # The NetworkSense IMGUI panel is useful interactively but should not be
    # burned into public gallery frames. Restore the operator's exact bytes
    # when the capture process ends, including on timeout or failure.
    [IO.File]::WriteAllText(
        $networkSenseConfig,
        $quietNetworkSenseConfig,
        [Text.UTF8Encoding]::new($false))
    $launchStartedAtUtc = [DateTime]::UtcNow
    Start-Process -FilePath $SteamExe -ArgumentList '-applaunch', '892970', '-console', `
        '-screen-fullscreen', '0', '-screen-width', "$CaptureWidth", '-screen-height', "$CaptureHeight", `
        '-monitor', "$monitorNumber"
    Write-Host "      requested display $DisplayIndex at ${CaptureWidth}x${CaptureHeight}"

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
} finally {
    [IO.File]::WriteAllBytes($networkSenseConfig, $networkSenseConfigBytes)
}

if (-not (Test-Path -LiteralPath $logOutput) -or
    (Get-Item -LiteralPath $logOutput).LastWriteTimeUtc -lt $launchStartedAtUtc -or
    -not (Select-String -LiteralPath $logOutput -SimpleMatch 'Portal connection cache enabled;' -Quiet)) {
    throw 'Portal-cache activation was not observed in the current BepInEx/LogOutput.log.'
}
Write-Host '      portal cache activation verified'

$captured = $seen - $before
if ($captured -lt $planned) {
    Write-Warning "only $captured of $planned shots were captured -- check BepInEx/LogOutput.log"
}

Write-Host '[5/5] building the gallery index'
$runIds = @()
if (Test-Path -LiteralPath $RunManifest) {
    try {
        $decodedRunIds = Get-Content -LiteralPath $RunManifest -Raw | ConvertFrom-Json
        foreach ($decodedRunId in $decodedRunIds) {
            $value = [string] $decodedRunId
            if ($value -and $value -ne 'System.Object[]') { $runIds += $value }
        }
    } catch { $runIds = @() }
}
if (Test-Path -LiteralPath $receipts) {
    $newLines = @(Get-Content -LiteralPath $receipts | Select-Object -Skip $before)
    foreach ($line in $newLines) {
        try {
            $row = $line | ConvertFrom-Json
            if ($row.run -and $runIds -notcontains [string]$row.run) { $runIds += [string]$row.run }
        } catch {}
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RunManifest) | Out-Null
$runIds | ConvertTo-Json | Set-Content -LiteralPath $RunManifest -Encoding utf8
$indexArgs = @((Join-Path $here 'build_valheim_index.py'), '--thumbs', '--large',
               '--clusters', $Clusters, '--dest', $GalleryDest, '--world', $World,
               '--names', $names,
               '--depth', (Join-Path $eraOut 'depth.json'),
               '--aesthetic', (Join-Path $eraOut 'aesthetic.json'),
               '--crop-right-ui-px', '120',
               '--derived', (Join-Path $eraOut 'derived-frames.json'))
foreach ($runId in $runIds) { $indexArgs += @('--run', $runId) }
& python $indexArgs
if ($LASTEXITCODE -ne 0) { throw 'build_valheim_index.py failed' }
Write-Host ''
Write-Host "done: $captured shot(s) this run"
Write-Host "runs: $($runIds -join ', ')"
Write-Host 'next: review receipts + thumbnails; retunes supersede automatically per (cluster, variant)'
