# Session retro — 2026-08-10 (Quest Studio to native multiplayer)

## One-line

Split authoring, runtime, and rehearsal into three products; built the file-first vertical through durable
multi-stage mutation; iterated the in-game workflow with the operator; and proved one certified experience
succeeds on an ordinary OMEN listen host while the identical i5 peer fails closed.

## What shipped in the working set

- A Unity-free `ComfyQuestContracts` implementation for experience validation, deterministic evaluation,
  canonical hashes, pack inspection, semantic versions, collisions, and atomic activation.
- A dedicated `ComfyQuestRuntime` plugin with explicit file loading, compact F9 UX, two-press CHECK/CAST,
  namespaced Charm references, durable workflow state, exactly-once actions, timers, rewards, bounded marked
  spawns, marked-only cleanup, version selection, rollback, and immutable receipts.
- A loopback Quest Studio thin vertical with structured authoring, certification, immutable history, semantic
  diff, authenticated publication, and receipt refresh over the same file contract.
- The architecture plan and four SVG views: data flow, stack, contracts, and implementation status.
- A native multiplayer acceptance harness and operator workbook using OMEN as an ordinary private listen host
  and i5 as a Steam Friends peer. AM4 and Lumberjacks cutover infrastructure are explicitly outside it.

## The evidence

- Shared suite: 351 passing tests. Runtime Release: zero warnings and zero errors.
- OMEN solo acceptance covered explicit hot loading, selection, rollback, exact-bound-object events,
  duplicate suppression, two-stage progress, durable timers, one-Wood reward, marked floor spawn, and cleanup.
- Native run `quest-peer-20260810-native-r2` activated content hash
  `1dbfaffa178a920325f19f00e8ba69abd52a82114d9447572afe3ea7a5776a5c` on both machines.
- OMEN listen host executed all six stable action IDs and terminal transition `complete`.
- i5 returned `mutation_authority_unavailable` and executed zero actions.
- Both temporary Quest Runtime configs restored to their exact pre-run SHA-256 values.

## What went well

The operator loop was unusually productive. Each live pass had one concrete objective and visible expected
result; screenshots immediately drove better target guidance, workflow hierarchy, key choice, outcome history,
and the final CHECK/CAST interaction. The runbook kept machine context explicit, which made a two-PC test feel
like a progression rather than a relay race.

The file boundary held throughout. Studio, manual copies, runtime controls, receipts, and the prospective MCP
surface all meet at `.questpack`; no watcher or browser-to-game command channel was needed. Runtime authority
also failed at the intended boundary: the peer could load and inspect the same bytes but could not inscribe or
execute them.

## What went wrong

The first multiplayer harness targeted AM4 because a proven three-machine launcher already existed. That
reused syntax but imported the wrong product context: AM4's Lumberjacks cutover world is infrastructure under
test, while Quest v1 authority is deliberately solo/listen-host. Disarming cutovers to make an unrelated test
work was the warning. The right topology was the ordinary player topology: OMEN hosts, i5 joins.

The i5 drawer then rendered as a black shell. BepInEx's main log showed Runtime loaded, which initially made
the installation look complete. Unity's `Player.log` held the real failure: `Newtonsoft.Json` was present on
OMEN from prior work but absent on i5. Runtime could start and draw its window title, then failed on the first
content read. The harness deployed project DLLs but not the transitive runtime dependency.

Finally, the collector expected terminal status `completed`; the runtime emits `complete`. All six actions and
the visible cleanup were correct, but the evidence gate rejected the run. Reading the receipt shape fixed the
collector without replaying successful gameplay.

## Lessons

1. **Use the product's authority topology for acceptance.** A convenient server harness is not neutral when
   that server is itself a networking experiment.
2. **A plugin loading is not a package loading.** Deployment certification must include and hash every runtime
   dependency, then exercise one code path that resolves each dependency.
3. **Read both game logs.** BepInEx proved plugin startup; Unity `Player.log` proved the frame-time exception.
4. **Human-visible success and machine evidence should cross-check each other.** Neither replaces the other;
   disagreement means inspect the gate before repeating the operator's work.
5. **One machine, one objective, one expected result works.** Preserve the atomic workbook style for future
   creator-loop and Lab migration acceptance.

## Remaining frontier

- Complete browser-originated publication, receipt refresh, and rollback as one retained creator trace.
- Build the rich graph/Grimoire, replay/import, and Arcane Sight slices on the shared contract.
- Slim Quest Lab's default surface after Studio parity, keeping the native host/peer run as a regression gate.
