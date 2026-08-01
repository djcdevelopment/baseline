# HEARTH/Mechnet product-boundary audit — 2026-08-01

Scope: every tracked file matching `hearth|mechnet` or `commandcenter|8710`, classified
against [`docs/baseline-vision-and-boundary.md`](../baseline-vision-and-boundary.md),
including the inbound-direction clause added the same day ("Baseline must not report
into, register with, or depend on HEARTH as a destination").

Shipping source code was already clean: the only matches under `Lumberjacks/src/**/*.cs`,
`network/**/*.py`, and `network/**/*.cs` are four authorship-attribution comments in
`Game.Gateway/Endpoints/` and one false positive on Valheim's `hearth` building piece in
`LumberjacksPriorityClassifier.cs:37`. No code calls HEARTH.

## The finding that mattered

The real defect named no private system at all. `network/mcp/etc/start-comfy-gateway.cmd`
resolved its interpreter through a second rung pointing at the operator's private venv,
so the *project-owned* MCP gateway silently preferred the operator's machine. A
name-based search would never have found it, and no content scanner would have flagged
it, because it shipped in no bundle. This is why the regression coverage added below asks
"does the distributable surface reach outside the checkout?" rather than "does any file
say HEARTH?".

## Resolved

| File | Was | Now |
| --- | --- | --- |
| `network/mcp/etc/start-comfy-gateway.cmd` | private-venv interpreter rung | `%COMFY_GATEWAY_PYTHON%`, else PATH — no third rung |
| `network/mcp/README.md` | "use Hearth's OMEN venv", private interpreter path ×2 | project-local venv + `requirements.txt` |
| `network/mod/ComfyNetworkSense/README.md` | private interpreter invoked for MCP tests | `python -m unittest` in the active environment |
| `Lumberjacks/docs/workbench/tools/mcp-mod-channel.md` | "separate from the fleet-wide Hearth gateway"; private-venv fallback documented | generic gateway disambiguation; project-owned startup path only |
| `network/mcp/requirements.txt` | *(did not exist — the pin lived only in the Dockerfile and in prose)* | single declaration; Dockerfile and contributor setup both install from it |

## Deliberately not changed

**The six roadmap journal entries** (`Lumberjacks/src/Game.Gateway/Community/roadmap.html`
lines 2384, 2982-2984, 5394, 5537, 6258, from `docs/roadmap/commit-notes.jsonl`). These
are append-only development provenance. They disclose no credential, private path, or
usable endpoint, and one of them *is* the boundary decision being recorded. Attribution
that work was drafted, routed, or reviewed through HEARTH is legitimate history and stays
byte-for-byte. The journal is append-only by design; the guard added to `roadmap.mjs`
applies to newly authored notes only and explicitly exempts history.

**A blanket `\b(hearth|mechnet)\b` scanner rule** was proposed and rejected. The names are
not secrets and are valid in provenance, boundary documentation, internal architecture
records, optional operator-integration docs, and any sentence distinguishing the project
MCP from private infrastructure. A name ban would suppress accurate architecture language
while missing unnamed coupling — as the launcher defect demonstrates.

## Publication hazard — internal only, exclude from distributable bundles

These are correct as internal records and are **not** being rewritten. They are listed
here because they contain the private endpoint and commandcenter-specific operational
instructions, and are therefore acceptable **only** while they remain internal.

| File | Hazard | Condition |
| --- | --- | --- |
| `Lumberjacks/docs/dashboard/index.html` | `HEARTH … local MCP door, :8710` in a published delegation policy (lines ~500, 518, 700) | Title reads "Community Dashboard: Strategy & Workflow" and the filename invites publication, but it is served by nothing and linked from no community surface. **Must not be published as-is.** |
| `Lumberjacks/docs/community-telemetry-strategy.md` | HEARTH backends, `HearthClient().call_sync(...)`, "from the commandcenter venv" (lines 66-70) | Adopted internal strategy. Not linked from `workbench.json`. Rewrite the delegation paragraph before any community publication. |

Neither is staged by `tools/workbench/New-WorkbenchZip.ps1`, which copies an explicit
allowlist. Both would now be caught by `h.private-hearth-endpoint` /
`f.path-commandcenter` if they ever were.

Lower-priority, same category: `fieldlab/runs/native-valheim/**` capture logs carry
commandcenter paths. Fine as internal evidence; they would fail the scanner if a run
bundle were ever distributed.

## Guards added

1. **`network/mcp/tests/test_distribution_independence.py`** — architecture regression over
   the distributable MCP/toolkit surface only (`network/mcp`,
   `network/mod/ComfyNetworkSense/README.md`, `Lumberjacks/docs/workbench/tools`).
   Internal evidence and provenance are out of scope on purpose. Fails on
   `C:\work\commandcenter`, the private venv, the fleet-worker layout, the private
   endpoint, and user-profile absolute paths; separately pins the launcher's interpreter
   precedence and the existence of a declared dependency file. Verified to fail when the
   original launcher rung is reintroduced.
2. **`tools/workbench/Test-WorkbenchZipPrivacy.ps1`** — `h.private-hearth-endpoint`
   (exact host:port, both spellings; loopback and port 8710 are *not* banned generally),
   `f.path-private-interpreter`, and `f.path-user-profile` (generalized from a single
   hardcoded account). The script's own hardcoded scratchpad path was removed — roots now
   resolve from `$PSScriptRoot` or a `-ScratchRoot` parameter — and a self-inspection test
   asserts the scanner contains no user-specific absolute path.
3. **`Lumberjacks/scripts/roadmap.mjs`** — `validatePrivateEnvironment`, wired into
   `addNote` beside the existing licensing lint, rejecting private paths, the private
   endpoint, credential header values, and private interpreter selection in newly authored
   public notes. It does **not** reject the names HEARTH or Mechnet.
