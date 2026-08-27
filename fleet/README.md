# Living fleet status

Baseline owns one small statement of fleet intent in [`intent.json`](intent.json).
The Pages workflow combines it with live GitHub facts twice an hour and publishes
three tables at `/status/`: current movement, next outcomes, and cross-repository
pins. Generated HTML, Markdown, and JSON exist only in the Pages artifact; scheduled
runs do not create commits.

Architecture visuals:

- [`repository-architecture.svg`](repository-architecture.svg) ([PNG
  export](repository-architecture.png)) explains why the five implementation
  repositories are sovereign, what each owns, the internal Quest decomposition, the
  permitted artifact seams, and how they tie back to Baseline.
- [`fleet-status-workflow.svg`](fleet-status-workflow.svg) shows the status data flow,
  Actions jobs, task sequence, timers, and feedback loops.

See [`WORKFLOW.md`](WORKFLOW.md) for the complete status-workflow narrative, failure
semantics, and operating procedure.

## Agent rhythm

Routine product work needs no Baseline follow-up. Repository HEAD, current-head CI,
activity age, and declared seam values are observed automatically.

Change `intent.json` only when one of these materially changes:

- current focus;
- next user-visible outcome;
- the proof that makes that outcome done;
- a blocker or PD-4 classification; or
- a repository or integration seam.

Update `intent_as_of` only after rereading the row. At 31 days the public projection
marks the declaration stale, but it continues to publish. Public text must not contain
credentials, private paths, tailnet endpoints, or private repository implementation
details.

## Verification and preview

```powershell
python tools\fleet\render_status.py --check-config
python -m unittest tests.test_fleet_status -v
python tools\fleet\render_status.py `
  --fixture tests\fixtures\fleet_status\github.json `
  --now 2026-08-19T12:00:00Z `
  --output <temporary-directory>
```

Use the Pages workflow's manual dispatch for an immediate public refresh. Otherwise a
product change appears on the next run at minute 17 or 47.

## GitHub access and failure behavior

Configure the repository secret `FLEET_READ_TOKEN` as a fine-grained, read-only token
with metadata, contents, and Actions access to the six fleet repositories. The public
repositories can fall back to the workflow token; Isolate cannot.

A malformed tracked intent stops deployment and leaves the last valid page live. A
remote repository/API failure instead publishes an `UNKNOWN` row, then fails the
separate audit job. Isolate exposes only centrally reviewed wording and a coarse CI
state; its URL, SHA, commit subject, workflow URL, paths, and raw errors are withheld.
