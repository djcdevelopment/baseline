# Workbench appliance convergence plan

Status: planned follow-on, 2026-08-02. Existing PD-5 policy determines the
direction; this is execution work, not a reopened product decision.

## Outcome

Baseline presents one local Workbench installation and one launcher even though
the appliance legitimately contains several service images. A person chooses a
declared runtime mode and gets the same browser, capability registry, receipts,
port contract, and recovery path:

- **Local:** Workbench, Gateway services, persistence, and the local Valheim lab
  are composed for full offline-first testing.
- **Remote:** the local Workbench connects directly to the admitted GCP services
  when they are running; it does not silently start duplicate local authorities.
- **Hybrid Lab:** local game/test execution uses an explicitly selected local or
  remote service endpoint per declared adapter, with the choice visible in Home
  and every receipt.

HEARTH remains Derek's independent machine-wide MCP on `8710`. Baseline's
profile-scoped Dev/Lab MCP remains a project component on loopback `8721`; neither
is bundled into or substituted for the other.

## Current gap

The implementation currently has three independently launched Compose projects:

| Project | Current role | Published ports |
|---|---|---|
| `lumberjacks-companion` | Workbench/Companion, optional SDK runner, optional Baseline Dev MCP | `8080`, Dev/Lab `8721` |
| `lumberjacks-local` | Gateway, EventLog, Progression, Operator API, Postgres | `4000`, `4002`, `4003`, `4004`, `4005/udp`, `5435` |
| `comfy-valheim-lab` | active local Valheim server | `2456-2457/udp` |

Those are valid process boundaries but not yet one turnkey operating experience.
`Start-LocalCompanion.ps1` is canonical only for the first project, so it cannot
currently prove that the service stack, server, tools, ports, and selected local/
remote authority all belong to one installation. Some Dev/Lab tools also depend
on a source mount and host runner rather than a versioned distribution payload.

## Ordered implementation

### AC-1 — Inventory and one port/mode contract

- Add a machine-readable appliance manifest naming every service, image, profile,
  durable volume, internal endpoint, published port, and supported mode.
- Reserve ports once. Home must show the selected origin and distinguish internal,
  loopback, LAN-test, Valheim, and remote endpoints.
- Extend the existing identity checks so a reachable service with the wrong
  project, revision, image, mode, or data root fails closed.

Done when one read-only command explains the whole installation without requiring
`docker compose ls`, source knowledge, or port folklore.

### AC-2 — One distribution and launcher

- Introduce one top-level versioned Compose distribution with Local, Remote, and
  Hybrid Lab profiles. Reuse the existing service images; do not collapse them
  into a monolith merely to reduce image count.
- Make one launcher initialize configuration, select the mode, preserve named
  state, converge the requested profile, and open `http://127.0.0.1:8080`.
- Keep the old launchers as compatibility shims until migration/recovery evidence
  proves the new entry point; then mark them non-canonical.

Done when a clean machine and this workstation both reach the same Workbench from
one command and one project identity.

### AC-3 — Gather the shipped tool surface

- Classify every Workbench capability as runtime-safe, Dev/Lab source-build, host
  adapter, or remote adapter.
- Bake runtime-safe tools and schemas into versioned images/packages. Keep the
  .NET SDK and source mount in Dev/Lab only. Package bounded Windows adapters with
  the distribution and verify every UI command path exists.
- Generate the Web and Baseline MCP catalogs from the same capability manifest;
  a catalog count is never evidence that a tool is runnable.

Done when Production needs no repository checkout and Dev/Lab explicitly reports
which capabilities require source, Valheim assemblies, a host adapter, or a remote
machine.

### AC-4 — Preserve and migrate owned state

- Map the existing Companion, Gateway/Postgres, and Valheim volumes/state roots to
  the new project without copying over a running writer.
- Rehearse inventory, hash comparison, cutover, rollback, and ordinary recreate
  using the existing `tools/` safety lanes.
- Prove that selecting Remote does not delete or fork Local state and that returning
  to Local resumes the same declared installation.

Done when a failed migration has a tested rollback and a normal image recreate
retains worlds, configuration, backups, enrollment association, and receipts.

### AC-5 — Human acceptance and retirement

- Run the no-coaching protocol from Home: identify whether the server is up, who is
  online, what is executing, which authority/mode is selected, where evidence lives,
  and the one recommended next action.
- Run Local with GCP stopped, Remote with local authorities stopped, and one explicit
  Hybrid Lab configuration. No fallback may silently change mode.
- After those receipts pass, retire competing “canonical” language and publish one
  reconstruction/recovery path.

## Non-negotiable gates

- No Docker socket in the web container and no arbitrary shell capability.
- No HEARTH endpoint, key, provider, ledger, or lifecycle dependency in the
  distribution.
- No destructive volume migration without a read-only inventory and recoverable
  rollback.
- No claim of turnkey completion from image build or structural HTML checks alone;
  clean-machine and human comprehension evidence are required.

## Finite remaining queue

1. Re-observe the repaired live Home on the clean committed image.
2. Implement AC-1 and AC-2 as the next Workbench engineering slice.
3. Implement AC-3 and AC-4, then run clean-machine/recreate evidence.
4. Close AC-5 and the existing WB-S2.13 unfamiliar-user/mobile gate together.
