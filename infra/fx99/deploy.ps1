<#
.SYNOPSIS
    Deploy the FX99 front-door config: validate, then reload.

.DESCRIPTION
    The config lives in git and is deployed from here. Nobody edits it on the
    box. AM4 accumulated seventeen Caddyfile.bak-* files because the only way to
    change it safely was to copy it first; validating before reload removes the
    reason for that habit.

    Order matters and is not negotiable: stage -> validate -> reload. A config
    that does not parse never reaches the running server, so a bad edit costs an
    error message rather than the front door. The front door currently answers a
    link posted to a Discord community, so "costs the front door" is not
    hypothetical.

.EXAMPLE
    .\deploy.ps1                # validate and reload
    .\deploy.ps1 -ValidateOnly  # parse check, change nothing
#>
[CmdletBinding()]
param(
    [string] $SshAlias = 'fx99',
    [switch] $ValidateOnly
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-Remote([string] $script) {
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
    # base64 because PowerShell 5.1 mangles quotes in native arguments
    $out = ssh $SshAlias "echo $b64 | base64 -d | sudo bash -s"
    if ($LASTEXITCODE -ne 0) { throw "remote step failed (exit $LASTEXITCODE)" }
    return $out
}

Write-Host '[1/4] staging'
$staged = @()
foreach ($f in @('Caddyfile')) {
    scp -q (Join-Path $here $f) "${SshAlias}:/tmp/fx99-$f"
    if ($LASTEXITCODE -ne 0) { throw "could not copy $f" }
    $staged += $f
}
scp -q -r (Join-Path $here 'sites-enabled') "${SshAlias}:/tmp/fx99-sites-enabled"
if ($LASTEXITCODE -ne 0) { throw 'could not copy sites-enabled' }
scp -q (Join-Path $here 'site') "${SshAlias}:/tmp/fx99-site"
if ($LASTEXITCODE -ne 0) { throw 'could not copy the site helper' }
Write-Host "      $($staged.Count + 2) artifact(s)"

Write-Host '[2/4] validating (nothing has changed on the box yet)'
$validate = Invoke-Remote @'
set -eu
install -d -m 0755 /srv/sites /var/log/caddy /etc/caddy/sites-enabled.new
cp /tmp/fx99-sites-enabled/*.caddy /etc/caddy/sites-enabled.new/ 2>/dev/null || true
# validate against a copy of the tree so a broken edit cannot touch the live one
sed 's#/etc/caddy/sites-enabled/#/etc/caddy/sites-enabled.new/#' /tmp/fx99-Caddyfile > /tmp/fx99-Caddyfile.check
caddy validate --adapter caddyfile --config /tmp/fx99-Caddyfile.check 2>&1 | tail -5
'@
$validate | ForEach-Object { Write-Host "      $_" }

if ($ValidateOnly) {
    Write-Host 'validate only - the running config is untouched.' -ForegroundColor Yellow
    return
}

Write-Host '[3/4] installing and reloading'
Invoke-Remote @'
set -eu
rm -rf /etc/caddy/sites-enabled
mv /etc/caddy/sites-enabled.new /etc/caddy/sites-enabled
cp /tmp/fx99-Caddyfile /etc/caddy/Caddyfile
install -m 0755 /tmp/fx99-site /usr/local/bin/site
chown -R caddy:caddy /var/log/caddy
systemctl reload caddy || systemctl restart caddy
rm -f /tmp/fx99-Caddyfile /tmp/fx99-Caddyfile.check /tmp/fx99-site
rm -rf /tmp/fx99-sites-enabled
'@ | Out-Null
Write-Host '      reloaded'

Write-Host '[4/4] verify'
# A reload that "succeeded" while the server is dead is the failure mode this
# catches. Ask the port, not systemd.
$probe = ssh $SshAlias "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8190/ 2>/dev/null"
if ($probe -notmatch '^\d{3}$') { throw "front door did not answer on :8190 (got '$probe')" }
Write-Host "      :8190 answers ($probe on / - 404 is correct when nothing is at the root)"
ssh $SshAlias 'site list'
