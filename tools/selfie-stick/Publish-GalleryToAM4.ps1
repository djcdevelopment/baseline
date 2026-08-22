<#
.SYNOPSIS
    Publish the interactive gallery to the /valheim/ route on AM4.

.DESCRIPTION
    The route is the long-lived Caddy handle_path serving ~/valheim-gallery/public
    on AM4 (NOT the funnel-demo lane). Previous pushes were hand-rolled tarballs;
    this script is that same lane with two things made unforgettable:

      1. The shipped index.json is SCRUBBED (scrub_index.py drops x/y/z and
         top_creator_id) — the local copy keeps full fidelity, the public copy
         does not carry build coordinates or creator ids.
      2. A full push replaces the active render directories so assets from a
         previous era cannot linger. A run-prefix delta remains available for
         updates to the same gallery, but cannot be combined with era archival.

    Talks to the box only through the `am4` ssh alias — the tailnet hostname
    stays out of this public repo.

.EXAMPLE
    .\Publish-GalleryToAM4.ps1                          # full replacement
    .\Publish-GalleryToAM4.ps1 -RenderPrefix 20260808-  # same-gallery delta
    .\Publish-GalleryToAM4.ps1 -GalleryPath .\out\era17\gallery -ArchiveCurrentAs era16
#>
[CmdletBinding()]
param(
    [string] $RenderPrefix = '',
    [string] $GalleryPath = '',
    [string] $ArchiveCurrentAs = '',
    [string] $RemoteDir = '~/valheim-gallery/public',
    [string] $SshAlias = 'am4'
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$gallery = if ($GalleryPath) { $GalleryPath } else { Join-Path $here 'out\gallery' }
$stage = Join-Path $env:TEMP 'vg-stage'
$tgz = Join-Path $env:TEMP 'vg-deploy.tgz'

if (!(Test-Path (Join-Path $gallery 'index.json'))) { throw "no index.json in $gallery - run build_valheim_index.py first" }
if ($ArchiveCurrentAs -and $RenderPrefix) {
    throw 'an era archive requires a full gallery push; omit -RenderPrefix'
}

Write-Host '[1/5] staging'
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage -Confirm:$false }
New-Item -ItemType Directory -Path (Join-Path $stage 'thumb'), (Join-Path $stage 'large') -Force | Out-Null

Copy-Item (Join-Path $here 'gallery\index.html') (Join-Path $stage 'index.html')
foreach ($side in 'depth.json', 'judge.json') {
    $p = Join-Path $gallery $side
    if (Test-Path $p) { Copy-Item $p (Join-Path $stage $side) }
}

& python (Join-Path $here 'scrub_index.py') (Join-Path $gallery 'index.json') (Join-Path $stage 'index.json')
if ($LASTEXITCODE -ne 0) { throw 'scrub_index.py failed - refusing to ship an unscrubbed index' }

$nThumb = 0; $nLarge = 0
foreach ($kind in 'thumb', 'large') {
    $src = Join-Path $gallery $kind
    Get-ChildItem $src -Filter "$RenderPrefix*.webp" | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $stage $kind)
        if ($kind -eq 'thumb') { $script:nThumb++ } else { $script:nLarge++ }
    }
}
$payloadKind = if ($RenderPrefix) { 'delta' } else { 'full payload' }
Write-Host "      $nThumb thumb(s), $nLarge large render(s) in the $payloadKind"

Write-Host '[2/5] tarball'
if (Test-Path $tgz) { Remove-Item -Force $tgz -Confirm:$false }
tar -czf $tgz -C $stage .
if ($LASTEXITCODE -ne 0) { throw 'tar failed' }
$mb = [math]::Round((Get-Item $tgz).Length / 1MB, 1)
Write-Host "      $tgz  ($mb MB)"

Write-Host '[3/5] ship'
scp -q $tgz "${SshAlias}:/tmp/vg-deploy.tgz"
if ($LASTEXITCODE -ne 0) { throw 'scp failed' }

Write-Host '[4/5] extract on the box'
$resolvedRemoteDir = "$(ssh $SshAlias "cd $RemoteDir && pwd -P")".Trim()
$expectedRemoteDir = "$(ssh $SshAlias 'cd ~/valheim-gallery/public && pwd -P')".Trim()
if ($LASTEXITCODE -ne 0 -or -not $expectedRemoteDir -or $resolvedRemoteDir -ne $expectedRemoteDir) {
    throw "refusing to update unexpected remote path: $resolvedRemoteDir"
}
if ($ArchiveCurrentAs) {
    if ($ArchiveCurrentAs -notmatch '^[a-z0-9][a-z0-9._-]*$') {
        throw "unsafe archive slug: $ArchiveCurrentAs"
    }
    $archiveCommand = "set -eu; cd $RemoteDir; if [ ! -f '$ArchiveCurrentAs/index.json' ]; then mkdir -p '$ArchiveCurrentAs'; cp -a index.html index.json '$ArchiveCurrentAs/'; [ ! -f depth.json ] || cp -a depth.json '$ArchiveCurrentAs/'; [ ! -f judge.json ] || cp -a judge.json '$ArchiveCurrentAs/'; [ ! -d thumb ] || cp -al thumb '$ArchiveCurrentAs/'; [ ! -d large ] || cp -al large '$ArchiveCurrentAs/'; [ ! -d img ] || cp -al img '$ArchiveCurrentAs/'; echo archived; else echo kept; fi"
    $archiveResult = ssh $SshAlias $archiveCommand
    if ($LASTEXITCODE -ne 0) { throw 'remote gallery archive failed' }
    Write-Host "      previous gallery: $archiveResult ($ArchiveCurrentAs/)"
}
if ($RenderPrefix) {
    ssh $SshAlias "cd $RemoteDir && tar xzf /tmp/vg-deploy.tgz && rm /tmp/vg-deploy.tgz"
} else {
    ssh $SshAlias "cd $RemoteDir && rm -rf ./thumb ./large ./img && rm -f ./index.html ./index.json ./depth.json ./judge.json && tar xzf /tmp/vg-deploy.tgz && rm /tmp/vg-deploy.tgz"
}
if ($LASTEXITCODE -ne 0) { throw 'remote extract failed' }

Write-Host '[5/5] verify'
$remoteIndex = Join-Path $stage 'remote-index.json'
scp -q "${SshAlias}:$RemoteDir/index.json" $remoteIndex
if ($LASTEXITCODE -ne 0) { throw 'could not retrieve deployed index for verification' }
$remoteDoc = Get-Content -LiteralPath $remoteIndex -Raw | ConvertFrom-Json
$expectedDoc = Get-Content -LiteralPath (Join-Path $stage 'index.json') -Raw | ConvertFrom-Json
if ($remoteDoc.n -ne $expectedDoc.n -or $remoteDoc.world -ne $expectedDoc.world) {
    throw "deployed index identity mismatch: expected $($expectedDoc.world)/$($expectedDoc.n), got $($remoteDoc.world)/$($remoteDoc.n)"
}
$creatorLeaks = @($remoteDoc.images | Where-Object { $_.PSObject.Properties.Name -contains 'top_creator_id' }).Count
$coordinateLeaks = @($remoteDoc.images | Where-Object {
    $_.PSObject.Properties.Name -contains 'x' -or
    $_.PSObject.Properties.Name -contains 'y' -or
    $_.PSObject.Properties.Name -contains 'z'
}).Count
if ($creatorLeaks -ne 0) { throw 'deployed index.json still carries top_creator_id - scrub did not take' }
if ($coordinateLeaks -ne 0) { throw 'deployed index.json still carries coordinates - scrub did not take' }
Write-Host "      remote index reports $($remoteDoc.world), $($remoteDoc.n) images"
Write-Host '      scrub verified: no creator ids or coordinates in the deployed index'
Remove-Item -Force $tgz -Confirm:$false
Remove-Item -Recurse -Force $stage -Confirm:$false
Write-Host 'done - check the live gallery in a browser'
