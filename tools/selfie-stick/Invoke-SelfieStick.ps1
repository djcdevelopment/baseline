<#
.SYNOPSIS
    One driver for the selfie-stick capture lanes.

.DESCRIPTION
    Supersedes Start-NextRun.ps1. Owns the run registry, the merged pre-flight,
    settleSeconds, DLL provenance, dispatch to either capture host, the AM4
    pull-back, provenance writing, and the scoring tail.

    It deliberately does NOT own the launch/wait/verify of a local capture.
    Invoke-OrbitCapture.ps1 and Invoke-InteriorCapture.ps1 keep that, including the
    finally block that restores the operator's BepInEx config bytes on every exit
    path -- success, timeout, failure or Ctrl-C. AM4 keeps run-capture.sh. Those are
    load-bearing and they work.

    Three lanes (storm, night sky, colour) each ended 2026-08-25 with findings and a
    slice of an execution surface. The verdicts they paid for are encoded here as
    guards rather than prose:

      * settleSeconds 3 is adopted -- zero occlusion rejects in both halves of a
        90-frame A/B, median frame gap 7.24 s against 10.24 s, 29% faster. The old
        queue DECLARED `settle` on two rows and read it nowhere; that A/B was run by
        hand-editing the cfg. This applies it, on whichever host is shooting.
      * The aesthetic head is an exposure meter and a veto, not a critic. Measured
        over 2,181 frames it moves 0.62 on time-and-weather and ~0 on anything
        structural, and it marks dark frames down on principle. No row's verdict is
        the LAION score.
      * A perfect receipt is not a photograph. The night lane's first run came back
        16/16 clearance=planned, occluded=false, and the moon in zero frames. Every
        row carries a verdict that measures the thing that was wanted.
      * Verify state, not the report of the command that was meant to change it.
        Every check in Test-Preflight earned its place by catching something that had
        already been reported fine.

.EXAMPLE
    .\Invoke-SelfieStick.ps1
    Print the registry with status derived from evidence. Fires nothing.

.EXAMPLE
    .\Invoke-SelfieStick.ps1 -Run night-ephemeris -Preflight
    Run every check for that row against its host. Fires nothing.

.EXAMPLE
    .\Invoke-SelfieStick.ps1 -Run night-ephemeris -Plan
    Plan it, shoot it on its host, pull it back, score it, rebuild the index.
#>
param(
    [string]   $Run = '',
    [ValidateSet('', 'omen', 'am4')]
    [string]   $On = '',
    [switch]   $Plan,
    [switch]   $Preflight,
    [switch]   $Force,
    [switch]   $SkipFollowUp,
    [int]      $TimeoutMinutes = 180,
    [int]      $CaptureWidth = 3840,
    [int]      $CaptureHeight = 2160,
    [string]   $ValheimRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim',
    [string]   $Am4Alias = 'homebase',
    [string]   $Am4Valheim = '/home/derek/valheim'
)

$ErrorActionPreference = 'Stop'

# ------------------------------------------------------------------ paths --
$here        = Split-Path -Parent $MyInvocation.MyCommand.Path
$era         = Join-Path $here 'out\era17'
$perception  = 'C:\work\omen-perception\venv\Scripts\python.exe'
$cfg         = Join-Path $ValheimRoot 'BepInEx\config'
$plugins     = Join-Path $ValheimRoot 'BepInEx\plugins'
$receipts    = Join-Path $cfg 'shotplan-receipts.jsonl'
$orbitCaps   = Join-Path $cfg 'comfy-orbit-captures'
$manualCaps  = Join-Path $cfg 'comfy-manual-captures'
$proofCfg    = Join-Path $cfg 'com.comfy.camera-proof.cfg'
$requestJson = Join-Path $cfg 'orbit-request.json'
$am4Cfg      = "$Am4Valheim/BepInEx/config"

$World     = 'ComfyEra17'
$Character = 'tugcorp'

# Plugins that draw on the screen. None of them belongs in a capture, and BepInEx
# scans plugins/ RECURSIVELY -- parking one into a subfolder parks nothing.
$OverlayPlugins = @('ComfyQuestRuntime.dll', 'ComfyQuestLab.dll', 'ComfyQuestContracts.dll')

# --------------------------------------------------------------- registry --
#
# `runIds` is the run-to-capture mapping. It is what the old queue lacked: with no
# notion of done, three of its seven rows still advertised work that had already
# fired. Seeded below from the 2026-08-27 audit; the driver appends to it.
#
# `verdict` is what counts as the row working -- never the aesthetic score.
$registry = @(
    [ordered]@{
        name    = 'am4-smoke'
        lane    = 'ops'
        plan    = 'am4-smoke'
        host    = 'am4'
        settle  = 3
        runIds  = @()
        what    = '4 frames on one roof, varied bearing and time -- proves the AM4 leg'
        why     = 'the whole AM4 path is unproven end to end: capture, pull-back, md5 ' +
                  'both ends, receipt merge, overlay check, index join. A two-frame ' +
                  'smoke test found three defects it was not built to find last time, ' +
                  'one of which would have invalidated the experiment. Four frames that ' +
                  'differ in camera AND time, because check_overlay measures per-pixel ' +
                  'sigma across VARIED frames and can say nothing about a fixed camera.'
        verdict = 'frames land on OMEN with md5 matching both ends, receipts merge ' +
                  'exactly once, no static band, and the index gains the run'
    },
    [ordered]@{
        name    = 'sky'
        lane    = 'colour'
        plan    = 'sky-probe'
        host    = 'omen'
        settle  = 3
        runIds  = @('20260824-094718')   # 70 planned rows, 70 receipts, 14 clusters,
                                         # Clear @ 0.32, pitch 74.0-86.2. 68 joined:
                                         # 70 captured less 2 rejects.
        what    = '14 sky platforms at dawn, 74 deg (16 off vertical), aimed at the ridge'
        why     = 'daytime side-on frames measure luma 207-233 against a gallery median ' +
                  'of 96 and are all fog-flagged. Overhead at 65 deg came back 100% ' +
                  'occluded and side-on at 22 deg 76%, because the default aim point is ' +
                  'the middle of the bounding box, which is INSIDE the build -- a steep ' +
                  'sight line hits the roof first. Aiming at the ridge fixed it: 0% occluded'
        verdict = 'occlusion-reject rate at 0%, luma_mean inside the 20-186 band'
    },
    [ordered]@{
        name    = 'creators'
        lane    = 'colour'
        plan    = 'creators-1'
        host    = 'omen'
        settle  = 3
        runIds  = @('20260824-083226')   # 240 planned rows, 240 receipts, 237 joined.
        what    = '48 unrepresented builders, one build each'
        why     = 'representation moves 163 -> 211 of 296 creators. These sit at old ' +
                  'cluster ids, so they must join against the frozen clusters.json'
        verdict = 'distinct top_creator_id in the index rises toward 211'
    },
    [ordered]@{
        name    = 'twilight'
        lane    = 'colour'
        plan    = 'twilight-1'
        host    = 'omen'
        settle  = 3
        runIds  = @('20260824-100400')   # 150 planned rows, 150 receipts, Clear 0.71/0.32.
        what    = '30 builds at time 0.71, the synthesised twilight slot'
        why     = 'time 0.71 is the floor indoors (warm_lift 0.079) and near the best ' +
                  'outdoors (0.170): a low sun floods a room so the fire cannot compete, ' +
                  'but outside it rakes a warm facade against a 60% blue sky'
        verdict = 'within-quad warm_lift outdoors at or above 0.15'
    },
    [ordered]@{
        name    = 'storm-1a'
        lane    = 'storm'
        plan    = 'storm-1a'
        host    = 'omen'
        settle  = 6                      # the control half of the settle A/B; do not "fix" this
        runIds  = @('20260825-094829')
        what    = '15 builds, 3 storm frames each, settleSeconds 6 -- the control half'
        why     = 'storm is the best-scoring condition this project has ever measured ' +
                  'indoors. Outdoors it had never been shot at all: every one of the 300 ' +
                  'ThunderStorm receipts was mode:interior, so storm outside was untested ' +
                  'rather than tested and lost'
        verdict = 'occlusion rejects 0; median frame gap ~10.2 s'
    },
    [ordered]@{
        name    = 'storm-1b'
        lane    = 'storm'
        plan    = 'storm-1b'
        host    = 'omen'
        settle  = 3
        runIds  = @('20260825-091907')
        what    = 'the other 15 builds, identical plan, settleSeconds 3'
        why     = 'split interleaved BY RANK, not cut in half: nightsky-1 is written in ' +
                  'rank order and rank tracks size and how well a build photographs, so ' +
                  'first-15/last-15 would have handed settle 6 the better subjects and the ' +
                  'A/B would have measured subject difficulty'
        verdict = 'occlusion rejects 0 and median frame gap ~7.2 s -- both held'
    },
    [ordered]@{
        name    = 'nightsky'
        lane    = 'night'
        plan    = 'nightsky'
        host    = 'am4'
        settle  = 3
        runIds  = @('20260825-072915', '20260825-075415')
        what    = '30 rooftop frames over 15 builds, aimed at disc azimuth 78 at t=0.90'
        why     = 'SHOT AND FAILED ITS VERDICT: disc found in 0 of 30. Not cloud -- stars ' +
                  'median 149 with 22/30 above 100, and 26/30 held the planned stance. The ' +
                  'bearing came from limb fits in two frames from two runs at one time. ' +
                  'Superseded by night-ephemeris; do not re-shoot this bearing.'
        verdict = 'FAILED, and for a reason now measured: it set --body-azimuth 78 ' +
                  'from a limb fit on two frames, while the disc actually sits on the ' +
                  'directional light (134.2 at t=0.90) to within 1.7 deg. It was aimed ' +
                  '56 deg away from the moon. Superseded by nightsky-2.'
    },
    [ordered]@{
        name    = 'nightsky-2'
        lane    = 'night'
        plan    = 'nightsky-2'
        host    = 'am4'
        settle  = 3
        runIds  = @()
        planner = 'plan_nightsky.py'
        # NO --body-azimuth. That is the whole fix. night-ephemeris measured the
        # disc against the arc equations over six frames at three times: azimuth
        # residual mean -0.01 deg (|max| 1.7), altitude mean -0.62 deg (|max| 2.3).
        # The disc IS the light, so the planner's own equations already put the
        # camera on the moon and forcing a bearing can only move it off.
        plannerArgs = @(
            '--rooftops', '<era>\rooftops.json',
            '--clusters', '<era>\clusters.json',
            '--names',    '<era>\cluster-names.json',
            '--times',    '0.90',
            '--bearings', '2',
            '--repeats',  '2',
            '--sky-margin', '3.0',
            '--top',      '15'
        )
        what    = '30 rooftop frames over 15 builds, aimed by the arc equations alone'
        why     = 'the original run set --body-azimuth 78 from a limb fit on two ' +
                  'frames and missed the moon by 56 degrees. Measurement says rho is ' +
                  '0 and the disc sits on the directional light to within 1.7 deg, so ' +
                  'the correct plan is the DEFAULT one. Repeats carry distinct variant ' +
                  'names because cloud position is a re-roll, not a setting.'
        verdict = 'a disc in a good fraction of 30, by EYE or by a fixed sky_check. ' +
                  'sky_check returned nan on all 21 night-ephemeris frames while the ' +
                  'moon is plainly visible in six of them -- it is conservative to the ' +
                  'point of being useless on a clipped or bloomed disc. Do not read a ' +
                  '0 from it as an absence again.'
    },
    [ordered]@{
        name    = 'night-ephemeris'
        lane    = 'night'
        plan    = 'night-ephemeris'
        host    = 'am4'
        settle  = 3
        runIds  = @()
        planner = 'plan_nightsky.py'
        # One stance, fixed upward aim, sweeping time x bearing. This MEASURES the disc's
        # ephemeris instead of trusting a limb fit taken from two frames at a single time.
        # --sky-margin only exists post-merge; on the unguarded planner this row would
        # re-emit the build that photographed its own lattice.
        plannerArgs = @(
            '--rooftops', '<era>\rooftops.json',
            '--clusters', '<era>\clusters.json',
            '--names',    '<era>\cluster-names.json',
            '--times',    '0.80,0.85,0.90,0.95,0.00,0.05',
            '--bearings', '6',
            '--repeats',  '1',
            '--sky-margin', '3.0',
            # Cluster 26, chosen on evidence not rank: clearest_skyline_deg 0.0 (open
            # sky in its clearest direction) and 40 m of roof reach at bearing 0.
            # Reach is what decides how high a moon the roofline can tolerate, so a
            # big roof is what lets ONE build cover six moon altitudes.
            '--cluster-ids', '26'
        )
        # Force the swath around the sky in five steps rather than trusting one
        # bearing. The planner aims where the LIGHT is (azimuth 134.2 at t=0.90);
        # the disc was fitted at ~78 from two frames. That 56 deg gap is why the
        # 30-shot run found a disc in 0 of 30.
        sweepAzimuths = @(60, 90, 120, 150, 180)
        what    = 'one high-clearance roof, 6 times x 6 bearings, fixed upward aim'
        why     = 'the 30-shot run is blocked on a real bearing, and rho is unmeasured. ' +
                  'Altitude and disc radius are NOT recoverable by limb fitting -- a short ' +
                  'arc of a huge circle trades centre distance against radius -- so this ' +
                  'sweeps the sky and lets sky_check report the residual instead.'
        # ANSWERED 2026-08-27 by run 20260827-085344: the disc IS the light. Azimuth
        # residual mean -0.01 deg (|max| 1.7), altitude mean -0.62 (|max| 2.3), over
        # six frames at three times. rho is 0. sky_check saw none of it.
        verdict = 'sky_check finds a disc in >0 frames AND the bearing residual is small. ' +
                  '0 of N is a RESULT: high star counts mean a wrong bearing, low star ' +
                  'counts mean cloud, and those want different answers. Do not re-run on ' +
                  'the hypothesis that maybe it passes.'
    }
)
#
# DROPPED: `hearth` (hearth-1, 324 frames). Its premise collapsed three times --
# "every fire is out" -> "fuel-burners only" -> "a stable ~4.4 per build" -- and the
# light dump then measured the prefab it is named after at power 14 (intensity x
# range^2) against a bonfire's 800. Re-scope it to builds MEASURED genuinely dark,
# or leave it dropped. The plan file is still on disk at out/era17/hearth-1.tsv.

# ------------------------------------------------------------- primitives --

function Read-JsonArray {
    <#
      ConvertFrom-Json in PS 5.1 emits a JSON array as ONE object rather than
      enumerating it, so the idiomatic `@(... | ConvertFrom-Json)` wraps it AGAIN
      and yields a 1-element array holding an Object[]. Invoke-OrbitCapture uses
      exactly that form on capture-runs.json, which is why it carries a filter for
      the literal string 'System.Object[]' -- and why its --run arguments collapse
      into one space-joined id that matches no run at all, silently selecting
      nothing. foreach enumerates correctly.
    #>
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    $obj = [IO.File]::ReadAllText($Path) | ConvertFrom-Json
    $out = @()
    foreach ($item in $obj) { if ($null -ne $item) { $out += [string]$item } }
    return $out
}

function Get-ReceiptLines {
    # shotplan-receipts.jsonl carries a UTF-8 BOM; json.loads on line 1 throws
    # unless the reader strips it.
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    $lines = [IO.File]::ReadAllLines($Path, [Text.UTF8Encoding]::new($false))
    return $lines
}

function Get-PlanFacts {
    param([string] $PlanName)
    $tsv = Join-Path $era "$PlanName.tsv"
    if (-not (Test-Path -LiteralPath $tsv)) { return $null }
    $rows = @(Get-Content -LiteralPath $tsv |
              Where-Object { $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' })
    $clusters = @($rows | ForEach-Object { ($_ -split "`t")[0] } | Sort-Object -Unique)
    return [ordered]@{
        Tsv      = $tsv
        Rows     = $rows.Count
        Clusters = $clusters.Count
        Minutes  = [math]::Round(($rows.Count * 11.5) / 60 + 6)
    }
}

function Get-RunStatus {
    <#
      Derived from evidence, never hand-maintained. A row is done when the runs it
      claims are on the accepted list. This is the check the old queue lacked.
    #>
    param($Row, [string[]] $Accepted)
    if (-not $Row.runIds -or $Row.runIds.Count -eq 0) { return 'queued' }
    $missing = @($Row.runIds | Where-Object { $Accepted -notcontains $_ })
    if ($missing.Count -eq $Row.runIds.Count) { return 'queued' }
    if ($missing.Count -gt 0) { return "partial (not accepted: $($missing -join ', '))" }
    if ($Row.verdict -like 'FAILED*') { return 'done (verdict failed)' }
    return 'done'
}

function Invoke-Native {
    param([string] $Exe, [string[]] $Arguments, [string] $What)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE)" }
}

function Invoke-Ssh {
    # Never 2>&1 a native exe in PS 5.1: it wraps stderr lines in ErrorRecords and
    # sets $? false on a successful exit.
    param([string] $Command, [switch] $AllowFail)
    $out = & ssh -o ConnectTimeout=8 -o BatchMode=yes $Am4Alias $Command
    if (-not $AllowFail -and $LASTEXITCODE -ne 0) {
        throw "ssh $Am4Alias failed (exit $LASTEXITCODE): $Command"
    }
    return $out
}

# -------------------------------------------------------------- preflight --

function Assert-Settle {
    <#
      settleSeconds lives in the mod's cfg and BepInEx rewrites that file from
      memory on shutdown, so it can only be changed with the game closed. The old
      queue declared this value on two rows and applied it nowhere.
    #>
    param([string] $Host_, [int] $Want)
    if ($Host_ -eq 'omen') {
        $text = [IO.File]::ReadAllText($proofCfg)
        $m = [regex]::Match($text, '(?m)^\s*settleSeconds\s*=\s*(\d+)\s*$')
        if (-not $m.Success) { throw "settleSeconds not found in $proofCfg" }
        $have = [int]$m.Groups[1].Value
        if ($have -ne $Want) {
            $new = [regex]::Replace($text, '(?m)^(\s*settleSeconds\s*=\s*)\d+\s*$', "`${1}$Want")
            [IO.File]::WriteAllText($proofCfg, $new, [Text.UTF8Encoding]::new($false))
            Write-Host "      settleSeconds $have -> $Want (game is closed, so this sticks)"
        } else {
            Write-Host "      settleSeconds = $have"
        }
    } else {
        $have = (Invoke-Ssh "grep -oP '^\s*settleSeconds\s*=\s*\K\d+' $am4Cfg/com.comfy.camera-proof.cfg") -join ''
        if ("$have".Trim() -ne "$Want") {
            Invoke-Ssh "sed -i -E 's/^([[:space:]]*settleSeconds[[:space:]]*=[[:space:]]*)[0-9]+[[:space:]]*`$/\1$Want/' $am4Cfg/com.comfy.camera-proof.cfg" | Out-Null
            Write-Host "      settleSeconds $have -> $Want on AM4"
        } else {
            Write-Host "      settleSeconds = $have on AM4"
        }
    }
}

function Test-PreflightCommon {
    param($Row, $Facts)

    Write-Host '  [common]'

    if (-not $Facts) { throw "plan $($Row.plan).tsv is missing from $era" }
    Write-Host "      plan: $($Facts.Rows) rows, $($Facts.Clusters) clusters, ~$($Facts.Minutes) min"

    # The mod re-parses the TSV its own way; validate_tsv reproduces LoadShotPlan.
    $validator = Join-Path $here 'plan_shots.py'
    & python -c @"
import sys, importlib.util
spec = importlib.util.spec_from_file_location('ps', r'$validator')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
if hasattr(m, 'validate_tsv'):
    m.validate_tsv(r'$($Facts.Tsv)')
    print('      TSV re-parses the way the mod does')
else:
    print('      NOTE: validate_tsv not exported; skipped')
"@
    if ($LASTEXITCODE -ne 0) { throw "the plan TSV does not re-parse: $($Facts.Tsv)" }

    # An index rebuild re-derives ~2,600 web images and takes ~15 min. Two collide.
    $gallery = Join-Path $era 'gallery'
    if (Test-Path -LiteralPath $gallery) {
        $recent = @(Get-ChildItem -LiteralPath $gallery -Recurse -Filter '*.webp' -ErrorAction SilentlyContinue |
                    Where-Object { $_.LastWriteTime -gt (Get-Date).AddSeconds(-45) })
        if ($recent.Count -gt 0) {
            throw "an index rebuild looks live: $($recent.Count) .webp written in the last 45 s"
        }
    }
    Write-Host '      no index rebuild in flight'

    # Not "nothing is reading worlds_local" -- backups live there too, and copying
    # from a frozen snapshot is the FIX. Check command lines, not process names.
    $copiers = @(Get-CimInstance Win32_Process -Filter "Name='scp.exe' OR Name='robocopy.exe'" -ErrorAction SilentlyContinue |
                 Where-Object { $_.CommandLine -match 'ComfyEra17\.db(?!\.)' -and $_.CommandLine -notmatch '_backup_auto-' })
    if ($copiers.Count -gt 0) {
        throw "something is reading the LIVE world file: PID(s) $(($copiers | ForEach-Object { $_.ProcessId }) -join ', ')"
    }
    Write-Host '      nothing is reading the live world file'
}

function Test-PreflightOmen {
    param($Row)
    Write-Host '  [omen]'

    $p = Get-Process valheim -ErrorAction SilentlyContinue
    if ($p) { throw "Valheim is running (pid $($p.Id)). The plan and the DLL are read at startup." }
    Write-Host '      valheim is not running'

    # light_dump takes precedence over sky_times AND over a shot plan. Left armed,
    # the next launch dumps and quits instead of shooting.
    if (Test-Path -LiteralPath $requestJson) {
        $req = [IO.File]::ReadAllText($requestJson)
        if ($req -match '"light_dump"\s*:\s*true') { throw "orbit-request.json is armed with light_dump:true -- it would dump and quit instead of shooting" }
        if ($req -match '"sky_times"')             { throw "orbit-request.json carries sky_times -- it would measure instead of shooting" }
    }
    Write-Host '      orbit-request.json is not armed for a dump'

    # BepInEx scans plugins/ recursively and only LogOutput.log says what loaded.
    # Checking the directory is the right instinct; it just has to be recursive.
    $found = @(Get-ChildItem -LiteralPath $plugins -Recurse -Filter '*.dll' -ErrorAction SilentlyContinue |
               Where-Object { $OverlayPlugins -contains $_.Name })
    if ($found.Count -gt 0) {
        $where = ($found | ForEach-Object { $_.FullName.Substring($plugins.Length).TrimStart('\') }) -join ', '
        throw ("an overlay plugin is loadable and would burn into the frames: $where`n" +
               "       Move it OUT of the plugins tree entirely -- a subfolder parks nothing.`n" +
               "       61 frames were lost to this once already.")
    }
    Write-Host '      no overlay plugin is loadable under plugins/'

    Assert-Settle -Host_ 'omen' -Want $Row.settle
}

function Test-PreflightAm4 {
    param($Row)
    Write-Host '  [am4]'

    $probe = Invoke-Ssh @'
set -e
[ -f ~/valheim/valheim.x86_64 ] && echo "valheim=yes" || echo "valheim=no"
pgrep -x valheim.x86_64 >/dev/null 2>&1 && echo "running=yes" || echo "running=no"
echo "dll=$(md5sum ~/valheim/BepInEx/plugins/ComfyCameraProof.dll 2>/dev/null | awk '{print $1}')"
echo "renderer=$(DISPLAY=:0 glxinfo -B 2>/dev/null | sed -n 's/^OpenGL renderer string: //p')"
echo "screen=$(DISPLAY=:0 xrandr --query 2>/dev/null | sed -n 's/^Screen 0:.*current \([0-9]* x [0-9]*\),.*/\1/p' | tr -d ' ')"
echo "overlay=$(find ~/valheim/BepInEx/plugins -name 'ComfyQuest*.dll' | wc -l)"
echo "portal=$(grep -cE '^[[:space:]]*portalConnectionCacheEnabled[[:space:]]*=[[:space:]]*true' ~/valheim/BepInEx/config/djcdevelopment.valheim.comfynetworksense.cfg)"
echo "world=$(md5sum ~/.config/unity3d/IronGate/Valheim/worlds_local/ComfyEra17.db 2>/dev/null | awk '{print $1}')"
'@
    $kv = @{}
    foreach ($line in $probe) { if ($line -match '^(\w+)=(.*)$') { $kv[$Matches[1]] = $Matches[2].Trim() } }

    if ($kv['valheim'] -ne 'yes')  { throw 'AM4 has no valheim.x86_64 -- the Linux depot has not downloaded' }
    if ($kv['running'] -eq 'yes')  { throw 'Valheim is already running on AM4 -- the DLL and plan are read at startup' }
    Write-Host '      valheim installed and not running'

    if ($kv['renderer'] -notmatch 'NVIDIA') {
        throw "X on :0 is not on the NVIDIA GPU (got: '$($kv['renderer'])'). Software rendering produces frames, very slowly, that look nothing like the gallery."
    }
    Write-Host "      rendering on: $($kv['renderer'])"

    # The Era 17 series shipped at 1080p off OMEN's BMC adapter because nothing
    # asserted this. Unity clamps to the screen; every other check still passes.
    $want = "${CaptureWidth}x${CaptureHeight}"
    if ($kv['screen'] -ne $want) {
        throw ("AM4's X screen is $($kv['screen']) but the capture asks for $want.`n" +
               "       A 4K window cannot exist in a smaller framebuffer -- you would get`n" +
               "       $($kv['screen']) frames and every other check would still pass.`n" +
               "       Grow it:  ssh $Am4Alias `"DISPLAY=:0 xrandr --fb $want`"`n" +
               "       Or flip to the headless X config:  ssh $Am4Alias 'sudo valheim-display headless'")
    }
    Write-Host "      X screen is $($kv['screen'])"

    $localDll = (Get-FileHash -LiteralPath (Join-Path $plugins 'ComfyCameraProof.dll') -Algorithm MD5).Hash.ToLower()
    if ($kv['dll'] -ne $localDll) {
        throw "AM4's ComfyCameraProof.dll is $($kv['dll']) but OMEN's is $localDll -- the two nodes would not be running the same code"
    }
    Write-Host "      ComfyCameraProof.dll matches OMEN: $localDll"

    if ([int]$kv['overlay'] -ne 0) { throw "AM4 has $($kv['overlay']) ComfyQuest*.dll under plugins/ -- they would burn a creator bar into the frames" }
    Write-Host '      no overlay plugin is loadable on AM4'

    if ([int]$kv['portal'] -lt 1) { throw 'portalConnectionCacheEnabled must be true on AM4 or run-capture.sh refuses' }
    Write-Host '      portal cache flag set'

    # Recorded, deliberately NOT asserted. AM4's copy starts byte-identical to the
    # frozen _backup_auto-* snapshot it came from, and then Valheim saves on exit,
    # so it drifts on the first capture and every one after. An equality gate here
    # would pass exactly once and refuse forever. It is provenance, not a guard --
    # and the index joins frames to the frozen clusters.json by position, so the
    # drift does not reach the gallery.
    Write-Host "      world md5 $($kv['world'])"
    Assert-Settle -Host_ 'am4' -Want $Row.settle
}

# ------------------------------------------------------------------ plan --

function Invoke-PlanRow {
    param($Row)
    if (-not $Row.planner) { throw "row '$($Row.name)' has no planner; shoot its existing TSV without -Plan" }
    $baseArgs = @(Join-Path $here $Row.planner)
    foreach ($a in $Row.plannerArgs) { $baseArgs += ($a -replace '<era>', $era) }

    if (-not $Row.sweepAzimuths) {
        Write-Host "  planning with $($Row.planner)"
        Invoke-Native -Exe 'python' -Arguments ($baseArgs + @('--out', (Join-Path $era "$($Row.plan).json"))) -What $Row.planner
        return
    }

    # An ephemeris SURVEY, not another shot at a guessed bearing.
    #
    # Variants get their yaw appended because the index supersedes on
    # (cluster, variant, environment, time_of_day) -- two frames of the same name
    # retire each other rather than joining, which is how 150 golden frames were
    # quietly replaced on 2026-08-24. Rows are merged from the TSVs the planner
    # already wrote rather than re-serialised, so every other column stays
    # byte-identical to what the planner emits.
    Write-Host "  ephemeris sweep: $($Row.sweepAzimuths.Count) forced azimuths"
    $header = $null
    $seen = @{}
    $rows = New-Object System.Collections.Generic.List[string]
    $planJson = New-Object System.Collections.Generic.List[object]

    foreach ($az in $Row.sweepAzimuths) {
        $out = Join-Path $era "_sweep-$($Row.plan)-$az.json"
        Invoke-Native -Exe 'python' -Arguments ($baseArgs + @('--body-azimuth', "$az", '--out', $out)) -What "$($Row.planner) at azimuth $az"
        $tsv = [IO.Path]::ChangeExtension($out, '.tsv')
        $kept = 0
        foreach ($line in (Get-Content -LiteralPath $tsv)) {
            if ($line -match '^\s*#') { if (-not $header) { $header = $line }; continue }
            if (-not $line.Trim()) { continue }
            $c = $line -split "`t"
            if ($c.Count -lt 14) { continue }
            # The photograph's identity is roof + direction + time. Two swaths that
            # both choose bearing 120 at t=0.90 are the same frame, not two.
            $key = "$($c[0])|$($c[5])|$($c[8])"
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key] = $true
            $c[1] = "$($c[1])y$([int][double]$c[5])"
            $rows.Add(($c -join "`t"))
            $kept++
        }
        $j = [IO.File]::ReadAllText($out) | ConvertFrom-Json
        foreach ($shot in $j.plan) {
            $k = "$($shot.cluster_id)|$($shot.yaw_deg)|$($shot.time_of_day)"
            if ($planJson | Where-Object { "$($_.cluster_id)|$($_.yaw_deg)|$($_.time_of_day)" -eq $k }) { continue }
            $shot.shot = "$($shot.shot)y$([int][double]$shot.yaw_deg)"
            $planJson.Add($shot)
        }
        Write-Host "      azimuth $az -> $kept new shot(s)"
        Remove-Item -LiteralPath $out, $tsv -Force -ErrorAction SilentlyContinue
    }

    if ($rows.Count -eq 0) { throw 'the sweep planned no shots at all' }
    $outTsv = Join-Path $era "$($Row.plan).tsv"
    $sw = New-Object IO.StreamWriter($outTsv, $false, [Text.UTF8Encoding]::new($false))
    try { $sw.WriteLine($header); foreach ($r in $rows) { $sw.WriteLine($r) } } finally { $sw.Dispose() }

    $doc = [ordered]@{ generated_from = 'Invoke-SelfieStick.ps1 ephemeris sweep'
                       world = $World; structures = 1; shots = $rows.Count
                       sweep_azimuths = $Row.sweepAzimuths; plan = $planJson }
    [IO.File]::WriteAllText((Join-Path $era "$($Row.plan).json"),
        (($doc | ConvertTo-Json -Depth 8) + "`n"), [Text.UTF8Encoding]::new($false))
    Write-Host "      $($rows.Count) shot(s) after dedupe -> $outTsv"
}

# --------------------------------------------------------------- capture --

function Invoke-CaptureOmen {
    param($Row, $Facts)
    $runner = 'Invoke-OrbitCapture.ps1'
    if ($Row.runner) { $runner = $Row.runner }
    # -SkipIndex because this driver owns the tail. Without it the index is derived
    # twice per run -- once here before any score exists, once in Invoke-Tail --
    # and each pass re-derives ~2,600 web images.
    & (Join-Path $here $runner) -SkipPlan -SkipIndex `
        -World $World -Character $Character `
        -Clusters (Join-Path $era 'clusters.json') `
        -PlanOut (Join-Path $era "$($Row.plan).json") `
        -GalleryDest (Join-Path $era 'gallery') `
        -RunManifest (Join-Path $era 'capture-runs.json') `
        -CaptureWidth $CaptureWidth -CaptureHeight $CaptureHeight `
        -TimeoutMinutes $TimeoutMinutes
    if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) { throw "$runner failed" }
}

function Invoke-CaptureAm4 {
    <#
      run-capture.sh keeps the same contract as the Windows runner and prints
      "RUN <id>" for each run it produced. AM4 keeps its OWN receipts file by
      design; merging the two nodes' receipts is this function's job.
    #>
    param($Row, $Facts)

    $remotePlan = "$am4Cfg/plans/$($Row.plan).tsv"
    Invoke-Ssh "mkdir -p $am4Cfg/plans && rm -f $remotePlan" | Out-Null
    & scp -q $Facts.Tsv "${Am4Alias}:$remotePlan"
    if ($LASTEXITCODE -ne 0) { throw 'scp of the plan failed' }

    # scp does NOT truncate: a smaller file over a larger one leaves a stale tail
    # that passes both a size check and a "transfer completed" check. Hash it.
    $localHash  = (Get-FileHash -LiteralPath $Facts.Tsv -Algorithm MD5).Hash.ToLower()
    # cut -c1-32, not awk '{print $1}': this is a double-quoted PowerShell string,
    # so $1 would be interpolated away before ssh ever saw it. md5sum always leads
    # with exactly 32 hex characters.
    $remoteHash = ((Invoke-Ssh "md5sum $remotePlan | cut -c1-32") -join '').Trim()
    if ($localHash -ne $remoteHash) { throw "plan TSV differs after transfer: $localHash vs $remoteHash" }
    Write-Host "      plan staged on AM4 (md5 $localHash)"

    $before = ((Invoke-Ssh "wc -l < $am4Cfg/shotplan-receipts.jsonl 2>/dev/null || echo 0") -join '').Trim()
    Write-Host "      AM4 had $before receipt(s) on file"

    Write-Host "  shooting on AM4 (timeout $TimeoutMinutes min)"
    $out = & ssh -o ConnectTimeout=8 -o BatchMode=yes -o ServerAliveInterval=30 $Am4Alias `
        "~/valheim-capture/run-capture.sh --plan '$remotePlan' --world '$World' --character '$Character' --timeout $TimeoutMinutes --width $CaptureWidth --height $CaptureHeight"
    $rc = $LASTEXITCODE
    foreach ($line in $out) { Write-Host "      | $line" }
    if ($rc -ne 0) { throw "run-capture.sh failed (exit $rc)" }

    $runIds = @()
    foreach ($line in $out) { if ($line -match '^\s*RUN\s+(\S+)\s*$') { $runIds += $Matches[1] } }
    if ($runIds.Count -eq 0) { throw 'run-capture.sh reported no RUN ids -- nothing was captured' }
    Write-Host "      AM4 produced: $($runIds -join ', ')"

    Sync-Am4Results -RunIds $runIds -Before ([int]$before)
    return $runIds
}

function Sync-Am4Results {
    param([string[]] $RunIds, [int] $Before)

    foreach ($id in $RunIds) {
        $dest = Join-Path $orbitCaps $id
        # rm the destination FIRST. This is the same non-truncating-write trap that
        # left 41,320 bytes of stale tail on a 1.3 GB world copy.
        if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
        New-Item -ItemType Directory -Path $dest -Force | Out-Null

        Write-Host "  pulling $id"
        & scp -q -r "${Am4Alias}:$am4Cfg/comfy-orbit-captures/$id/." $dest
        if ($LASTEXITCODE -ne 0) { throw "scp of run $id failed" }

        # md5 both ends, per file. Size and exit code have both lied here before.
        $remote = @{}
        foreach ($line in (Invoke-Ssh "cd $am4Cfg/comfy-orbit-captures/$id && md5sum * 2>/dev/null")) {
            if ($line -match '^([0-9a-f]{32})\s+\*?(.+)$') { $remote[$Matches[2].Trim()] = $Matches[1] }
        }
        $bad = @()
        foreach ($name in $remote.Keys) {
            $lf = Join-Path $dest $name
            if (-not (Test-Path -LiteralPath $lf)) { $bad += "$name missing locally"; continue }
            $lh = (Get-FileHash -LiteralPath $lf -Algorithm MD5).Hash.ToLower()
            if ($lh -ne $remote[$name]) { $bad += "$name $lh != $($remote[$name])" }
        }
        if ($bad.Count -gt 0) { throw "pull-back of $id is corrupt:`n       $($bad -join "`n       ")" }
        Write-Host "      $($remote.Count) file(s), md5 verified both ends"
    }

    # Receipts: append only lines this OMEN receipts file does not already carry,
    # keyed on (run, file), so a re-pull cannot double-append.
    $remoteLines = Invoke-Ssh "cat $am4Cfg/shotplan-receipts.jsonl 2>/dev/null"
    $have = @{}
    foreach ($line in (Get-ReceiptLines $receipts)) {
        if ($line -match '"run"\s*:\s*"([^"]+)".*?"file"\s*:\s*"([^"]+)"') { $have["$($Matches[1])/$($Matches[2])"] = $true }
    }
    $added = 0
    $append = New-Object System.Collections.Generic.List[string]
    foreach ($line in $remoteLines) {
        if (-not $line.Trim()) { continue }
        if ($line -notmatch '"run"\s*:\s*"([^"]+)"') { continue }
        $runId = $Matches[1]
        if ($RunIds -notcontains $runId) { continue }
        $key = $runId
        if ($line -match '"file"\s*:\s*"([^"]+)"') { $key = "$runId/$($Matches[1])" }
        if ($have.ContainsKey($key)) { continue }
        $append.Add($line.TrimEnd()); $have[$key] = $true; $added++
    }
    if ($added -gt 0) {
        # Append without a BOM -- the BOM belongs at the start of the file only.
        $sw = New-Object IO.StreamWriter($receipts, $true, [Text.UTF8Encoding]::new($false))
        try { foreach ($l in $append) { $sw.WriteLine($l) } } finally { $sw.Dispose() }
    }
    Write-Host "      $added receipt line(s) merged into OMEN's receipts"
}

# ---------------------------------------------------------------- verify --

function Assert-NoOverlay {
    <#
      Per-pixel standard deviation across VARIED frames, frozen AND lit.

      Two things this deliberately does NOT do:

      * It does not judge on the frozen percentage alone when the run has few
        distinct cameras. check_overlay says so itself -- "consecutive frames are
        the same structure from adjacent bearings and share too much scene to
        tell an overlay from a wall". Four frames of one roof at two bearings
        measured 0.35% frozen-and-lit, all of it the same lit tents and fire in
        both frames. A guard that fires on a case it cannot judge is decoration.
      * It does not treat the right-edge strip as a defect. NetworkSense's
        transport recovery tab is deliberately retained in the running client and
        removed from the derived images; the same 120 px goes to both tools.

      What it DOES hard-fail on is a band, at any brightness, in any sample size.
      A HUD is a band. That is the property the creator bar had.
    #>
    param([string[]] $RunIds, $Facts)

    $distinctCameras = 0
    if ($Facts -and (Test-Path -LiteralPath $Facts.Tsv)) {
        $keys = @{}
        foreach ($line in (Get-Content -LiteralPath $Facts.Tsv)) {
            if ($line -match '^\s*#' -or -not $line.Trim()) { continue }
            $c = $line -split "`t"
            if ($c.Count -ge 6) { $keys["$($c[2]),$($c[4]),$($c[5])"] = $true }
        }
        $distinctCameras = $keys.Count
    }

    foreach ($id in $RunIds) {
        $dir = Join-Path $orbitCaps $id
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        Write-Host "  overlay check: $id ($distinctCameras distinct camera(s) in the plan)"
        $out = & python (Join-Path $here 'check_overlay.py') --images $dir --ignore-right-px 120
        $rc = $LASTEXITCODE
        foreach ($line in $out) { Write-Host "  $line" }

        $band = @($out | Where-Object { $_ -match 'static (horizontal|vertical) band' })
        if ($band.Count -gt 0) {
            throw ("a static BAND is drawn on $id -- that is a HUD, not scenery:`n" +
                   "       $($band -join "`n       ")`n" +
                   "       Turn its surface off at the mod and re-shoot. Cropping hides it in`n" +
                   "       the gallery and leaves it in the originals, which is how it survived`n" +
                   "       five runs.")
        }
        if ($rc -ne 0) {
            if ($distinctCameras -ge 8) {
                throw "check_overlay flagged $id over tolerance across $distinctCameras cameras. Do not publish these frames."
            }
            Write-Warning ("check_overlay is over tolerance on $id but found no band, and the plan " +
                           "has only $distinctCameras distinct camera(s) -- too little scene change " +
                           "to separate an overlay from shared architecture. Treating as inconclusive.")
        }
    }
}

function Write-Provenance {
    param($Row, [string] $Host_, [string[]] $RunIds, $Facts)
    $modSha = ''
    Push-Location 'C:\work\_retired\comfy'
    try { $modSha = (& git rev-parse HEAD) -join '' } catch { $modSha = 'unknown' } finally { Pop-Location }
    $baseSha = (& git -C $here rev-parse --short HEAD) -join ''
    $prov = [ordered]@{
        label         = $Row.name
        lane          = $Row.lane
        host          = $Host_
        fired_at      = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        settle        = $Row.settle
        plan_rows     = $Facts.Rows
        dll_md5       = (Get-FileHash -LiteralPath (Join-Path $plugins 'ComfyCameraProof.dll') -Algorithm MD5).Hash
        mod_head      = $modSha
        baseline_head = $baseSha
        capture_size  = "${CaptureWidth}x${CaptureHeight}"
        run_ids       = $RunIds
        overlay       = 'check_overlay.py clean'
        verdict       = $Row.verdict
    }
    $path = Join-Path $era "run-provenance-$($Row.name).json"
    [IO.File]::WriteAllText($path, (($prov | ConvertTo-Json -Depth 4) + "`n"), [Text.UTF8Encoding]::new($false))
    Write-Host "  provenance -> $path"
}

# ------------------------------------------------------------------ tail --

function Build-Index {
    param([string] $Why)
    $runIds = Read-JsonArray (Join-Path $era 'capture-runs.json')
    if ($runIds.Count -eq 0) { throw 'capture-runs.json yielded no run ids' }
    Write-Host "  index ($Why): $($runIds.Count) accepted run(s)"
    $a = @(
        (Join-Path $here 'build_valheim_index.py'), '--thumbs', '--large',
        '--captures', $manualCaps,
        '--orbit-captures', $orbitCaps,
        '--receipts', $receipts,
        '--clusters', (Join-Path $era 'clusters.json'),
        '--dest', (Join-Path $era 'gallery'),
        '--world', $World,
        '--names', (Join-Path $era 'cluster-names.json'),
        '--depth', (Join-Path $era 'depth.json'),
        '--aesthetic', (Join-Path $era 'aesthetic.json'),
        '--crop-right-ui-px', '120',
        '--derived', (Join-Path $era 'derived-frames.json')
    )
    foreach ($id in $runIds) { $a += @('--run', $id) }
    Invoke-Native -Exe 'python' -Arguments $a -What 'build_valheim_index.py'
}

function Assert-IndexNotEmptied {
    param([int] $Before)
    $idx = Join-Path $era 'gallery\index.json'
    $n = 0
    if (Test-Path -LiteralPath $idx) {
        $j = [IO.File]::ReadAllText($idx) | ConvertFrom-Json
        $n = @($j.images).Count
    }
    if ($n -lt $Before) {
        throw "the index LOST frames: $Before -> $n. That is the --run filter selecting nothing; do not publish."
    }
    Write-Host "  index holds $n frames (was $Before)"
}

function Invoke-Tail {
    param($Row, [string[]] $RunIds)

    $idx = Join-Path $era 'gallery\index.json'
    $before = 0
    if (Test-Path -LiteralPath $idx) {
        $j = [IO.File]::ReadAllText($idx) | ConvertFrom-Json
        $before = @($j.images).Count
    }

    # Pass 1 materialises gallery/large, which every scorer reads. Pass 2 folds the
    # scores back in. Both are necessary; the win is one arg list in one place
    # rather than two that have already drifted apart.
    Build-Index -Why 'pass 1, to derive gallery/large'

    $large = Join-Path $era 'gallery\large'
    $steps = @(
        @{ label = 'aesthetic'; exe = $perception; args = @((Join-Path $here 'score_images.py'), '--images', $large, '--out', (Join-Path $era 'aesthetic.json')) },
        @{ label = 'depth';     exe = $perception; args = @((Join-Path $here 'depth_layers.py'), '--images', $large, '--out', (Join-Path $era 'depth.json')) },
        @{ label = 'colour';    exe = 'python';    args = @((Join-Path $here 'color_layers.py'), '--images', $large, '--out', (Join-Path $era 'color.json')) },
        @{ label = 'names';     exe = 'python';    args = @((Join-Path $here 'name_structures.py'), '--index', $idx, '--thumbs', $large, '--out', $era) }
    )
    foreach ($s in $steps) {
        try {
            & $s.exe $s.args
            if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
            Write-Host "  $($s.label) ok"
        } catch {
            Write-Warning "$($s.label) did not finish ($_). The frames are on disk; rerun it."
        }
    }

    Build-Index -Why 'pass 2, folding the scores in'
    Assert-IndexNotEmptied -Before $before

    if ($Row.lane -eq 'night') {
        Write-Host '  verdict: sky_check (NOT the aesthetic head)'
        # sky_check's --run is a single value, not an append action: passing it
        # twice keeps only the last and silently drops the other run. One call per
        # run id, one output per run id.
        foreach ($id in $RunIds) {
            & python (Join-Path $here 'sky_check.py') `
                --plan (Join-Path $era "$($Row.plan).json") `
                --receipts $receipts --captures $orbitCaps --run $id `
                --depth (Join-Path $era 'depth.json') `
                --out (Join-Path $era "skycheck-$($Row.name)-$id.json")
            if ($LASTEXITCODE -ne 0) { Write-Warning "sky_check did not finish for $id; the frames are on disk" }
        }
    }

    Write-Host ''
    Write-Host "  VERDICT for $($Row.name): $($Row.verdict)" -ForegroundColor Cyan
}

# ------------------------------------------------------------------ main --

$accepted = Read-JsonArray (Join-Path $era 'capture-runs.json')

if (-not $Run) {
    Write-Host ''
    Write-Host 'selfie-stick runs' -ForegroundColor Cyan
    Write-Host ('-' * 78)
    foreach ($row in $registry) {
        $facts  = Get-PlanFacts $row.plan
        $status = Get-RunStatus -Row $row -Accepted $accepted
        $colour = 'Gray'
        if ($status -eq 'queued') { $colour = 'Green' }
        if ($status -like '*failed*' -or $status -like 'partial*') { $colour = 'Yellow' }
        $size = 'plan MISSING'
        if ($facts) { $size = "$($facts.Rows) shots / $($facts.Clusters) builds / ~$($facts.Minutes) min" }
        Write-Host ''
        Write-Host ("  {0,-16} [{1}] {2}" -f $row.name, $row.lane, $status) -ForegroundColor $colour
        Write-Host ("      on {0}, settle {1}, {2}" -f $row.host, $row.settle, $size)
        Write-Host ("      {0}" -f $row.what)
        Write-Host ("      verdict: {0}" -f $row.verdict) -ForegroundColor DarkGray
    }
    Write-Host ''
    Write-Host ('-' * 78)
    Write-Host "  $($accepted.Count) accepted capture run(s) on file"
    Write-Host '  fire one with:  .\Invoke-SelfieStick.ps1 -Run <name> [-Plan]'
    Write-Host '  check only:     .\Invoke-SelfieStick.ps1 -Run <name> -Preflight'
    Write-Host ''
    return
}

$row = $registry | Where-Object { $_.name -eq $Run }
if (-not $row) { throw "no run called '$Run'. Run with no arguments to see the registry." }
if ($On) { $row.host = $On }

$status = Get-RunStatus -Row $row -Accepted $accepted
if ($status -like 'done*' -and -not $Force) {
    throw "'$Run' is already $status (runs: $($row.runIds -join ', ')). Use -Force to shoot it again."
}

Write-Host ''
Write-Host "$($row.name) -- $($row.what)" -ForegroundColor Cyan
Write-Host "  host $($row.host), settle $($row.settle), status $status"
Write-Host ''

if ($Plan) { Invoke-PlanRow -Row $row }

$facts = Get-PlanFacts $row.plan
Test-PreflightCommon -Row $row -Facts $facts
if ($row.host -eq 'omen') { Test-PreflightOmen -Row $row } else { Test-PreflightAm4 -Row $row }

if ($Preflight) {
    Write-Host ''
    Write-Host '  preflight only -- nothing fired.' -ForegroundColor Green
    return
}

Write-Host ''
$newRuns = @()
if ($row.host -eq 'omen') {
    Invoke-CaptureOmen -Row $row -Facts $facts
    $newRuns = @(Read-JsonArray (Join-Path $era 'capture-runs.json') | Where-Object { $accepted -notcontains $_ })
} else {
    $newRuns = Invoke-CaptureAm4 -Row $row -Facts $facts
    $manifest = Join-Path $era 'capture-runs.json'
    $all = @(Read-JsonArray $manifest)
    foreach ($id in $newRuns) { if ($all -notcontains $id) { $all += $id } }
    [IO.File]::WriteAllText($manifest, (($all | ConvertTo-Json -Depth 2) + "`n"), [Text.UTF8Encoding]::new($true))
}

Assert-NoOverlay -RunIds $newRuns -Facts $facts
Write-Provenance -Row $row -Host_ $row.host -RunIds $newRuns -Facts $facts

if ($SkipFollowUp) {
    Write-Host ''
    Write-Host "  captured $($newRuns -join ', '); follow-up skipped." -ForegroundColor Green
    return
}

Invoke-Tail -Row $row -RunIds $newRuns
Write-Host ''
Write-Host "  done: $($newRuns -join ', ')" -ForegroundColor Green
