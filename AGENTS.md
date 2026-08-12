# Baseline repository working notes

## Baseline is the fleet hub

Active implementation lives in the sovereign repositories named in
[`REPO-MAP.md`](REPO-MAP.md). Baseline owns durable decisions, evidence, public corpus
mirrors/projections, and discovery. Do not restore product code here or add a sibling
checkout path to make a build pass.

Cross-repository code uses exact published packages. DLLs, zips, generated pages, and
corpus sources cross by immutable revision or release tag with byte counts and SHA-256
verification.

## Landing work — one ask, not a relay race

“Go”, “push”, “land it”, “ship it”, or “merge it in” authorizes the whole remaining
chain for that work: commit, pull `--ff-only`, and push `main`. Direct commits to
`main` are normal for this R&D hub; do not create a feature branch or PR unless asked.

Stop and ask only for a force-push, history rewrite, deleting work you did not create,
or authority outside the requested scope. When a test or hook blocks an authorized
landing, fix the cause and retry. Never use `--no-verify`.

Before committing:

1. inspect `git status` and preserve unrelated changes;
2. stage and commit explicit pathspecs, never a blanket working tree;
3. run the relevant checks below;
4. pull `--ff-only`; and
5. push `origin main` without force.

## Hub verification

```powershell
python -m unittest discover -s tests -v
python tools\corpus\test_corpus.py
python tools\corpus\build.py --check
python -m unittest tests.test_entrypoint_links -v
git diff --check
```

There is no roadmap-journal ceremony in Baseline. The journal and its pre-commit hook
belong to `lumberjacks-platform`, the implementation program they describe.

## Corpus mirrors

`corpus/mirrors/lumberjacks/` is a read-only reconstruction input, not a second
authority. Refresh it only from a pushed 40-character `lumberjacks-platform` commit:

```powershell
python tools\corpus\sync_lumberjacks_mirror.py --revision <commit-sha>
python tools\corpus\sync_lumberjacks_mirror.py --check --revision <commit-sha>
python tools\corpus\build.py
python tools\corpus\build.py --check
```

Commit the two snapshots, provenance receipt, and regenerated projections together.
G8 must fail when a file, hash, byte count, upstream path, or revision is altered.

## Decision and evidence lifecycle

Open decisions belong in `DECISIONS-PENDING.md` only when at least two viable choices
have materially different consequences, an owner, and a deadline/trigger. Durable
rationale graduates to one canonical Project Decision under `docs/decisions/`.

Technical claims follow [PD-4](docs/decisions/pd-4-evidence-standard.md): label them
VERIFIED with reproducible output, INFERRED, BLOCKED with the missing prerequisite, or
UNVERIFIED. Historical evidence remains historical; do not imply that retaining a
receipt means its old deployment is live.

## Checkout roots and safe paths

`C:\work\baseline` is the Baseline root. Current product roots are
`C:\work\networksense`, `C:\work\lumberjacks-platform`, `C:\work\comfy-quest`,
`C:\work\sovereign-shards`, and `C:\work\isolate`. Retired pre-cutover checkouts are
not authorities.

Scripts derive paths from their own repository root (`$PSScriptRoot` in PowerShell)
or accept an explicit artifact path. Never encode `C:\work\...` into executable
defaults and never traverse into a sibling repository.

## i5 lane

The i5 laptop is a roaming peer and may be offline. Its owning deployment scripts now
live with the relevant product repository. Run one BatchMode link preflight; if it is
offline, report that state and stop. Never retry-loop or fall back to password auth.
