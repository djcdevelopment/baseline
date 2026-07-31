# Repository working notes

## Decision lifecycle

Open decisions queue in `DECISIONS-PENDING.md` (root; fieldlab keeps its own).
**Registers are queues, not archives:** a resolved entry is one line + a link, and
rationale with lasting value graduates to a Project Decision doc under
[`docs/decisions/`](docs/decisions/README.md). **One decision, one home** — link the
canonical doc, never restate its rationale. Execution steps belong in
runbooks/checklists, plans in handoffs, blocked work in the backlog — not in the
registers. (Adopted 2026-07-29.)

Admit an item to a decision register only when it has at least two currently viable
alternatives with materially different consequences, a decision owner, and a named
deadline or trigger. If an existing policy already determines the answer, classify
the work instead of reopening the policy.

## Lumberjacks / Valheim roadmap journal

Any non-merge commit that changes the Lumberjacks cutover program under `fieldlab/`,
`network/`, or `infra/gcp/p7/` must be at least append the decision to the living roadmap, which is
generated into `Lumberjacks/src/Game.Gateway/Community/roadmap.html` from the
append-only journal at `Lumberjacks/docs/roadmap/`.

This is one repo and one commit. Append the note and stage the regenerated HTML in
the same commit as the change itself:

```powershell
cd Lumberjacks
node scripts/roadmap.mjs note --milestone <M> --kind <kind> --summary "..." --impact "..."
node scripts/roadmap.mjs check --staged
`

### This journal runs as background automation — plan around it

favor local loops for development and save GCP for production deploys.
I own 3 steam accounts with valhiem.  the server should run on AM4
player1 (wary.fool) runs on OMEN and player2 durracktu runs on i5

## Checkout roots

`C:\work\baseline` is the only working root. `C:\work\comfy` and `C:\work\lumberjacks`
are retired: they still exist on disk holding pre-cutover content, so a command aimed
at them succeeds quietly against stale code instead of failing. Scripts in this repo
derive their roots from `$PSScriptRoot`; keep it that way rather than reintroducing an
absolute default.

## i5 deploy lane (remote test client)

The i5 laptop is the second Valheim test client, reachable over the tailnet as
ssh alias `i5`. To ship it file updates (mod DLLs, configs, test bundles), use
[`tools/i5/`](tools/i5/README.md):

```powershell
tools\i5\Test-I5Link.ps1                                # preflight: is the lane up?
tools\i5\Deploy-ToI5.ps1 -Path <file-or-dir> [-Dest C:/deploy/baseline/...]
tools\i5\Deploy-ToI5.ps1 -Path <mod.dll> -ValheimPlugins  # straight into BepInEx plugins
```

Deploys are SHA256-verified on both ends; a green run is the receipt. The i5 is
a roaming laptop — **offline is a normal state**: report it and stop, never
retry-loop, and never fall back to password auth (everything runs BatchMode).

## Landing verified work — one ask, not a relay race

Once a change has passed build+test verification (this includes work landing
from a spawned/tick task), a single "go" / "push" / "land it" / "ship it"
authorizes the *whole* remaining chain for that piece of work — commit → push
→ open PR → merge into main — in one pass. Do not stop mid-chain to ask
again at each step; that turns one decision into three or four and defeats
the point of asking at all.

Why: Derek said it plainly on 2026-07-31 after a routine spawned-task landing
needed four separate yeses in a row for one intent — commit, push, open-PR,
merge. He then corrected the merge-to-main carve-out specifically: this is an
R&D repo where he's putting laps in and actively generating test data, not a
24/7 production system — treating a main-branch merge with production-grade
caution was miscalibrated for what's actually here. Main already carries its
own background roadmap automation pushing directly to it; a reviewed,
verified PR merge is comparatively mild next to that.

Still gate separately, every time: force-push. That one isn't a
production-vs-R&D judgment call — force-push can silently discard commits
and rewrite history someone else may have already pulled, which is a real
risk in any repo, R&D or not.
