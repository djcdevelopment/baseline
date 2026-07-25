<#
.SYNOPSIS
Prove the two-client motion-phase bundle adapter without live Valheim clients.
#>
[CmdletBinding()]
param(
    [string] $OutputDirectory = 'captures/cre-e06-bundle-adapter-fixtures'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
if (-not [IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory = Join-Path $repoRoot $OutputDirectory
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$samplesPath = Join-Path $PSScriptRoot 'fixtures\samples.jsonl'
$bundlePath = Join-Path $OutputDirectory 'cre-e06-fixture.zip'
$adapterScript = Join-Path $repoRoot 'fieldlab\scripts\Summarize-TwoClientMotionPhaseBundles.ps1'
Compress-Archive -LiteralPath $samplesPath -DestinationPath $bundlePath -Force

function Invoke-Adapter {
    param(
        [Parameter(Mandatory = $true)][string] $Name,
        [switch] $OmitI5
    )

    $caseRoot = Join-Path $OutputDirectory $Name
    $receiptPath = Join-Path $caseRoot 'receipt.json'
    $arguments = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $adapterScript,
        '-OmenBundlePath', $bundlePath,
        '-OutputDirectory', $caseRoot,
        '-OutputJson', $receiptPath
    )
    if (-not $OmitI5) {
        $arguments += @('-I5BundlePath', $bundlePath)
    }
    $processOutput = (& powershell.exe @arguments 2>&1 | Out-String).Trim()
    $exitCode = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
        throw "$Name did not write a receipt (exit=$exitCode): $processOutput"
    }
    [ordered]@{
        exit_code = $exitCode
        receipt_path = $receiptPath
        receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    }
}

$success = Invoke-Adapter -Name 'success'
$missingI5 = Invoke-Adapter -Name 'missing-i5' -OmitI5

$checks = [ordered]@{
    success_exit_zero = ($success.exit_code -eq 0)
    success_ready = ($success.receipt.ready -eq $true)
    success_both_machines = ($success.receipt.machines.omen.ok -eq $true -and $success.receipt.machines.i5.ok -eq $true)
    success_fixture_received = (
        [int64]$success.receipt.machines.omen.summary.derived.received_samples -eq 40 -and
        [int64]$success.receipt.machines.i5.summary.derived.received_samples -eq 40
    )
    missing_i5_exit_one = ($missingI5.exit_code -eq 1)
    missing_i5_not_ready = ($missingI5.receipt.ready -eq $false)
    missing_i5_reason = ($missingI5.receipt.machines.i5.error -eq 'capture_bundle_missing')
}
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
$result = [ordered]@{
    schema_version = 1
    event_type = 'motion_phase.bundle_adapter_fixture_result'
    generated_utc = [DateTimeOffset]::UtcNow.ToString('o')
    verdict = if ($failed.Count -eq 0) { 'motion_phase_bundle_adapter_fixtures_passed' } else { 'motion_phase_bundle_adapter_fixtures_failed' }
    checks = $checks
    success_receipt = $success.receipt_path
    missing_i5_receipt = $missingI5.receipt_path
}
$resultPath = Join-Path $OutputDirectory 'summary.json'
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding utf8
$result | ConvertTo-Json -Depth 6
if ($failed.Count -gt 0) { exit 1 }
