<#
.SYNOPSIS
    Publish the pinned Quest Picker page to the live /questpicker route on AM4.

.DESCRIPTION
    The lj-workbench container reads
    LUMBERJACKS_QUESTPICKER_HTML=/var/lib/lumberjacks/roadmap/quest-picker.html
    from a read-only bind of the host's /srv/lumberjacks/roadmap and re-reads it
    behind an mtime-and-length cache, so publishing is a file copy — no image
    build, no container restart. The route was deployed 2026-08-12
    (lumberjacks-gateway:m31-questpicker-20260812-r1, Caddy allowlist included);
    what this script moves is only the content.

    This script is the ONLY writer of quest-picker.html on the box. Until
    2026-08-17 the workbench asset publisher (lumberjacks-platform,
    tools/workbench/Publish-WorkbenchAssets.ps1) shipped the repo's SAMPLE page
    to the same path on every publish, which is how the live surface served
    "Sample Guild" while the real 314-quest page sat committed here. That lane
    no longer touches quest-picker.html; the image-baked sample remains only as
    the cold-start fallback when no file is mounted.

    Publish gate (fails closed): tools/questpicker/verify_picker_pin.py must
    pass, and the bytes shipped are demanded equal to the pin's recorded
    output.sha256 — remote-side before install, and live via the served
    X-QuestPicker-Sha256 header after. What stays forbidden is publishing bytes
    the pin cannot account for; regenerate the pin with the page, never around
    it (see data/README.md, "Refreshing the picker").

    Talks to the box only through the `am4` ssh alias (same convention as
    tools/selfie-stick/Publish-GalleryToAM4.ps1). /srv/lumberjacks/roadmap is
    root-owned, so the install step runs under sudo with the remote script
    base64-encoded and CRLF-normalized — the BOM/CRLF-proof pattern proven by
    the workbench publisher.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\questpicker\Publish-QuestPickerToAM4.ps1
#>
[CmdletBinding()]
param(
    [string] $SshAlias = 'am4',
    [string] $RemoteRoot = '/srv/lumberjacks/roadmap',
    [string] $PublicBaseUrl = 'https://am4.tail8e749c.ts.net'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pagePath = Join-Path $root 'data\processed\quest-picker.html'
$pinPath = Join-Path $root 'data\processed\quest-picker-pin.json'

if (-not (Test-Path $pagePath)) { throw "quest-picker.html missing at $pagePath" }
if (-not (Test-Path $pinPath)) { throw "quest-picker-pin.json missing at $pinPath - the pin is the publish authorization" }

Write-Host '[1/5] pin verification (attribution gate)'
Push-Location $root
try {
    & python tools/questpicker/verify_picker_pin.py
    if ($LASTEXITCODE -ne 0) { throw 'verify_picker_pin.py failed - the page or a catalog drifted from the pin; regenerate and re-pin before publishing' }
} finally { Pop-Location }

$pin = [System.IO.File]::ReadAllText($pinPath) | ConvertFrom-Json
$pageHash = (Get-FileHash -LiteralPath $pagePath -Algorithm SHA256).Hash.ToLowerInvariant()
$pageBytes = (Get-Item $pagePath).Length
if ($pageHash -ne $pin.output.sha256) {
    throw "page sha256 $pageHash does not equal the pin's recorded $($pin.output.sha256) - the verifier should have caught this; refusing to publish"
}
Write-Host "      $pageBytes bytes, sha256 $($pageHash.Substring(0,12))..., generator $($pin.generator.revision.Substring(0,8)) per pin"

$stamp = [guid]::NewGuid().ToString('N').Substring(0, 8)

Write-Host '[2/5] upload to /tmp'
& scp -q $pagePath "${SshAlias}:/tmp/questpicker-$stamp.html"
if ($LASTEXITCODE -ne 0) { throw 'scp failed' }

Write-Host '[3/5] hash-verify and install on the box'
$remoteScript = @'
set -euo pipefail
root="$1"; stamp="$2"; page_hash="$3"
actual="$(sha256sum "/tmp/questpicker-$stamp.html" | awk '{print $1}')"
test "$actual" = "$page_hash"
install -m 0644 "/tmp/questpicker-$stamp.html" "$root/quest-picker.html.tmp"
mv -f "$root/quest-picker.html.tmp" "$root/quest-picker.html"
rm -f "/tmp/questpicker-$stamp.html"
printf 'installed %s/quest-picker.html %s\n' "$root" "$page_hash"
'@
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes(($remoteScript -replace "`r`n", "`n")))
& ssh $SshAlias "echo $encoded | base64 -d | sudo bash -s -- '$RemoteRoot' '$stamp' '$pageHash'"
if ($LASTEXITCODE -ne 0) { throw 'remote install failed - nothing was moved into place unless the printed receipt says so' }

Write-Host '[4/5] live verification'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072
$resp = Invoke-WebRequest -UseBasicParsing -Uri "$PublicBaseUrl/questpicker"
$served = $null
foreach ($k in $resp.Headers.Keys) {
    if ($k -ieq 'X-QuestPicker-Sha256') { $served = "$($resp.Headers[$k])".ToLowerInvariant() }
}
if ($served -ne $pageHash) {
    throw "live X-QuestPicker-Sha256 is '$served', published $pageHash - the origin is not serving what was just installed"
}

Write-Host '[5/5] receipt'
[pscustomobject]@{
    questpicker_html_sha256 = $pageHash
    bytes                   = $pageBytes
    generator_revision      = $pin.generator.revision
    remote_path             = "$RemoteRoot/quest-picker.html"
    verified                = "live $PublicBaseUrl/questpicker serves the pinned bytes (X-QuestPicker-Sha256 match)"
}
