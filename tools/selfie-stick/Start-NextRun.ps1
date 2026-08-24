<#
.SYNOPSIS
    Show what capture runs are queued, and fire one when Valheim is free.

.DESCRIPTION
    The era arguments are the easy thing to get wrong -- point a run at the wrong
    clusters.json and every frame joins to another era's cluster ids, which is the
    mislabelling era isolation exists to prevent and which does not announce itself.
    This holds them, so starting the next run is a plan name rather than nine paths.

    Run it with no arguments to see the queue. Run it with -Run <name> to go.

    After the capture it does the whole tail: aesthetic scores, depth metrics,
    names for any new structures, and the gallery rebuild. Those are per-frame
    measurements, so a failure in one of them costs nothing that a rerun cannot
    recover -- the photographs are already on disk by then, and the script says so
    rather than stopping.

    It does NOT publish. That is a separate, deliberate act:
        .\Publish-GalleryToAM4.ps1 -GalleryPath .\out\era17\gallery -EraSlug era17

.EXAMPLE
    .\Start-NextRun.ps1                 # what is queued?
    .\Start-NextRun.ps1 -Run sky        # the 70-frame sky probe, ~15 min
    .\Start-NextRun.ps1 -Run creators   # 48 unrepresented builders, ~50 min
#>
[CmdletBinding()]
param(
    [string] $Run = '',
    [int] $TimeoutMinutes = 180,
    [switch] $SkipFollowUp
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$era = Join-Path $here 'out\era17'
$perception = 'C:\work\omen-perception\venv\Scripts\python.exe'

# One row per queued run. Adding the next one is a row, not a new script.
$queue = @(
    [ordered]@{
        name    = 'sky'
        plan    = 'sky-probe'
        what    = '14 sky platforms at dawn, 74 deg (16 off vertical), aimed at the ridge'
        why     = 'daytime side-on frames measure luma 207-233 against a gallery median ' +
                  'of 96 and are all fog-flagged. Overhead at 65 deg came back 100% ' +
                  'occluded and side-on at 22 deg 76%, because the default aim point is ' +
                  'the middle of the bounding box, which is INSIDE the build -- a steep ' +
                  'sight line hits the roof first. Aiming at the ridge fixed it: 0% occluded'
    },
    [ordered]@{
        name    = 'creators'
        plan    = 'creators-1'
        what    = '48 builds by 48 builders with nothing in the gallery yet'
        why     = 'representation moves 163 -> 211 of 296 creators. These sit at old ' +
                  'ranks 967-1294, so a score-ordered sweep would never reach them'
    }
)

function Get-PlanFacts([string] $plan) {
    $tsv = Join-Path $era "$plan.tsv"
    if (-not (Test-Path -LiteralPath $tsv)) { return $null }
    $rows = @(Get-Content -LiteralPath $tsv | Where-Object { $_ -notmatch '^#' -and $_.Trim() })
    $ids = @($rows | ForEach-Object { ($_ -split "`t")[0] } | Sort-Object -Unique)
    # ~11.5 s/frame measured across the ten Era 17 runs, plus the world load
    [pscustomobject]@{
        Tsv = $tsv; Shots = $rows.Count; Structures = $ids.Count
        Minutes = [math]::Round(($rows.Count * 11.5) / 60 + 6)
    }
}

if (-not $Run) {
    Write-Host ''
    Write-Host '  QUEUED CAPTURE RUNS' -ForegroundColor Cyan
    Write-Host ''
    foreach ($q in $queue) {
        $f = Get-PlanFacts $q.plan
        if (-not $f) {
            Write-Host ("  {0,-10} plan missing: {1}.tsv" -f $q.name, $q.plan) -ForegroundColor DarkYellow
            continue
        }
        Write-Host ("  {0,-10} {1} shots over {2} structures, about {3} min" -f
                    $q.name, $f.Shots, $f.Structures, $f.Minutes) -ForegroundColor White
        Write-Host ("             {0}" -f $q.what) -ForegroundColor Gray
        Write-Host ("             {0}" -f $q.why) -ForegroundColor DarkGray
        Write-Host ("             .\Start-NextRun.ps1 -Run {0}" -f $q.name) -ForegroundColor DarkCyan
        Write-Host ''
    }
    if (Get-Process valheim -ErrorAction SilentlyContinue) {
        Write-Host '  Valheim is running right now -- close it before starting a run.' -ForegroundColor Yellow
    } else {
        Write-Host '  Valheim is not running. Good to go.' -ForegroundColor Green
    }
    Write-Host ''
    Write-Host '  Nothing here publishes. When the gallery looks right:' -ForegroundColor DarkGray
    Write-Host '    .\Publish-GalleryToAM4.ps1 -GalleryPath .\out\era17\gallery -EraSlug era17' -ForegroundColor DarkGray
    Write-Host ''
    return
}

$chosen = $queue | Where-Object { $_.name -eq $Run }
if (-not $chosen) {
    throw "no queued run called '$Run'. Run with no arguments to see the queue."
}
$facts = Get-PlanFacts $chosen.plan
if (-not $facts) { throw "plan $($chosen.plan).tsv is missing from $era" }
if (Get-Process valheim -ErrorAction SilentlyContinue) {
    throw 'Valheim is running. Close it first -- the plan and the DLL are read at startup.'
}

Write-Host ("starting '{0}': {1} shots over {2} structures, about {3} min" -f
            $chosen.name, $facts.Shots, $facts.Structures, $facts.Minutes) -ForegroundColor Cyan

& (Join-Path $here 'Invoke-OrbitCapture.ps1') -SkipPlan `
    -World 'ComfyEra17' -Character 'tugcorp' `
    -Clusters (Join-Path $era 'clusters.json') `
    -PlanOut (Join-Path $era "$($chosen.plan).json") `
    -GalleryDest (Join-Path $era 'gallery') `
    -RunManifest (Join-Path $era 'capture-runs.json') `
    -TimeoutMinutes $TimeoutMinutes

if ($SkipFollowUp) { return }

# Everything past here is measurement over frames that are already safely on disk.
# A failure is worth reporting and not worth stopping for.
Write-Host ''
Write-Host 'scoring the new frames' -ForegroundColor Cyan
$steps = @(
    @{ label = 'aesthetic'; exe = $perception
       args = @((Join-Path $here 'score_images.py'),
                '--images', (Join-Path $era 'gallery\large'),
                '--out', (Join-Path $era 'aesthetic.json')) },
    @{ label = 'depth'; exe = $perception
       args = @((Join-Path $here 'depth_layers.py'),
                '--images', (Join-Path $era 'gallery\large'),
                '--out', (Join-Path $era 'depth.json')) },
    @{ label = 'names'; exe = 'python'
       args = @((Join-Path $here 'name_structures.py'),
                '--index', (Join-Path $era 'gallery\index.json'),
                '--thumbs', (Join-Path $era 'gallery\large'),
                '--out', $era) }
)
foreach ($step in $steps) {
    try {
        & $step.exe $step.args
        if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
    } catch {
        Write-Warning "$($step.label) did not finish ($_). The frames are on disk; rerun it."
    }
}

Write-Host ''
Write-Host 'folding the scores and names into the gallery' -ForegroundColor Cyan
$runIds = @(Get-Content -LiteralPath (Join-Path $era 'capture-runs.json') -Raw | ConvertFrom-Json)
$indexArgs = @((Join-Path $here 'build_valheim_index.py'), '--thumbs', '--large',
               '--clusters', (Join-Path $era 'clusters.json'),
               '--dest', (Join-Path $era 'gallery'), '--world', 'ComfyEra17',
               '--names', (Join-Path $era 'cluster-names.json'),
               '--depth', (Join-Path $era 'depth.json'),
               '--aesthetic', (Join-Path $era 'aesthetic.json'),
               '--crop-right-ui-px', '120',
               '--crop-top-ui-px', '128',
               '--derived', (Join-Path $era 'derived-frames.json'))
foreach ($id in $runIds) { $indexArgs += @('--run', [string]$id) }
& python $indexArgs

Write-Host ''
Write-Host "'$($chosen.name)' is done and scored." -ForegroundColor Green
if ($chosen.name -eq 'sky') {
    Write-Host '  The verdict is a number, not a look: how many of the 70 came back' -ForegroundColor Gray
    Write-Host '  fog-flagged, and did luma_mean land near 96? Still flagged means' -ForegroundColor Gray
    Write-Host '  these are not photographable with this rig -- leave --exclude-sky on.' -ForegroundColor Gray
}
Write-Host '  Review it, then publish when it looks right:' -ForegroundColor Gray
Write-Host '    .\Publish-GalleryToAM4.ps1 -GalleryPath .\out\era17\gallery -EraSlug era17' -ForegroundColor DarkGray
