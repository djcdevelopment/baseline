<#
.SYNOPSIS
    Measure where the sun and the moon are, at every time of day.

.DESCRIPTION
    The night-sky planner needs the bearing and altitude of whatever is lighting
    the sky, per forced time of day, plus the angular radius of the moon's disc.
    Fitting circles to captured frames gives an answer -- azimuth 75, altitude 67,
    radius 44 degrees at t=0.90 -- but the limb it fits is cut by trees and by the
    ring feature, so it is a fit over noise. EnvMan knows exactly.

    ComfyCameraProof 0.2.0+ dumps it. There is no console typing here, same as
    every other unattended path: orbit-request.json carries a "sky_times" list,
    the mod sees it after the world loads, walks the times, writes
    comfy-camera-proof-sky.json and quits.

    No screenshots are taken, so none of the orbit runner's HUD-quieting or
    portal-cache preflight applies. This only needs a loaded world.

.EXAMPLE
    .\Invoke-SkyDump.ps1
    .\Invoke-SkyDump.ps1 -Times 0.85,0.90,0.95 -Out .\out\era17\sky.json
#>
[CmdletBinding()]
param(
    [string] $World = 'ComfyEra17',
    [string] $Character = 'tugcorp',
    [double[]] $Times = @(),
    [int] $TimeoutMinutes = 20,
    [string] $Out = '',
    [string] $ValheimRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim',
    [string] $SteamExe = 'C:\Program Files (x86)\Steam\steam.exe'
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg = Join-Path $ValheimRoot 'BepInEx\config'
$dump = Join-Path $cfg 'comfy-camera-proof-sky.json'
$dll = Join-Path $ValheimRoot 'BepInEx\plugins\ComfyCameraProof.dll'
if (-not $Out) { $Out = Join-Path $here 'out\era17\sky.json' }

if (Get-Process valheim -ErrorAction SilentlyContinue) {
    throw 'Valheim is running. Close it first -- the request and the DLL are read at startup.'
}
if (-not (Test-Path -LiteralPath $dll)) { throw "ComfyCameraProof is not installed: $dll" }

# The whole day at 0.025. The planner wants az(t) and alt(t) as curves, not two
# points, and a 41-sample walk costs about a minute of the mod's time.
if (-not $Times -or $Times.Count -eq 0) {
    $Times = 0..40 | ForEach-Object { [math]::Round($_ / 40.0, 3) }
}
$list = ($Times | ForEach-Object { $_.ToString([System.Globalization.CultureInfo]::InvariantCulture) }) -join ', '
Write-Host ("[1/4] {0} time(s) to sample" -f $Times.Count)

# A stale dump would read as a successful run that never happened.
if (Test-Path -LiteralPath $dump) {
    Remove-Item -LiteralPath $dump -Force
    Write-Host '      removed the previous dump'
}

Write-Host '[2/4] arming the mod'
$req = "{`n  ""world"": ""$World"",`n  ""character"": ""$Character"",`n" +
       "  ""quit_when_done"": true,`n  ""sky_times"": [ $list ]`n}`n"
[IO.File]::WriteAllText((Join-Path $cfg 'orbit-request.json'), $req,
                        [Text.UTF8Encoding]::new($false))

# ComfyNetworkSense joins a server when this exists, and would fight for the menu.
$autojoin = Join-Path $cfg 'comfy-network-sense\native-autotest-request.json'
$parked = $false
if (Test-Path -LiteralPath $autojoin) {
    Move-Item -LiteralPath $autojoin -Destination "$autojoin.disabled-for-skydump" -Force
    $parked = $true
    Write-Host '      parked the server auto-join request'
}

try {
    Write-Host '[3/4] launching Valheim'
    Start-Process -FilePath $SteamExe -ArgumentList '-applaunch', '892970', '-console'

    $deadline = (Get-Date).AddMinutes($TimeoutMinutes)
    $seen = $false
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 10
        if (Test-Path -LiteralPath $dump) { $seen = $true; break }
        if (-not (Get-Process valheim -ErrorAction SilentlyContinue)) {
            # The game going away without a dump means the boot never got there.
            if (Test-Path -LiteralPath $dump) { $seen = $true }
            break
        }
    }
} finally {
    if ($parked) {
        Move-Item -LiteralPath "$autojoin.disabled-for-skydump" -Destination $autojoin -Force
    }
}

if (-not $seen) {
    throw "no dump appeared at $dump within $TimeoutMinutes min -- check BepInEx\LogOutput.log"
}

Write-Host '[4/4] collecting'
$deadline = (Get-Date).AddMinutes(2)
while ((Get-Process valheim -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
Copy-Item -LiteralPath $dump -Destination $Out -Force
Write-Host "      $Out"
Write-Host ''
Write-Host '  Read it with:  python fit_sky.py --sky ' -NoNewline
Write-Host $Out
