# Companion workbench and reconstruction strategy

Status: implementation slice for the local alpha/dev/admin/test hub.

## Boundary model

The local Docker Companion at `127.0.0.1:8080` is the operator workbench. It is where the
operator sees local readiness, release identity, live trace, milestone position, physical-client
controls, headless-lab entry points, and retained evidence.

The public Gateway remains the remote edge:

- Steam/OpenID sign-in and callback;
- enrollment and client-pull authorization;
- public release manifest and package route;
- P7 server/Gateway telemetry.

The public edge may be reached by the local workbench for read-only telemetry. It must not proxy
the local admin surface or receive raw Steam credentials. A local profile is represented by linked
state and redacted hashes; the source config remains on the client.

## Hierarchy

The workbench checklist is intentionally a view over existing sources, not a replacement:

```text
active goal
└── milestone
    └── feature / experiment lane
        └── source document, commit, or receipt family
            └── latest local snapshot + raw evidence bundle
```

The catalog ships with the Companion image so a reset image still explains where the work is. The
running container adds source revision, branch, dirty state, image label, local status, Gateway
reachability, and latest capture presence. The catalog is the plan; the live packet is the current
machine observation.

## Execution lanes

| Lane | Best use | Human touch | Evidence |
|---|---|---:|---|
| Local workbench | Coordinate and understand the experiment | none after opening | source-aware status, snapshots, links |
| Public Gateway/P7 | Real latency, release, server, and remote telemetry | none | deployment/Valheim/cutover/motion APIs |
| OMEN + i5 physical clients | Human feel, GPU/display/runtime variance, role reversal | one join window, then watch | two-client capture, player names, raw JSONL/bundles |
| Docker headless/rendered clients | Synthetic generation, replay, authority experiments | one-time volume seeding | scenario receipts, normalized evidence, MCP receipts |
| SSH/admin lane | Start, inspect, and update sanctioned machines | none after key trust | command receipts and hashes |

The server account is a server identity in this topology; it is not spent on a GUI client loop.
The two player identities stay on OMEN and i5 for physical feel tests. Headless clients use
separate seeded volumes or an explicitly alternate account assignment, never concurrent reuse of a
physical Steam session.

## Preserve value from every interaction

Existing transport captures already preserve `summary.json`, `samples.jsonl`, and optional bundles.
The workbench adds a redacted snapshot action. A snapshot contains:

- UTC timestamp and event type;
- Companion/bootstrap/image/source identity;
- branch, revision, and dirty state when supplied by the launcher;
- local Valheim/config/profile readiness without raw credentials;
- installed release and short package hash;
- the shipped goal/milestone/lane catalog.

Snapshots are immutable files under the persistent `companion-data` volume. New observations create
new snapshots; they do not rewrite old ones. A future evidence index can correlate snapshots,
captures, roadmap notes, and commits without reconstructing a Discord conversation.

## Reset and reconstruct

The safe reset is an image reset, not a data reset:

1. Capture a redacted workbench snapshot.
2. Pull or rebuild the latest Companion image through the canonical launcher.
3. Preserve the `companion-data` volume.
4. Open `/workbench` and confirm source/image identity.
5. Open `/trace`, the latest snapshot, and the relevant capture bundle.
6. Repeat only the smallest bounded experiment whose source seam changed.

`docker compose down -v` is not a reconstruction command; it destroys the local evidence volume.
If the volume is lost, reconstruct from the Git source revision, public Gateway release manifest,
retained capture bundles, and any exported snapshots. Treat missing snapshots as a provenance gap,
not as permission to infer what happened.

## Next integrations, in order

1. Keep the workbench catalog aligned with the CSV/roadmap sources through a small generator or
   explicit review when milestone truth changes.
2. Add a local “run card” that links a selected feature lane to one synthetic, one physical, or
   one headless command without becoming a generic workflow engine.
3. Add a compact append-only local event index for snapshots, captures, and operator annotations.
4. Add optional host/SSH health tiles for Docker, GPU client, i5, and headless Compose lanes.
5. Only then revisit Steam callback-to-localhost pairing and delegated identity; keep the public
   Gateway as the identity root until the contracts are clearer.
