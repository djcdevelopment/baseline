# Runbook — testing `isolate` forward into certainty

- Date: 2026-08-07
- Subject: the untracked `isolate_implementation_plan.md` at the baseline repo root
- Posture: **do not execute that plan as written.** Its Phase 2 command is destructive and its
  Phase 1 gate cannot fail. Both are proven below.

This runbook replaces it with ordered gates. Each gate is cheap, read-only unless stated, and
has a pass criterion that a broken system can actually fail. They are ordered so the gate most
likely to kill the plan runs first.

---

## Part 0 — What was verified before writing this (2026-08-07, OMEN)

Everything in this table was observed, not inferred.

| # | Claim | Evidence |
|---|---|---|
| 1 | `isolate` is a single-commit repo (`ec74746`) with **no git remote**. | `git log`, `git remote -v` in `C:\work\isolate` |
| 2 | `C:\work\isolate\docker\valheim-lab.compose.yml` is **byte-identical** to `fieldlab/autonomous/valheim-lab.compose.yml`. | `diff` returned clean |
| 3 | Both declare `name: comfy-valheim-lab` — the **same compose project as the currently running lab**. | `docker compose ls` shows `comfy-valheim-lab` running(1) |
| 4 | `comfy-valheim-lab-valheim-server-1` has been **Up 9 hours** on `ghcr.io/community-valheim-tools/valheim-server:latest`. | `docker ps -a` |
| 5 | With no env file, `docker compose -f C:\work\isolate\docker\valheim-lab.compose.yml config` **succeeds** (warnings only) and resolves the server world mounts to `/state/server/config` and `/state/server/data` — blank host paths. | `docker compose config --format json` |
| 6 | Port **8721 is already owned** by `lumberjacks-companion-dev-mcp-1` (project `lumberjacks-companion`, image `lumberjacks-companion-dev-mcp:local`). Its `/identity` answers today. | `docker ps`, live GET `/identity` |
| 7 | Port **8720 is closed**. The isolate compose publishes the gateway on `${COMFY_GATEWAY_PORT:-8720}`. | live GET refused |
| 8 | `gateway_identity()` **hardcodes** `"project": "baseline"`. | `network/mcp/comfy_gateway/kernel/gateway.py:175` |
| 9 | `Test-WorkbenchMcpIdentity.ps1` expects `project = 'baseline'` **and** requires provider `comfy_gateway.toolsurface.workbench`; the isolate compose `command:` mounts only `valheim,inference`. | script params vs. compose lines 104–107 |
| 10 | `valheim-lab.env.example` sets `COMFY_ROOT=C:/work/baseline` — the gateway build context points back at **baseline**. | `fieldlab/autonomous/valheim-lab.env.example` |
| 11 | `ghcr.io/community-valheim-tools/comfy-gateway:latest` (the compose default image) is **not present locally**; the only gateway image on disk is `comfy-valheim-lab-comfy-gateway:latest`, built 2 weeks ago. | `docker image ls` |
| 12 | `isolate`'s own test suite is **RED**: 2 of 11 fail — `test_distribution_independence` asserts `network/mod/ComfyNetworkSense/README.md` exists, which PD-8 deliberately left in `baseline`. | `python -m unittest discover -s network\mcp\tests` |
| 13 | **i5 is offline.** `ssh i5` → connection timed out to `i5-laptop.tail8e749c.ts.net:22`. | `ssh -o BatchMode=yes` |

### The two findings that matter most

**A. The plan's Phase 2 command silently destroys the running lab's world state.**

```
docker compose -f C:\work\isolate\docker\valheim-lab.compose.yml up -d valheim-server comfy-gateway
```

Same project name → it adopts the live `comfy-valheim-lab` project. `AUTONOMOUS_ROOT` is unset →
the world mounts become blank-rooted absolute paths. Compose does **not** error; it recreates the
running server against an empty state directory. This is the bad failure mode: green output,
detached world.

**B. The plan's Phase 1 gate is incapable of failing usefully.**

Probing `127.0.0.1:8721` attests the *lumberjacks companion* container, which is up and healthy
and has nothing to do with `isolate`. And because `gateway_identity()` hardcodes
`project: "baseline"`, an isolate-built gateway is **indistinguishable from a baseline one** by
the very endpoint PD-8 nominates as the contract boundary. Provenance attestation that cannot
tell the two repos apart is decoration.

---

## Part 1 — Gates

Legend: **[RO]** read-only · **[FIX]** changes files · **[MUT]** starts/stops containers.

### G0 — Freeze the blast radius **[RO]**

Confirm the live lab is what you think it is before touching anything.

```powershell
docker compose ls --all
```

**PASS:** `comfy-valheim-lab` shows `running(1)` and its config-file list includes
`C:\work\baseline\fieldlab\autonomous\valheim-lab.compose.yml`.
**Then:** never invoke a compose command against the isolate file without `-p` (see G3).
**Note:** that project's recorded config list still carries a `C:\work\comfy\...` path from the
retired checkout. The project is already carrying stale identity; adding a third file to it is
how you lose the world.

---

### G1 — Contract-drift guard **[RO]**

The premise of PD-8 is that `isolate` and `baseline` are separable. Today they are copies.

```powershell
fc.exe C:\work\baseline\fieldlab\autonomous\valheim-lab.compose.yml C:\work\isolate\docker\valheim-lab.compose.yml
```

**PASS today:** "no differences encountered" — which is the *problem*, not the success.
**What it proves:** there is no boundary yet, only duplication. Two identical files with no sync
check and no owner is a divergence bomb. The plan's own touchpoint list makes it worse: it
proposes `[MODIFY] fieldlab/autonomous/valheim-lab.compose.yml` (the **baseline** copy) while
claiming to test `isolate`.
**Decision required before any further gate:** which copy is authoritative? Until that is
answered, G2 has no defensible target.

---

### G2 — Make the boundary testable **[FIX]**

These are not tests. They are the minimum changes that make G4 onward capable of returning a
meaningful failure. Do them in `isolate`.

1. **Give the identity endpoint a variable project.** `gateway.py:175` must read the project from
   config/env (e.g. `COMFY_PROJECT`, defaulting to `baseline` for compatibility) instead of a
   literal. Without this, no downstream attestation can distinguish the repos.
2. **Give the compose file safe defaults.** `${AUTONOMOUS_ROOT}` and `${COMFY_ROOT}` must either
   carry defaults that point inside `isolate`, or the file must refuse to render without them.
   A blank-string substitution that yields a valid-looking bind mount is the failure in finding A.
3. **Rename the compose project.** `name: comfy-valheim-lab` → `name: isolate-lab` (or always pass
   `-p`). Same-name adoption of a live project is the destructive path.
4. **Repair or scope the red tests.** `test_distribution_independence` asserts a path PD-8
   intentionally left behind. Either narrow its scope list to what `isolate` owns, or record why
   it stays red. AGENTS.md forbids publishing images with tests failing, so this blocks the
   promotion lane as written.

**PASS:** `python -m unittest discover -s network\mcp\tests` is green, from `C:\work\isolate`
with `PYTHONPATH` set to `C:\work\isolate\network\mcp`.

---

### G3 — Bring up the isolate gateway **alone**, in its own project **[MUT]**

No server, no clients, no port collision. Write `C:\work\isolate\docker\isolate-lab.env` first:

```
COMFY_ROOT=C:/work/isolate
AUTONOMOUS_ROOT=C:/work/isolate/labstate
COMFY_GATEWAY_PORT=8722
COMFY_PROJECT=isolate
```

Render before running — this is the step that would have caught finding A:

```powershell
docker compose -p isolate-lab --env-file C:\work\isolate\docker\isolate-lab.env -f C:\work\isolate\docker\valheim-lab.compose.yml config
```

**PASS:** zero "variable is not set" warnings, project renders as `isolate-lab`, and every
`source:` path begins with `C:/work/isolate`.
**FAIL → stop.** Any blank-rooted source path means G2 step 2 is not done.

Then, gateway only, built from isolate's own context (the ghcr image does not exist locally —
`--build` is mandatory, not optional):

```powershell
docker compose -p isolate-lab --env-file C:\work\isolate\docker\isolate-lab.env -f C:\work\isolate\docker\valheim-lab.compose.yml up -d --build comfy-gateway
```

**PASS:** `docker ps` shows `isolate-lab-comfy-gateway-1` on `0.0.0.0:8722->8720`, and
`comfy-valheim-lab-valheim-server-1` is **still Up with its original uptime unbroken**.
**FAIL:** if the running server restarts, you adopted the wrong project — `docker compose -p
isolate-lab down` immediately and re-check `-p`.

---

### G4 — Identity attestation that can actually fail **[RO]**

Negative control first. This must **fail**, or the gate is blind:

```powershell
powershell -ExecutionPolicy Bypass -File tools\workbench\Test-WorkbenchMcpIdentity.ps1 -Profile Lab -McpPort 8721 -ExpectedImage "isolate-lab-comfy-gateway:latest"
```

**PASS = a non-zero exit / image mismatch verdict.** Port 8721 is the companion container. If this
returns `verdict: passed`, the gate is not reading what it claims to read and nothing after it
counts.

Then the real probe:

```powershell
powershell -ExecutionPolicy Bypass -File tools\workbench\Test-WorkbenchMcpIdentity.ps1 -Profile Lab -McpPort 8722 -ExpectedImage "isolate-lab-comfy-gateway:latest"
```

**Expected result today: `verdict` fails on a missing required provider.** The script requires
`comfy_gateway.toolsurface.workbench`; the compose `command:` mounts only `valheim,inference`.
That is a genuine contract gap, not a flake. Resolve it deliberately — either add the provider to
the compose command, or relax the requirement for the Lab profile and write down why.
**PASS:** the verdict is understood and its `identity.image` / `identity.project` fields match the
isolate build. **This is the first moment the decoupling is actually evidenced.**

---

### G5 — Server + telemetry, without adopting the live lab **[MUT]**

Only after G4 gives a clean, isolate-attributable identity.

```powershell
docker compose -p isolate-lab --env-file C:\work\isolate\docker\isolate-lab.env -f C:\work\isolate\docker\valheim-lab.compose.yml up -d valheim-server
```

**Prerequisite:** decide the world question first. `AUTONOMOUS_ROOT=C:/work/isolate/labstate` is a
**fresh empty world**. That is the correct choice for a boundary test. Do not point it at the
baseline state root to "save time" — that reintroduces the coupling you are testing for, and
per standing practice we do not make defensive copies of test data.

**PASS:** the new server container starts under `isolate-lab-*`, ports do not collide with the
live 2456–2457/udp binding (change `SERVER_PORT` in the env file if they do), and the live lab is
still untouched.

Quiescence check — note this talks to the **Lumberjacks gateway on :4000**, not the MCP gateway,
so it reports on the live lab and is a *safety* check, not an isolate check:

```powershell
powershell -ExecutionPolicy Bypass -File tools\workbench\Test-LocalLabQuiescence.ps1
```

**PASS:** zero peers, no named players — i.e. nothing you are about to disturb has a human on it.

---

### G6 — Multi-peer motion: **BLOCKED, do not attempt today**

The plan's Phase 3 requires i5. **i5 is offline** (verified: TCP timeout to
`i5-laptop.tail8e749c.ts.net:22`). Re-probe before planning around it:

```powershell
powershell -ExecutionPolicy Bypass -File tools\i5\Test-I5Link.ps1
```

**If it fails:** stop. Do not substitute a single-host loop and call it a multi-peer result — a
one-host run cannot exercise the ZDO delivery path the plan claims to verify, and reporting it as
such is the exact failure this runbook exists to prevent.
**What is legitimately runnable single-host now:** G3–G5 (gateway provenance + telemetry file
generation). That is a *runtime boundary* result, not a *netcode* result. Label it that way.

---

### G7 — Evidence receipt **[FIX]**

Write `fieldlab/evidence/isolate-boundary-verification-20260807.json` recording, per gate: the
command, the raw verdict, and pass/fail. Include the **negative control result from G4** — a
receipt without a demonstrated failure mode is not evidence. Explicitly record G6 as `blocked:
i5_offline` rather than omitting it.

---

## Part 2 — What this buys you, and what it does not

**Certainty you get from G0–G5:** that `isolate` can stand up its own gateway from its own source,
under its own project, with mounts that resolve inside its own tree, and that `/identity` can tell
you which of the two repos you are talking to. That is precisely the PD-8 claim and nothing more.

**Certainty you do not get:** anything about multi-peer ZDO delivery, motion capture, or the
promotion lane. The promotion lane in `isolate/README.md` step 3 assumes a published
`ghcr.io/community-valheim-tools/comfy-gateway` image that does not exist locally and lives behind
a repo with no remote configured. Until `isolate` has a remote and a published tag, `baseline`
cannot "consume versioned images" — it can only rebuild from a sibling directory, which is the
coupling PD-8 set out to remove.

**Sequencing recommendation:** G1's authority question and G2's four fixes are the real work. G0
is the safety interlock. Run G0 today regardless — the plan file is sitting in the repo root and
the command in it is one paste away from taking the live world down.
