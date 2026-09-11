# The Comfy Community — Kinship Viewport Integration Specification
## Dual-Mode Architectural & Archival Codex (Contract & Implementation Guide)

---

### Executive Overview

The **Kinship Viewport** is a synchronized, dual-mode lens into Valheim co-construction provenance. It bridges emotive skaldic oral history with hard CAD joinery telemetry across shared monuments. 

This document outlines the **dual-mode client state machine**, **REST/WebSocket API contracts**, **NumPy sparse attribution schema**, and **Zero-Trust browser cryptographic verification protocols** required for any engineering builder integrating this viewport into their frontend stack.

---

## 1. Dual-Mode State Machine & Interaction Contract

The viewport operates on an instant client-side toggle between two distinct cognitive modes without page reloads or layout drift:

```
                  ┌──────────────────────────────────────────────┐
                  │          Active Kinship Context              │
                  │  (Builder A ⇄ Builder B · Active Monument)   │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   [ Mode 1: PHOTOGRAPHIC CHRONICLE ]            [ Mode 2: ARCHITECTURAL BLUEPRINT ]
   - High-fidelity twilight photography          - Interactive SVG/WebGL schematic (CAD)
   - Skaldic verse & lore recounting             - Foundation caisson / structural pins
   - Domestic sanctum & comfort buff             - Material allotment ratio & piece loads
   - Co-building social laurels                  - Engineering accords & snap-mesh rules
```

### State Store Contract (React / Vue / Svelte / Zustand)

```typescript
export interface KinshipViewportState {
  // Navigation & Entity Context
  activeBuilderId: string;       // e.g. "TC-7386-E7" (Tugcow)
  activeAllyId: string;          // e.g. "LN-0912" (Loanati)
  activeMonumentId: string;      // e.g. "MON-338abcbb" (Great Fjord Bastion)
  
  // Viewport Interaction
  currentMode: 'chronicle' | 'blueprint';
  zoomLevel: number;             // 1.0 = 100% (Blueprint mode only)
  selectedPinId?: string | null; // e.g. "PIN-01", "PIN-02"
  
  // Cache / Telemetry
  isAllianceVerified: boolean;
  kinshipAffinity: number;       // e.g. 92410
  allianceTier: 'Tier I' | 'Tier II' | 'Tier III';
}
```

---

## 2. API Contract Specification (BFF & FastAPI CQRS)

### A. Viewport Payload Endpoint
* **Route**: `GET /api/v1/kinship/viewport`
* **Query Parameters**:
  - `primary_builder_id` (string, required): e.g. `b_tugcow`
  - `ally_builder_id` (string, required): e.g. `b_loanati`
  - `monument_id` (string, optional): Defaults to highest weighted shared build.

#### Response Payload (`200 OK`):
```json
{
  "kinship_meta": {
    "primary_builder": {
      "id": "TC-7386-E7",
      "handle": "Tugcow",
      "standing": "Master Carpenter",
      "title": "Tugcow of Comfy",
      "role": "Hearth Lead",
      "total_pieces": 7386,
      "works_registered": 39,
      "works_imaged": 7
    },
    "allied_builder": {
      "id": "LN-0912",
      "handle": "Loanati",
      "standing": "Master Harbor Joiner",
      "bond_tier": "Tier I",
      "kinship_affinity": 92410,
      "shared_pieces": 813,
      "shared_eras": 3,
      "joint_works_count": 4,
      "ward_access": "Unrestricted"
    },
    "shield_wall_ribbon": [
      { "id": "TC-7386", "name": "Tugcow", "role": "Hearth Lead", "is_primary": true },
      { "id": "LN-0912", "name": "Loanati", "tier": "Tier I", "score": 92410, "is_active": true },
      { "id": "e103f2a3", "name": "e103f2a3", "shared_pcs": 214 },
      { "id": "toinin", "name": "Toinin", "shared_pcs": 178 },
      { "id": "atlas", "name": "Atlas", "shared_pcs": 142 },
      { "id": "yonighost", "name": "YoniGHOST", "shared_pcs": 99 },
      { "id": "ibocain", "name": "Ibocain", "shared_pcs": 74 }
    ]
  },
  "active_monument": {
    "monument_id": "MON-338abcbb",
    "name": "Great Fjord Bastion & Harbor Mead-Hall",
    "era": 7,
    "era_display": "Era VII",
    "total_pieces": 469,
    "integrity_score": 98.4,
    "grid_coordinates": { "x": -1840, "y": 320, "elevation": "60m Sea Cliff" },
    "attribution_split": {
      "primary_pieces": 300,
      "primary_pct": 64.0,
      "ally_pieces": 169,
      "ally_pct": 36.0
    },
    "materials_breakdown": [
      { "material": "Core Wood Beams", "count": 178, "pct": 38.0 },
      { "material": "Darkwood Trim", "count": 122, "pct": 26.0 },
      { "material": "Granite Footing", "count": 103, "pct": 22.0 },
      { "material": "Iron-Banded Straps", "count": 66, "pct": 14.0 }
    ],
    "chronicle_mode": {
      "hero_image_url": "/assets/captures/monument-338abcbb.webp",
      "skaldic_verse": "When the autumn sea surges tore away the third slipway, Tugcow drove heartwood pilings twenty ells deep...",
      "oral_chronicler": "Chronicler Valthor · Day 842",
      "domestic_sanctum": {
        "title": "The Shared Hearth: West Wing Quarters",
        "comfort_level": 17,
        "rest_buff_minutes": 24,
        "ward_details": "Twin Dragon-head beds, Mutual Iron Chest Vault, Guardian Ward key shared since Era VII."
      },
      "achievements": [
        {
          "id": "ach_ironwood",
          "title": "The Ironwood Anchor",
          "tier": "GOLD",
          "description": "Engineered deep-sea foundation pilings enduring 3 consecutive server storm cycles without wave decay."
        },
        {
          "id": "ach_hearth",
          "title": "Hearth-Fast Cohabitant",
          "tier": "AMBER",
          "description": "Maintained active twin bed claims & mutual iron ward chests for over 420 continuous in-game days."
        },
        {
          "id": "ach_joiner",
          "title": "Master Joiner Harmony",
          "tier": "RUNECRAFT",
          "description": "Exceeded 90k Kinship affinity with zero beam-overlap collision warnings across 4 interconnected monuments."
        }
      ]
    },
    "blueprint_mode": {
      "scale": "1:50",
      "datum_offset": 0.00,
      "total_height_m": 64.2,
      "pins": [
        { "id": "PIN-01", "label": "PIN 01: Sub-Harbor Caissons", "x_pct": 24, "y_pct": 74, "elevation": "-14m Bedrock Anchor" },
        { "id": "PIN-02", "label": "PIN 02: Hearth Flue Cross-Bent", "x_pct": 52, "y_pct": 36, "elevation": "+12m Overhang" },
        { "id": "PIN-03", "label": "PIN 03: Sea Slipway Gate", "x_pct": 33, "y_pct": 68, "elevation": "Keel Clearance" }
      ],
      "engineering_accords": [
        {
          "title": "Zero-Collision Cantilever Accord",
          "spec": "Validated 26° roof slope integration without clipped geometry.",
          "protocol": "CLEAN SNAP MESH"
        },
        {
          "title": "Deep-Water Caisson Anchoring",
          "spec": "Submerged granite caissons engineered to support 14-tier timber bents against ocean storm tidal physics.",
          "protocol": "-14M BEDROCK ANCHOR"
        },
        {
          "title": "Cohabitation & Ward Synergy",
          "spec": "Twin dragon bed claims registered in West Wing with Ward #04 mutual iron chest access.",
          "protocol": "420 DAYS SUSTAINED"
        }
      ]
    }
  },
  "joint_monument_ledger": [
    { "id": "MON-338abcbb", "name": "Great Fjord Bastion", "era": "Era VII", "pieces": 469, "ratio": "TC 64% / LN 36%", "is_active": true },
    { "id": "MON-a92f0041", "name": "Stave Church of the Mist", "era": "Era VIII", "pieces": 192, "ratio": "TC 75% / LN 25%", "is_active": false },
    { "id": "MON-88de34b2", "name": "Black Forest Watchpost", "era": "Era VIII", "pieces": 88, "ratio": "TC 45% / LN 55%", "is_active": false },
    { "id": "MON-c4cc43f7", "name": "Longship Drydock", "era": "Era IX", "pieces": 64, "ratio": "TC 40% / LN 60%", "is_active": false }
  ]
}
```

---

## 3. Mathematical Attribution Formula & Zero-Trust Hash

### The Log-Weighted Overlap Metric
Every joint monument and ally affinity rank is deterministically derived from world save byte slices:

$$\text{KinshipScore}(A, B) = \sum_{b \in \text{SharedBuilds}} \left( \min(P_{A,b}, P_{B,b}) \times \log_{10}(\text{TotalPieces}_b) \right)$$

* **$P_{A,b}$**: Proportional contribution of Builder A on build $b$.
* **$P_{B,b}$**: Proportional contribution of Builder B on build $b$.
* **$\log_{10}(\text{TotalPieces}_b)$**: Natural logarithmic damper that prevents thousands of isolated campfire placements from drowning out high-difficulty megastructures.

### Cryptographic Browser Verification
Each view renders an immutable SHA-256 verification badge:
```
HASH: 4b901a88c3f-v2
PAYLOAD: ACTIVE · ZERO-TRUST PROJECTION
```
This guarantees to players that piece counts and attribution shares cannot be edited by community admins or altered without invalidating the cryptographic checksum.

---

## 4. Frontend Component Integration (Drop-in Architecture)

```tsx
import React, { useState } from 'react';
import { useKinshipData } from '@/hooks/useKinshipData';
import { ChronicleView } from '@/components/kinship/ChronicleView';
import { BlueprintView } from '@/components/kinship/BlueprintView';
import { ShieldWallRibbon } from '@/components/kinship/ShieldWallRibbon';
import { JointMonumentLedger } from '@/components/kinship/JointMonumentLedger';

export function KinshipViewportContainer({ primaryBuilderId, initialAllyId }: Props) {
  const [activeAlly, setActiveAlly] = useState(initialAllyId);
  const [mode, setMode] = useState<'chronicle' | 'blueprint'>('chronicle');
  const [activeMonument, setActiveMonument] = useState('MON-338abcbb');

  const { data, isLoading } = useKinshipData(primaryBuilderId, activeAlly, activeMonument);

  if (isLoading) return <ViewportSkeleton />;

  return (
    <div className="kinship-viewport-root bg-[#090f16] text-[#e2e8f0]">
      {/* 1. Aligned 3-Column Identity Header */}
      <BuilderIdentityHeader builder={data.kinship_meta.primary_builder} />

      {/* 2. Guild Shield-Wall Ribbon */}
      <ShieldWallRibbon 
        allies={data.kinship_meta.shield_wall_ribbon} 
        activeId={activeAlly}
        onSelectAlly={setActiveAlly} 
      />

      {/* 3. Master Viewport Switcher & Context Bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[#222c3a]">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-amber-400 font-bold">
            KINSHIP VIEWPORT: {data.kinship_meta.primary_builder.handle} ⇄ {data.kinship_meta.allied_builder.handle}
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/40">
            ALLIANCE VERIFIED
          </span>
        </div>

        {/* The Master Mode Switcher Buttons */}
        <div className="flex items-center gap-1 bg-[#121822] p-1 rounded-lg border border-[#222c3a]">
          <button
            onClick={() => setMode('chronicle')}
            className={`px-3 py-1.5 rounded text-xs font-serif font-bold transition ${
              mode === 'chronicle' ? 'bg-[#f59e0b] text-[#090f16]' : 'text-gray-400 hover:text-white'
            }`}
          >
            ◈ Photographic Chronicle
          </button>
          <button
            onClick={() => setMode('blueprint')}
            className={`px-3 py-1.5 rounded text-xs font-serif font-bold transition ${
              mode === 'blueprint' ? 'bg-[#f59e0b] text-[#090f16]' : 'text-gray-400 hover:text-white'
            }`}
          >
            📐 Architectural Blueprint
          </button>
        </div>
      </div>

      {/* 4. Dynamic Dual-Mode Canvas & Sidebar */}
      <div className="grid grid-cols-12 gap-6 p-6">
        <div className="col-span-8">
          {mode === 'chronicle' ? (
            <ChronicleView monument={data.active_monument} onSwitchToBlueprint={() => setMode('blueprint')} />
          ) : (
            <BlueprintView monument={data.active_monument} onSwitchToChronicle={() => setMode('chronicle')} />
          )}
        </div>
        <div className="col-span-4 space-y-6">
          <AlliedBuilderDossier ally={data.kinship_meta.allied_builder} />
          <JointMonumentLedger 
            items={data.joint_monument_ledger} 
            activeId={activeMonument}
            onSelectMonument={setActiveMonument}
          />
        </div>
      </div>
    </div>
  );
}
```

---

*Authored by Stitch for The Comfy Community Valheim Archival Engineering Group.*
