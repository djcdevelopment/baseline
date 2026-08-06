# Launch runbook — operator

For Derek, as the person who owns this. Written 2026-08-06 against verified live state.
Everything below was checked, not recalled; where something is inferred it says so.

The unveil is **the tools**, not the world. That line is already drawn in the
announcement and in every card status. Nothing here asks you to move it.

---

## 1. What we know works

Receipts retained, re-verified 2026-08-06 unless noted.

| Thing | Evidence |
|---|---|
| **The public Workbench** | `workbench-verify-live --post-publish` → **71 checks, 0 failed**. Receipt: `captures/workbench-verify-live.json` |
| **Served page = committed render** | live sha256 `346259b9…` equals the local artifact, byte for byte |
| **Downloads survive the wire** | quest-picker + community-telemetry each stream with matching size, digest, and `X-Download-Sha256` header |
| **Public reachability** | `am4.tail8e749c.ts.net` resolves on public DNS (8.8.8.8 → 208.111.35.209). `/workbench`, `/community`, `/roadmap`, `/networksense`, `/events`, `/testing`, `/health` all 200 |
| **Discord** | invite resolves, correct guild, non-expiring; all 7 threads + all 9 first-task links live |
| **`/ops` is fail-closed** | 403 unauthenticated. `/gallery` 401. Both correct |
| **Netcode gates C0–C8, C10a** | complete on AM4 with falsifier receipts (12,339 server calls zero drops; poison blocked 76/76) |
| **C3 durable journal replay** | re-proved on P7 2026-08-03, 1,643 objects before/after |
| **M0 frozen release** | published and byte-verified |
| **Test suites** | 619 C# test attributes, 29 generator tests green |
| **A modded server is up** | `Comfy Era16 Lab`, world `ComfyEra16`, up 3 days, telemetry heartbeat on |

**The one number people will ask about:** the 83,220/83,220 ZDO golden proof is real, and it
is **one client, one window, 2026-07-16**. Say that second half out loud every time. It is
not a claim about Valheim networking in general and the roadmap says so itself.

---

## 2. What we want to test again

Ordered by what actually unblocks something.

### Free — no GCP spend, can run this week

- [ ] **Wedge repro on AM4.** Reproduce the candidate-8/11 livelock locally using
      `zdoJournalApplyThrottleMs` (exists: `network/mod/ComfyNetworkSense/Config/PluginConfig.cs:114`),
      then prove r42 breaks it. This is the pre-req your own register names, and it is the
      difference between "r42 passes unit tests" and "r42 fixes the thing".
      **Done when:** the stall reproduces on demand *before* the fix and does not *after*.
- [ ] **Cold-machine tool install.** Take one of the two published zips onto a machine that
      has never seen this project and follow only the one-pager. This is `no_go` item 6 and
      it is the cheapest one to close.
- [ ] **C9 motion verdict on the Lumberjacks lane.** The `smooth` verdict banked 08-05 was
      on *vanilla native sync*, not the Lumberjacks path. The real one is still open.

### Needs a window, and a decision first

- [ ] **Enrollment-consumer lane on P7.** The ADR-0017 gate. Every C8/C10b proof ran the
      harness journal lane; every real tester runs the enrollment lane, which has **never**
      been exercised on P7 (`active_consumers: 0`, 4,421 receipts pending, applied 0).
      **Blocked on tooling that does not exist** — the client harness has no
      enrollment/consumer switch. That build is part of the gate's cost.
- [ ] **Candidate 12.** Needs the r42 coupled pair cut, re-promotion, a fresh boot receipt,
      P7 started, and `zdoRedirectEnabled=true` restored first. A run against a native-mode
      server measures the wrong lane.
- [ ] **Two humans, two Steam clients.** Still never passed. Everything else is a proxy for it.

### Fix before the next unveil

- [ ] **`verify-live` checks liveness, not identity.** It asserted `/join` was fine because
      it answered 200 — while `/join` belonged to a different product. Add an identity
      assertion (expect `Server: Kestrel`, or a known marker in the body) to the routes class.

---

## 3. Where we can fall back

**You are already standing on the fallback, and it works.** The AM4 server runs
`lumberjacksCutoverMode = native` — vanilla Valheim sync, with the Lumberjacks telemetry
heartbeat still on. That is why `/community` has live data. It is the position the 08-05
session retreated to after the modded lane failed four ways, and it has been up three days.

| If this breaks | Fall back to | How |
|---|---|---|
| The Lumberjacks lane misbehaves in a session | Native sync | `lumberjacksCutoverMode = native` — already set. Restart the server container |
| The ZDO redirect wedges clients | Redirect off | Restore `.bak-20260805T1020Z`; wipe the WAL after any restart or clients livelock at spawn |
| A Gateway image goes bad | Previous image | Re-pin the prior digest. **No terraform, no compose changes** |
| The published page is wrong | Re-publish | `Publish-WorkbenchAssets.ps1` — it is a file copy, no image build, no restart. Gates fail closed |
| Steam enrollment can't be routed | The LAN guest package | `tools/guest-package/` — older, but it has preflight and diagnostics (see §6) |
| The whole web surface is down | The repo | It is public. Every tool's source and one-pager is readable without the site |

**Do not** `terraform apply` from baseline — a plan would destroy the VM and 4 live
resources. **Do not** run `~/gallery/users.sh` on AM4 before Saturday: it calls
`gen_caddyfile.sh`, which overwrites `/etc/caddy/Caddyfile` wholesale with a template that
has none of the storefront routes. That takes the entire public surface down in one command.

---

## 4. The install plan

### Today — the tools (this is the launch)

No install, no account, no server. Someone clicks the Workbench, downloads a zip, unzips it,
runs it. That is the whole flow, and it is verified end to end through the public wire.

- **Quest picker** — a self-contained HTML page. Open it in a browser. Nothing to install.
- **Community telemetry** — a local stack; the kit carries its own instructions.
- **ComfyStewardView** — separate public repo, point it at a world save.

### Not today — joining the world

There is no publicly open install path, and that is deliberate. Two mechanisms exist:

1. **Steam self-service enrollment** (intended path). Invite → Steam OpenID → personalized
   mod-pack zip with credentials baked into the BepInEx config → extract → restart Valheim.
   Built, test-covered, **not publicly routed** — the funnel sends `/join` to an unrelated
   IRC portal — and **never walked end to end**. That walk is task SJ-1.
2. **LAN guest package** (`tools/guest-package/`). Older. Sealed DLL + config merge, hash
   verified against the manifest, backs up what it overwrites, writes a receipt, rolls back
   on any failure. Has a **read-only preflight** and a **secret-scrubbing diagnostics
   collector** — see §6.

When you do open it: **one client at a time** while the enrollment queue is shared. That is
a real constraint, not caution.

---

## 5. How we explain it to people

The copy is written and it is good. Don't rewrite it under time pressure.

- **The announcement** — `Lumberjacks/docs/workbench/discord/00-announcement.md`. Post it by
  hand; the bot has a hardcoded denylist against posting it. Placeholder is filled, the
  stale "networking on hold" premise is fixed, it says three runnable tools and puts the
  Steam card in the not-open section.
- **What alpha means** — `docs/community/expectations.md`. One operator, best-effort, built
  in the open, batch rhythm in days not minutes.
- **The player door** — `docs/community/README.md`.
- **Each tool** — its own one-pager and its own thread. Already posted.

**The three sentences to keep saying:**

1. *"What's open today is the tooling. The server isn't."*
2. *"Every status on that page is what the thing does today, not what it's going to do."*
3. *"Running one of these once and telling me what happened — including that it broke — is a complete contribution."*

**If someone asks about the networking work:** it is closer than it has ever been, the
machine side is green on everything a machine can check, and what is left needs a human
driving two Steam clients for hours. No dates.

**If someone finds the IRC portal at `/join`:** that is a different project sharing the same
box. It is not the Valheim join flow. Nothing on the Workbench links to it any more.

---

## 6. Making it not effort to join and test

This is the part worth your attention, because most of the friction is removable and some of
the fix is already built and just not pointed at.

### The shortest real test loop you have today

**A friendly tester can play the modded server right now, over the tailnet, with no
enrollment, no invite flow, and no routing fix.** This sidesteps every `no_go` item because
the server is in native mode:

- The server is up: `Comfy Era16 Lab`, world `ComfyEra16`, UDP **2456–2457**, no password,
  `SERVER_PUBLIC=false` so it is direct-connect only, not in the Steam browser.
- Tailscale **carries UDP fine** — it is only *Funnel* that cannot. The "UDP can't ride the
  funnel" caveat does not apply to a tailnet peer.
- So: share the tailnet with one person, they direct-connect to AM4 on `2456`, done.
- Telemetry heartbeat is on, so their session shows up on `/community` — you get real data
  and real feedback without opening anything public.

**Do this before Saturday if you want one honest outside voice.** It costs a Tailscale
invite and zero infrastructure change.

### Already built, currently buried

`tools/guest-package/` has two things that exist precisely to remove tester effort, and no
community-facing doc points at either:

- **`Invoke-GuestPreflight.ps1`** — read-only. Checks DLL hash, BepInEx present, Valheim not
  running, config writable, gateway health, TLS, bootstrap and enrollment id. Emits a
  PASS/FAIL JSON verdict and changes nothing. A tester runs this *before* touching anything
  and either gets a green light or a named remedy per check.
- **`Collect-ComfyGuestDiagnostics.ps1`** — copies the mod config and BepInEx log with
  secrets redacted, then **fails hard if anything secret-shaped survives**. That replaces
  "please paste your log and remember to scrub it," which is a thing testers get wrong and
  then feel bad about.

Surfacing these two is a doc change, not a build.

### The friction that is left, ranked

1. **`/join` belongs to something else.** Until the funnel stops shadowing it, there is no
   self-service path at all. Highest leverage single fix for onboarding.
2. **One client at a time.** Until the enrollment queue is recipient-scoped, "invite the
   community" is not a thing that can work. Two testers would steal each other's records.
3. **No tester FAQ.** Task SJ-2, and it cannot be written until SJ-1 is walked once.
4. **Invites are manual** — admin-generated, one-use, 24h, no self-serve. Fine for a
   handful, a bottleneck past that.
5. **Install is extract-and-restart.** Acceptable; the zip deliberately omits the personal
   config so a re-download never clobbers settings someone changed.

### The order I would fix them in

Walk the flow yourself once over the tailnet (free, today) → fix `/join` routing → write the
FAQ from what actually tripped you → then recipient-scope the queue. Each step makes the next
one cheaper, and only the last one needs real engineering.
