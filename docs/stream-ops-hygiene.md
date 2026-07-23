# Stream Operations & Hygiene

Building in public is how we share the journey, but everything shown on a live
stream is effectively published forever. This checklist isn't about paranoia —
it's about protecting the humans who trust us. Exposing a volunteer's credential
or a player's identity raises the cost of caring. These practices keep the
workspace safe so we can focus on giving hours back to the community without
anxiety.

## Pre-stream checklist

Run through these before screen-capturing or going live so secrets and
identifiers stay out of frame.

- [ ] **Streaming terminal profile:** launch a dedicated profile with a clean
      environment (no untracked `.env` loaded).
- [ ] **Clear shell history:** start a fresh/ephemeral session so up-arrow doesn't
      surface old secrets.
- [ ] **Clean editor workspace:** close any panes showing `.env`, `.pem`, `.key`,
      or files under `infra/`.
- [ ] **Hide local MCP secrets:** ensure `C:\work\commandcenter\.mcp.json` is
      closed and not visible in any background window.
- [ ] **OBS cropping:** verify the scene crops or excludes sensitive terminal /
      editor panes.
- [ ] **No secret echo:** confirm nothing you plan to run will echo an environment
      secret to stdout.
- [ ] **Safe log target:** confirm the log view you'll demo is an aggregate (safe)
      view, not a raw tail (see below).

## Player-data on screen

Player identities must never be broadcast.

**The rule: aggregate views are safe; raw files and tails are not.**

- **Safe to show raw:** the community dashboard and the v0 telemetry API — these
  are aggregates-only and carry no player ids by design.
- **Never show raw:** `Valheim\BepInEx\config\comfy-network-sense\telemetry-client.jsonl`,
  `gameplay-events.jsonl`, the client BepInEx log (`Valheim\BepInEx\LogOutput.log`),
  or raw server/gateway log tails. These carry identifiers like `playerId`,
  `owner_id`, and player names.

## If a leak happens anyway

Mistakes happen. If a secret flashes on screen, **rotate first, apologize
second** — assume it's compromised and cycle it immediately.

| Secret | Where it lives | How to rotate |
| :--- | :--- | :--- |
| `POSTGRES_PASSWORD` | P7 VM: `/etc/comfy-p7/environment` (0600) | SSH to the VM, edit `/etc/comfy-p7/environment`, then `sudo systemctl restart comfy-lumberjacks-p7` |
| `VALHEIM_TELEMETRY_KEY` | P7 VM: `/etc/comfy-p7/environment` | SSH to the VM, edit the file, then `sudo systemctl restart comfy-lumberjacks-p7` |
| `LUMBERJACKS_CLIENT_ACCESS_KEY` _(embedded into personalized mod zips at enrollment)_ | P7 VM: `/etc/comfy-p7/environment` | SSH to the VM, edit the file, `sudo systemctl restart comfy-lumberjacks-p7`, **then** re-issue affected volunteer packs via `/join/reissue` |
| `LUMBERJACKS_ADMIN_KEY` | P7 VM: `/etc/comfy-p7/environment` | SSH to the VM, edit the file, then `sudo systemctl restart comfy-lumberjacks-p7` |
| `X-Hearth-Key` | Dev box: `C:\work\commandcenter\.mcp.json` (+ the HEARTH gateway key config on OMEN) | Edit the `X-Hearth-Key` value in `C:\work\commandcenter\.mcp.json` and in the HEARTH gateway's key config on OMEN, then bounce the door (`/checkmcp --restart`) |

## Scoped TODO — log redaction

A `--redact` flag / env toggle on the noisiest raw log-tail path (masking
`playerId`, `owner_id`, and player names) would make live log demos safe. It does
**not** exist yet — until it's built, rely on the "never show raw" rule above.
