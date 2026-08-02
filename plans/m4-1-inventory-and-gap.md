# M4-1 — Turnkey Stack: Inventory & Gap Pass

Status: roadmap discovery, not an operator decision. Run this inventory when the
adoption lane resumes. M4-2/3/4 remain gated until a turnkey demonstration is
actually booked or imminent.

## Objective
A complete inventory of every service in the system with its containerization
status, config/secret needs, and the gap list standing between today and
`docker compose up` on a stranger's machine. This is the scoping doc M4-2
builds from.

## Context
Clarification: the client mod runtime remains on the player's Steam install,
but its historical `.NET Framework/net48` compilation workaround is the Docker
Workbench image. The image mounts Valheim read-only and disables plugin copy;
this is a build capability, not an attempt to containerize the live client.

Known state: the gateway is image-pinned (Dockerfile at `network/mcp/`);
Lumberjacks (net9) builds in the `sdk:9.0` container; the omen-dashboard
telemetry stack is docker; the Valheim dedicated server runs on P7 with the
mod via BepInEx; the config site exists; the client mod runtime (net48) is not
containerized — it rides the player's Steam install and is the deliberate
runtime boundary.

## Steps
1. Walk `infra/`, `network/mcp/`, `Lumberjacks/`, the dashboard stack, and
   P7 deploy notes (`handoffs/`, recent commits). For each service produce a
   row: name / role / image exists? / builds in container? / host-only? /
   ports / volumes / config files / secrets consumed / depends-on.
2. Identify the Valheim server container option (steamcmd-based images are
   standard practice) and what mounting BepInEx + the mod requires.
3. List every secret with its lab-mode answer (generate on first run vs. dummy
   vs. genuinely required) — feeds M4-3.
4. Write `plans/m4-inventory.md` (the output artifact): the table, the gap
   list ranked by effort, and a proposed compose topology diagram (mermaid ok).
5. Flag anything where docs contradict reality — that's a finding, name it.

## Acceptance
- Table covers every process that runs in production today; nothing "assumed".
- Each gap has an effort guess (S/M/L) and blocking-or-not for the demo
  scenario (join local server → kill lands on localhost dashboard).

## Out of scope
Building the compose file (M4-2). No production changes at all.
