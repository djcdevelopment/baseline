# Creative runtime experiments

This family tests whether Lumberjacks can make mod and presentation work observable,
budgeted, routable, and reversible without prematurely changing Valheim authority.

The experiments reuse AuthorityLab's scenario, append-only event, receipt, comparison,
and bounded-failure contracts. Synthetic cost units prove policy shape only. Measured
patch and frame costs must replace them before a live gate is considered.

## Current train

| Experiment | Result | Meaning |
|---|---|---|
| `cre-e01-runtime-envelope` | supported | protected mutations survived; presentation degraded monotonically; route semantics and bounded queue held; repeat hash matched |
| `cre-e02-gateway-pressure-route` | supported | both real Gateway motion paths delivered the same nine selected frames in order while all 23 suppressed decisions stayed out of transport |

Next: complete the patch-load A/B run, map measured cost into CRE-E01, and add
duplicate/reorder/loss/reconnect transport fixtures. No P7 gameplay change is
authorized by these results.
