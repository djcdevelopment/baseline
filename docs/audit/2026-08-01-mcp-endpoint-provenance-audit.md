# MCP endpoint provenance audit — 2026-08-01

Status: audit completed read-only; the later operator-authorized retirement is
recorded under "Subsequent resolution" below. The durable lifecycle policy
remains [PD-6](../decisions/pd-6-development-mcp-lifecycle.md); the execution
sequence is in the [Workbench Saga](../../plans/workbench-v1-saga-strategy.md).

## Finding

The default MCP endpoint was not a project identity boundary. At audit time,
both the active Baseline checkout and the retired Comfy checkout configured
their clients for the same loopback URL:

```text
http://127.0.0.1:8720/mcp
```

At the time of the audit, that port was owned by PID 14164, whose live process
lineage was:

```text
PID 14164
  python.exe -m comfy_gateway.kernel.gateway
    --providers comfy_gateway.toolsurface.valheim,
                comfy_gateway.toolsurface.inference,
                comfy_gateway.toolsurface.matrix
    --host 127.0.0.1 --port 8720
  parent: cmd.exe /c C:\work\comfy\fieldlab\scripts\start-comfy-gateway.cmd
```

The wrapper changes directory to `C:\work\comfy` and sets
`PYTHONPATH=C:\work\comfy\network\mcp`. Its source tree has a different
SHA-256 and file set from the active Baseline gateway, including no
`toolsurface/workbench.py` provider.

This was not merely an agent's transient working directory. The enabled
`ComfyGatewayBoot` scheduled task launches that retired wrapper at logon. Its
last run was 2026-07-30 20:22:37; PID 14164 started two seconds later.

HEARTH is a separate service: `HearthGatewayBoot` launches
`C:\work\commandcenter\hearth\etc\start-hearth-gateway.cmd`, and the live
HEARTH listener was observed on `127.0.0.1:8710`. The old `:8720` process is
therefore best classified as a retained old Baseline/Comfy gateway, not the
HEARTH listener. Whether the scheduled task should be retired remains an
operator decision; no process or task was changed during this audit.

## Evidence impact

The source-resolved ledgers split recent MCP traffic into two provenance
classes:

| Ledger | Recent calls | Interpretation |
|---|---:|---|
| `C:\work\comfy\network\mcp\var\ledger\events.jsonl` | 6 | Default-port Valheim calls: `valheim_mcp_health`, four `valheim_server_log_tail` calls, and `valheim_handshake_trace`; these were served by the retired source tree. |
| `C:\work\baseline\network\mcp\var\ledger\events.jsonl` | 4 | `workbench_*` calls at 2026-08-01T17:40Z through the explicit alternate development port; these do not prove that the old `:8720` listener served Workbench. |

Consequences:

1. Default-port Valheim MCP evidence from the July 31/August 1 development
   window is **provenance-suspect**, not automatically invalid. It must be
   rerun or explicitly reclassified after the Baseline endpoint passes an
   identity check.
2. Workbench API, browser, Companion `:8080`, and Lumberjacks Gateway `:4000`
   evidence remains a separate class unless a receipt explicitly names the
   MCP transport.
3. A `200 /healthz` response is insufficient evidence. The expected source
   root, source revision/hash, provider set, profile, port, caller registry,
   and ledger path must agree before an MCP result can be accepted.

## Required control before further MCP-sensitive work

The next Workbench checkpoint must establish one project-owned Dev MCP identity
on an explicit loopback port (the current working candidate is `8721`) while
leaving the unknown `:8720` owner untouched. The check must:

- inspect the listener and its parent process/task;
- obtain a machine-readable gateway identity, not only health;
- compare expected Baseline source root, revision/hash, providers, profile,
  caller registry, and ledger directory;
- refuse to treat a mismatched endpoint as the project Dev MCP;
- record the endpoint identity in the job receipt and support export;
- quarantine historical default-port MCP receipts until they are rerun or
  reclassified by the operator.

Only after this gate passes should the plan resume MCP-sensitive physical
testing or claim the Web/MCP shared-surface requirement as complete.

## Adaptation landed after the audit

The active Baseline gateway now has an authenticated, read-only `/identity`
route (`baseline.mcp.identity.v1`). The Dev/Lab Compose profile passes its
profile, published port, source revision/dirty state, image, provider set,
caller registry, and ledger metadata into that response. The packaged
`tools/workbench/Test-WorkbenchMcpIdentity.ps1` checker fails closed with
`mcp_endpoint_unavailable` or `mcp_endpoint_identity_mismatch`; it never stops
an unknown listener. This is a control implementation, not a live acceptance
receipt yet.

The optional `ComfyNetworkSense` Raven/MCP helper was subsequently migrated off
legacy `:8720` literals. Its configuration now defaults disabled, accepts only
an explicit loopback HTTP(S) origin, and cannot be enabled from the in-game
transport toggle unless the Dev/Lab configuration first opts in.

The active checkout's `fieldlab/scripts/start-comfy-gateway.ps1` was also a
future ambiguity source: it hard-coded a user-profile Python path and `:8720`.
It now derives the repository root, resolves Python from `COMFY_GATEWAY_PYTHON`
or `PATH`, and defaults to the explicit `:8721` Dev port. That source change did
not itself alter the scheduled task; the later host retirement is recorded below.

## Subsequent resolution

After the read-only audit, Derek authorized the Workbench plan to move forward.
The audited `ComfyGatewayBoot` task was disabled without unregistering it, and
the exact identity-checked Python PID 14164 was stopped. Verification found no
remaining host listener on `8720`; HEARTH remained listening on `8710` as PID
39328. Six Claude Desktop clients lost only their stale Comfy MCP connections;
their separate HEARTH connections remained established.

Before retirement, the live Baseline Dev container passed the authenticated
identity check on host `8721` with project `baseline`, profile `Dev`, revision
`66c80dcec04ff10f0467e36b83d224bb6e22d745`, image
`lumberjacks-companion-dev-mcp:local`, the Workbench provider, the Baseline
caller registry, and the Baseline ledger. The minimum quarantined evidence set
was then rerun through that endpoint: `valheim_mcp_health`, a filtered
`valheim_server_log_tail`, and `valheim_handshake_trace` all produced successful
events in `network/mcp/var/ledger/events.jsonl` at 2026-08-01T22:39:20Z.
