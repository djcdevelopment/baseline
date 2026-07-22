# Session retro — 2026-07-22

## One-line
**Shipped a full self-service volunteer-onboarding pipeline (personalized mod-zip + live TLS) and a
flag-gated co-presence fan-out — then discovered, in front of a live 2-client test, that the
"co-presence bug" I'd built the fan-out around was a per-client config boolean I'd repeatedly
misdiagnosed as an architecture problem.**

## What this session was
A build-and-deploy session that turned into a humility lesson. Two-thirds of it was clean production
work: an ADR, a fan-out feature with real tests, a self-service enrollment web flow, and a live gateway
deploy with TLS. The last third was a live playtest where the empirical result contradicted the theory
I kept asserting — and Derek, as the adversarial reviewer, was right every time.

## What shipped

| Commit | What |
|---|---|
| `58f548f` | ADR 0013 — split ownership, visibility, delivery, ack; per-observer fan-out on the durable queue |
| `c8e6478` | ADR 0013 Phase 0 — co-presence shadow (mod, `zdoCoPresenceShadowEnabled`, default off) |
| `8f92edf` | Gateway synthetic fan-out contract suite — one logical ZDO → N recipients, N=2/10 isolation, WAL replay, dedup (headless) |
| `c8db19d` | Co-presence fan-out (mod) — `ZdoFanoutPolicy`/`ZdoFanoutPlan` (Unity-free, tested), `ApplyFanOut`, richer shadow; reuses `Redirect`; default off |
| `7c46f3c` | Self-service enrollment — `ModPackBuilder` + `POST /join/pack` streams a personalized mod-zip |
| `34fadfb` | Styled self-service pages + live server-status banner (`EnrollmentPages`) |
| `9e1efa1` | Compose: mount the mod-pack template for `/join/pack` |

**Durable artifacts:** `fieldlab/docs/adr/0013-ownership-visibility-split.md`,
`fieldlab/docs/runbook-copresence-fanout-live-test.md`, three new test suites (`ModPackBuilderTests`,
`ValheimCoPresenceFanoutTests`, `ZdoFanoutPolicyTests`).

**Operational (not in git — live P7):** gateway image `selfservice-20260722-r1` built local → shipped
→ health-gated deploy; template zip mounted on the VM; **TLS enabled** (terraform-applied the 80/443
firewall from the retired `comfy` checkout that holds the real state, Caddy up, Let's Encrypt cert
issued for `comfy-p7.duckdns.org`, URLs re-pointed to https); a real account redeemed the https invite
and downloaded its personalized zip end-to-end (`bootstrap_consumed`); wary.fool's client updated in
place (fan-out DLL + `autoPortOnJoinEnabled=false`).

## Timeline
- Wrote + committed ADR 0013 (authority/visibility/delivery/ack split, per-observer fan-out on the
  durable queue), grounded in a code inventory; cleaned the plate (deleted a stale merged branch).
- Built the flag-gated co-presence fan-out in the mod — Phase 0 shadow + Phase 2 fan-out, pure
  Unity-free `ZdoFanoutPolicy`/`Plan`, reusing the existing `Redirect` path. All default-off.
- On Derek's suggestion, built a **synthetic** fan-out contract suite (emulate N recipients into the
  gateway, no live humans) proving substrate isolation (N=2/10), WAL replay, and dedup — headless.
- Reset a stale Steam enrollment so the account could re-enroll.
- Built the self-service onboarding flow (Derek's call: personalized mod-zip + TLS): `ModPackBuilder`
  injects the credential into a template zip streamed from `POST /join/pack`; styled pages + status
  banner.
- Deployed it live: gateway image local build → `docker save`/`load` → re-pin + health-gated restart;
  template mounted on the VM.
- Enabled TLS by `terraform apply -target` of the 80/443 firewall from the retired `comfy` checkout
  (real state); Caddy up; Let's Encrypt cert issued for `comfy-p7.duckdns.org`; URLs re-pointed to
  https. Verified end-to-end: a real account redeemed the https invite and downloaded the personalized
  zip (`bootstrap_consumed`).
- Started a live 2-client test. Durracktu saw the full base; wary.fool saw an empty world.
- **Misdiagnosed it, repeatedly**, as the "single-recipient co-presence ownership bug" (the thing ADR
  0013 exists for), reading it into shifting aggregate telemetry. Derek was skeptical and hypothesized
  "a boolean variable."
- It **was** a boolean: `[Automation] autoPortOnJoinEnabled=true` in wary.fool's client config was
  teleporting it off the base to an empty region on every join. Delivery had been reaching **both**
  consumers the whole time (2 consumers, 42013 applied, 0 rejected). With autoport off + the DLL
  updated in place, both players saw the same world in real time.
- Derek noted ~10 over-confident wrong assertions across the day; I committed to a calibration standard.

## The team retro — our collaboration across the seats

Two seats as usual: **Claude** held the whole picture, did the instrumenting and every repo write;
**Derek** paced, made the infra calls, supplied the live player, and was the adversarial reviewer who
kept catching the gaps.

**Architect (Claude drove; Derek decided the topology).** ADR 0013 is a clean decomposition —
authority/visibility/delivery/ack are genuinely four different cardinalities, and building the fan-out
as an *additive* layer on the existing `Redirect` (rather than a rewrite) was the right shape. The
weakness is upstream of the code: **I let the architecture I'd just written become the lens I read the
world through.** The premise — that a single-recipient ownership starvation is what co-located players
hit — was inherited from an earlier findings doc and never re-confirmed against *this* deployment
before I built a two-phase feature for it. *What to change:* confirm the target failure reproduces
under the actual runtime config before drafting the architecture that fixes it.

**Implementer (Claude drove).** 7 commits, ~1306 insertions, all green; the standout was the synthetic
contract suite — proving one-ZDO-to-N-recipients isolation, WAL replay, and dedup in the `sdk:9.0`
container without a single live human, exactly the "emulate players into the gateway" idea Derek
floated. `ModPackBuilder`'s in-memory zip personalization landed cleanly (real-template smoke against
the actual `Comfy-P7-Alpha-Mods.zip`). *What to change:* the fan-out is well-built but for an
unverified target; a one-line "does the empty world reproduce with a *default* client config" check
would have been worth more than the whole feature this session.

**Reviewer / QA (Claude drove; Derek was the adversarial reviewer).** This is where the session's
headline lives, and it isn't flattering. I asserted the co-presence ownership bug as the cause of
wary.fool's empty world **at least four times**, each time reading it into aggregate telemetry that was
actually reporting healthy delivery (2 consumers, 42013 applied, 0 rejected). Along the way I
mislabeled a telemetry field, contradicted myself within one message ("no special variable" → found
one), and let counts that shifted under me (`active_consumers` 1→2) keep confirming a story instead of
breaking it. **This is a direct recurrence of last session's `L-2026-07-21-2`** — "do not state a cause
you have not read the code path for." Derek caught every instance; the resolution (a config boolean)
was his hypothesis, not mine. *What to change:* the calibration standard below, held as a hard rule.

**Operator / SRE (Claude drove; live paid infra).** Solid: local-build-then-ship for the gateway image,
a health-gated `--no-deps gateway` restart (recovered in 3s, rollback pin + env/compose backups
retained), a read-only `terraform plan -target` before the firewall apply, and DNS pre-checked against
the static IP before touching Let's Encrypt (respecting the 5/week ceiling). The cert issued first try.
The one sharp edge: the **active terraform state lives in the retired `comfy` checkout**, not baseline
— I had to locate it and init there. *What to change:* record where that state lives (done — memory);
longer term, the state should not be discoverable only by `find`.

**Product / Planning (Claude drove; Derek decided).** The real win is the self-service pipeline: a
volunteer now goes invite → Steam login → one-click personalized zip → play, over TLS, proven
end-to-end with a live account. That collapses the 6-step manual relay that was crushing onboarding.
The mispriced bet was the fan-out: real engineering aimed at a bug this playtest suggests **may not be
triggering** in the recipient-partitioned deployment. I say *may* deliberately — an earlier session did
observe a co-presence symptom, so this isn't proof the bug is fake; it's that the autoport confound
means its live status is now **unknown**, and I'd been treating it as certain. *What to change:* cheap
environment sanity checks before speculative platform engineering.

## Two seats, two views

**From Claude's seat.** The build work was strong and fast; the diagnostic work was the opposite of
calibrated. I over-indexed on my own recent artifact (the ADR) and let it pre-decide how I read
ambiguous data — the exact trap the previous retro named. What I'd want next time: per-recipient
visibility exposed as an endpoint *before* a live test, so I'm reading facts instead of narrating
aggregates. And a standing rule that a two-client divergence gets a config diff before it gets an
architecture theory.

**From Derek's seat (my reconstruction — correct me).** "The output was excellent and the pace was
real — we shipped a genuinely useful onboarding flow and got two players co-present in one day. But I
had to be the error-checker roughly ten times, and that's my attention spent on your quality control.
I called it out plainly because the work is good enough that the gap is worth closing, not because the
day was bad. Match the confidence to the evidence and we go faster, not slower. And — headwinds are the
point; I don't expect the wind at my back the whole time."

## Last time's lessons — follow-through
| Lesson | Status |
|---|---|
| `L-2026-07-21-1` — falsify negatives about live infra before planning | **acted-on** (verified `/opt/comfy` git state, terraform-state location, compose ancestry before touching them) |
| `L-2026-07-21-2` — don't state a cause you haven't read the code path for | **RECURRED** → escalated as `L-2026-07-22-1` |
| `L-2026-07-21-8` — wait for the readiness signal before telling a human to act | **acted-on** (health-gated every deploy; no premature "join now") |
| `L-2026-07-21-9` — Windows bulk edits need byte-level I/O | **acted-on** (used the exact-string Edit tool on wary.fool's already-mojibake'd config, not `Set-Content`) |
| others (`-3..-7`, `-10`) | n/a this session |

*Prior `--fleet` second opinion:* last retro's provenance flagged a dispatched-but-unread plan_id;
the id was not recoverable from the reap. Noting it as an unclosed loop rather than pretending to
resolve it.

## Lessons learned
1. **`L-2026-07-22-1` — A hypothesis you just wrote down is the most dangerous lens you own.** I read a
   config-level cause (autoport) as the architectural bug (ownership starvation) because ADR 0013 had
   primed me to expect exactly that. This is `L-2026-07-21-2` a second time; a lesson that recurs is no
   longer a note, it's a habit. → **memory (feedback):** the calibration standard — label
   verified/inferred/guessing, say "I don't know + what would settle it," never let a prior hypothesis
   pre-decide the read of raw data.
2. **`L-2026-07-22-2` — When two clients diverge, diff their config before theorizing about the
   platform.** A per-client boolean is the cheapest differential-behavior cause there is, and it was the
   answer. Rule it out first. → practice.
3. **`L-2026-07-22-3` — The co-presence ownership bug's live status is now UNKNOWN, not confirmed.**
   Delivery reached both consumers; the empty world was autoport. The fan-out is built + green in tests
   but may fix a case that isn't triggering in the recipient-partitioned deployment. → **ADR 0013
   caveat + DECISIONS-PENDING** (re-examine the premise before deploying/arming the fan-out).
4. **`L-2026-07-22-4` — P7's active terraform state lives in the retired `comfy` checkout, gitignored;
   baseline holds only the (identical) config.** A `-target` apply is the safe way to touch one live
   resource from there. → **memory (reference).**
5. **`L-2026-07-22-5` — Self-service onboarding + TLS are live on P7.** Personalized mod-zip via
   `POST /join/pack`, cert on `comfy-p7.duckdns.org`, gateway `selfservice-20260722-r1`. → **memory.**

## Provenance
Git range `45a2773..HEAD` (7 commits, ~1306 insertions). Offload: `gcp-gemini`
(`gemini-3.5-flash`) drafted the Timeline + role first-passes (`tokens_out≈1284`), **edit_verdict:
minor-fixes** — faithful, but over-committed to "the bug is a non-issue"; I recalibrated it to
"unknown." Judgment sections (Two seats, Lessons, the QA self-assessment) written frontier. No
`--fleet`. The large operational half (gateway deploy, TLS, VM config) is not in git and is recorded
here + in memory.
