# Session retro — 2026-07-30 (P7 boot root-cause, and a gate that was lying)

## One-line

Two signals that **reported the opposite of reality** — a systemd unit that called itself active
while nothing ran, and a publish gate that failed against a byte-correct deployment — both
**diagnosed without starting the VM**, and both closed at the mechanism rather than the symptom.

## What this session was

Diagnosis and hardening, not build. The entire P7 investigation was carried out **from repo files
with the VM stopped**; the one cloud command executed all session was a read-only power-state
check, which confirmed the VM was already `TERMINATED`. Nothing was deployed, and no world was
loaded.

It also turned into an unplanned correction pass: the second half of the session established that
the work item the handoff said was pending had **already been done**, and that the only reason it
looked outstanding was a defect in the checker.

## What shipped

| Commit | What |
|---|---|
| `23259db` | Make the P7 boot path deterministic instead of hand-built |
| `4ba0246` | Clear the false stale-render reading on the live workbench |
| `3c3762f` | Merge `main` (the demo-session retro) — append-only journal reconciled by union, HTML re-rendered |

New durable artifacts:

- [`infra/gcp/p7/RUNBOOK-boot-determinism.md`](../../infra/gcp/p7/RUNBOOK-boot-determinism.md) —
  diagnosis, by-hand apply steps, and a next-boot procedure that captures the wedged-boot evidence
  **before** the fix destroys it.
- [`fieldlab/docs/adr/0014`](../docs/adr/0014-boot-must-converge-or-say-so.md) — boot must converge
  or say so loudly.
- [`fieldlab/docs/adr/0015`](../docs/adr/0015-pin-line-endings-for-load-bearing-bytes.md) — pin line
  endings for bytes that are hashed or parsed elsewhere.
- [`.gitattributes`](../../.gitattributes) — the repo-wide mechanism ADR 0015 decides on.

## Timeline

Derek reported the boot inconsistency with two concrete observations forty minutes apart: boot 1
all seven containers healthy and serving public TLS, boot 2 six containers in `Created` and
postgres `Exited (128)`, nothing serving for fifteen minutes, SSH answering normally throughout.
The brief was explicit — diagnose from the repo, **do not start the VM**, stage a runbook.

Reading the boot chain turned up a headline the docs contradicted: **nothing in the repo ever
installed or enabled `comfy-lumberjacks-p7.service`**. The unit was committed; `bootstrap.sh.tftpl`
set up disk, swap, docker and the ops agent and stopped. Enablement was hand-made state on the box
— while `RUNBOOK-cost-and-cycle.md` justified stop/start as safe on the grounds that there was "no
hand-built state to lose". Three more defects compounded it: `ConditionPathExists` skips a unit
*silently*, `docker compose up -d` returns at `Created` so `Type=oneshot` marks it active while
nothing runs, and no `Restart=` meant one transient failure parked the stack forever.

Derek then supplied the context that reframed the whole incident: the boots were not systems work.
He had run into a friend and fired up GCP to show what he was building. An ad-hoc demo, outside the
standing keep-GCP-asleep policy.

Asked to pivot to the local/AM4 lane, the investigation found it was **not pending work — it was
already live and green**. The handoff's claim that the live page still served a pre-review render,
with a republish owed, was false: the served page was byte-exact with the committed render. The
reason it looked stale was a real bug — `workbench-verify-live.mjs` hashes the local HTML as a raw
Buffer, and with no `.gitattributes` a Windows `autocrlf` checkout hashed `2bb23be9…` against a
server serving `976f51cc…`. After pinning line endings, the full live verification returned
**PASS — 69 checks, 0 failed, 0 warnings**.

## The team retro — our collaboration across the seats

*(Seat drafts offloaded to `gcp-gemini`; framing and the two blame-assignment calls corrected at
frontier — see Provenance.)*

**Architect.** The load-bearing call was what *not* to change: every service hard-depends on
postgres going healthy, which is exactly why one unhealthy postgres left six containers in
`Created`. The tempting fix — loosen the dependency — would have traded one visible failure for
four silent crash-loops, and it was correctly refused. The failure was one of scope rather than
judgment: a hazard identified yesterday (`autocrlf` smudge) was fixed only where it was found, so
it recurred a day later somewhere else. The architectural lesson is that a cross-cutting hazard
fixed locally is not fixed.

**Implementer.** Two tight commits, each closing its defect at the mechanism: `Assert` over
`Condition` so a missing path is loud, `--wait` so exit 0 means converged, `Restart=on-failure` so
transients self-heal, and the startup script now installing the unit so enablement stops being
hand-made. What to change is verification discipline on claims that cannot be run here:
`Restart=on-failure` under `Type=oneshot` is asserted from knowledge, not exercised, and the honest
mitigation was to write `systemd-analyze verify` into the runbook rather than to assert it works.

**Reviewer/QA.** The strongest and weakest moments were both in this seat. Strongest: the CRLF
false-positive was caught only because a hash mismatch was **measured rather than believed** —
`tr -d '\r' | sha256sum` turned "the deploy is stale" into "the gate is wrong" in one command.
Weakest: an early CR-count check used `grep -o '\r'`, which counts the letter *r*, and produced
nonsense numbers that briefly suggested a CRLF problem in the systemd unit that did not exist. The
recovery was right — re-measure with `tr -cd '\r' | wc -c` before reporting anything — but the
first instrument should have been the reliable one.

**Operator/SRE.** The do-not-start-the-VM constraint held absolutely: a seven-container boot
failure was root-caused entirely from committed files, and the only cloud call was read-only. The
docs were corrected in the right register — the README and cost-runbook claims were marked
**FALSIFIED with the evidence**, not quietly overwritten, so the next reader learns that a
`systemctl restart` never exercised the reboot path. The demo boot itself was a reasonable
operator call made on bad information: the runbook told Derek stop/start was safe. The fault sits
with the document, not the decision.

**Product/Planning.** Scope stayed proportionate — when Derek said the goal was local loop and AM4,
the response was to check where that lane actually stood rather than to keep pushing P7. That check
paid for itself by removing a phantom task from his plate. The planning gap was upstream and in the
artifact: the handoff asserted a pending republish without a verifiable basis, and a status
document that states unverified work as fact will keep manufacturing tasks until it is corrected.

## Two seats, two views

**From Claude's seat.** The best decision was refusing to weaken the postgres dependency to make a
symptom disappear. The most useful habit was measuring instead of asserting — it produced the one
genuinely surprising result of the session, that the *checker* was broken and the deployment was
fine. Where I over-reached: I ran a CR-count check with a broken regex and briefly reported alarming
numbers before re-measuring. Where I under-reached: having found `verify-live` hashes a raw Buffer,
I fixed the repo-side cause and deliberately left the script's fragility in place; that is defensible
(published bytes should *be* LF) but it is a known sharp edge I chose not to file down, and ADR 0015
says so out loud rather than hiding it. What I would want to know next time: which status claims in
`HANDOFF-*.md` were *verified* versus *assumed* at the time of writing — the republish item read
identically to a verified fact.

**From Derek's seat** *(my reconstruction, to be corrected).* He reported a real inconsistency, got
told his own documentation had been lying to him about it, and then found out the follow-up task he
thought he owed had already been done. The framing he supplied — "this is confusion I caused" —
matters less than what it revealed: he made a normal call (show a friend the work) on the basis of a
runbook that said stop/start was safe. I would expect him to care most that the docs now say what is
actually true and are explicit about what remains unverified, and least about the systemd minutiae.
The pointed question he would likely ask: if a demo needs no cloud VM at all, why did the docs make
booting one look like the obvious move?

## Last time's lessons — follow-through

| Lesson | Status |
|---|---|
| `L-2026-07-29-1` — prove bytes with shas, never narrative | **acted-on, and it still bit.** The practice worked perfectly — a measured sha is the only reason the CRLF false-positive was caught. But the lesson was captured as a note inside one workbook, never generalized, so the same root cause recurred elsewhere one day later. Now a repo-wide mechanism ([ADR 0015](../docs/adr/0015-pin-line-endings-for-load-bearing-bytes.md)) |
| `L-2026-07-29-2` — omit `max_tokens` on thinking rungs | **acted-on** (offload omitted the cap; `gcp-gemini` returned 545 tokens complete, no clipping) |
| `L-2026-07-29-7` — stopped is the default; running is booked | **acted-on** (VM never started; the single cloud call was a read-only `describe`) |
| `L-2026-07-29-10` — verify the repo before registering a gap | **acted-on** (the "stale render" gap was checked before being acted on, and turned out not to exist) |
| `L-2026-07-29-11` — a lesson is only as durable as the artifact it names | **acted-on, and directly vindicated.** Today's recurrence of `L-…-1` is precisely this failure mode; the response was an ADR plus a repo mechanism, not a third practice note |
| `L-2026-07-29-16` — a proxy that looks like a local service is a demo trap | **acted-on, and scoped.** Confirmed the AM4 workbench is **not** a P7 proxy, so `omen-dashboard-is-a-proxy`'s "no VM, no dashboard" does not apply to that surface; memory corrected |
| `L-2026-07-29-3/4/5/6/8/9`, `L-…-12/13/14/15` | **n/a this session** (no recovery, goldens, harness-block, or live-world work) |

## Lessons learned

1. **`L-2026-07-30-1` — A gate that fails on correct input is worse than no gate.** `verify-live`
   reported a byte-correct deployment as stale, and the recorded response was to schedule a
   republish. A check that cries wolf does not merely fail to inform; it actively trains its
   operator to route around it. When a gate fails, establish whether the artifact or the gate is
   wrong **before** acting. → **ADR** ([0015](../docs/adr/0015-pin-line-endings-for-load-bearing-bytes.md)).

2. **`L-2026-07-30-2` — A silent skip is the worst failure mode a service can have.** systemd's
   `Condition*` marks a unit `inactive (dead)` with no error and no log, which is indistinguishable
   from "hasn't booted yet" — the box answers SSH and serves nothing. Prefer `Assert*` wherever
   absence means "we cannot serve". → **ADR** ([0014](../docs/adr/0014-boot-must-converge-or-say-so.md)).

3. **`L-2026-07-30-3` — "Verified" must name what was exercised.** The README's reliability claim
   rested on a `systemctl restart`, which never touches the mount race, the daemon's restart
   policies, or the shutdown teardown — the three things a cold boot tests. The claim was not
   dishonest, it was under-specified, and it cost a real incident. Falsified claims were marked
   **with their evidence** rather than replaced, so the next reader learns the distinction. →
   **practice.**

4. **`L-2026-07-30-4` — Fix a cross-cutting hazard with a cross-cutting mechanism.** Yesterday's
   `autocrlf` lesson was real, correct, and scoped to one workbook — so it did not prevent the same
   root cause from surfacing in the publish gate a day later. Cross-cutting hazards belong in a
   repo-wide mechanism, not in the document of whoever hit them first. → **ADR 0015 + `.gitattributes`.**

5. **`L-2026-07-30-5` — Check your instrument before reporting its reading.** A CR-count run through
   `grep -o '\r'` counted the letter *r* and produced numbers that implied a CRLF defect in a file
   that had none. Re-measuring with `tr -cd '\r' | wc -c` settled it in one command. When a
   measurement is surprising, suspect the measurement first. → **practice.**

6. **`L-2026-07-30-6` — A status document that states unverified work as fact manufactures tasks.**
   The handoff's pending-republish item read exactly like a verified fact and would have consumed
   operator time on work already done. Status docs should mark what was verified, when, and by what
   command. → **doc** (handoff corrected inline with the evidence).

## Provenance

Git range `7e76b1a..HEAD` on `baseline` — 2 authored commits plus a merge of `main`'s demo-session
retro (`7d5826f`), all lived this session; no reconstruction except Derek's seat, marked as such.
**No VM was started**; the sole cloud call was a read-only `gcloud compute instances describe`
returning `TERMINATED`. Live verification against AM4 was read-only HTTP plus
`npm run workbench:verify-live -- --post-publish` (PASS, 69/0/0, receipt at
`Lumberjacks/captures/workbench-verify-live.json`).

Offload per doctrine: the five seat paragraphs were drafted by `gcp-gemini` /
`gemini-3.5-flash` (`routed_by pinned:gcp-gemini`, `tokens_out` 545, `max_tokens` omitted per
`L-2026-07-29-2`). **Edit verdict: `minor-fixes`** — no invented facts, but two seats assigned
blame the facts do not support (Operator/SRE framed the demo boot as a policy "violation";
Product/Planning called the AM4 pivot "poor situational awareness"). Both were rewritten at
frontier: the operator acted on documentation that was wrong, and the pivot request could not have
known the handoff was stale. Timeline, lessons, ADRs and every repo-coherent write are frontier.

The merge of `main` reconciled the append-only journal by **union on `id`, ordered by `at`**
(287 ours + 286 theirs → 288 union, 3 distinct new notes preserved), not by choosing a side;
`roadmap.html` was re-rendered from the merged inputs rather than hand-resolved.

**Unverified and staged, by design:** every P7 boot fix. The VM stays stopped;
`RUNBOOK-boot-determinism.md` step 3 (a cold stop/start) is the outstanding proof, and the
bootstrap half needs terraform, which is off the table from this checkout.
