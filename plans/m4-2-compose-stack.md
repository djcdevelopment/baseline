# M4-2 — Turnkey Lab Compose Stack

## Objective
`docker compose up` brings up the whole server-side system locally —
valheim-server (BepInEx + mod), gateway, telemetry, dashboard, config-site —
with named services so the compose file doubles as the architecture diagram.
A compose stack, NOT a single image: seeing the pieces move is the point.

## Context
Prereq: M4-1 inventory (read `plans/m4-inventory.md` first — it has the
topology, ports, and gap list). Secrets handling comes from M4-3; if M4-3
hasn't landed, stub with generate-on-first-run placeholders and note it.
The client mod stays on the player's Steam install — the demo (M4-4) uses the
tester's own Valheim client as the "player."

## Steps
1. Create `infra/lab/docker-compose.yml` + `infra/lab/README.md`. Service
   names are legible roles: `valheim-server`, `gateway`, `telemetry`,
   `dashboard`, `config-site`. Explicit `depends_on`, healthchecks per
   service, one named network, volumes for world data and logs.
2. Valheim server: steamcmd-based image with BepInEx and the built mod
   mounted; world/save volume; document the "Game server connected" readiness
   line as the healthcheck/wait condition (world reload is slow — bake the
   wait in, don't let users judge too early).
3. Reuse existing images/Dockerfiles wherever the inventory says they exist;
   only write new Dockerfiles where the inventory marked a gap.
4. Lab profile defaults: aggregates-only API on localhost, dev keys, no
   external egress required after image pull.
5. Smoke script `infra/lab/smoke.ps1`: compose up → wait healthy → hit
   dashboard and config-site endpoints → report. This becomes a runnable
   proof (M3-4).

## Acceptance
- Fresh machine path documented: prerequisites (Docker Desktop/WSL2 on
  Windows), one command, expected wait time, what "up" looks like.
- Smoke script passes locally.
- compose file readable as a system map — a newcomer can name the five pieces
  and their arrows from the file alone.

## Out of scope
Client-side anything; production deploy changes; peering (M6).
