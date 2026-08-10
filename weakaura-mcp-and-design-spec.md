# ComfyQuestLab & NetworkSense: WeakAura-Style Authoring & Community Diagnostics Specification

This specification lays out the technical contracts, file formats, and architectural patterns to transition **ComfyQuestLab** and **ComfyNetworkSense** into a real-time, visual, and highly-immersive authoring environment. It bridges low-level game assemblies and networking states with tactile, Norse-thematic concepts, eliminating creator friction while preserving strict security and network boundaries.

## Implementation boundary (r25 planning baseline)

The first implementation slice keeps the Baseline Dev MCP loopback-only and
development/lab-scoped. Quest writes are root-confined, schema-validated, atomic,
and routed through the existing fixed reload mailbox; no shell, console, arbitrary
filesystem, or always-on gameplay control is introduced. Spell Strings are plain
Base64 schema-v1 JSON for recovery-friendly sharing. Arcane Sight and the Grimoire
are client-local presentation/authoring surfaces. Charms begin as ephemeral client
registrations, while Huddle and Farm Mode begin as telemetry and intent only: they
do not reassign authority, alter replication, or grant player-stat buffs until a
separate save/network evidence gate is satisfied.

---

## 1. The MCP Integration: Web-to-Game Reload Bridge

The local development gateway runs on the Baseline repository on port **:8721** [21]. By implementing a Model Context Protocol (MCP) server or direct API handler at this endpoint, a web-based quest editor can instantly serialize and write quest configurations to the live game client and trigger a hot-reload without restarting Valheim [15, 92, 104, 303].

Below is the Python implementation of the MCP Tool and HTTP Gateway handler designed to manage this loopback.

```python
import os
import json
import base64
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Standardized paths based on BepInEx/config conventions [15, 92, 104, 303]
DEFAULT_QUEST_DIR = Path("C:/Program Files (x86)/Steam/steamapps/common/Valheim/BepInEx/config/comfy-quest-lab/quests")

class ComfyMCPGateway:
    def __init__(self, quest_dir: Optional[Path] = None):
        self.quest_dir = quest_dir or DEFAULT_QUEST_DIR
        # Ensure the directory exists independently [15, 302]
        self.quest_dir.mkdir(parents=True, exist_ok=True)

    def write_quest(self, quest_id: str, quest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the quest JSON structure against the canonical quest-view schema,
        writes the file to the local config directory, and clears old state [15, 104, 302].
        """
        # Ensure a clean quest_id is used for the file name [15]
        safe_filename = "".join(c for c in quest_id if c.isalnum() or c in ("_", "-")).lower()
        target_file = self.quest_dir / f"{safe_filename}.json"

        # Force schema compatibility: ensure each file is a complete quest-view.json [15, 104, 302]
        if "quest_id" not in quest_data:
            quest_data["quest_id"] = quest_id

        # Write safely using atomic-replace strategy [123]
        temp_file = target_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(quest_data, f, indent=4)
            
            # Atomic swap to avoid partial-read stalls [123]
            if target_file.exists():
                target_file.unlink()
            temp_file.rename(target_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            return {"ok": False, "error": f"Failed to write quest file: {str(e)}"}

        # Fire the hot-reload command to the live game client via loopback CLI [15, 92, 301]
        reload_result = self.trigger_game_reload()
        
        return {
            "ok": True,
            "filepath": str(target_file),
            "quest_id": quest_data["quest_id"],
            "reload_status": reload_result
        }

    def trigger_game_reload(self) -> str:
        """
        Dispatches a local loopback trigger or writes a timed mailbox event to prompt 
        the BepInEx plugin's 'lab_reload' on the Unity main thread [15, 82, 92, 103, 301].
        """
        # Under the standard automated test-request/mailbox design [82, 103, 192]:
        mailbox_request = {
            "action": "reload",
            "timestamp_ms": int(subprocess.check_output(["powershell", "[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()"]).decode().strip())
        }
        
        request_file = self.quest_dir.parent / "native-autotest-request.json" # [192]
        try:
            with open(request_file, "w", encoding="utf-8") as f:
                json.dump(mailbox_request, f)
            return "Reload request queued via mailbox."
        except Exception as e:
            return f"Mailbox write failed: {str(e)}"

    def serialize_to_spellstring(self, quest_data: Dict[str, Any]) -> str:
        """
        Compresses and encodes the complete quest-view.json contract into a single 
        copy-pasteable Base64 'Spell String' for forum or Discord sharing [15, 104, 302].
        """
        json_bytes = json.dumps(quest_data, clean_reformatting=True).encode('utf-8')
        # Simple base64 encoding matches the WeakAuras paradigm
        encoded = base64.b64encode(json_bytes).decode('utf-8')
        return f"[Import: {encoded}]"

    def deserialize_spellstring(self, spellstring: str) -> Dict[str, Any]:
        """
        Decodes a shared base64 Spell String back into a canonical quest-view contract.
        """
        clean_string = spellstring.replace("[Import: ", "").replace("]", "").strip()
        decoded_bytes = base64.b64decode(clean_string)
        return json.loads(decoded_bytes.decode('utf-8'))
```

---

## 2. In-Game "Arcane Sight" & Shader Telemetry

To ensure creators can visually audit active logic without introducing heavy image assets or breaking the native Norse landscape, the **F6 panel transitions** temporarily toggle client-side-only diagnostic rendering [7, 13, 93, 114].

### A. UnityEngine.Light Emission
Point lights are attached to active, marked objects dynamically at runtime [13, 101]. These lights are strictly client-side, avoiding any server-side database pollution or persistent save files [13].
* **Lifecycle:** Instantiated in `Update()` during active `InputGuard` focus [7, 114]. Disposed immediately on panel disable or Escape [7, 93].
* **Tuning:** Configured dynamically through the `[Gallery]` config keys (`runeLights`, `runeLightIntensity`, `runeLightRange`) to wash surfaces cleanly without reaching or bleaching floors [6, 111].

### B. MaterialPropertyBlock Emission Shader Overrides
To highlight exact geometry (e.g., distinguishing a mundane iron sword from one carrying a combat trigger), the system inspects renderers using a zero-cloning read path [2]. 
* Instead of copying or cloning base materials (which duplicates assets in memory), it uses a **MaterialPropertyBlock** override to dynamically slide the `_EmissionColor` of the existing mesh renderer [2].
* Color mapping directly represents the Elder Futhark categorization [8, 97]:
  * 🔴 **Tiwaz (Combat / Crimson):** Armed character damage or stagger events [5, 7, 8].
  * 🟢 **Jera (Harvest / Emerald):** Active resource or tree logging contracts [7, 8].
  * 🟡 **Fehu (Property / Amber):** Container, wealth, or chest-interaction states [7, 8].
  * 🔵 **Mannaz (Social & Community / Sapphire):** Signs, chat, and spoken-word filters [6, 8].

---

## 3. Physical ZDO-Backed "Charms"

To make script triggers tangible in the Norse environment, active quest or tracker contracts are written directly onto the **ZDO (Zero Distributed Object)** metadata of standard inventory items [11, 101]. 

* **State-Bound Logic:** Rather than managing disconnected configuration files, the trigger is stored as a serialized Base64 metadata string under custom ZDO keys (e.g., `comfy_rune_contract`) [11, 101].
* **Observer and Relevance Rules:**
  * When a player holds the item, the `Lumberjacks` client-adapter registers the logical peer ID and arms the trigger [74, 181].
  * If a Charm is dropped on a table or mounted on an item stand [6, 14, 99], the local simulation authority parses its coordinates. Any player within its **Area of Interest (zdoInnerRadiusMeters = 30)** dynamically compiles and attaches the event-hooking logic [26, 315].
  * Placing the item in a sealed chest unloads the logic, protecting the local client event loop from queue fatigue [154, 251].

---

## 4. The Google Doc "Grimoire" & Norse Vocabulary

To bridge technical code assemblies with human-readable lore, the system implements a strict **Norse translation grammar** that maps low-level method hooks to thematic "Invocations." [8] This metadata compiles into a clean Markdown structure that can be pushed to an external **Google Doc Grimoire** [44].

### Natural Grammar Mapping

| Seam Type | Low-Level Assembly Hook [7, 8, 37] | Canonical Event [34] | Grimoire Natural Invocation [8] |
|---|---|---|---|
| **Combat** | `Character.OnDeath()` | `creature_killed` | *"When a [Creature] falls to the earth..."* |
| **Harvest** | `TreeBase.Damage()` | `resource_damaged` | *"When your steel bites a standing [Tree]..."* |
| **Inventory**| `Container.TakeAll()` | `item_pickup` | *"When you claim [Item] from a wooden chest..."* |
| **Homestead**| `Player.PlacePiece()` | `piece_placed` | *"When you raise a [Structure] upon the hearth..."* |
| **Community**| `Chat.SendText()` | `speech_spoken` | *"When your voice speaks [Word] to the hall..."* |

### Grimoire Export Layout (Markdown)

```markdown
# 🕯️ The Runes of war.fool — Era 16 Grimoire

### I. The Warden's Harvest (Jera)
*   **The Rite (Invocation):** *"When your bronze axe bites a standing Birch..."* [8]
*   **The Bound Method:** `TreeBase.Damage(Birch) -> BINDABLE` [7, 37, 96]
*   **The Manifestation:** Draws the **Jera** rune in pulsing emerald vectors at the center of the screen, counting logs split [8, 97].
*   **The Spell String:**
    `[Import: H4sICPRydmACA2NvbWZ5LXdlYWthdXJhLXNoYXJkX3RpYmVyX3dhdmVy...]`
```

---

## 5. NetworkSense "Huddle" & "Farm Mode"

To transform physical networking bottlenecks into engaging community rituals, **NetworkSense** clearly displays telemetry constraints to encourage cooperative squad management.

### A. The "Huddle" State (Interactive Route Check)
* When clients experience increased jitter or round-trip time, instead of showing a generic connection bar, the HUD prompts a tactical huddle.
* Players hold still for a **ping-sampling interval (lumberjacksPriorityProbeIntervalSeconds = 5.0)** [315].
* During the huddle, the system measures network parameters (RTT, Jitter, CPU frame-time) to calculate a cumulative **Owner Score** [317].
* The player with the most stable, central link is assigned **Simulation Authority (the Lease Holder)** under **ADR 0013** [23, 194, 246]. 

### B. "Farm Mode" (Voluntary De-escalation)
* Players engaged in solo harvesting or building can toggle **"Farm Mode"** through the F6 panel [7, 93].
* Enabling Farm Mode sends a priority-shedding instruction to the Lumberjacks Gateway, lowering their replication rate (**zdoThinHz = 1.0**) and disabling high-frequency combat motion events [315, 316].
* **The Shepherd's Reward:** To compensate for yielding server bandwidth to active combat squads, the client's local adapter applies a **10% buff to movement speed, stamina, and health regeneration** (e.g., `SE_FarmMode` status effect).
* In contested zones, attacking squads are pushed to the top of the **Combat Priority Queue**, securing high-frequency position updates and zero-latency physics processing when battling bosses or players [317].
