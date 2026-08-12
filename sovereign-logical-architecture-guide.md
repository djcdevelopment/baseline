# Sovereign Sharding & Logging Logical Architecture Guide

This guide describes the logical architecture of the decoupled Valheim multiplayer
sharding system and the sovereign repository topology that carries it.
(A companion diagram will be added when drawn; an earlier draft referenced
`sovereign-logical-architecture.png`, which was never produced.)

**Corrected 2026-08-11** against the actual tree as part of the repo-split plan
(see `docs/decisions/` PD-9 once landed). Every component below is labeled:

- ✅ **shipped** — code exists, tested, in the tree today
- 🟡 **substrate** — partial machinery exists; the described behavior does not
- 🔮 **planned** — no code exists; design intent only (PD-4: `UNVERIFIED`)

To preserve the lightweight integrity of the core game, the architecture is
divided into sovereign repositories across client, server, and container
environments.

---

## 1. Repository Modularity & Boundaries (five repos)

### 🗂 baseline (Index)
The architecture and questions repo: cross-repo map (`REPO-MAP.md`), port
registry (`docs/PORTS.md`), decision register (PDs), corpus/site, program
evidence archive. Ask here first instead of scanning the fleet. Holds no
product code after the split.

### 🟦 networksense (Telemetry Baseline)
Optimized strictly for client-side diagnostic visibility, HUD updates, and
localized gameplay optimizations. Runs universally on any client; zero
awareness of containerization, routing, or Docker environments.
*   ✅ **Diagnostics HUD:** console-driven (`network_sense_hud`,
    `network_sense_detail`); shows heartbeat age, ping-age jitter, fps, and
    frame-time p95. There is **no default keybinding** — all shortcuts ship as
    `KeyCode.None` by design. (An earlier draft called this "F6 HUD (Sovereign
    Hearth)"; neither the binding nor that name exists in the tree.)
*   ✅ **ScoreCalculator:** computes the player's network "Owner Score"
    (`Core/Scoring/ScoreCalculator.cs`); surfaced in HUD, panel, and telemetry.
    Whether the score feeds zone-ownership lease negotiation is 🔮 — the lease
    runners exist, the score→lease link does not.
*   🟡 **Low Impact mode (was "Farm Mode"):** the replication-thinning substrate
    exists (`ZdoThinHz`, shipping at 5.0 Hz — not 1.0), and the design doc
    (`network/player-opt-in-modes.md`) specifies **+5% stamina regen while out
    of danger** — not the 10% movement+stamina buff an earlier draft claimed.
    No gameplay buff code is shipped.
*   🔮 **Huddle Indicator:** squad huddles for clock sync and race-free lease
    negotiation. Design intent only; zero code.

### ⬜ lumberjacks-platform (Core Transport Foundation)
The Steam-free network transport layer, gateway services, and deployment
program. (New repo name — `Lumberjacks` is the retired archive.)
*   ✅ **C7 (Steam-Free Cold Join):** bypasses Steam matchmaking/lobbies/auth;
    retained evidence in `fieldlab/evidence/c7-steam-free-cold-join/`.
*   ✅ **WebSocket & UDP Session Planes:** reliable ordered envelopes (WS) and
    high-frequency sequenced motion frames (UDP) on a unified session.
*   ✅ **Client/Server Main-Thread Adapters:** network buffers queued safely
    into the Unity Update loop. **Note:** the client half (~6,800 LOC) is
    currently compiled *inside* the ComfyNetworkSense assembly; extracting it
    into its own client library is a planned refactor, not part of the split.
*   Shared surface: `Comfy.Transport.Contracts` (NuGet, source-only) carries
    the admissions + ZDO policy contracts to every consumer.

### 🟩 comfy-quest (Quest Product)
The quest vertical: ComfyQuestLab (✅), ComfyQuestRuntime (✅, thin — input and
kill patches only), ComfyQuestContracts (✅, netstandard2.0, published as
`Comfy.Quest.Contracts`), Quest Studio (✅, carved from Game.Companion as
`Comfy.Quest.Studio`; Companion remains the host). Files are the handoff:
Studio emits immutable `.questpack`s; Runtime loads them explicitly.

### 🟧 sovereign-shards (The New Sharding Repository) — all 🔮
Our specialized, creator-centric vertical: container orchestration, Discord
bot automation, routing handshakes, async sidecar logging. **Greenfield: none
of the components below exist yet.**
*   🔮 **ComfyPortalRouter (Client Plugin):** a tiny BepInEx adapter hooking
    portal traversal: break the central gateway connection, force a local
    character-save backup, hot-swap the active socket to the target shard's
    port. (Distinct from the shipped `PortalConnectionCache`, which is a
    link-graph performance fix, not shard routing.)
*   🔮 **Shard Manager Daemon (`shard_manager.py`):** runs on port **`:8730`**
    on the server host. (An earlier draft claimed `:8721`, which PD-6 reserves
    for the live Dev MCP — see `docs/PORTS.md`.) Monitors portal-routing
    requests, drives the Docker socket API to warm shard containers, maps
    active ports.
*   🔮 **Discord Bot Interface (!party):** out-of-game huddle lobby — temporary
    party channels, ping tests, signed JWT session tokens, live container boot
    logs. (No JWT infrastructure exists anywhere in the fleet today.)
*   🔮 **Armory Watch Sidecar (`armory_watch_daemon.py`):** tails local JSON
    equipment snapshots, validates item quality against a write-ahead ledger,
    fail-closed lockout + Discord audit webhook. **Depends on an
    `OnEquipmentChange` hook in ComfyQuestRuntime that does not exist yet** —
    Runtime today writes receipts, not `armory_snapshot.json`. That hook is
    the first build item for this flow.

---

## 2. Core Architectural Data Flows (all 🔮 planned)

### A. Gated Party Formation & Shakedown Ceremony
1.  A squad leader initiates an event in Discord using **`!party create [ShardID]`**.
2.  The Discord Bot requests an ephemeral **JWT Session Token** from the Shard
    Manager on port **`:8730`**.
3.  While the Shard Manager warms the shard container via the Docker API,
    players perform an in-game telemetry **Huddle** to measure RTT and jitter,
    streamed back to the Discord channel. (Huddle is 🔮 in networksense.)
4.  Once the shard finishes booting and replaying its Write-Ahead Ledger, the
    container locks its ports to handshakes matching the signed party JWT.

### B. In-Game Portal Hot-Swapping
1.  A player walks into a sharded portal; **`ComfyPortalRouter`** intercepts.
2.  The client backs up the local character save (`.fch`) against state
    corruption. (No save-backup code exists today.)
3.  The client gracefully disconnects its **C7 connection** (✅ shipped) from
    the central gateway.
4.  The client hot-swaps its socket to the mapped shard port and performs a
    Steam-free handshake with the signed JWT.

### C. Decoupled Sidecar Logging & Audit Loop
1.  In-shard, on gear change or food consumption, **`ComfyQuestRuntime`** would
    write a lightweight local `armory_snapshot.json` to the shared volume —
    **requires the not-yet-built equipment hook.**
2.  **`armory_watch_daemon.py`** tails the filesystem on a 0.5 s interval,
    keeping the main game thread free of query lag.
3.  Overleveled gear (e.g., a Level 13 Bronze Buckler) is validated against
    the write-ahead ledger's cryptographic signature.
4.  Missing/forged signature → fail-closed teleport to the main server +
    Discord audit webhook.
