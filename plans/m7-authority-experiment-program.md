# M7 authority R&D experiment program

Status: planned and authorized for synthetic, replay, local-lab, and P7-shadow work
Promotion boundary: no behavior-changing P7 authority change without a reviewed experiment packet
Parent strategy: `plans/m7-authority-expansion-working-strategy.md`
Builder handoff: `plans/m7-authority-experiment-execution-handoff.md`

## Research question

Which Valheim network judgments can Lumberjacks make more predictably, cheaply, and
legibly than native Valheim, and what is the smallest amount of lab tooling needed
to learn that without repeatedly consuming a human test session?

This is product R&D. The product under investigation is not only a replacement
equation. It is the complete feedback loop:

```text
idea -> prediction -> synthetic fingerprint -> native comparison
     -> disposable local authority -> real-world shadow -> one human judgment
     -> retained learning -> next idea
```

The lab is allowed to be temporary scaffolding. A useful experiment may end by
deleting code, baking one constant into configuration, or deciding that Valheim
should keep a plane.

## Working style

- One experiment answers one important question.
- Write the prediction before the run. Never rewrite it to match the result.
- Prefer a 5-30 minute bounded run over a permanent service.
- Reuse one scenario across pure, Gateway, local Valheim, and P7-shadow drivers.
- A harness failure is not a refuted hypothesis.
- A surprising result is valuable if the raw evidence and setup are retained.
- Native Valheim is the first comparison oracle, not an assumption of correctness.
- Synthetic runs prove direction, wiring, and invariants; they do not prove player
  quality or production capacity.
- Promotion is not the default outcome. `keep_native`, `learn_more`, and
  `abandon_idea` are successful conclusions.
- Do not ask Derek to relog because a build, package, command name, config, capture,
  or rollback check could have been automated.

## Lightweight experiment structure

Use one folder per experiment:

```text
fieldlab/experiments/m7/<experiment-id>/
  experiment.md
  scenario.yaml
  runs/
    <run-id>/
      receipt.json
      summary.md
      raw/
```

Keep one append-only program log:

```text
fieldlab/experiments/m7/learning-log.jsonl
```

This is intentionally not a database, manifest service, or formal attestation
system. `experiment.md` is the pre-run thought. `receipt.json` is machine-readable
fact. `summary.md` is the interpretation. The learning log records why the next
experiment changed.

### Experiment card

Each `experiment.md` uses this small contract:

```markdown
# <id> - <question>

Status: planned | running | analyzed | superseded

## Goal
The product capability or uncertainty this experiment serves.

## Objective
The one thing changed, compared, or observed in this experiment.

## Hypothesis
The causal claim being tested.

## Predicted outcome
Concrete directional observations written before the run.

## Limits
Time, clients, objects, authority mode, world, and explicit non-claims.

## Assumptions
Facts temporarily treated as true so the experiment can proceed.

## Known limitations and ADRs
Relevant debt, uncertain premises, and decisions that constrain interpretation.

## Setup and procedure
Driver, scenario, artifacts, capture, stop rules, and rollback.

## Results
Pending before the run. Afterward: measurements, observation, anomalies, and
result classification.

## What changed in our understanding
Which assumption strengthened, weakened, or broke; what this unlocks or removes.

## Next experiment
The smallest next question justified by this result.
```

### Result classifications

Use only:

- `supported`: observations moved in the predicted direction;
- `refuted`: usable evidence contradicted the hypothesis;
- `mixed`: different parts moved differently;
- `inconclusive`: the run was valid but could not distinguish explanations;
- `harness_failed`: setup or instrumentation prevented interpretation.

Do not collapse these into a generic pass/fail.

### Learning-log row

One JSONL row after interpretation:

```json
{
  "schema_version": 1,
  "timestamp_utc": "2026-07-24T00:00:00Z",
  "experiment_id": "m7-e04-native-candidate-capture",
  "run_id": "local-20260724-001",
  "result": "mixed",
  "observation": "Native candidates differed by observer in the shared zone.",
  "interpretation": "Distance alone does not explain the complete native set.",
  "assumption_changed": "A full spatial snapshot is sufficient as the only oracle.",
  "confidence": "medium",
  "decision": "Add object semantics to the replay classifier before local strict mode.",
  "next_experiment": "m7-e05-native-vs-lumberjacks-replay",
  "evidence": ["runs/local-20260724-001/receipt.json"]
}
```

## Unit-test budget

Unit tests protect the lab from lying; they do not attempt to prove the product.
Keep them limited to:

1. scenario/event parsing and rejection of malformed required fields;
2. deterministic generation from the same seed;
3. one or two sharp invariants such as no cross-recipient decision and at-most-one
   terminal apply;
4. command timeout/auto-stop and rollback-state handling.

Policy quality, scaling shape, native agreement, visual quality, and authority
fitness are experiment results. Do not build large mock matrices for them.

Existing `InterestManager`, `SpatialGrid`, `ZdoFanoutPolicy`, simulation, and queue
tests are sufficient starting seams. Add a unit test only when a lab run exposes a
specific regression that would be cheaper to catch before the next run.

## Execution map

| Driver | Runs where | Best for | Human touch |
|---|---|---|---|
| `pure` | OMEN .NET 9 build container | generated worlds, equations, deterministic comparisons | none |
| `gateway` | OMEN Docker | protocol clients, queues, transport, N-observer pressure | none |
| `replay` | OMEN Docker | new policy against retained native or prior traces | none |
| `local_valheim_shadow` | local server plus owned clients | actual Unity/native decisions without changing behavior | initial cached Steam state only |
| `local_valheim_strict` | disposable local world | one reversible authority claim | none after clients are in-world |
| `p7_shadow` | P7 plus owned clients | Era16 density and real latency without behavior change | one join if clients cannot autojoin |
| `p7_canary` | P7 | final bounded claim | approval plus one predeclared visual question |

Machine/account binding stays in ignored local inventory. Experiment files use
`server_host`, `player_a`, and `player_b`, never credentials or Steam identifiers.

## Experiment train

### M7-E00 - Can the lab tell the truth?

**Goal:** establish a feedback loop we can trust before studying authority.

**Objective:** run one tiny pure scenario twice, then run one intentionally malformed
scenario and one forced timeout.

**Hypothesis:** identical seed, input, policy, and artifacts produce the same normalized
decision hash; malformed/timeout runs produce named non-success receipts without hanging.

**Predicted outcome:**

- the two valid summaries and normalized hashes match;
- timestamps and run IDs differ but are excluded from the normalized hash;
- malformed input is rejected before execution;
- timeout reaches `stopped` and retains the partial receipt.

**Limits:** no Steam, Unity, Gateway load, or policy-quality claim; under five minutes.

**Assumptions:** stable serialization and seeded generator are enough for repeatability.

**Known limitations/ADRs:** canonical event versions remain append-only; this is lab
repeatability, not immutable attestation.

**Result:** pending.

**Unlocks:** every later experiment. A failure changes the harness, not an authority
equation.

### M7-E01 - Does the relevance equation have the expected shape?

**Goal:** understand the basic geometry before comparing with Valheim.

**Objective:** generate concentric object densities and move one observer across
near/mid/far boundaries under the current band policy.

**Hypothesis:** candidate count is monotonic with radius and density; boundary crossings
produce explainable subscription transitions; undamped edges chatter under deliberate
boundary noise.

**Predicted outcome:**

- larger outer radius never reduces the candidate set;
- 2x and 4x density increase considered objects and estimated bytes in the same direction;
- clean crossings produce one enter/leave transition;
- noisy movement around exactly 30m/64m produces chatter, confirming the hysteresis debt.

**Limits:** five seeds, N=1 observer, generated objects, no CPU-capacity claim.

**Assumptions:** geometric fixtures can expose directional behavior even though Valheim
object semantics are absent.

**Known limitations/ADRs:** FieldLab ADR 0010 says predictability matters more than peak
quality; ADR 0011 places Valheim AoI on the producer; Lumberjacks ADR 0015 defines the
existing spatial model.

**Result:** pending.

**Path branch:** if shape is wrong, repair the pure selector. If shape is right but
chatter is large, add a hysteresis candidate to replay rather than immediately changing
runtime code.

### M7-E02 - Does recipient fan-out remain independent as N grows?

**Goal:** prove the observer set is represented independently from ownership.

**Objective:** run one logical revision through N=2, N=10, and N=100 synthetic observers
with duplicates, stale revisions, reconnect, and one slow consumer.

**Hypothesis:** every in-band observer receives at most one applicable copy, one
observer's state never suppresses another, and work grows approximately with the number
of in-band observers.

**Predicted outcome:**

- zero cross-recipient poll or ACK;
- zero duplicate terminal apply;
- slow/reconnecting observer changes only its own backlog;
- decisions and bytes rise roughly linearly with in-band observer count.

**Limits:** generated traffic through pure/Gateway drivers; no Unity apply or real-player
capacity claim; N=100 is pressure shape, not a supported-player promise.

**Assumptions:** existing recipient-scoped queue semantics are the right substrate.

**Known limitations/ADRs:** FieldLab ADR 0013's original co-presence premise is uncertain;
Lumberjacks ADR 0020 owns recipient durability. Existing N=2/N=10 tests are reused as
smoke seams rather than expanded into a large unit suite.

**Result:** pending.

**Path branch:** nonlinear growth points to indexing/serialization work. Isolation
failure stops all local strict fan-out work.

### M7-E03 - What fingerprint separates straight, stutter, turn, and teleport motion?

**Goal:** distinguish transport cadence problems from interpolation/prediction problems
without asking a player to repeatedly run a course.

**Objective:** send deterministic straight, stutter, stop/start, turn, and teleport
traces through pure and Gateway motion drivers.

**Hypothesis:** each input pattern produces a distinct update/correction fingerprint,
and the observed glide/teleport behavior can later be correlated with either cadence,
extrapolation error, or correction magnitude.

**Predicted outcome:**

- straight motion has stable direction and low input variance;
- stutter has more start/stop edges and shorter prediction windows;
- turns spike direction error;
- teleport is clearly separable from ordinary correction;
- UDP and WebSocket fallback preserve the same logical trace ordering.

**Limits:** no rendering and no claim about what feels smooth; fixed synthetic latency
and loss profiles first.

**Assumptions:** logical motion traces can narrow the likely cause before Unity visuals.

**Known limitations/ADRs:** Lumberjacks ADRs 0013/0014 define dual-channel transport and
input-driven simulation; client interpolation remains a separate presentation problem.

**Result:** pending.

**Path branch:** cadence correlation prioritizes send scheduling; prediction-error
correlation prioritizes interpolation/extrapolation; neither means the other layer should
be rebuilt.

### M7-E04 - What does native Valheim actually select per observer?

**Goal:** obtain the comparison data M7 currently lacks.

**Objective:** on a disposable local server, capture the native candidate list before
Lumberjacks suppression for one stationary, one straight-route, and one boundary-crossing
run.

**Hypothesis:** native candidate sets differ by observer, ownership/revision state, and
object semantics; distance alone will explain much but not all of the set.

**Predicted outcome:**

- the probe proves it sees the list before redirect mutation;
- repeated stationary samples mostly stabilize;
- observer movement changes membership;
- some long-reach or force-send objects violate a simple radius-only expectation.

**Limits:** one local world, one then two clients, bounded object-detail rows, shadow only.
No judgment that native selection is optimal.

**Assumptions:** `CreateSyncList` plus a bounded full-object snapshot provides enough
information for first replay.

**Known limitations/ADRs:** Harmony postfix ordering is load-bearing; FieldLab ADR 0009
requires an independent source; ADR 0011 notes the far-to-approach re-sync risk.

**Result:** pending.

**Path branch:** if the capture is incomplete, improve instrumentation before writing a
new selector. Do not infer missing native decisions from Gateway traffic.

### M7-E05 - Where does Lumberjacks agree and disagree with native relevance?

**Goal:** learn which distinctions a Lumberjacks selector needs.

**Objective:** replay E04's exact observers and object snapshots through full, radius,
tiered, landmark, and one hysteresis-candidate policy.

**Hypothesis:** the current tiered/landmark model captures most spatial decisions, while
meaningful disagreements cluster by object class or native revision/force-send semantics.

**Predicted outcome:**

- a large intersection for ordinary nearby static objects;
- radius-only omissions or extras cluster in identifiable semantic classes;
- landmark grants recover some long-range native candidates;
- hysteresis reduces transition churn without materially changing stable membership.

**Limits:** offline decisions only; native is a comparison baseline, not a correctness
label; no delivery or visual claim.

**Assumptions:** E04 captured enough features to explain major disagreement clusters.

**Known limitations/ADRs:** ADR 0010 values predictable transitions; ADR 0011 says the
producer owns the geometry; FieldLab ADR 0013 separates visibility from ownership.

**Result:** pending.

**Path branch:** semantic clustering justifies classification work. Random disagreement
means the trace is missing context. Close agreement unlocks local shadow.

### M7-E06 - Is the co-presence problem real under clean configuration?

**Goal:** stop designing around a possibly false premise.

**Objective:** place two default-config local clients first in separate regions, then in
the same built area, with co-presence shadow enabled and fan-out disabled.

**Hypothesis:** if native candidate presentation starves an observer, the shadow names
specific in-band ZDOs absent from that observer's native path; if both paths are already
complete, the prior empty-world symptom was configuration-induced.

**Predicted outcome:**

- both clients start with auto-teleport and old test bias disabled;
- shadow and native rows identify whether an actual per-observer gap exists;
- any visual/world difference maps to object IDs rather than only aggregate counts;
- separated regions produce little or no shared visibility set.

**Limits:** local disposable world, two owned clients, no fan-out behavior change, one
shared and one separated route.

**Assumptions:** default client configs and matching artifacts remove the known false
positive.

**Known limitations/ADRs:** FieldLab ADR 0013 is proposed and explicitly says its premise
is uncertain after `autoPortOnJoinEnabled` mimicked the defect.

**Result:** pending.

**Path branch:** no real gap means do not ship fan-out as a bug fix; continue only as a
measured scaling/visibility experiment. A real gap unlocks E07.

### M7-E07 - Can one static read-copy class be Lumberjacks-owned and rolled back?

**Goal:** prove the smallest reversible relevance promotion locally.

**Objective:** for one non-mutating static object class, compare shadow, strict
Lumberjacks read-copy fan-out, and in-run rollback to native delivery.

**Hypothesis:** visibility can be promoted independently of ownership: both observers
apply the same static class, ownership remains unchanged, and rollback resumes native
delivery without duplicate apply or world mutation.

**Predicted outcome:**

- shadow predicts the strict recipient set;
- both clients reach the same object/revision set;
- native eligible sends for the declared class reach zero only during strict mode;
- ownership token does not move because of visibility;
- rollback completes inside the declared bound and later native revisions apply once.

**Limits:** local disposable world, one class, two clients, short window, no creatures,
containers, portals, ownership, or P7 behavior.

**Assumptions:** client `RPC_ZDOData` can instantiate a read copy it does not own.

**Known limitations/ADRs:** ADRs 0011 and 0013 require suppress/ack/emit and
authority/visibility/delivery/ack to remain distinct. Save hashes are required even
though mutation is not intended.

**Result:** pending.

**Path branch:** success strongly argues ownership interception is unnecessary for
visibility. Failure separates client-apply, ack, and ownership explanations before
another strict run.

### M7-E08 - When would Lumberjacks ownership be more stable?

**Goal:** decide whether ownership replacement deserves product investment.

**Objective:** replay native owner transitions and candidate telemetry while a
Lumberjacks shadow selector compares no damping, cooldown, and hysteresis choices.

**Hypothesis:** near-tie owner scores cause avoidable churn, and a small deterministic
dwell/dead-band reduces swaps without retaining a clearly bad owner for long.

**Predicted outcome:**

- no-damping shadow changes owner most often near score crossings;
- cooldown/hysteresis reduces swaps;
- fail/disconnect still causes prompt transfer;
- retained-owner penalty is measurable rather than hidden.

**Limits:** shadow/replay only initially; no live owner mutation; one controlled local
two-client route.

**Assumptions:** current telemetry captures enough score inputs to replay candidate
choices.

**Known limitations/ADRs:** ADR 0010 makes damping a fidelity requirement; the existing
ledger states ownership hysteresis is not yet a runtime knob; I2 proves pin capability,
not good owner policy.

**Result:** pending.

**Path branch:** weak benefit means keep native ownership. Strong stable benefit justifies
a later local ownership experiment, separate from relevance.

### M7-E09 - Which RPC family is worth mirroring first?

**Goal:** replace RPC assumptions with an inventory and one cheap learning slice.

**Objective:** classify observed routed RPCs by direction, reliability, idempotency,
world mutation, payload shape, and frequency, then select one idempotent non-mutating
family for codec/reorder/duplicate replay.

**Hypothesis:** most RPCs should remain compatibility traffic initially, while at least
one bounded non-mutating family can validate the mirror/compare path cheaply.

**Predicted outcome:**

- inventory reveals a small number of high-frequency or high-value families;
- the first selected family replays deterministically under duplicate/reorder input;
- malformed payloads fail boundedly;
- no reason appears to replace Steam/base peer transport wholesale.

**Limits:** inventory and offline mirror only; no world-mutating RPC suppression.

**Assumptions:** observed local routes are representative enough to choose a first family,
not to declare the inventory complete.

**Known limitations/ADRs:** M7 explicitly evaluates replacement on measured value;
world-mutating RPCs require save integrity and a separate experiment.

**Result:** pending.

### M7-E10 - Does Era16 confirm the local relevance findings?

**Goal:** test external validity against the real dense world without changing it.

**Objective:** run the strongest E05 policy in P7 shadow across quiet, dense, shared,
separated, and far-to-approach routes.

**Hypothesis:** disagreement categories seen locally recur in Era16, while density changes
volume more than the shape of the policy's mistakes.

**Predicted outcome:**

- no P7 delivery or ownership behavior changes;
- local disagreement categories remain recognizable;
- dense regions increase decisions/CPU/bytes predictably;
- far-to-approach exposes whether snapshot seeding is required;
- a promotion packet can name one narrow class or conclude `keep_native`.

**Limits:** P7 shadow only, bounded routes, two owned clients at most, no authority flag.

**Assumptions:** local experiments produced stable artifacts and a useful comparator.

**Known limitations/ADRs:** P7 latency and Era16 density add realism but still do not prove
cohort capacity; current Wave 0 visual debt remains separate.

**Result:** pending.

### M7-E11 - One bounded P7 canary

**Goal:** answer one final product question that simulation and shadow cannot answer.

**Objective:** promote only the class/policy named by E10, run a bounded role-reversible
course, rollback automatically, and ask one prewritten visual question.

**Hypothesis:** the promoted claim behaves as shadow predicted and produces no new
visible discontinuity, persistence problem, or recipient error.

**Predicted outcome:** written by E10, not invented immediately before this run.

**Limits:** separate owner authorization, exact artifacts, one claim, automatic timeout,
automatic rollback, no widening.

**Assumptions:** all pre-human gates use the exact bytes and configuration under test.

**Known limitations/ADRs:** human perception remains necessary for presentation quality;
one canary is not a capacity claim.

**Result:** pending.

## How results shape the path

| Finding | Interpretation | Next move |
|---|---|---|
| Synthetic correlation is wrong | Equation or harness is not understood | Stay pure; do not invoke Unity |
| Pure is stable but native capture is incomplete | Instrumentation is the bottleneck | Improve oracle capture, not policy |
| Native disagreement clusters by class | Valheim semantics matter | Add the smallest classifier/grant needed |
| Native disagreement looks random | Missing state or wrong Harmony seam | Find missing context before strict mode |
| Co-presence gap does not reproduce | Prior symptom was likely config-induced | Do not ship fan-out as a fix; measure it only as an alternative |
| Read-copy visibility works without owner changes | Ownership is not required for relevance | Keep ownership native while advancing visibility |
| Read-copy fails only client apply | Transport/queue may be fine | Isolate Unity injection/ownership acceptance |
| Hysteresis reduces unexplained churn | Predictability improves | Test one bounded damping candidate |
| Hysteresis adds long bad-owner dwell | Damping cost is too high | Keep native or change score inputs |
| CPU dominated by enumeration | Selector architecture needs indexing/cache | Invest in spatial snapshot/index work |
| CPU dominated by serialization/delivery | Selection is not the current bottleneck | Preserve native selection and optimize downstream |
| P7 shadow differs materially from local | Local fixture lacks an important dimension | Extend fixture from the observed category, then replay |
| P7 shadow offers no measured advantage | Replacement has not earned complexity | Record `keep_native` and move to another plane |

## Learning cadence

After every analyzed run:

1. append one learning-log row;
2. update only the affected experiment's result and understanding sections;
3. mark assumptions as strengthened, weakened, or broken;
4. select the smallest next experiment from evidence;
5. stop building tooling that no longer answers a live question.

Every five analyzed experiments, write a one-page synthesis:

- what we now know;
- what we still only assume;
- which authority planes have earned more work;
- which ideas were retired;
- what human observation remains unavoidable;
- which scaffolding should become product code, configuration, or be deleted.

## First runnable slice

Build and run only E00-E03 before restoring Unity automation:

1. scenario/event schemas and the small `AuthorityLab` runner;
2. deterministic receipt normalization;
3. geometric relevance generator;
4. N-observer Gateway driver;
5. motion pattern generator;
6. one combined synthesis showing what is ready for E04 native capture.

Then build the minimum lab-only autojoin/command path needed for E04-E06. Do not
restore the old swarm's matrix scheduler, infinite polling, or broad config surface
unless an experiment demonstrates that one of them is still needed.
