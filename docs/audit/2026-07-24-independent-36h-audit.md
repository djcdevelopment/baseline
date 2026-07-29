# Independent Audit — baseline (+ commandcenter), last 36 hours

**Auditor register:** independent internal-audit read of an R&D / supply-chain / AI / fintech /
identity / community / open-source shop. **Observe + recommend only — no code was changed.**
**Window:** commit range `002b12c^..HEAD` = **184 commits**, 2026-07-22 23:46 → 2026-07-24 02:29 PDT
(26.72 h active). **Method:** one read pass, computed into a metric tensor; every finding
adversarially verified against `file:line` before inclusion (four scout claims were *corrected*
by that pass — see §3). Numbers are reproducible from the commands in the appendix.

---

## 1. Executive summary

- **Cadence is extreme and machine-paced:** 184 commits in 26.7 h = **6.9 commits/hr**, one every
  ~8.8 min, **95% additive** (25,846 added / 1,488 removed — a ~17:1 add:delete ratio). This is a
  background roadmap automation committing under a single human identity (184/184 `Derek Ciula`),
  not a team. It is a deliberate, documented posture — not a defect — but it has audit consequences
  for provenance and reversibility (§3, §4).
- **The effort vector rotated mid-window.** The first half was **delivery/onboarding** (Companion,
  bootstrap releases r2→r26, i5 deploy lanes); the second half pivoted hard to **netcode R&D** (the
  M7 authority-experiment lab, `fieldlab/`, `plans/`). Acceleration is unmistakable: `tools/` +139,
  `fieldlab/` +97, `plans/` +47 file-revisions in the newer half vs `Lumberjacks/src` −97,
  `Lumberjacks/docs` −81 in the older. See the acceleration slice in §2.
- **Much of the "velocity" is generated mass, not new logic.** The two hottest files (104 revisions
  each) are *both* machine-generated — `roadmap.html` and `commit-notes.jsonl` — regenerated once per
  commit. The density-weighted matrix (§2) separates load-bearing code from regenerated bulk: real
  hand-written code mass is ~19k of the 27k churn, concentrated in `tools/` (PowerShell orchestration)
  and `Lumberjacks/src` (C#).
- **Engineering quality is above-average for R&D**, with conspicuous honesty: pre-registered
  hypotheses with a five-class result taxonomy (not pass/fail), hash-verified determinism, fail-safe-OFF
  rollback flags, a removed-and-tombstoned autonomous swarm, and inline self-corrections of prior
  overclaims. Credits are itemized in §3.
- **The moat is not the code — and that is the good news for the open-source posture.** The defensible
  assets are the reverse-engineering map + ADRs, the ZDO band/fanout *policies*, the receipt-backed
  research *method*, and the fleet the code runs against — none of which a repo clone confers. The
  BSL-1.1 instrument adopted this window is a well-built "show-all, keep-commercial" lever. §4–§5.

---

## 2. The metric tensor

> **On the "32×32×…×32" ask:** seven base axes bucketed to 32 levels is a rank-7 outer product of
> ~34.4 **billion** cells. But the realized object is a **sparse, rank-deficient tensor** — only ~10
> subsystems populate it. So we don't materialize it; we read once, compute the base axes, and
> **project to the informative slices**. That is the whole "matrix math" trick made rigorous: lazy
> evaluation of a sparse tensor, surfacing only the high-norm slices below.

### Base axes (the five you named, made computable)

| axis | symbol | definition |
|---|---|---|
| Volume | V | churn lines (add+del) in window |
| Mass | m | churn weighted by information content: code (`.cs/.ps1/.py/.mjs`)=1.0, prose (`.md`)=0.5, config/data (`.json/.yaml`)=0.3, regenerated `.html`=0.1, generated run-artifacts / journal / regenerated roadmap=0.05 |
| Density | ρ=m/V | information per line ∈ (0,1] |
| Docs | D=doc_mass/code_mass | how well-explained |
| Velocity | v | file-revisions per active hour (direction = which subsystem) |

**Slice A — subsystem × base axes** (rows sorted by mass):

| subsystem | V (churn) | m (mass) | ρ (density) | D (docs) | v (rev/hr) |
|---|---:|---:|---:|---:|---:|
| `tools/` | 9,604 | 9,170 | **0.95** | 0.04 | 7.60 |
| `Lumberjacks/src` | 5,498 | 3,309 | 0.60 | ~0.00 | 7.37 |
| `plans/` | 3,251 | 1,621 | 0.50 | pure-doc | 1.83 |
| `fieldlab/` | 3,513 | 1,442 | 0.41 | **0.60** | 5.20 |
| `network/` | 918 | 813 | **0.89** | 0.13 | 1.50 |
| `Lumberjacks/tools` | 1,070 | 763 | 0.71 | 0.17 | 2.10 |
| `infra/` | 715 | 541 | 0.76 | 0.33 | 0.75 |
| `licensing` (root corpus) | 574 | 256 | 0.45 | pure-doc | 0.34 |
| `Lumberjacks/docs` | 1,265 | 213 | **0.17** | pure-doc | **8.35** |
| — cold archives — | | | | | |
| `comfy` (archive) | 0 | 0 | — | — | 0 |
| `Lumberjacks` (archive) | 0 | 0 | — | — | 0 |
| `ComfyStewardView` | 0 | 0 | — | — | 0 |

Read the extremes: **`tools/`** is the mass + density leader (dense hand-written PowerShell).
**`Lumberjacks/docs`** has the *highest velocity but the lowest density* (0.17) — it churns fastest
because the journal + roadmap regenerate every commit, not because logic is changing. **`fieldlab/`**
is the documentation leader (D=0.60): research that explains itself. **`network/`** is small but the
second-densest (0.89): little churn, high load per line — characteristic of the moat.

### Derived axes (tensor products of the base — the audit signal)

| subsystem | p = m·v (momentum) | E = ½mv² (energy) | a (accel, newer−older revs) | T (peak revs/file) | **L (moat-exposure)** |
|---|---:|---:|:---:|---:|:---|
| `tools/` | **69,700** | **264,600** | ▲ +139 | 32 (`wave0/README.md`) | mixed: lab runner portable, i5/P7 lanes captive |
| `Lumberjacks/src` | 24,400 | 89,900 | ▼ −97 | 104 (`roadmap.html`, *generated*) | Companion portable / Gateway ZDO core captive |
| `fieldlab/` | 7,500 | 19,500 | ▲ +97 | 14 | **captive — crown-jewel method/evidence** |
| `plans/` | 2,970 | 2,730 | ▲ +47 | 7 | **give-away risk — R&D playbook in prose** |
| `Lumberjacks/docs` | 1,780 | 7,430 | ▼ −81 | 104 (`commit-notes.jsonl`, *generated*) | public-by-design |
| `Lumberjacks/tools` | 1,600 | 1,670 | ▼ −38 | 23 (`latest-bootstrap.json`) | portable app + captive publish |
| `network/` | 1,220 | 910 | ~0 | 10 (`ComfyNetworkSense.cs`) | split: framing public / `Core/Services` captive |
| `infra/` | 405 | 152 | ▼ −6 | 3 | captive (P7-specific) |
| `licensing` | 86 | tiny | ▲ late spike | 1 | the instrument itself |

**Momentum & energy** both peak overwhelmingly at `tools/` — the project's direction is most committed
to (and most effort is burning in) the orchestration tooling, with `Lumberjacks/src` a distant second.
**Acceleration** is the headline dynamic: the ▲ rows (tools, fieldlab, plans) are the R&D pivot; the ▼
rows (Companion src/docs/tools) are the cooling delivery push. **Temperature** is a trap — the two
hottest files are generated, so raw churn heat over-weights automation; density (Slice A) is the
honest corrective. **Moat-exposure `L`** is the audit's headline column and feeds §4.

> Provenance charge `q` (a 7th axis): structurally **1.0 single-identity** across every row — no
> separation of duties, automation commits as the human. Treated in §3/§4 rather than as a heat cell.

---

## 3. Findings (ranked; each verified against `file:line`)

### Method note — this audit corrected its own scouts
An independent audit cannot repeat scout assertions unverified. The verification pass **overturned
three** scout claims outright and **narrowed a fourth** — a useful reminder that fast scouts surface
leads, not verdicts:

- ~~"~10,700 flatpak object files bloat the repo"~~ → **FALSE.** Git-tracked count = **0**;
  `.gitignore:51` ignores `fieldlab/autonomous/state/`. The 10,583 files exist only as untracked,
  ignored local disposable-client state — a local-disk note, not repo/history bloat.
- ~~"Companion `GatewayClient` has no HTTP timeout (100 s default)"~~ → **FALSE.**
  `Lumberjacks/src/Game.Companion/Program.cs:9` sets `Timeout = TimeSpan.FromSeconds(10)`.
- ~~"commandcenter commits HEARTH auth material — `hearth/var/callers.json` (X-Hearth-Key values)"~~
  → **FALSE.** `hearth/var/` is git-ignored (`hearth/.gitignore:1`); the runtime keys are not tracked.
  Only a `hearth/etc/callers.json` template is tracked (verify it seeds no live keys). Two scouts
  disagreed on this; direct `git ls-files` settled it.
- "The public feed cannot leak identity because `actor_id` is set server-side and no field can hold
  it" → **NARROWED** (F7 below): the conclusion holds, but `actor_id` is *client-asserted*
  (`GameplayEventProducer.cs:60,125`), not server-authoritative, and `Detail` is a free string kept
  clean by producer *convention*, not structural impossibility.

### Ranked findings

| # | severity | finding | evidence |
|---|---|---|---|
| 1 | **HIGH** (latent op) | A blanket `terraform apply` from baseline would **destroy 4 live resources and replace the prod VM** (boot-image + startup-script drift; state still references the deleted 150 GB disk). Documented & deliberately deferred — but it is the single biggest footgun. | `infra/gcp/p7/RECONCILE-GAP.md:50-83`; code declares `data_disk_size_gb=150` (`variables.tf:33`) vs live 32 GB |
| 2 | MED | **Test & CI gap.** The publicly-distributed **Companion** app and 5 services (EventLog, OperatorApi, Persistence, Progression, ServiceDefaults) have **zero unit tests**; the new Workbench endpoints are untested; there is **no CI** (`.github/workflows` absent). The commit-contract is the only automated gate. | no `Game.Companion.Tests`; no `.github/`; new `WorkbenchPage.cs`/`WorkbenchCatalog.cs` untested |
| 3 | MED (verified) | **Timing-unsafe key checks + unauthenticated internal services.** Gateway admin/telemetry-key checks use plain `!=` string comparison (a timing side-channel); no `CryptographicOperations.FixedTimeEquals` exists anywhere in Gateway source. On the private plane, EventLog `POST /events`, Progression `POST /process-event`, and OperatorApi carry no auth/rate-limit, and OperatorApi relays request bodies with an unbounded `ReadToEndAsync` (DoS). Bounded in practice by private-plane IP gating + the Gateway's own auth, but the services are open by themselves. | `SteamEnrollmentEndpoints.cs:13,39`; `ValheimTelemetryHeartbeatEndpoints.cs:19`; OperatorApi proxy |
| 4 | MED | **Floating supply-chain tags.** `Lumberjacks/Dockerfile` + Companion Dockerfile pin `dotnet/sdk:9.0` & `dotnet/aspnet:9.0`; `infra/gcp/p7/docker-compose.yml:27` uses `postgres:16-alpine`. The delivered bootstrap zip is hash-pinned end-to-end, but the *executed container* is built from mutable upstream bases → not reproducible/verifiable. | `Lumberjacks/Dockerfile:5,80`; `docker-compose.yml:27` |
| 5 | MED (identity) | **Provenance conflation.** All 184 in-window commits are git-authored `Derek Ciula`, but the roadmap journal records `"author":"Codex"` — they are **AI-authored, human-attributed**, auto-committed and force-pushed to `main`. Documented & accepted for a solo repo; matters the moment a contributor or signature-based trust enters. | `docs/roadmap/commit-notes.jsonl` (`author:"Codex"`); `README.md:25-36`; `DECISIONS-PENDING.md:37-39` |
| 6 | LOW | **"Open source" on a BSL project.** The public roadmap calls a BSL-1.1 (explicitly *not* OSI open-source) project a "solo open-source sample." Honest term: *source-available* / *community-first source*. | `roadmap.html:1558-1559` |
| 7 | LOW | **`plans/` publishes the R&D playbook.** `plans/m7-authority-experiment-program.md` lays out the full method — research question, the E00–E11 experiment train, the decision table — so shipping the repo hands a reader the reproducible methodology, not just results. Weigh against §4's "method is moat." | `m7-authority-experiment-program.md:179` (experiment train), `:546` (decision table) |
| 8 | LOW | **`network/` moat boundary is prose, not directory.** The deliberately-shareable framing (`network/README.md`) sits in the same tree as the real implementation (`network/mod/ComfyNetworkSense/Core/Services/`). One careless `git add network/` publishes the moat next to the note that says it's safe to share. | `network/README.md` vs `network/mod/.../ZdoRedirectRunner.cs` |
| 9 | LOW | **Public fleet topology.** The public roadmap discloses node names OMEN/i5/P7, the GCP deployment `comfy-lumberjacks-p7`, and VM sizing `n2-highmem-2`. Not secrets, but it maps the operator's dev fleet. | `roadmap.html:1329,354,1146` |
| 10 | LOW | **Hardcoded tailnet default.** `zdoRedirectEndpoint` defaults to `http://100.124.12.37:4000` — a specific tailnet host baked into mod config. | `network/mod/ComfyNetworkSense/Config/PluginConfig.cs:667` |
| 11 | LOW | **Two rollback inconsistencies.** `rollback-network-sense.ps1:16` only `test -f`s the DLL (no sha256) before install — weaker than the sha256-both-ends `Promote-GatewayImage.ps1:138`. And Companion **bootstrap** rollback is manual (hand-repoint `current.json`), unlike the scripted Gateway env re-pin. | `rollback-network-sense.ps1:16`; `Publish-CompanionBootstrap.ps1:59-62` |
| 12 | LOW | **Companion bind depends on the port map.** The container binds `http://+:8080`; loopback containment is only the compose mapping `127.0.0.1:8080:8080`. Running the image with `-p 8080:8080` exposes the admin+workbench surface on all interfaces. | `Dockerfile:12`; `docker-compose.yml:8` |

### Positive findings (verified — credit where due)
- **F7 identity, corrected & sound:** the public `CapturedEvent` record carries no `actor_id` field at
  all and the `AllowedTypes` allow-list drops identity/social event types, so the public feed cannot
  carry identity — even though the underlying claim's *mechanism* was overstated. `GameplayEventFeed.cs:155`
  ("Carries no actor identity, name, or position by design"), tested at `TelemetryV0EndpointsTests.cs:417-422`.
- **Scientific honesty (F2, F8):** E04 "supported" rows self-label as parser-only —
  `learning-log.jsonl` "this is parser evidence only, not native capture evidence"; the
  `zdoRedirectEnabled` config description self-corrects a prior overclaim —
  `PluginConfig.cs:647` "THIS IS THE LIVE SERVING PATH … not a lab experiment."
- **Determinism discipline:** `tools/authority-lab` produces byte-identical hash-stamped receipts with
  `additionalProperties:false` schemas; `Promote-GatewayImage.ps1` verifies sha256 on both ends + image-id
  and wraps a `trap rollback`. Strong .NET test coverage on the netcode core (Contracts/Gateway/Simulation/
  ComfyNetworkSense — ~50 xunit files with real assertions).
- **Operational safety:** `tools/wave0` is bounded (every HTTP call `-TimeoutSec`, every wait deadlined),
  fixture-tested across all error branches, key-auth-only SSH, no destructive ops. The autonomous swarm
  was removed and tombstoned (`SWARM-HARNESS-REMOVED.md`) with a recovery SHA.
- **Cost hygiene (fintech lens):** VM downsized to `n2-highmem-2`, backups split dev(OFF)/prod, free-tier
  log noise disabled; commandcenter tracks a real-USD offload ledger with honest unpriced-call handling
  (verified Vertex pricing, $5.53 priced trial floor, 1% of a 200M-token trial runway — the binding
  constraint is idle standing infra, not token burn).

---

## 4. Open-source posture — "show all without giving it away"

**Thesis: the moat was never the source.** The read pass shows the defensible assets are:

1. **The reverse-engineering map + 13 ADRs** (`fieldlab/NETCODE-MAP.md`) — Valheim's managed
   replication path named down to decompiled signatures, with the intended hook + wire format for each
   of five "funnels." Expensive to reproduce; this is the real IP.
2. **The production policies** — `ZdoBandPolicy` (distance-band AoI) and `ZdoFanoutPolicy` (per-observer
   visibility, "at most one redirect per recipient per revision," ownership deliberately *not* an
   input) in `network/mod/ComfyNetworkSense/Core/Services/`.
3. **The receipt-backed research method + accumulated evidence** — the `fieldlab/experiments/m7`
   idea→prediction→fingerprint→native-compare→one-human-judgment→retained-learning loop.
4. **The fleet** — OMEN / i5 / P7 / HEARTH. The i5 and P7 lanes, the two-client feel window, the P7
   promotion drill: all wired to specific hosts and identities. A repo clone confers none of it.

**What that means:** you can show all the code because 1–4 don't transfer with a `git clone`. The
`network/README.md` instinct is already correct — it publishes **philosophy and lineage only**, no
implementation. The BSL-1.1 adopted this window (100-active-member community grant, donation-only cost
recovery, AGPL conversion 2030-07-24) is a well-built lever that keeps commercial rights while letting
communities run and inspect everything.

**The two nameable gaps** (details/severity in §3): (a) the public roadmap/README call a BSL project
"open source" — BSL is explicitly *not* OSI open-source; the honest word is *source-available* or
*community-first source*; (b) the shareable `network/` framing sits in the *same directory tree* as the
real mod source, so the safe/unsafe split is by prose intent, not by a directory boundary — one wrong
`git add` of `network/mod/` publishes the moat next to the framing that says it's safe to share.

---

## 5. Research categories worth pursuing

Seven avenues, each tied to a concrete in-window finding and to the goal of *staying free-spirited /
show-all without giving away the work.*

1. **Source-available license economics & enforcement** — study BSL/FSL/SSPL and the Elastic,
   HashiCorp, MongoDB, Sentry re-licensing histories; Change-Date tuning; the open-core-vs-open-edge
   boundary. *Payoff:* you publish confidently because you know exactly what the grant does and doesn't
   give. *(Ties to the BSL adoption + the "open source" wording gap.)*
2. **Commoditize-your-complement / moat theory** (Spolsky) — formalize that the moat is the running
   fleet + evidence corpus + community trust, not the source. *Payoff:* license the *intent* to show all,
   backed by a written moat map so nothing load-bearing leaks by reflex. *(Ties to §4.)*
3. **Provenance & supply-chain integrity** — SLSA levels, Sigstore/cosign signing, SBOMs, reproducible
   builds. *Payoff:* fixes the floating-base-image gap *and* turns "full source + reproducible proof"
   into a trust moat that a copier can't cheaply match. *(Ties to the floating-tag + manual-rollback
   findings.)*
4. **Data / evidence moats & privacy-preserving publication** — differential privacy, k-anonymity,
   aggregates-only APIs (the public v0 feed is already shaped this way). *Payoff:* publish the *method*
   and aggregate results while the raw capture corpus + identity stay private — the corpus is the asset,
   not the code. *(Ties to the identity-clean finding + the telemetry v0 surface.)*
5. **P2P / mesh transport research** (iroh / QUIC / libp2p, authenticated NAT traversal) — convergent
   with the commandcenter B70 "Buzz Mesh" direction. *Payoff:* protocols *want* to be open and publishing
   protocol research is high-status, low-moat-cost; the implementation tuning stays the edge.
6. **Federated / edge-LLM offload economics** — the HEARTH token-arbitrage & routing policy (real Vertex
   per-Mtok pricing, trial-USD accounting). *Payoff:* publish the routing *pattern* as a paper/blog; keep
   the fleet topology and the spend ledger private. *(Ties to the commandcenter HEARTH work.)*
7. **Attribution & AI-authorship provenance in solo+automation projects** — commit provenance, CLA
   design, AI-disclosure (already in `CONTRIBUTING.md`), signed commits. *Payoff:* clean provenance lets
   you accept community contributions and open-source without inheriting license contamination — and
   addresses the 184/184 single-identity, automation-commits-as-human posture. *(Ties to §3 provenance.)*

---

## 6. Appendix — method & reproducibility

**Window:** `git rev-list --count 002b12c^..HEAD` → 184. Active span 26.72 h (first→last author date).

**Cadence / churn:**
```
git log 002b12c^..HEAD --numstat --format="" \
 | awk 'NF==3 && $1!="-"{a+=$1;d+=$2} END{print a" added "d" removed"}'   # 25846 / 1488
```

**Mass weights** (per file class, applied to add+del churn): code `.cs/.ps1/.py/.mjs` = 1.0; prose
`.md` = 0.5; config/data `.json/.yaml` = 0.3; regenerated `.html` = 0.1; generated run-artifacts,
`commit-notes.jsonl`, regenerated `roadmap.html`, and `valheim-volunteer-roadmap.json` = 0.05.
`m = Σ wᶜ·churnᶜ`; `ρ = m/V`; `D = doc_mass / code_mass`; `v = filerevs / 26.72`; `p = m·v`;
`E = ½·m·v²`; acceleration = (newer-half filerevs) − (older-half filerevs), split at the 92nd commit
(`1967e57`, 2026-07-23 11:09).

**Raw class totals (churn):** PowerShell 9,163 · docs-md 6,639 · C# 5,495 · html 2,297 · json 1,528 ·
generated-run 1,510 · yaml 181 · journal 104 · python 73.

**Scope confirmation:** only `baseline` and `commandcenter` had commits in-window; `comfy`,
standalone `Lumberjacks`, `ComfyStewardView` (and other `C:\work` repos) were cold.

_This memo is intentionally left uncommitted for review._
