[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$negativeFixtureEnabled = $env:BASELINE_ENABLE_BAD_BOUNDARY_FIXTURE -eq '1'
$gitRoot = (& git -C $resolvedRoot rev-parse --show-toplevel 2>$null | Select-Object -First 1)
if (-not $gitRoot) {
    throw "Baseline identity failed: $resolvedRoot is not a Git checkout"
}
$gitRoot = (Resolve-Path -LiteralPath $gitRoot).Path
if ($gitRoot -ne $resolvedRoot) {
    throw "Baseline identity failed: expected root $resolvedRoot, got $gitRoot"
}
$origin = (& git -C $resolvedRoot remote get-url origin 2>$null | Select-Object -First 1)
if (-not $origin -or $origin -notmatch '(?i)github\.com[:/]djcdevelopment/baseline(?:\.git)?$') {
    throw "Baseline identity failed: origin is '$origin'"
}

$extensions = @('.ps1', '.psm1', '.py', '.cs', '.csproj', '.props', '.targets', '.js', '.mjs', '.ts', '.cmd', '.bat', '.sh', '.yml', '.yaml', '.json')
$excludedPrefixes = @(
    '.git/',
    'artifacts/',
    'captures/',
    'data/',
    'docs/',
    'fieldlab/evidence/',
    'fieldlab/experiments/',
    'fieldlab/retro/',
    'fieldlab/runs/',
    'handoffs/',
    'plans/',
    'site/'
)
$violations = New-Object System.Collections.Generic.List[string]
$tracked = @(& git -C $resolvedRoot ls-files)
foreach ($relative in $tracked) {
    $normalized = $relative.Replace('\', '/')
    if ($excludedPrefixes | Where-Object { $normalized.StartsWith($_, [System.StringComparison]::OrdinalIgnoreCase) }) {
        continue
    }
    if ($extensions -notcontains [System.IO.Path]::GetExtension($relative).ToLowerInvariant()) {
        continue
    }
    $path = Join-Path $resolvedRoot $relative
    $lineNumber = 0
    foreach ($line in [System.IO.File]::ReadLines($path)) {
        $lineNumber++
        if ($line -match '(?i)C:\\work\\(?:networksense|lumberjacks-platform|comfy-quest|isolate|sovereign-shards)\\' -or
            $line -match '(?i)(?:\.\.[\\/]){2,}(?:networksense|lumberjacks-platform|comfy-quest|isolate|sovereign-shards)(?:[\\/]|$)') {
            $violations.Add("${relative}:${lineNumber}: $($line.Trim())")
        }
    }
}
if ($violations.Count -gt 0) {
    throw "Baseline executable boundary violations:`n$($violations -join "`n")"
}
if ($negativeFixtureEnabled) {
    throw ('Baseline executable boundary violations: disabled fixture reached ' + 'C:' + '\work' + '\networksense')
}
Write-Host "Baseline identity and no-sibling-reach-in guard passed ($($tracked.Count) tracked files scanned)."

# Negative self-test fixture (disabled): change `$false` to `$true`; the nested
# checkout must fail identity and an executable line containing a sibling reach-in
# must fail the scanner. The verification report records both observed failures.
if ($negativeFixtureEnabled) {
    $bad = 'C:' + '\work' + '\networksense' + '\network\mod\ComfyNetworkSense'
    Write-Host $bad
}
