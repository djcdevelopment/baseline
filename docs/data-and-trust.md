# Data & Trust

Announced capture is the pitch; discovered capture poisons trust. This tool
doesn't exist to monitor you, and it isn't a verdict on how anyone plays or runs
things. We use data to make it *cheaper to care* about the community — to
celebrate the art you create, shrink the maintenance burden, and keep this world
running smoothly. You own your gameplay, which is why everything here is strictly
opt-in and transparent.

<!--
  SOURCE MAP (M1-1 acceptance: every captured field cites its source; grep-verifiable).
  Gameplay capture (creature, weapon=hit.m_skill, ranged, playerId):
    network/mod/ComfyNetworkSense/Core/Services/GameplayEventProducer.cs:123-131
  Event types (first_hit/killing_blow/weapon_used/quest_completed/transport_control_changed):
    network/mod/ComfyNetworkSense/Core/Services/GameplayEventProducer.cs (GameplayEventTypes)
  Gateway POST envelope (event_type/occurred_at_utc/world_id/region_id/actor_id/detail/payload):
    network/mod/ComfyNetworkSense/Core/Services/GameplayEventProducer.cs:290-298
  Payload keys (creature/weapon/ranged) + quest keys (quest_id/guild/category/bot_command):
    network/mod/ComfyNetworkSense/Core/Services/GameplayEventProducer.cs:277-287
  Performance-sample fields (rtt_ms/jitter_ms/fps/frame_time_*/bytes_*/packets_*/nearby_*/danger_nearby/
    player_id/player_name/owner_id/session_id/region_id/build_version):
    network/mod/ComfyNetworkSense/Core/Models/ClientTelemetrySample.cs:36-67
  Public privacy split / identity-stripped allow-list / exposure delay:
    Lumberjacks/src/Game.ServiceDefaults/GameplayEventFeed.cs:13-74
  Opt-out switches (gameplayEventProducerEnabled / questEvaluatorEnabled, default OFF, [Gameplay] section):
    network/mod/ComfyNetworkSense/Config/PluginConfig.cs:689-723
-->

## What is captured

If you choose to enable the capture tools, the mod observes two specific areas.

**Gameplay activity.** When you engage in combat, the mod captures events
(`first_hit`, `killing_blow`, `weapon_used`) along with the creature's category
(with "(Clone)" stripped), your weapon-skill name (`weapon`), whether the attack
was `ranged`, and your player id (sent as `actor_id`). When you complete a quest (`quest_completed`)
it additionally records the `quest_id`, your `guild`, the quest `category`, and
the `bot_command`. It also captures alpha transport switches
(`transport_control_changed`). Every event is stamped with an `occurred_at_utc`
timestamp, a `world_id`, a `region_id`, and a non-identifying `detail` label.

**Performance samples.** To help keep the server running smoothly, the mod takes
network and PC-health samples: your game version (`build_version`), session and
cluster IDs, ping (`rtt_ms`), jitter (`jitter_ms`), framerate (`fps`), frame
timings (`frame_time_ms`, `frame_time_p95_ms`), and data rates (bytes and packets
in/out per second). It also records your `player_id`, `player_name`, `owner_id`,
and counts of what's loaded around you: `nearby_players`, `nearby_entities`,
`nearby_build_pieces`, and a simple `danger_nearby` flag.

## What is never captured

We keep strict, honest boundaries. The following simply does not exist in the
capture code:

- **No chat or voice content.**
- **No world position or coordinates.** The mod counts *how many* things are
  nearby to measure performance impact; it never records your X/Y/Z location.
- **No keystrokes or free text.** The public `detail` is always a bounded label
  (a weapon skill or quest name), never something you typed.

## Where it lives

1. **On your machine:** local log files under
   `Valheim\BepInEx\config\comfy-network-sense\`. You own these files.
2. **The operator's server:** a durable EventLog that holds the raw records for
   community management.
3. **The public:** aggregated, identity-stripped data in the unauthenticated
   `/api/v0/telemetry/events` feed and the `/community` dashboard.

## Who can see what

Privacy is enforced by construction. The public feed is delayed by a configurable
number of seconds and **never** includes the acting player's identity.

| | You (any player) | The operator (server) | The public / anyone |
|---|---|---|---|
| **Gameplay activity** (creature / weapon / quest) | your own local logs | full record, including your player id and quest payload | only delayed, non-identifying labels (e.g. "a sword was used on a skeleton"; "a quest was completed") |
| **Your player id & name** | known to you | visible in the durable EventLog | **never visible** |
| **Performance samples** | your own local logs | visible, to diagnose lag / desync / server health | **never visible** (stays on the private server plane) |

## How to opt out

You are in control. Gameplay capture ships **OFF by default** — to contribute
data you must intentionally opt in. You can toggle these at any time (they are
hot-reloadable) in your BepInEx config under the `[Gameplay]` section:

- `gameplayEventProducerEnabled` — combat and weapon events
- `questEvaluatorEnabled` — quest-completion matching

To stop all capture, remove the mod. And if the mod's gateway URL is left blank,
nothing ever leaves your machine — only your local files are written.

## Watch it being built

This system is built in the open, honoring the community every step of the way.
Integrations and coding happen live on stream.

- <VOD links to be added>
