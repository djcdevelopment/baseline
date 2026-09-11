# API Architecture & Endpoint Specification: Next.js + FastAPI Backend
**The Comfy Community — Valheim Chronicler Archive**
*Architecture Pattern: Hybrid Next.js Edge / BFF + FastAPI CQRS Event-Sourced Archival Service*

---

## 1. System Topology & Request Flow

```
                                 ┌─────────────────────────────────────────┐
                                 │     Client Browser (Zero-Trust Ledger)  │
                                 │ - LocalStorage / IndexedDB Sync Vault   │
                                 │ - Audio Player / Kinship Graph Cache    │
                                 └───────────────┬─────────────────────────┘
                                                 │
                                                 │ HTTPS / JSON / Payloads
                                                 ▼
             ┌─────────────────────────────────────────────────────────────────────────┐
             │                     NEXT.JS APPLICATION LAYER (BFF)                     │
             │   - App Router Pages: /valheim, /valheim/creators, /valheim/creators/[id]│
             │   - Route Handlers (Edge & Node Runtime): /api/v1/...                   │
             │   - Client Payload Signer & Discord Webhook Proxy                       │
             └───────────────────────────────────┬─────────────────────────────────────┘
                                                 │ Internal Network / mTLS / gRPC or REST
                                                 ▼
             ┌─────────────────────────────────────────────────────────────────────────┐
             │                      FASTAPI CQRS CORE SERVICE                          │
             │                                                                         │
             │     ┌────────────────────────┐      ┌────────────────────────────────┐  │
             │     │      COMMAND SIDE      │      │           QUERY SIDE           │  │
             │     │  (Write / Ingestion)   │      │    (Projections / Graph)       │  │
             │     │  /api/v1/commands/...  │      │    /api/v1/queries/...         │  │
             │     └───────────┬────────────┘      └───────────────┬────────────────┘  │
             │                 │                                   │                   │
             │                 ▼                                   ▼                   │
             │     ┌────────────────────────┐      ┌────────────────────────────────┐  │
             │     │   EventStoreDB / PG    │─────▶│  Read Cache (Redis / SQLite)   │  │
             │     │ (Append-only Event Log)│Replay│  (Materialized Projections)    │  │
             │     └────────────────────────┘      └────────────────────────────────┘  │
             └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Next.js BFF Route Handlers (`app/api/...`)

These routes sit between the client and FastAPI, managing edge caching, payload generation, rate limiting, and Discord webhook dispatching without exposing private webhook URLs.

### A. Gateway & Archetype Navigation
* **`GET /api/gateway/stats`**
  - **Purpose**: Power the lean landing gateway (<256 chars cognitive lift) with fast, CDN-cached counters.
  - **Runtime**: `edge`
  - **Cache**: `s-maxage=300, stale-while-revalidate=86400`
  - **Response `200 OK`**:
    ```json
    {
      "erasCount": 9,
      "erasActive": [7, 8, 9, 10, 11, 12, 14, 16, 17],
      "totalBuilders": 2585,
      "totalCaptures": 12102,
      "totalPieces": 4892100,
      "currentPhotographedEras": "7–9, 12, 14, 16–17",
      "pendingPhotographyEras": "10–11"
    }
    ```

* **`GET /api/gateway/archetypes`**
  - **Purpose**: Returns the 5 intent categories (Mason, Architect, Chronicler, Scout, Mechanist) and their direct curated filter targets.
  - **Response `200 OK`**: List of intent configs with suggested era queries and exemplar builder IDs.

---

### B. Builders Directory & Search
* **`GET /api/creators`**
  - **Query Params**:
    - `q` (string, optional): Search query (supports regex/substring on names & aliases).
    - `era` (integer, optional): Filter by era participation (e.g. `14`).
    - `with_albums` (boolean, default `false`): Filter only creators with captured photos.
    - `sort` (enum: `pieces_desc`, `albums_desc`, `name_asc`, `photos_desc`).
    - `cursor` / `limit` (pagination, default limit `50`).
  - **Response `200 OK`**:
    ```json
    {
      "items": [
        {
          "builderId": "b_ditseey_primary",
          "name": "Ditseey",
          "aliases": ["✨ditseey✨", "💟Ditseey☠Đ₳₦₲ɆⱤ☠ʀᴀɴ₲Ɇʀʳᵉᵖ💟"],
          "rank": "Megabuilder",
          "serverRank": 4,
          "totalAlbums": 112,
          "totalPieces": 80151,
          "photographedAlbums": 21,
          "activeEras": [11, 12, 14, 16, 17],
          "signaturePieces": ["bd1ac417", "fa06785d"]
        }
      ],
      "nextCursor": "eyJsYXN0SWQiOiJiX2Rp..."
    }
    ```

---

### C. Viking "MySpace" Builder Profile
* **`GET /api/creators/[builderId]`**
  - **Purpose**: High-fidelity payload backing screens like Ditseey, Reina Borg, Ibocain, and Tugcow.
  - **Response `200 OK`**:
    ```json
    {
      "builderId": "b_reina_borg",
      "primaryName": "Reina Borg",
      "standing": "Megabuilder",
      "roleArchetype": "Shieldmaiden Architect & Multi-Role Coordinator",
      "avatarUrl": "/assets/portraits/reina-borg.webp",
      "norseSign": "Raven & Astrolabe",
      "flair": {
        "statusMood": "Surveying guild spans on Build 06a9eca2",
        "beaconState": "SURVEYING GUILD SPANS (ERA 14)",
        "anthemTitle": "Wardruna – Voluspá",
        "anthemAudioUrl": "/audio/anthems/wardruna-voluspa.mp3",
        "aboutMe": "Cross-functional master architect across 8 server eras...",
        "whoIdLikeToMeet": "Artisans who cherish multi-builder attribution..."
      },
      "metrics": {
        "totalAlbums": 216,
        "totalPieces": 99745,
        "photographedAlbums": 24,
        "activeEras": [7, 8, 9, 10, 11, 12, 14, 17]
      },
      "shieldWallTop8": [
        { "id": "b_hammerstein", "name": "Hammerstein", "role": "Forge Lead", "sharedBuilds": 18, "kinshipScore": 94.2 },
        { "id": "b_norselokk", "name": "Norselokk", "role": "Rampart Eng", "sharedBuilds": 14, "kinshipScore": 88.7 }
      ]
    }
    ```

* **`GET /api/creators/[builderId]/ledger`**
  - **Query Params**: `era` (integer, e.g. `14`), `limit`, `offset`.
  - **Response `200 OK`**: Paginated list of build records, total piece count, contributor attribution matrix (% shares), and camera status (`PHOTOGRAPHED` | `PENDING_CAMERA` | `UNPHOTOGRAPHED`).

---

### D. Client Ledger & Discord Webhook Integration
* **`POST /api/dispatch/discord-ticket`**
  - **Purpose**: Proxies survey/photo requests to Discord FIFO Webhook without leaking webhook secret.
  - **Rate Limit**: 5 requests per IP / volunteer handle per 10 minutes.
  - **Request Body**:
    ```json
    {
      "volunteerHandle": "Skald_Gunnar#049",
      "buildId": "bd1ac417",
      "era": 14,
      "builderAttribution": "Ditseey (37.3%), Bluecollar (35.1%)",
      "styles": ["WIDE_OVERVIEW", "INTERIOR_SIGNATURE", "TWILIGHT_PASS"],
      "instructions": "Need drone pass of the cantilevered sea needle.",
      "isUrgent": true,
      "contactPreference": "discord_dm",
      "clientPayloadHash": "sha256:7f4c9..."
    }
    ```
  - **Response `201 Created`**:
    ```json
    {
      "ticketId": "DISPATCH-2024-0491",
      "status": "QUEUED_FIFO",
      "discordThreadUrl": "https://discord.com/channels/comfy/.../thread-991"
    }
    ```

* **`POST /api/claims/generate-payload`**
  - **Purpose**: Verifies and cryptographically signs a claim payload for client-side storage (`localStorage`) or manual copying.
  - **Response `200 OK`**: `{ "payload": "eyJhbGciOiJIUzI1...", "hash": "sha256:..." }`

---

## 3. FastAPI CQRS Core Service (`/api/v1/...`)

FastAPI handles the high-throughput, compute-heavy side: raw zdo/world-save event ingestion, spatial clustering, kinship graph calculation, and read projection materialization.

### A. Command Side (Writes / Events)

```python
# Routers: app.routers.commands
```

| Method | Endpoint | Description | Payload / Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/commands/ingest/world-save` | Ingests `.db`/`.fwl` batch or zdo piece dump for an era | `WorldSaveIngestCommand` (era, worldHash, fileStream) |
| `POST` | `/api/v1/commands/builds/claim` | Record an unverified client claim marker | `ClaimBuildCommand` (buildId, claimant, claimType, sharePct, signature) |
| `POST` | `/api/v1/commands/photos/request` | Submit a photo survey ticket | `PhotoRequestCommand` (buildId, styles, notes, volunteerHandle) |
| `POST` | `/api/v1/commands/stele/inscribe` | Inscribe runic testimonial on builder's wall | `InscribeSteleCommand` (targetBuilderId, authorName, text) |
| `POST` | `/api/v1/commands/profile/customize`| Update builder flair (status, anthem, pinned monuments) | `CustomizeProfileCommand` (builderId, statusMood, anthemUrl) |

---

### B. Query Side (Materialized Read Projections)

```python
# Routers: app.routers.queries
```

| Method | Endpoint | Description | Caching / Performance |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/queries/gateway/archetype-summary` | Aggregated metrics for landing portal | Redis Cache (TTL: 1 hour) |
| `GET` | `/api/v1/queries/builders/{builder_id}/profile` | Pre-materialized `BuilderProfileView` | Redis JSON / Memory cache |
| `GET` | `/api/v1/queries/builders/{builder_id}/top8` | Dynamically recomputed Kinship Shield-Wall | Graph Projection (NumPy matrix) |
| `GET` | `/api/v1/queries/builds/{build_id}/pieces` | Deep piece-by-piece inspect breakdown (wood, stone, iron) | Streaming JSON / Gzip |
| `GET` | `/api/v1/queries/eras/{era_id}/monuments` | Major monuments in a specific server era | Redis Set / Sorted ZSet |
| `GET` | `/api/v1/queries/search/autocomplete` | Substring & alias matcher for instant builder lookup | Redis Trie / RediSearch |

---

## 4. FastAPI Domain Models & Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class PhotoStyle(str, Enum):
    WIDE_OVERVIEW = "wide_overview"
    INTERIOR_SIGNATURE = "interior_signature"
    HEIGHT_VARIATION = "height_variation"
    TWILIGHT_TONE = "twilight_tone"
    ENTRY_DETAIL = "entry_detail"

class ClaimType(str, Enum):
    SOLE_CREATOR = "SOLE_CREATOR"
    CO_ARCHITECT = "CO_ARCHITECT"
    FOUNDATION_MASON = "FOUNDATION_MASON"
    TIMBER_CARPENTER = "TIMBER_CARPENTER"

class ClaimBuildCommand(BaseModel):
    build_id: str = Field(..., example="bd1ac417")
    era: int = Field(..., example=14)
    claimant_handle: str = Field(..., example="Skald_Gunnar#049")
    claim_type: ClaimType = Field(default=ClaimType.CO_ARCHITECT)
    claimed_percentage: float = Field(..., ge=0.0, le=100.0, example=37.3)
    notes: Optional[str] = Field(None, max_length=500)
    client_signature: str = Field(...)

class KinshipCollaborator(BaseModel):
    collaborator_id: str
    collaborator_name: str
    role_tag: str
    shared_builds_count: int
    shared_pieces_count: int
    kinship_score: float
    key_shared_build_id: str

class BuilderProfileView(BaseModel):
    builder_id: str
    primary_name: str
    aliases: List[str]
    standing: str
    server_rank: int
    avatar_url: str
    metrics: Dict[str, int]
    flair: Dict[str, str]
    shield_wall_top_8: List[KinshipCollaborator]
```

---

## 5. Security, Rate Limiting & Zero-Trust Architecture

1. **Discord Webhook Obfuscation**: The webhook URL is stored in backend environment secrets (`DISCORD_SURVEY_WEBHOOK_URL`). The Next.js BFF acts as a forward proxy and validates rate limits using Redis token buckets.
2. **Deterministic & Immutable Attributions**: World save pieces are read-only. Calling `POST /commands/builds/claim` registers a social/community endorsement record; it is mathematically impossible for a claim command to alter or tamper with the raw ingested piece logs.
3. **Offline & Client-First Compatibility**: All search filters and claim payloads function entirely client-side via IndexedDB if the backend API is temporarily unreachable.
