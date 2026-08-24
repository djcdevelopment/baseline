<#
.SYNOPSIS
    Publish the interactive gallery to the /valheim/ route on the front door.

.DESCRIPTION
    The front door is FX99: /srv/sites/valheim, served at /valheim/ by the
    directory convention in infra/fx99 (NOT the funnel-demo lane). It moved off AM4
    on 2026-08-24 because AM4 is on wifi and measured 0.56 MB/s against FX99's 14,
    and because AM4 was at 95% disk. Previous pushes were hand-rolled tarballs;
    this script is that same lane with two things made unforgettable:

      1. The shipped index.json is SCRUBBED (scrub_index.py drops x/y/z and
         top_creator_id) — the local copy keeps full fidelity, the public copy
         does not carry build coordinates or creator ids.
      2. A full push replaces the active render directories so assets from a
         previous era cannot linger. A run-prefix delta remains available for
         updates to the same gallery, but cannot be combined with era archival.

    Talks to the box only through an ssh alias — the tailnet hostname stays out of
    this public repo.

.EXAMPLE
    .\Publish-Gallery.ps1                          # full replacement
    .\Publish-Gallery.ps1 -RenderPrefix 20260808-  # same-gallery delta
    .\Publish-Gallery.ps1 -GalleryPath .\out\era17\gallery -ArchiveCurrentAs era16
#>
[CmdletBinding()]
param(
    [string] $RenderPrefix = '',
    [string] $GalleryPath = '',
    [string] $ArchiveCurrentAs = '',
    [string] $EraSlug = '',
    [switch] $SiblingErasOnly,
    [string] $RoutePath = '/valheim/',
    [string] $RemoteDir = '/srv/sites/valheim',
    [string] $SshAlias = 'fx99',
    [int]    $HttpPort = 8190
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

# Each era is a complete standalone copy of the page at its own path, so until
# now nothing linked them and the archive was reachable only by typing its URL.
# eras.json gives the page the list; hrefs are absolute under the route because
# the root and an archived era sit at different depths. Optional on the page --
# a deploy without it just shows no era chips.
$eraManifest = $null
if ($EraSlug) {
    if ($EraSlug -notmatch '^[a-z0-9][a-z0-9._-]*$') { throw "unsafe era slug: $EraSlug" }
    $known = @()
    # slug|world for every index.json already on the box -- the archived eras,
    # and "." for the gallery currently at the root. Lets a chip read
    # "ComfyEra16" rather than the directory name; eras written before the
    # --world flag existed have no world key and keep their slug.
    #
    # Delivered base64 because PowerShell 5.1 re-parses a native command's
    # arguments and eats the embedded quotes: passed literally, grep received a
    # bare [^"]* and failed with "Unmatched [".
    $probeScript = @'
cd REMOTEDIR 2>/dev/null || exit 0
for f in index.json */index.json; do
  [ -f "$f" ] || continue
  w=$(grep -o '"world"[[:space:]]*:[[:space:]]*"[^"]*"' "$f" | head -1 |
      sed 's/.*"world"[[:space:]]*:[[:space:]]*"//; s/"$//')
  echo "$(dirname "$f")|$w"
done
'@
    $probeScript = $probeScript.Replace('REMOTEDIR', $RemoteDir)
    $probe = 'echo ' +
             [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($probeScript)) +
             ' | base64 -d | sh'
    $labels = @{}
    $outgoingWorld = ''
    foreach ($line in @(ssh $SshAlias $probe)) {
        $parts = ([string]$line).Trim() -split '\|', 2
        $slug = $parts[0]
        $world = if ($parts.Count -gt 1) { $parts[1] } else { '' }
        if (-not $slug) { continue }
        if ($slug -eq '.') { $outgoingWorld = $world; continue }
        if ($slug -eq $EraSlug -or $known -contains $slug) { continue }
        $known += $slug
        if ($world) { $labels[$slug] = $world }
    }
    # The era being archived this run is not on the box under that name yet; its
    # label is the world that is at the root right now.
    if ($ArchiveCurrentAs -and $known -notcontains $ArchiveCurrentAs) {
        $known += $ArchiveCurrentAs
        if ($outgoingWorld) { $labels[$ArchiveCurrentAs] = $outgoingWorld }
    }
    $labelSource = if ($SiblingErasOnly) { Join-Path $gallery 'index.json' }
                   else { Join-Path $stage 'index.json' }
    $label = (Get-Content -LiteralPath $labelSource -Raw | ConvertFrom-Json).world
    if (-not $label) { $label = $EraSlug }
    $entries = @([ordered]@{ slug = $EraSlug; label = $label; href = $RoutePath })
    foreach ($slug in ($known | Sort-Object -Descending)) {
        $entries += [ordered]@{ slug = $slug
                                label = $(if ($labels[$slug]) { $labels[$slug] } else { $slug })
                                href = "$RoutePath$slug/" }
    }
    $eraManifest = [ordered]@{ current = $EraSlug; eras = $entries }
    $eraManifest | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $stage 'eras.json') -Encoding utf8
    Write-Host ("      eras.json: $EraSlug is current, siblings " +
                $(if ($known) { $known -join ', ' } else { 'none' }))

    # An archived era is a whole page at its own path, so the chips only work
    # both ways if each sibling also gets a manifest naming ITSELF current, and
    # a copy of the page that reads one. Its own index.json and renders are
    # never touched. Idempotent; ships no images.
    $syncLines = @('set -eu', "cd $RemoteDir")
    foreach ($slug in @($EraSlug) + @($known)) {
        $doc = [ordered]@{ current = $slug; eras = $entries }
        $b64 = [Convert]::ToBase64String(
            [Text.Encoding]::UTF8.GetBytes(($doc | ConvertTo-Json -Depth 5 -Compress)))
        if ($slug -eq $EraSlug) {
            $syncLines += "echo $b64 | base64 -d > eras.json"
        } else {
            # guarded with if/fi, not `continue`: this is a flat script, and
            # `continue` outside a loop aborts it under set -e
            $syncLines += "if [ -d '$slug' ]; then"
            $syncLines += "  echo $b64 | base64 -d > '$slug/eras.json'"
            $syncLines += "  cp -a index.html '$slug/index.html'"
            $syncLines += "fi"
        }
    }
    $eraSyncScript = ($syncLines -join "`n") + "`n"
}

if ($SiblingErasOnly) {
    if (-not $EraSlug) { throw '-SiblingErasOnly needs -EraSlug' }
    Write-Host '[chips] refreshing era manifests on the box (no renders shipped)'
    ssh $SshAlias ("echo " +
        [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($eraSyncScript)) +
        ' | base64 -d | sh')
    if ($LASTEXITCODE -ne 0) { throw 'era chip sync failed' }
    Write-Host '      done'
    return
}

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
# A full push replaces the render directories, so pointing this at the wrong
# path deletes someone's data. The guard used to compare against a hardcoded
# ~/valheim-gallery/public, which stopped meaning anything when the front door
# moved to FX99. What actually matters is not the host's layout: the target must
# be an absolute path, not a root or a home directory, and must either be empty
# or already be a gallery. Anything else is a typo.
$resolvedRemoteDir = "$(ssh $SshAlias "cd $RemoteDir && pwd -P")".Trim()
if ($LASTEXITCODE -ne 0 -or -not $resolvedRemoteDir) {
    throw "could not resolve remote path $RemoteDir on $SshAlias"
}
if ($resolvedRemoteDir -notmatch '^/' -or
    ($resolvedRemoteDir -split '/' | Where-Object { $_ }).Count -lt 2) {
    throw "refusing to publish to a top-level path: $resolvedRemoteDir"
}
# Single-quoted here-string with a placeholder, same as the era probe above.
# A double-quoted string would let PowerShell evaluate $( ) locally before ssh
# ever sees it, and the failure is a Get-ChildItem parameter error that says
# nothing about what went wrong.
$galleryProbe = @'
cd 'REMOTEDIR' || exit 1
# a current render
[ -f index.json ] && exit 0
[ -f index.html ] && exit 0
# a gallery root holding only archived eras -- what a fresh migration looks like
# before its first publish, and a real state rather than a typo
for d in */; do [ -f "$d/index.json" ] && exit 0; done
# genuinely empty
[ -z "$(ls -A .)" ] && exit 0
exit 1
'@
$galleryProbe = $galleryProbe.Replace('REMOTEDIR', $resolvedRemoteDir)
$probeB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($galleryProbe))
ssh $SshAlias "echo $probeB64 | base64 -d | sh" | Out-Null
$looksLikeGallery = if ($LASTEXITCODE -eq 0) { 'ok' } else { 'no' }
if ("$looksLikeGallery".Trim() -ne 'ok') {
    throw ("refusing to replace $resolvedRemoteDir - it is neither empty nor an " +
           'existing gallery. Check -RemoteDir and -SshAlias.')
}
if ($ArchiveCurrentAs) {
    if ($ArchiveCurrentAs -notmatch '^[a-z0-9][a-z0-9._-]*$') {
        throw "unsafe archive slug: $ArchiveCurrentAs"
    }
    $archiveCommand = "set -eu; cd $RemoteDir; if [ ! -f '$ArchiveCurrentAs/index.json' ]; then mkdir -p '$ArchiveCurrentAs'; cp -a index.html index.json '$ArchiveCurrentAs/'; [ ! -f depth.json ] || cp -a depth.json '$ArchiveCurrentAs/'; [ ! -f judge.json ] || cp -a judge.json '$ArchiveCurrentAs/'; [ ! -d thumb ] || cp -al thumb '$ArchiveCurrentAs/'; [ ! -d large ] || cp -al large '$ArchiveCurrentAs/'; [ ! -d img ] || cp -al img '$ArchiveCurrentAs/'; echo archived; else echo kept; fi"
    $archiveResult = ssh $SshAlias $archiveCommand
    if ($LASTEXITCODE -ne 0) { throw 'remote gallery archive failed' }
    Write-Host "      previous gallery: $archiveResult ($ArchiveCurrentAs/)"
    if ($eraManifest) {
        # Same list, but the archived era is the one marked current, and it needs
        # the newer index.html to have the chips at all.
        $archived = [ordered]@{ current = $ArchiveCurrentAs; eras = $eraManifest.eras }
        $archivedJson = ($archived | ConvertTo-Json -Depth 5 -Compress)
        $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($archivedJson))
        ssh $SshAlias "set -eu; cd $RemoteDir/'$ArchiveCurrentAs'; printf '%s' '$b64' | base64 -d > eras.json"
        if ($LASTEXITCODE -ne 0) { throw 'writing the archived era manifest failed' }
    }
}
if ($RenderPrefix) {
    ssh $SshAlias "cd $RemoteDir && tar xzf /tmp/vg-deploy.tgz && rm /tmp/vg-deploy.tgz"
} else {
    ssh $SshAlias "cd $RemoteDir && rm -rf ./thumb ./large ./img && rm -f ./index.html ./index.json ./depth.json ./judge.json ./eras.json && tar xzf /tmp/vg-deploy.tgz && rm /tmp/vg-deploy.tgz"
}
if ($LASTEXITCODE -ne 0) { throw 'remote extract failed' }
if ($eraSyncScript) {
    ssh $SshAlias ("echo " +
        [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($eraSyncScript)) +
        ' | base64 -d | sh')
    if ($LASTEXITCODE -ne 0) { throw 'era chip sync failed' }
    Write-Host '      era chips synced across every published era'
}
if ($ArchiveCurrentAs -and $eraManifest) {
    # The archived copy was taken from the OUTGOING deploy, so its index.html
    # predates the era chips. Give it the page just uploaded; its own index.json
    # and renders are untouched.
    ssh $SshAlias "set -eu; cd $RemoteDir; cp -a index.html '$ArchiveCurrentAs/index.html'"
    if ($LASTEXITCODE -ne 0) { throw 'refreshing the archived era page failed' }
}

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

# Everything above checked the FILE. None of it checks that anything SERVES the
# file, so all of it passes green against a stopped web server -- which is how a
# publish can report success while the route 404s. Ask the route.
#
# base64 again: the quoting in a curl-plus-python one-liner does not survive
# PowerShell's native-argument handling, and the failure is a bash syntax error
# that says nothing about the deploy.
$routeCheck = @'
S=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:PORTROUTE")
N=$(curl -s "http://127.0.0.1:PORTROUTEindex.json" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['images']))" 2>/dev/null)
echo "$S ${N:-0}"
'@
$routeCheck = $routeCheck.Replace('PORT', "$HttpPort").Replace('ROUTE', $RoutePath)
$checkB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($routeCheck))
$routeResult = "$(ssh $SshAlias "echo $checkB64 | base64 -d | sh")".Trim() -split '[\s]+'
if ($routeResult[0] -ne '200') {
    throw ("the files deployed but $RoutePath does not serve them " +
           "(HTTP '$($routeResult[0])' on ${SshAlias}:$HttpPort). " +
           'The web server is the thing to look at, not the payload.')
}
if ($routeResult[1] -ne "$($expectedDoc.n)") {
    throw ("$RoutePath serves $($routeResult[1]) images but the payload has " +
           "$($expectedDoc.n) -- the route is pointed somewhere stale.")
}
Write-Host "      route verified: $RoutePath answers 200 with $($routeResult[1]) images"

Remove-Item -Force $tgz -Confirm:$false
Remove-Item -Recurse -Force $stage -Confirm:$false
Write-Host 'done - check the live gallery in a browser'
