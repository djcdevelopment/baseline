# GCP burn-rate review — 2026-07-25

## Method / confidence

**Verified:** resource inventory read directly via `gcloud` (instances, disks,
snapshots, addresses, buckets, enabled APIs, resource policies).

**Estimated:** all dollar figures. There is **no BigQuery billing export**
configured on any billed project, so no actual invoiced amounts were readable
from the CLI. Dollar values below are list-price arithmetic against the
verified inventory and should be treated as ±20%.

**Unmeasured:** network egress (Valheim game traffic), Cloud Logging /
Monitoring ingestion. Both bill on volume that is not visible from inventory.

## Scope

| Project | Billing | Compute |
|---|---|---|
| `lumberjacks-exp-20260711-djc` | linked | **all of it** |
| `comfy-em` | linked | none (compute API disabled) |
| `lumberjacks-synthmon-260711` | linked | none (0 instances, 0 disks) |
| `bigtimedemo` | **not linked** | n/a |

No Vertex AI ReasoningEngines / endpoints running. The historical
ReasoningEngine bleed (see ADR-0026) has not regressed.

## Verified inventory — `lumberjacks-exp-20260711-djc`

- VM `comfy-lumberjacks-p7`: **n2-highmem-2** (2 vCPU / 16 GB), us-west1-b,
  status **RUNNING**
- Disks: `comfy-lumberjacks-p7` 40 GB boot + `comfy-lumberjacks-p7-state-v2`
  32 GB, both pd-balanced = **72 GB**
- Static external IP `8.231.129.249` — IN_USE
- Buckets: `comfy-p7-cutover-...` 4.77 GB, `lumberjacks-roadmap-djc` 0.14 GB
- Snapshot schedule `comfy-lumberjacks-p7-daily-snapshot`:
  daily @ 10:00 UTC, `maxRetentionDays: 7`,
  `onSourceDiskDelete: KEEP_AUTO_SNAPSHOTS`

## Estimated monthly split

| Line | Est. $/mo | Share |
|---|---|---|
| n2-highmem-2, 24/7 | ~$76–96 | **~80%** |
| Snapshots (268.8 GB) | ~$7.00 | ~7% |
| Disks (72 GB pd-balanced) | ~$7.20 | ~7% |
| Static IP (attached, running) | ~$2.92 | ~3% |
| Buckets (4.9 GB) | ~$0.10 | <1% |
| Egress | unknown | ? |

## Finding 1 — the disk resize addressed ~12% of the burn

Disk went 190 GB (40 + 150) -> 72 GB (40 + 32).

- Before: ~$19.00/mo
- After: ~$7.20/mo
- **Saved: ~$11.80/mo (~$0.39/day)** out of a ~$3.20/day total.

Real, but the always-on VM is ~80% of spend and was not touched. This is why
the burn rate still feels high.

## Finding 2 — ~250 GB of orphaned pre-cutover snapshots

Retention is 7 days, but `onSourceDiskDelete: KEEP_AUTO_SNAPSHOTS` meant the
old 150 GB disk's auto-snapshots survived its deletion and are not aging out.

| Snapshot | Src disk | Stored |
|---|---|---|
| `...20260717105022-1li4f4a0` | 150 GB | 120.11 GB |
| `...20260718105022-zopa3hsp` | 150 GB | 1.53 GB |
| `...20260719105022-1hf6jta0` | 150 GB | 1.24 GB |
| `...20260720105022-j08pag2n` | 150 GB | 0 GB |
| `...20260721105022-06p03fu7` | 150 GB | 9.03 GB |
| `...20260722105022-27bgp4y5` | 150 GB | 21.01 GB |
| `...20260723105022-nhxiyrky` | 150 GB | 25.52 GB |
| `comfy-p7-state-precutover-20260724` | 150 GB | 72.03 GB |
| **subtotal — dead-disk lineage** | | **250.47 GB** |
| `...20260724105022-f7qxyx9t` | 32 GB | 14.69 GB |
| `...20260725105022-uilyqci2` | 32 GB | 3.65 GB |
| **subtotal — live-disk lineage** | | **18.34 GB** |
| **total** | | **268.81 GB** |

Snapshot storage for a deleted disk now exceeds the live disk footprint.

Secondary observation: 14.69 GB and 3.65 GB daily deltas against a 32 GB disk
are high churn, consistent with the in-container hourly BACKUPS rewriting
blocks daily. Worth confirming that is still wanted in this environment.

## Recommended actions — biggest lever first

### 1. Right-size or schedule the VM (~$25–45/mo, or ~$2.52/day when stopped)

16 GB RAM is generous for a Valheim dedicated server. Options, cheapest last:

- `n2-standard-2` (2 vCPU / 8 GB) — ~$25/mo cheaper
- `e2-standard-2` (2 vCPU / 8 GB) — ~$45/mo cheaper
- Stop when idle — saves compute only; disks and snapshots keep billing

Requires a stop/start. Verify the server's actual RSS before committing.

```
gcloud compute instances stop comfy-lumberjacks-p7 \
  --project=lumberjacks-exp-20260711-djc --zone=us-west1-b

gcloud compute instances set-machine-type comfy-lumberjacks-p7 \
  --project=lumberjacks-exp-20260711-djc --zone=us-west1-b \
  --machine-type=n2-standard-2

gcloud compute instances start comfy-lumberjacks-p7 \
  --project=lumberjacks-exp-20260711-djc --zone=us-west1-b
```

NOTE: terraform drift. Do NOT `terraform apply` from baseline to reconcile
this — the plan destroys the VM plus 4 live resources. Update state manually
or accept the drift.

### 2. Delete orphaned pre-cutover snapshots (~$6.50/mo)

DESTRUCTIVE. These are all lineage of the deleted 150 GB disk. Confirm the
32 GB `state-v2` disk is healthy and the world is intact before running.
Consider keeping `comfy-p7-state-precutover-20260724` until the cutover is
fully trusted — it is the largest single item (72 GB, ~$1.87/mo) but it is
also the rollback point.

```
gcloud compute snapshots delete \
  comfy-lumberjacks-p-us-west1-b-20260717105022-1li4f4a0 \
  comfy-lumberjacks-p-us-west1-b-20260718105022-zopa3hsp \
  comfy-lumberjacks-p-us-west1-b-20260719105022-1hf6jta0 \
  comfy-lumberjacks-p-us-west1-b-20260720105022-j08pag2n \
  comfy-lumberjacks-p-us-west1-b-20260721105022-06p03fu7 \
  comfy-lumberjacks-p-us-west1-b-20260722105022-27bgp4y5 \
  comfy-lumberjacks-p-us-west1-b-20260723105022-nhxiyrky \
  --project=lumberjacks-exp-20260711-djc
```

### 3. Get real numbers — enable BigQuery billing export

The reason this review is estimates rather than invoiced dollars. One-time
setup, then daily per-SKU cost is queryable via `bq`, and this whole review
becomes a query instead of an inventory crawl. Configure at:
Billing -> Billing export -> BigQuery export (standard usage cost).

Also worth setting a billing budget alert — `billingbudgets.googleapis.com`
is already enabled on the project.
