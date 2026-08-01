# Repository working notes

## Landing work — one ask, not a relay race (read before asking anything procedural)

**"Go" / "push" / "land it" / "ship it" / "good work, merge it in" authorizes the
whole remaining chain for that work — commit → push → open PR → merge into `main` —
in one pass.** Do not stop mid-chain to ask again at each step, and do not park the
last step as an offer in your closing summary ("not pushed — say the word"). That is
the same relay race with better manners: it still costs a turn.

Every one of those turns re-charges the operator for the entire conversation, at the
end of a session when it is largest. Four yeses for one intent is the most expensive
possible way to finish, and it lands the cost at the worst possible moment. One
instruction in, work on `main` out.

`main` here is an R&D trunk that already takes direct pushes from background roadmap
automation. Committing straight to it is normal; a feature-branch-and-PR plan is wrong
unless asked for. Treating a merge here with production-grade caution is miscalibrated
for what is actually here — Derek's correction, 2026-07-31, after a routine
spawned-task landing needed four separate yeses for one intent.

**Stop and ask only for:** force-push, history rewrite, deleting work you did not
create, or anything reaching outside this repo. Force-push is not a
production-vs-R&D judgment call — it can silently discard commits and rewrite history
someone else already pulled, which is a real risk in any repo.

**When a hook or rule blocks you, fix the cause and retry — do not hand the failure
back.** Hitting a rule is not a new question; it is part of the work you were already
told to finish. The four you will actually hit:

1. **Roadmap-note ceremony.** Touching `fieldlab/`, `network/`, or `infra/gcp/p7/`
   without a journal note fails `pre-commit`. Fix: run the note command below; it
   regenerates the HTML for you. Never `--no-verify`.
2. **`main` moves under you.** Background automation commits and pushes here. Pull
   before you start and again before you push; a rejected push usually just needs
   `git pull --ff-only`.
3. **Push protection on `origin`.** Realistic-looking credential *fixtures* are
   rejected even though the UI suggests scanning is off. Fix by rewriting the fixture,
   never by the allow-this-secret URL.
4. **`core.hooksPath` points at the main checkout.** Editing `.githooks/` from inside
   a worktree changes nothing for your commit; fix the script the hook calls instead.

The whole chain, when the ceremony applies:

```powershell
cd Lumberjacks; node scripts/roadmap.mjs note --milestone <M> --kind <kind> --summary "..." --impact "..." --verification "..."
cd ..; git add -A; git commit -F <message-file>; git pull --ff-only; git push origin main
```

In Claude sessions the `/land` skill runs this whole protocol — including the blocker
handling above — in one invocation. It is user-scoped, so it works from any repo.

Adopted 2026-07-31, **moved to the top of this file and expanded 2026-08-01**. The rule
already existed and the stall kept happening anyway, because it sat at line ~107 below
four other sections — a worker that reads far enough to find it has usually already
asked. Placement was the bug; the blocker list above is the other half, since the
authorization alone never covered "tried to merge, hit a rule, came back to ask."

**Unverified** (see [PD-4](docs/decisions/pd-4-evidence-standard.md)): this is proven
the first time a fresh worker session lands a change from a single "merge it in" with
no follow-up question. If you are that session and you still had to ask, the gap you
hit belongs in the list above — add it.

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

