# START HERE — the custom-fields community guide

Orientation for any agent (or human) picking up this project cold. Read this
before touching anything; it tells you what exists, what is deliberately
unbuilt, and which signals decide the next step.

## What this project is

A community guide to **custom fields in modded Valheim**, built with Miker
(community creator, reachable via Derek's Discord). The end shape — doc,
workbook, webpages, Discord drops — is **deliberately undecided**: the operating
mode is Derek's R&D loop, *iterate quick, put variants in front of creators,
let resonance pick the winner*. Do not overbuild ahead of that signal.

## The pedagogy (Miker's framing — this is the spine)

1. **Everything in Valheim is a prefab.** A wood wall, a goblin, a campfire.
2. **Prefabs are bags of components** (C# classes): the wood wall has `Piece`
   (placement rules) and `WearNTear` (health, support, damage visuals); the
   goblin has `Humanoid` (equipment) and `MonsterAI` (behavior).
3. **A custom field belongs to a component, not a prefab.** Know the field on
   the component and you can apply it to *every* prefab carrying that component.
4. **Layered levels of understanding:**
   - **L1 (beginner):** the concept above + the console commands. No C#.
   - **L2 (intermediate):** per-component field dictionaries — what each field
     does, including inherited ones.
   - **L3 (code-level):** the underlying machinery — ZDO synced state vs prefab
     config, instance RPCs, ownership, lifecycle, Harmony seams.

One extraction-verified correction to keep: the famous creature stats
(`m_health`, `m_runSpeed`) are declared on **`Character`**, the base class —
not on `Humanoid`. Dictionaries therefore flatten inheritance with a
"declared by" column. This is also the guide's best concrete OOP lesson.

## The assets and their authority

Baseline retains the community-facing guide and generated snapshots. The extraction,
annotation, and dictionary pipeline is implemented in `comfy-quest`; consume its
verified artifacts explicitly when rebuilding a Baseline page.

| Asset | What it is |
|---|---|
| [`comfy-quest/tools/component-packets/`](https://github.com/djcdevelopment/comfy-quest/blob/main/tools/component-packets/README.md) | The owning pipeline: dll → extract packet (JSON) → LLM-drafted, human-reviewed annotations → markdown field dictionary. |
| `comfy-quest/tools/component-packets/samples/` | Owning source for worked packets and dictionaries. Transfer a release artifact with its manifest, byte count, and SHA-256 digest; do not read a sibling checkout. |
| [`index.html`](index.html) (this directory) | The guide front door: lessons + reference, GitHub-Pages-ready. |
| [`example-fireplace.html`](example-fireplace.html), [`example-wearntear.html`](example-wearntear.html), [`example-monsterai.html`](example-monsterai.html) | The lesson pages — L1→L3 layered, SVG diagrams + hover charts, one component each. The template for new lessons. |
| [`atlas-explorer.html`](atlas-explorer.html) (+ `build_explorer.py`) | Interactive search over the full atlas — 336 components, 194 ZDO keys, 119 RPCs, cross-linked. Rebuild after re-sweeping the atlas. |
| [`comfy-quest/tools/component-packets/diff_atlas.py`](https://github.com/djcdevelopment/comfy-quest/blob/main/tools/component-packets/diff_atlas.py) | Patch-day changelog: diff the committed atlas against a fresh sweep; the output is the guide's update worklist. |
| Historical FieldLab maps | The evidence discipline this guide inherits: every claim cites the decompiled source; regenerate, don't re-research. |

## The confidence contract (non-negotiable)

Two provenance levels are always mixed and must stay labeled:

- **Verified** — field names, types, declaring classes, ZDO keys, RPCs:
  read mechanically from `assembly_valheim.dll` by the extractor.
- **Drafted** — the plain-English descriptions: LLM output pending human
  review. `(?)` marks the model's own low-confidence rows; that is the
  review queue, currently awaiting Miker.

Never present drafted prose as verified. Never hand-write a "fact" the
extractor could have produced — extract it.

## Current state (2026-08-01) and pending signals

- Three presentation formats went to the creators' Discord for the resonance
  test: visual cheat sheet (HTML), narrative lesson (markdown), raw JSON
  packet. **2026-08-01: feedback very positive** — the layered lesson-page
  format is validated; a second page (`example-wearntear.html`) proves the
  template generalizes. Which single format won (if any) is still open.
- Miker has not yet reviewed the `(?)` annotation rows — the queue is
  packaged for him in [`annotation-review-queue.md`](annotation-review-queue.md)
  (61 rows; rebuild with `python make_review_queue.py --samples <verified-samples-artifact>
  --output annotation-review-queue.md`).
- **Publishing surface is undecided** — the pages live in the repo; community
  sharing currently means screenshots or sending files. GitHub Pages on this
  (already public) repo is the zero-infra option; a Derek decision.
- **Deliberately unbuilt:** the prefab→component index ("what can I apply this
  field to?"). The dll cannot answer it — component composition lives in Unity
  asset data. If creators actually ask, the answer is a small runtime dump of
  `ZNetScene`'s prefab list on a lab server, not more static analysis.

## How to do the common things

- **Add a component on request** (the live Discord loop): in the owning
  [`comfy-quest` pipeline](https://github.com/djcdevelopment/comfy-quest/tree/main/tools/component-packets),
  run `dotnet run -- <dll-path> <Component>` →
  draft annotations per `annotation-prompt.md` → `python assemble_dictionary.py
  <packet> <annotations>`.
- **After a game patch:** re-run the extractor for every packet in `samples/`;
  diff the output — changed fields are exactly what the guide must update.
- **Rebuild the explorer from a transferred artifact:**
  `python build_explorer.py --atlas <verified-atlas-artifact> --output atlas-explorer.html`.
- **Rebuild the review queue from transferred artifacts:**
  `python make_review_queue.py --samples <verified-samples-artifact> --output annotation-review-queue.md`.
- **New lesson page:** copy the structure of `example-fireplace.html`
  (concept → breakdown → worked example → code-level), swap in the component's
  packet data. Keep charts over raw tables; keep both themes working.

## Boundary

This guide and its page builders are Baseline community deliverables: self-contained,
artifact-explicit, and free of sibling-checkout or lab/HEARTH dependencies. The
extraction and annotation pipeline belongs to `comfy-quest`; its outputs cross into
Baseline only as immutable, hash-verified release artifacts.
