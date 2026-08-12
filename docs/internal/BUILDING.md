# Building and verifying the Baseline hub

Baseline no longer builds the mod, platform, Quest product, or MCP kernel. Those loops
live in the owning repositories listed in [REPO-MAP.md](../../REPO-MAP.md). A source
reference to a sibling checkout is a boundary failure, not a build shortcut.

## Local hub verification

From the Baseline root:

```powershell
python -m unittest discover -s tests -v
python tools\corpus\test_corpus.py
python tools\corpus\build.py --check
python -m unittest tests.test_entrypoint_links -v
git diff --check
```

The corpus check rebuilds every projection in memory and also verifies the immutable
Lumberjacks mirror’s repository, 40-character revision, upstream paths, raw URLs,
byte counts, and SHA-256 digests.

## Refreshing the platform mirror

Choose an already-pushed `lumberjacks-platform` commit, never a moving branch or tag:

```powershell
python tools\corpus\sync_lumberjacks_mirror.py --revision <40-character-sha>
python tools\corpus\sync_lumberjacks_mirror.py --check --revision <same-sha>
python tools\corpus\build.py
python tools\corpus\build.py --check
```

The sync command uses `GH_TOKEN`, `GITHUB_TOKEN`, or the authenticated `gh` client to
read the private upstream without printing credentials. Commit both mirrored files,
`provenance.json`, and regenerated projections together.

## Repository ceremony

Baseline has no roadmap-journal pre-commit ceremony. That hook and append-only journal
belong to `lumberjacks-platform`. Commit only intentional paths, pull with
`--ff-only` before pushing, and never force-push without explicit operator approval.

The split removes tracked product source with ordinary Git history. An older local
checkout may still contain ignored build/runtime residue such as `node_modules`,
FieldLab container state, MCP ledger state, or Companion `dist` output. Those bytes
are neither tracked nor authoritative and must never be used as a source fallback.
Removing local residue is a separate operator cleanup decision, not part of the
repository split commit.

Each product repository defines its own build/test/release commands in its `AGENTS.md`
and CI workflow. Cross-repository integration uses released packages or artifacts;
do not run a fleet build by traversing local checkouts.

## Windows encoding

Do not round-trip UTF-8 files through Windows PowerShell 5.1
`Get-Content | Set-Content`. Use a targeted patch or the repository’s generator so
Unicode and line endings remain stable.
