# Architecture & Domain Data Blueprint: Valheim Chronicler Archive
**Pattern: CQRS (Command Query Responsibility Segregation) & Event-Sourced Archival Ledger**
*Context: Supporting Lean Onboarding Gateway, Viking "MySpace" Profiles, Shared Attribution, and Zero-Trust Client Claims*

---

## 1. High-Level CQRS Architecture Overview

In this system, world-save files and raw server log files are immutable historical artifacts (read-side ingestion), while user claims, photo dispatches, runic inscriptions, and builder profile personalizations happen client-side or via webhook command dispatchers.

```
       ┌────────────────────────┐
       │   Valheim World Saves  │ (.db / .fwl / zdo dumps)
       └───────────┬────────────┘
                   │ Ingestion Pipeline (Batch / Replay)
                   ▼
       ┌────────────────────────┐
       │     EVENT STORE        │ (Append-Only Immutable Log)
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐  ┌──────────────────────────────────────────────┐
│  COMMAND SIDE    │  │  QUERY / READ SIDE (Materialized Projections)│
│  (Write / Event) │  │                                              │
│  - Claim Build   │  │  ┌─────────────────┐    ┌──────────────────┐ │
│  - Request Photo │  │  │ Era Overview    │    │ Builder Profile  │ │
│  - Inscribe Stele│  │  │ Projection      │    │ "MySpace" View   │ │
│  - Discord Hook  │  │  └─────────────────┘    └──────────────────┘ │
└──────────────────┘  │  ┌─────────────────┐    ┌──────────────────┐ │
                      │  │ Kinship Top 8   │    │ Piece Attribution│ │
                      │  │ Graph Projection│    │ Matrix           │ │
                      │  └─────────────────┘    └──────────────────┘ │
                      └──────────────────────────────────────────────┘
```

---

## 2. Event-Sourced Core Domain Events

All state in the Comfy Community Archive is derived from replayable, immutable events:

### A. Archival Ingestion Events (System / World Pipeline)
* **`PieceRecorded`**:
  ```json
  {
    "eventId": "evt_pc_9918231",
    "timestamp": 1698240000,
    "eraId": 14,
    "worldHash": "e0a4455a",
    "buildId": "b4859027",
    "pieceType": "piece_stone_wall_4x2",
    "position": { "x": -2410.5, "y": 89.2, "z": 1204.1 },
    "creatorId": "builder_ditseey_primary",
    "creatorRawName": "Ditseey"
  }
  ```
* **`BuildClusterFormed`**:
  Clusters individual pieces into a spatial structure or named monument based on bounding density and distance thresholds.
* **`HistoricalPhotoIngested`**:
  Associates photographic passes with a build album (`buildId`, camera angles, weather study, photographer ID).

### B. User / Community Command Events (Command Side)
* **`BuildClaimed`**:
  ```json
  {
    "eventId": "evt_clm_401928",
    "timestamp": 1711928400,
    "buildId": "bd1ac417",
    "claimantHandle": "Skald_Gunnar#049",
    "claimType": "CO_ARCHITECT",
    "claimedPercentage": 37.3,
    "notes": "Co-designed cantilevered sea towers with Bluecollar",
    "clientPayloadHash": "sha256:d8f2...99a"
  }
  ```
* **`SteleInscribed`** *(Guestbook Wall)*:
  Appends an entry to a builder's runic stele.
* **`PhotoRequestDispatched`**:
  Dispatches a photography order (styles: `INTERIOR_STUDY`, `TWILIGHT_PASS`, etc.) directly to the Discord FIFO ticket webhook.
* **`ProfileCustomized`** *(MySpace Personalization)*:
  Custom status mood, selected mead hall anthem audio, and pinned signature exhibits.

---

## 3. Read Model Projections (Materialized Views)

Because reads must be blazingly fast and support high diversity across player styles, projections are tailored to specific consumption contexts:

### 1. The Lean Gateway Projection (`GatewayArchetypeView`)
* **Purpose**: Power the stripped-down, low-cognitive-lift landing portal.
* **Payload**: High-level counters (eras populated, total registered pieces, active photographers) + 5 intent entry points (Mason, Architect, Chronicler, Scout, Mechanist) without heavy metadata dumps.

### 2. The Builder "MySpace" Profile Projection (`BuilderProfileView`)
Generated per unique builder identity, backing screens like Ditseey, Reina Borg, Tugcow, and Ibocain:
```typescript
interface BuilderProfileProjection {
  builderId: string;
  primaryName: string;
  aliases: string[];
  standing: "Megabuilder" | "Major Architect" | "Homestead Artisan" | "Ranger";
  avatarImageRef: string; // e.g. {{DATA:IMAGE:IMAGE_4}}
  
  // Vitals
  metrics: {
    totalAlbums: number;
    totalPieces: number;
    photographedAlbums: number;
    activeEras: number[];
    serverRankPercentile: number; // e.g. Top 0.1%
  };

  // Social / Norse MySpace Elements
  flair: {
    statusMood: string;
    beaconState: string;
    anthemAudioUrl: string;
    anthemTitle: string;
    norseSign: string;
    preferredBiome: string[];
    aboutMe: string;
    whoIdLikeToMeet: string;
  };

  // The Kinship "Top 8" Projection (Shared Overlap)
  shieldWallTop8: Array<{
    collaboratorId: string;
    collaboratorName: string;
    roleTag: string; // e.g. "Forge Lead", "Homestead Partner"
    sharedBuildsCount: number;
    sharedPiecesCount: number;
    keySharedBuildId: string;
  }>;

  // Signature Monuments
  signatureMonuments: Array<{
    buildId: string;
    title: string;
    era: number;
    pieceCount: number;
    builderAttributionPercent: number;
    coArchitects: Array<{ name: string; percent: number }>;
    photoUrl?: string;
    isClaimable: boolean;
  }>;

  // Telemetry Ledger (Grouped by Era)
  eraLedger: Record<number, Array<{
    buildId: string;
    totalPieces: number;
    builderShare: number;
    photoStatus: "PHOTOGRAPHED" | "PENDING_CAMERA" | "UNPHOTOGRAPHED";
    photoCount: number;
    contributors: Array<{ name: string; percent: number }>;
  }>>;
}
```

---

## 4. The Kinship & Attribution Overlap Graph

The critical breakthrough between diverse profiles (Megabuilders, Crossfunctional Coordinators, Homesteaders) is **Kinship Calculation**. 

### How the "Top 8" is Calculated:
For any builder $A$, their kinship score with builder $B$ across all erased eras is computed by:

$$\text{KinshipScore}(A, B) = \sum_{b \in \text{SharedBuilds}} \left( \min(P_{A,b}, P_{B,b}) \times \log_{10}(\text{TotalPieces}_b) \right)$$

Where $P_{A,b}$ is builder $A$'s percentage contribution to build $b$.
* This ensures that co-architecting a 15,000-piece fortress (like Ditseey & Bluecollar on `bd1ac417`, or Reina Borg & Hammerstein on `06a9eca2`) ranks higher than incidental co-placement on tiny outposts.
* It dynamically produces the beloved **"Shield-Wall Top 8"** for each builder profile without manual curation!

---

## 5. Summary of Architecture Benefits

1. **Zero-Lock Client Privacy**: Users can browse, filter, claim builds, and compile photo requests locally in browser memory (`localStorage` / IndexedDB). No backend account registration required.
2. **Deterministic Attribution**: Raw piece percentages are computed purely from world file saves; claiming does not alter historical attribution—it creates an authenticated claim payload.
3. **Infinite Replayability**: If an algorithm for clustering builds improves or a new era is salvaged, projections can be re-indexed seamlessly from the Event Store.
4. **Adaptive Presentation**: The exact same query model powers both the **ultra-lightweight, 256-character landing gateway** and the **hyper-dense, 50-metric Viking MySpace profile**.
