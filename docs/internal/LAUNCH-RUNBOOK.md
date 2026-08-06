# Launch runbook — operator

**What this is:** the operator's working page for taking Baseline's tools to a community.
What is proven, what still needs testing, what to fall back to, what installing actually
involves, what to say, and where the friction is.

**Who it is for:** whoever is operating this. Today that is one person. It assumes you can
read the repo but not that you were in the room for any of it.

**State as of 2026-08-06.** Everything below was checked against the live system on that
date, not recalled. Where something is inferred it says so. If you are reading this much
later, re-check §1 before trusting §3.

### The one distinction that governs everything here

Two different launches get confused constantly, and separating them is the whole decision:

- **The tools** — a catalog of things people download and run on their own machine.
  **Open.** Verified end to end through the public wire.
- **The world** — joining the modded Valheim server and playing. **Not open**, by decision,
  and the roadmap's own register says `platform_readiness: "not_ready"` with nine `no_go`
  entries, two labelled stop-ship.

Nothing in this runbook proposes moving that line. The announcement already draws it.

### Terms, if you are new

Full list in [`GLOSSARY.md`](GLOSSARY.md); these are the ones this page leans on.

| Term | Short version |
|---|---|
| **AM4** | The box hosting the public surface. `am4.tail8e749c.ts.net` is a **Tailscale Funnel** — genuinely public, not tailnet-only. Carries HTTP; not Valheim's UDP. |
| **P7** | The GCP VM (`comfy-lumberjacks-p7`). **Terminated since 2026-07-25.** `comfy-p7.duckdns.org` resolves to nothing running. |
| **The Gateway** | The Lumberjacks service that owns sessions, admission, enrollment and world-state delivery. |
| **Cutover mode** | Which stack owns world state. `native` = vanilla Valheim sync with telemetry still on. |
| **C-gates** | Numbered acceptance gates for the netcode cutover. C0–C8 + C10a done on AM4; **C10b never green**. |
| **r42** | The Gateway session-plane fix cut landed 2026-08-05 (`b206c31`). Unit-tested only, never deployed. |
| **Enrollment lane vs. harness lane** | Two different paths world data can take. Every proof ran the **harness** lane; every real player runs the **enrollment** lane, which has never been exercised on P7. That mismatch is [ADR 0017](../../fieldlab/docs/adr/0017-prove-the-lane-users-ship-on.md). |

---

## 1. What we know works

Re-verified 2026-08-06.

| Thing | Evidence |
|---|---|
| The public Workbench | `workbench-verify-live --post-publish` → **71 checks, 0 failed**. Receipt: `captures/workbench-verify-live.json` |
| Served page = committed render | live sha256 `346259b9…`, byte-identical to the local artifact |
| Downloads survive the wire | both zips stream with matching size, digest, and `X-Download-Sha256` |
| Public reachability | resolves on public DNS (8.8.8.8 → 208.111.35.209); `/workbench`, `/community`, `/roadmap`, `/networksense`, `/events`, `/testing`, `/health` all 200 |
| Discord | invite resolves, correct guild, non-expiring; 7 threads + 9 task links live |
| Access control | `/ops` 403s, `/gallery` 401s, both unauthenticated. Correct |
| Netcode C0–C8, C10a | complete on AM4 with falsifier receipts — 12,339 server calls zero drops, poison blocked 76/76 |
| Durable journal replay (C3) | re-proved on P7 2026-08-03, 1,643 objects before and after |
| M0 frozen release | published, byte-verified |
| Tests | 619 C# test attributes, 29 generator tests, green |
| A modded server is up | `Comfy Era16 Lab`, world `ComfyEra16`, 3 days uptime, telemetry reporting |

**Say the second half of this out loud, every time:** the golden proof is 83,220 of 83,220
eligible ZDO revisions with zero native — and it is **one client, one window, 2026-07-16**.
It is not a claim about Valheim networking in general. The roadmap says so itself.

---

## 2. What we want to test again

### Free — no cloud spend, runnable this week

| | Test | Done when |
|---|---|---|
| ☐ | **Wedge repro on AM4.** Reproduce the candidate-8/11 livelock with `zdoJournalApplyThrottleMs` (`network/mod/ComfyNetworkSense/Config/PluginConfig.cs:114`), then show r42 breaks it | the stall reproduces on demand *before* the fix and not *after* |
| ☐ | **Cold-machine tool install.** One published zip, a machine that has never seen this project, only the one-pager as a guide | a stranger's path works, or you know exactly where it doesn't. Closes `no_go` #6 |
| ☐ | **C9 motion verdict on the Lumberjacks lane** | you have watched the *Lumberjacks* path. The `smooth` verdict banked 08-05 was on vanilla native sync, so the real one is still open |

### Needs a window, and a decision first

| | Test | Blocked on |
|---|---|---|
| ☐ | **Enrollment lane on P7** — the ADR 0017 gate | tooling that does not exist: the client harness has no enrollment/consumer switch. Last measured `active_consumers: 0`, 4,421 receipts pending, 0 applied |
| ☐ | **Candidate 12** | the r42 coupled pair cut, re-promotion, a fresh boot receipt, P7 started, and `zdoRedirectEnabled=true` restored. Run against a native-mode server it measures the wrong lane |
| ☐ | **Two humans, two Steam clients** | nothing but time. Never passed. Everything else is a proxy for it |

### Fix before the next unveil

☐ **`verify-live` checks liveness, not identity.** It passed `/join` because the route
answered 200 — while that route belonged to a different product entirely. Assert identity
too (expect `Server: Kestrel`, or a known body marker) in the routes class.

---

## 3. Where we can fall back

**You are already standing on the fallback, and it is working.** The AM4 server runs
`lumberjacksCutoverMode = native` — vanilla Valheim sync with the Lumberjacks telemetry
heartbeat still on, which is why `/community` shows live data. It is where the 2026-08-05
session retreated after the modded lane failed four ways, and it has held for three days.

| If this breaks | Fall back to | How |
|---|---|---|
| The Lumberjacks lane misbehaves mid-session | Native sync | `lumberjacksCutoverMode = native` — already set; restart the server container |
| The ZDO redirect wedges clients | Redirect off | restore `.bak-20260805T1020Z`, then **wipe the WAL** — after any restart, a stale bank livelocks clients at spawn |
| A Gateway image goes bad | The previous image | re-pin the prior digest. **No terraform, no compose changes** |
| The published page is wrong | Re-publish | `Publish-WorkbenchAssets.ps1` — a file copy, no image build, no restart, gates fail closed |
| Enrollment can't be routed | The LAN guest package | `tools/guest-package/` — older, but it has preflight and diagnostics (§6) |
| The whole web surface is down | The repo | it is public; every tool's source and one-pager reads fine without the site |

> **Two things that break production in one command.**
> Never `terraform apply` from this repo — a plan would destroy the VM and four live
> resources. Never run `~/gallery/users.sh` on AM4 — it calls `gen_caddyfile.sh`, which
> overwrites `/etc/caddy/Caddyfile` wholesale with a template containing none of the
> storefront routes, taking `/workbench`, the downloads, the `/ops` guard and the mech proxy
> down together. To change a gallery login, hand-edit the `basic_auth` block instead.

---

## 4. The install plan

### Today — the tools

**There is no install.** Click the Workbench, download a zip, unzip, run. Verified end to
end through the public wire.

- **Quest picker** — a self-contained HTML page; open it in a browser.
- **Community telemetry** — a local stack; the kit carries its own instructions.
- **ComfyStewardView** — separate public repo; point it at a world save.

### Not today — joining the world

No publicly open path, deliberately. Two mechanisms exist:

1. **Steam self-service enrollment** — the intended path. Invite → Steam sign-in →
   personalized mod-pack zip with credentials already in the config → extract → restart
   Valheim. Built and test-covered, but **not publicly routed** (the funnel gives `/join` to
   an unrelated IRC portal) and **never walked end to end**. That walk is task SJ-1 on the
   `steam-join` card.
2. **LAN guest package** (`tools/guest-package/`) — older. Sealed DLL plus config merge,
   hash-verified against its manifest, backs up what it overwrites, writes a receipt, rolls
   back on failure.

When it does open: **one client at a time**, until the shared enrollment queue is
recipient-scoped. Two testers would steal each other's records. That is a correctness
constraint, not caution.

---

## 5. How we explain it to people

The copy is written and it is good. Do not rewrite it under time pressure.

| Audience need | Where it lives |
|---|---|
| The announcement | `Lumberjacks/docs/workbench/discord/00-announcement.md` — **post by hand**; the bot has a hardcoded denylist against posting it |
| What alpha means | [`docs/community/expectations.md`](../community/expectations.md) |
| The player door | [`docs/community/README.md`](../community/README.md) |
| Each tool | its own one-pager and its own Discord thread, already posted |

**Three sentences worth repeating:**

1. *"What's open today is the tooling. The server isn't."*
2. *"Every status on that page is what the thing does today, not what it's going to do."*
3. *"Running one of these once and telling me what happened — including that it broke — is a complete contribution."*

**If asked about the networking work:** closer than it has ever been, the machine side is
green on everything a machine can check, and what is left needs a human driving two Steam
clients for hours. No dates.

**If someone finds the IRC portal at `/join`:** that is a different project sharing the same
host. It is not the Valheim join flow, and nothing on the Workbench links to it.

---

## 6. Making it not effort to join and test

Most of the friction is removable, and some of the fix is already built and simply not
pointed at.

### The shortest real test loop available today

**A friendly tester can play the modded server right now, over the tailnet — no enrollment,
no invite flow, no routing fix.** It works because the server is in native mode, so none of
the `no_go` items apply:

- The server is up, UDP **2456–2457**, direct-connect only (`SERVER_PUBLIC=false`, so it is
  not listed in the Steam browser).
- **Tailscale carries UDP fine.** The "UDP can't ride the funnel" caveat is about *Funnel*
  specifically and does not apply to an ordinary tailnet peer.
- So: share the tailnet with one person, they direct-connect to AM4 on 2456.
- Telemetry is on, so their session appears on `/community` — real data and real feedback
  without opening anything public.

Cost: one Tailscale invite. Zero infrastructure change. **Worth doing before any unveil**, so
that at least one person who is not you has walked it.

### Already built, currently buried

`tools/guest-package/` holds two things that exist to remove tester effort, and no
community-facing doc points at either:

- **`Invoke-GuestPreflight.ps1`** — read-only, changes nothing. Checks DLL hash, BepInEx
  present, Valheim not running, config writable, gateway health and TLS, bootstrap and
  enrollment id. Emits a PASS/FAIL verdict with a named remedy per failed check. Replaces
  *"did I break something before I even started."*
- **`Collect-ComfyGuestDiagnostics.ps1`** — copies the mod config and BepInEx log with
  secrets redacted, then **fails hard if anything secret-shaped survives**. Replaces *"paste
  your log, and remember to scrub it"* — a thing testers get wrong and then feel bad about.

Surfacing both is a doc change, not a build.

### Remaining friction, ranked

1. **`/join` belongs to something else.** Until the funnel stops shadowing it there is no
   self-service path at all. Highest-leverage single fix for onboarding.
2. **One client at a time.** Until the enrollment queue is recipient-scoped, "invite the
   community" cannot work.
3. **No tester FAQ.** Task SJ-2 — and it cannot honestly be written until SJ-1 is walked once.
4. **Invites are manual** — admin-generated, one-use, 24h. Fine for a handful, a bottleneck
   past that.
5. **Install is extract-and-restart.** Acceptable. The zip deliberately omits the personal
   config so a re-download never clobbers settings someone changed.

### The order to fix them in

Walk the flow yourself over the tailnet (free, today) → fix `/join` routing → write the FAQ
from what actually tripped you → then recipient-scope the queue. Each step makes the next
cheaper, and only the last is real engineering.
