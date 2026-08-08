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
      2. Renders ship as a delta by run-id prefix, because the old corpus is
         already on the box and re-shipping 200 MB for 50 is silly.

    Talks to the box only through the `am4` ssh alias — the tailnet hostname
    stays out of this public repo.

.EXAMPLE
    .\Publish-GalleryToAM4.ps1                          # delta: 20260808-* renders
    .\Publish-GalleryToAM4.ps1 -RenderPrefix ""         # full re-push of all renders
#>
[CmdletBinding()]
param(
    [string] $RenderPrefix = '20260808-',
    [string] $RemoteDir = '~/valheim-gallery/public',
    [string] $SshAlias = 'am4'
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$gallery = Join-Path $here 'out\gallery'
$stage = Join-Path $env:TEMP 'vg-stage'
$tgz = Join-Path $env:TEMP 'vg-deploy.tgz'

if (!(Test-Path (Join-Path $gallery 'index.json'))) { throw "no index.json in $gallery - run build_valheim_index.py first" }

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
Write-Host "      $nThumb thumb(s), $nLarge large render(s) in the delta"

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
ssh $SshAlias "cd $RemoteDir && tar xzf /tmp/vg-deploy.tgz && rm /tmp/vg-deploy.tgz"
if ($LASTEXITCODE -ne 0) { throw 'remote extract failed' }

Write-Host '[5/5] verify'
$remote = ssh $SshAlias "grep -o '\`"n\`": *[0-9]*' $RemoteDir/index.json | head -1"
$leak = ssh $SshAlias "grep -c 'top_creator_id' $RemoteDir/index.json || true"
Write-Host "      remote index reports  $remote"
if ("$leak".Trim() -ne '0') { throw "deployed index.json still carries top_creator_id - scrub did not take" }
Write-Host '      scrub verified: no creator ids in the deployed index'
Remove-Item -Force $tgz -Confirm:$false
Remove-Item -Recurse -Force $stage -Confirm:$false
Write-Host 'done - check the live gallery in a browser'
