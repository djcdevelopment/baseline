# 04 - Publish and repin readiness report

Date: 2026-08-12

## Result

VERIFIED - Publication, repin, and release-consumer readiness is implemented and
pushed at these exact sovereign-repository revisions; this report does not claim
that any package or release was published:

```text
git -C C:\work\lumberjacks-platform rev-parse HEAD
d5128c03d1df5c2ab45adf042bcc7e8c48ad290b

git -C C:\work\comfy-quest rev-parse HEAD
a7043648fe171152f71c5af743a2b81a9f8eef02

git -C C:\work\networksense rev-parse HEAD
8d9ced6179569d9049af982bb47e41e2f8b56a19
```

VERIFIED - Hosted CI is green at all three readiness revisions:

```text
gh run list --repo djcdevelopment/lumberjacks-platform --limit 1 --json databaseId,headSha,status,conclusion,name,event
[{"conclusion":"success","databaseId":31586106534,"event":"push","headSha":"d5128c03d1df5c2ab45adf042bcc7e8c48ad290b","name":"ci","status":"completed"}]

gh run list --repo djcdevelopment/comfy-quest --limit 1 --json databaseId,headSha,status,conclusion,name,event
[{"conclusion":"success","databaseId":31579881772,"event":"push","headSha":"a7043648fe171152f71c5af743a2b81a9f8eef02","name":"ci","status":"completed"}]

gh run list --repo djcdevelopment/networksense --limit 1 --json databaseId,headSha,status,conclusion,name,event
[{"conclusion":"success","databaseId":31579060267,"event":"push","headSha":"8d9ced6179569d9049af982bb47e41e2f8b56a19","name":"ci","status":"completed"}]
```

## Ordered NuGet publication readiness

VERIFIED - Lumberjacks Platform carries `.github/workflows/publish-nuget.yml` for
the first `Comfy.Transport.Contracts` publication. The `nuget-v0.1.0` lane checks
the tag target and `origin/main` ancestry, requires `NUGET_API_KEY`, refuses an
already-present public version, packs with the full repository commit, validates
the exact ID/version/repository commit/dependency-free payload, pushes without
`--skip-duplicate`, polls NuGet.org, and validates the bytes served by NuGet.org.
The local rehearsal also executed its unexpected-payload negative:

```text
tools\nuget\Test-TransportNuGetReadiness.ps1 -DotNet C:\work\dotnet9\dotnet.exe
VERIFIED id=Comfy.Transport.Contracts version=0.1.0 commit=d5128c03d1df5c2ab45adf042bcc7e8c48ad290b entries=11
{"Schema":"lumberjacks-transport-nuget-readiness/v1","Package":"Comfy.Transport.Contracts.0.1.0.nupkg","RepositoryCommit":"d5128c03d1df5c2ab45adf042bcc7e8c48ad290b","PayloadTamperRejected":true,"BlindDuplicateSkip":false,"Verdict":"passed"}
```

VERIFIED - Comfy Quest carries `.github/workflows/publish-nuget.yml` with the
required dependency order: pack and strictly validate `Comfy.Quest.Contracts`,
push it, poll and validate its public bytes, restore Studio from the NuGet.org-only
configuration with Contracts pinned exactly to `[0.1.0]`, then pack, strictly
validate, push, poll, and validate `Comfy.Quest.Studio`. Its duplicate option is not
a blind success path: the workflow still downloads and validates the public package
ID, version, repository commit, dependencies, and complete payload before proceeding.

VERIFIED - Comfy Quest's committed pre-publication state remains explicit and
machine-checked:

```text
python tools\nuget\repin_public.py --check-interim
VERIFIED exact 0.1.0-local interim pins and local-first feed
```

VERIFIED - The package validators in both producer repositories reject undeclared
ZIP entries, unsafe paths, metadata drift, wrong repository identity or commit, and
wrong dependency constraints. The Transport rehearsal above executed its tamper
negative; Quest's ordered workflow uses `tools/nuget/validate_nupkg.py` both before
each push and after each public download.

## Exact public profiles and explicit interim profiles

VERIFIED - NetworkSense has a NuGet.org-only public configuration and exact public
contract properties `[0.1.0]`, while `nuget.interim.config` and
`eng/dependencies.interim.props` retain the explicit `0.1.0-local` rehearsal path.
Its hosted CI selects that path explicitly with
`-p:ComfyDependencyProfile=interim`; the public profile has not restored successfully
because the packages do not yet exist.

```text
rg -n "ComfyQuestContractsVersion|ComfyTransportContractsVersion" eng
eng\dependencies.public.props:3:    <ComfyQuestContractsVersion>[0.1.0]</ComfyQuestContractsVersion>
eng\dependencies.public.props:4:    <ComfyTransportContractsVersion>[0.1.0]</ComfyTransportContractsVersion>
eng\dependencies.interim.props:3:    <ComfyQuestContractsVersion>0.1.0-local</ComfyQuestContractsVersion>
eng\dependencies.interim.props:4:    <ComfyTransportContractsVersion>0.1.0-local</ComfyTransportContractsVersion>
```

VERIFIED - Lumberjacks Platform carries a coordinated public profile with exact
`[0.1.0]` Quest Contracts and Studio pins plus a NuGet.org-only source, alongside an
explicit interim profile with exact `[0.1.0-local]` pins and `packages-local`. The
transaction includes the Companion.Tests Studio `ProjectReference` to
`PackageReference` conversion and restores original bytes if a write fails. Both
profiles and that conversion passed in a temporary fixture; the live tree still
matches interim:

```text
tools\dependencies\Set-DependencyProfile.ps1 -Profile interim -Check
{
    "Schema":  "lumberjacks-dependency-repin/v1",
    "Profile":  "interim",
    "ChangedFiles":  [],
    "Check":  true,
    "Verdict":  "passed"
}

tools\dependencies\Test-DependencyProfiles.ps1
{"Schema":"lumberjacks-dependency-profile-test/v1","Profiles":["public","interim"],"ProjectReferenceConversion":"passed","Verdict":"passed"}
```

VERIFIED - Comfy Quest's `repin_public.py --apply --version 0.1.0` is prepared as a
single guarded transaction: it downloads and strictly validates both public
packages before changing producer versions, changes every public consumer constraint
to exact `[0.1.0]`, switches to NuGet.org only, and removes only the allowlisted
interim package files. That apply command was deliberately not run.

VERIFIED - The interim packages remain present rather than being deleted before
publication. A direct inventory returned three nupkgs in Platform, two in Quest, and
three in NetworkSense:

```text
C:\work\lumberjacks-platform interim_nupkgs=3 names=[Comfy.Quest.Contracts.0.1.0-local.nupkg,Comfy.Quest.Studio.0.1.0-local.nupkg,Comfy.Transport.Contracts.0.1.0-local.nupkg]
C:\work\comfy-quest interim_nupkgs=2 names=[Comfy.Quest.Contracts.0.1.0-local.nupkg,Comfy.Quest.Studio.0.1.0-local.nupkg]
C:\work\networksense interim_nupkgs=3 names=[Comfy.Quest.Contracts.0.1.0-local.nupkg,Comfy.Quest.Studio.0.1.0-local.nupkg,Comfy.Transport.Contracts.0.1.0-local.nupkg]
```

## Local release candidates and consumer proofs

VERIFIED - The retained NetworkSense candidate is a local split-proof bundle, not a
GitHub release. The pure Platform consumer verifier accepted its manifest-v1 bundle
without SSH, Docker, source lookup, build, deployment, or network access:

```text
infra\gcp\p7\scripts\Test-ModReleaseArtifact.ps1 `
  -ArtifactDirectory C:\work\networksense\artifacts\releases\mod-v0.5.80-split-proof `
  -ExpectedTag mod-v0.5.80-split-proof `
  -ExpectedSourceRevision 8d9ced6179569d9049af982bb47e41e2f8b56a19 `
  -ExpectedReleaseId m7-c10b-20260807-r42 `
  -ExpectedDependencyProfile interim

Schema            : lumberjacks-mod-release-artifact-verification/v1
Repository        : djcdevelopment/networksense
Tag               : mod-v0.5.80-split-proof
SourceRevision    : 8d9ced6179569d9049af982bb47e41e2f8b56a19
ReleaseId         : m7-c10b-20260807-r42
Version           : 0.5.80
DependencyProfile : interim
Sha256            : 6d07d0756c7d928113ec4f0b10e83c73a2f4e6f8119cc4d2f6dfa66c7dbfdc24
Bytes             : 940544
AssemblyName      : ComfyNetworkSense
AssemblyVersion   : 0.5.80.0
FileVersion       : 0.5.80
Verdict           : passed
```

VERIFIED - Platform's independent G6 fixture appended one byte to the same producer
contract and required rejection:

```text
tools\Test-ArtifactHashGate.ps1
{"Schema":"lumberjacks-boundary-guard/v2","Guard":"G6","PositiveFixture":"synthetic comfy-mod-release-manifest/v1 bundle","NegativeFixture":"same bundle with one byte appended to ComfyNetworkSense.dll","ArtifactSha256":"b9d5c9e9c95ea8f1366c0171483738541be93acd3c67920f1d80a4658763c7c0","TamperExecuted":true,"TamperRejected":true,"VerifierPure":true,"Verdict":"passed"}
```

VERIFIED - The retained Comfy Quest candidate is also local only. Its producer
verifier accepted the four declared assets and its self-test rejected both a hash
tamper and standalone/ZIP drift:

```text
python tools\release\verify_quest_release.py --release-dir artifacts\releases\a704364 --expected-tag quest-v0.2.0-split-proof --expected-questlab docs\generated\questlab.html --expected-revision a7043648fe171152f71c5af743a2b81a9f8eef02
VERIFIED tag=quest-v0.2.0-split-proof version=0.2.0 revision=a7043648fe171152f71c5af743a2b81a9f8eef02 release_id=questlab-v0.2.0-20260809-r24 assets=4

python tools\release\verify_quest_release.py --self-test
PASS: hash tamper was rejected
PASS: standalone/ZIP drift was rejected after hashes were updated
SELFTEST PASS: valid, tampered, and drifted release cases behaved correctly
```

VERIFIED - Platform's Quest consumer importer passed a four-asset positive fixture,
deterministic pin/vendor/catalog check, manifest-hash negative, staged-ZIP negative,
source-asset negative, and extra-asset negative. Its live lock remains explicitly
`state: unpinned`, with null tag, revision, and manifest hash:

```text
tools\workbench\Test-QuestReleaseImporter.ps1
{
    "schema":  "lumberjacks-quest-release-import-test/v1",
    "verdict":  "passed",
    "checks":  [
                   "PowerShell 5 string and PowerShell 7 DateTime timestamps: passed",
                   "valid four-asset release: passed",
                   "pin, vendor, catalog update, deterministic check: passed",
                   "expected manifest hash mismatch: rejected",
                   "staged ZIP tamper: rejected",
                   "source asset tamper: rejected",
                   "extra release asset: rejected",
                   "unpinned state makes no live-release claim: passed"
               ]
}
```

## Publication blockers and commitment point

BLOCKED - NuGet.org does not currently serve any of the three intended IDs. A fresh
flat-container query returned:

```text
$ids = @('Comfy.Transport.Contracts','Comfy.Quest.Contracts','Comfy.Quest.Studio')
foreach ($id in $ids) {
  $uri = 'https://api.nuget.org/v3-flatcontainer/' + $id.ToLowerInvariant() + '/index.json'
  try { $response = Invoke-WebRequest -Uri $uri -UseBasicParsing; Write-Output ($id + ' HTTP ' + [int]$response.StatusCode) }
  catch { Write-Output ($id + ' HTTP ' + [int]$_.Exception.Response.StatusCode) }
}

Comfy.Transport.Contracts HTTP 404
Comfy.Quest.Contracts HTTP 404
Comfy.Quest.Studio HTTP 404
```

BLOCKED - Publication authority is absent. `NUGET_API_KEY` is not present in the
local process, all three repositories report an empty repository-secret list, and
all three report zero GitHub environments; therefore the workflows' required
`nuget-production` environment and secret do not exist:

```text
Write-Output ('NUGET_API_KEY_ENV=' + [bool](Test-Path Env:NUGET_API_KEY))
NUGET_API_KEY_ENV=False

foreach ($repo in @('djcdevelopment/lumberjacks-platform','djcdevelopment/comfy-quest','djcdevelopment/networksense')) {
  $secrets = @(gh secret list --repo $repo --json name --jq '.[].name')
  $environmentResult = gh api "repos/$repo/environments" | ConvertFrom-Json
  Write-Output ($repo + ' repo_secrets=[' + ($secrets -join ',') + '] environments=[' + (($environmentResult.environments.name) -join ',') + '] total_count=' + $environmentResult.total_count)
}

djcdevelopment/lumberjacks-platform repo_secrets=[] environments=[] total_count=0
djcdevelopment/comfy-quest repo_secrets=[] environments=[] total_count=0
djcdevelopment/networksense repo_secrets=[] environments=[] total_count=0
```

VERIFIED - No remote tag or GitHub Release was created in any of the three
repositories. Read-only remote/API checks returned:

```text
foreach ($checkout in @('C:\work\lumberjacks-platform','C:\work\comfy-quest','C:\work\networksense')) {
  $origin = git -C $checkout remote get-url origin
  $tagRefs = @(git -C $checkout ls-remote --tags origin)
  $repository = $origin -replace '^https://github.com/','' -replace '\.git$',''
  $releaseCount = gh api "repos/$repository/releases?per_page=100" --jq length
  Write-Output ($origin + ' remote_tag_refs=' + $tagRefs.Count + ' releases=' + $releaseCount)
}

https://github.com/djcdevelopment/lumberjacks-platform.git remote_tag_refs=0 releases=0
https://github.com/djcdevelopment/comfy-quest.git remote_tag_refs=0 releases=0
https://github.com/djcdevelopment/networksense.git remote_tag_refs=0 releases=0
```

BLOCKED - The public repin, deletion of vendored interim packages, release tagging,
and rollback transition all require successfully published and re-downloaded public
bytes. Those prerequisites are absent, so none of those state changes was made and
the public-package commitment point has not been crossed.

INFERRED - Until the three immutable public packages are published and pass their
consumer restores, rollback remains a return to the explicit interim boundary (or
the sealed Baseline source), not an exact public-version repin. After that proof, a
separate coordinated transaction may change rollback to exact version repinning.

VERIFIED - No publication receipt, tag, release, live Quest lock, or public restore
has been fabricated from the local candidates. They are readiness and compatibility
evidence only.
