# The Comfy Community — Valheim Chronicler Archive
## Master Project Archive, Table of Contents & Technical Overview (v1.0.0 Release)

---

### Executive Summary & System Blueprint

The **Valheim Chronicler Archive** is an immutable, event-sourced preservation platform and social attribution network designed to capture, index, and celebrate over **4.89 million construction blocks**, **12,102 photographic surveys**, and **2,585 registered Viking builders** across **9 server eras** (Eras 7 through 17) within The Comfy Community.

This archive bridges the gap between deep, technical infrastructure (world-save byte deserialization, SciPy sparse CSR projection matrices, Zero-Trust cryptographic browser claims) and immersive Norse digital culture (Viking "MySpace" builder profiles, die-cut folk-art persona gateways, and live Shield-Wall Top 8 attribution graphs).

---

## 📦 Master Table of Contents (Inventory Manifest)

### Section 1: User Interface & Experience Architecture (Canvas Screens)

| Artifact Ref | Title / Component | Target Route | Core Purpose & UX Pattern |
| :--- | :--- | :--- | :--- |
| **`SCREEN_25`** | **Visual Gateway & Character Archive** | `/valheim` | **The Low-Cognitive-Lift Front Door.** Features 5 die-cut Viking persona cutouts with strict <256 character cognitive lift. Lets visitors choose their intent without technical intimidation. |
| **`SCREEN_44`** | **Across the Eras — Builders Directory** | `/valheim/creators` | Comprehensive directory indexing 2,585 builders. Provides instant substring filter, era chips (Eras 7–17), sort orders, and signature creation badges. |
| **`SCREEN_8`** | **Ditseey — Rune-Witch Megabuilder & Coastal Codex** | `/valheim/creators/b_ditseey` | High-fidelity Viking "MySpace" creator profile for server rank #4 (80,151 pieces, 112 albums). Features custom status mood, Nordic ambient anthem, and dynamic Shield-Wall Top 8. |
| **`SCREEN_13`** | **Reina Borg — Shieldmaiden Architect & Guild Codex** | `/valheim/creators/b_reina_borg` | Profile showcasing cross-functional multi-role coordination, collaborative guild spans, and multi-builder attribution ratios. |
| **`SCREEN_15`** / **`SCREEN_17`**| **Ibocain — Master Builder Profile & Archival Runestone** | `/valheim/creators/b_ibocain` | Veteran megabuilder profile (184,203 pieces) highlighting colossal fortresses, stone foundation attributions, and public runic stele guestbook. |
| **`SCREEN_11`** | **Tugcow — Homestead Carpenter & Archival Runestone** | `/valheim/creators/b_tugcow` | Profile celebrating grassroots homestead carpenters, hearth longhouses, and intimate community settlements. |
| **`SCREEN_34`** | **Archival Survey Dispatch & Discord Webhook Ticket Nexus**| `/valheim/dispatch` | Secure volunteer photographic survey dispatch portal. Generates FIFO ticket embeds forwarded to private Discord operations channels. |
| **`SCREEN_39`** | **Chronological Eras Timeline & World Claims** | `/valheim/eras` | Interactive world-save wipe timeline detailing photographic coverage across active eras (7–9, 12, 14, 16–17) vs pending eras (10–11). |
| **`SCREEN_40`** | **Claim Build Attribution — Cryptographic Payload** | `/valheim/claims` | Zero-Trust browser participation manager. Generates sha256 client-side payload signatures without requiring mandatory centralized accounts. |
| **`SCREEN_41`** | **Thorgaar the Mason — Album & Piece Inspector** | `/valheim/inspect/b_thorgaar` | Deep structural piece inspector breaking down wood, corewood, stone, and iron piece placement ratios per structure. |
| **`SCREEN_26`** | **Persona Happy Paths & Taxonomy Flow Matrix** | `/valheim/architecture/flows` | Complete UX flow matrix and Unified Domain Model (UDM) mapping the 5 player personas to their desired outcomes and menu hierarchies. |

---

### Section 2: Full-Stack Codebase, SDKs & Algorithms (Documents)

| Document Ref | File / Specification | Language / Stack | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **`DOCUMENT_7`** | **CQRS Data Architecture & Kinship Blueprint** | Architecture / Markdown | Detailed CQRS design separating immutable batch world-save replay from write commands (claims, photo requests, runic steles). |
| **`DOCUMENT_6`** | **Next.js & FastAPI API Route Architecture** | OpenAPI / Endpoint Spec | Complete endpoint mapping for Edge BFF (`/api/gateway/...`, `/api/creators/...`, `/api/dispatch/...`) and FastAPI CQRS backend (`/api/v1/...`). |
| **`DOCUMENT_5`** | **Valheim Chronicler Archive — Pydantic V2 Schemas** | Python (Pydantic V2) | Production data schemas: `BuilderProfileView`, `KinshipCollaborator`, `ClaimBuildCommand`, `PhotoRequestCommand`, and `GatewayStatsView`. |
| **`DOCUMENT_4`** | **TypeScript SDK & Universal API Client** | TypeScript (Next.js / Node) | 100% type-safe universal client library (`ValheimArchiveClient`) with singleton export and offline zero-trust browser compatibility. |
| **`DOCUMENT_3`** | **FastAPI & NumPy Kinship Overlap Engine** | Python (NumPy / SciPy) | Vectorized linear algebra implementation computing the Shield-Wall Top 8 using sparse CSR matrices: $\sum \min(P_A, P_B) \cdot \log_{10}(\text{Pieces})$. |
| **`DOCUMENT_2`** | **React / Next.js Kinship Graph & Dashboard** | React / Tailwind / Lucide | Multi-mode visualization component featuring Radial Shield-Wall Graph, Attribution Matrix, Key Monuments Grid, and Kin Inspector Drawer. |

---

### Section 3: Visual Identity & Brand Assets (Design Tokens & Art)

* **Design System (`DESIGN_SYSTEM_1`)**:
  - **Theme**: Valheim Chronicler Dark Archive (`#090f16` surface base, `#121822` container low, `#f59e0b` hearth amber accent, `#38bdf8` runic sky, `#10b981` emerald beacon).
  - **Typography**: Bodoni Moda (Norse codex display headers) + Inter/JetBrains Mono (telemetry and coordinate labels).
* **Character Illustrations & Portraits**:
  - **`IMAGE_10`**: Ditseey (Rune-Witch Megabuilder)
  - **`IMAGE_12`**: Tugcow (Homestead Carpenter)
  - **`IMAGE_14`**: Reina Borg (Shieldmaiden Architect)
  - **`IMAGE_16` / `IMAGE_18`**: Ibocain (Master Colossus Builder)
  - **`IMAGE_28`–`IMAGE_32`**: 5 Die-Cut Ragged Cardboard Persona Cutouts (Mason, Architect, Chronicler, Scout, Mechanist)
* **Photographic Captures & Map Assets**:
  - **`IMAGE_42`**: Cartographic vellum sea chart of the Comfy Valheim archipelago.
  - **`IMAGE_43`**: Cinematic twilight mountain fortress photo pass (`bd1ac417`).
  - **`IMAGE_45`**: Longhouse mead hall settlement at dusk with warm ember lighting.
  - **`IMAGE_46`**: Official Valheim Chronicler Archive logo mark.

---

### Section 4: Architecture & Mathematical Specifications

#### 1. The Kinship Overlap Formula
For any target builder $A$, their kinship score with collaborator $B$ across all active and erased eras is computed via:

$$\text{KinshipScore}(A, B) = \sum_{b \in \text{SharedBuilds}} \left( \min(P_{A,b}, P_{B,b}) \times \log_{10}(\text{TotalPieces}_b) \right)$$

Where:
- $P_{A,b} \in [0.0, 1.0]$ is builder $A$'s proportional share of placed pieces on build $b$.
- The $\log_{10}(\text{TotalPieces}_b)$ dampens single-piece noise while giving mathematically justified weight to co-constructed megastructures (e.g. 15,807 pieces on *The Grand Bastion* `bd1ac417`).

#### 2. Zero-Trust Local Storage & Discord Dispatch Security
1. **Client Privacy**: Builders can search, filter, and assert claims purely in client memory (`localStorage` / IndexedDB).
2. **Cryptographic Claim Signatures**: Claims produce a signed JSON payload with a `sha256` integrity hash. Claims never mutate immutable historical world files.
3. **Webhook Isolation**: Discord survey requests are proxied via Next.js Edge route handlers (`POST /api/dispatch/discord-ticket`) with token bucket rate-limiting (5 requests/10 min/IP), ensuring server webhook secrets are never exposed to the client.

---

### Section 5: Directory Structure & File Manifest (Zip Package Layout)

```
valheim-chronicler-archive/
├── README.md                                  # Executive overview, installation & quick start
├── docs/
│   ├── ARCHITECTURE_CQRS.md                   # CQRS Event-Store & Projection Blueprint (DOCUMENT_7)
│   ├── API_ROUTE_SPECIFICATION.md             # Next.js BFF & FastAPI Endpoint Specs (DOCUMENT_6)
│   ├── TAXONOMY_AND_USER_FLOWS.md             # UDM Persona Happy Paths & Matrix (SCREEN_26)
│   └── KINSHIP_MATHEMATICAL_FORMULA.md        # NumPy Sparse CSR derivation & role tags
├── backend/
│   ├── pyproject.toml                         # Poetry / Pip requirements (FastAPI, NumPy, SciPy, Pydantic)
│   ├── app/
│   │   ├── models/
│   │   │   └── domain.py                      # Pydantic V2 Schemas & Enums (DOCUMENT_5)
│   │   ├── routers/
│   │   │   ├── commands.py                    # Write endpoints (Claim, Photo Ticket, Stele Inscribe)
│   │   │   └── queries.py                     # Read endpoints (Gateway Stats, Profiles, Ledgers)
│   │   └── services/
│   │       └── kinship_engine.py              # NumPy / SciPy Sparse Kinship Overlap Engine (DOCUMENT_3)
├── frontend/
│   ├── package.json                           # Next.js 14, Tailwind CSS, Lucide-React dependencies
│   ├── lib/
│   │   └── valheim-archive-sdk.ts             # Universal TypeScript SDK & API Client (DOCUMENT_4)
│   ├── components/
│   │   ├── KinshipDashboard.tsx               # React Shield-Wall Graph & Matrix (DOCUMENT_2)
│   │   ├── PersonaCutoutGateway.tsx           # Minimalist 5-Persona Portal (SCREEN_25)
│   │   ├── VikingMyspaceProfile.tsx           # Builder Profile Shell (SCREEN_8, 13, 15)
│   │   └── DiscordTicketModal.tsx             # Survey Dispatch Modal (SCREEN_34)
│   └── styles/
│       └── design-tokens.css                  # Valheim Dark Theme tokens & Bodoni Moda font setup
└── assets/
    ├── portraits/                             # Ditseey, Reina Borg, Ibocain, Tugcow (IMAGE_10, 12, 14, 16)
    ├── personas/                              # 5 Folk-art die-cut character cutouts (IMAGE_28-32)
    └── captures/                              # World photographs & cartographic charts (IMAGE_42, 43, 45, 46)
```

---

*Compiled by Stitch for The Comfy Community Valheim Archival Project.*
