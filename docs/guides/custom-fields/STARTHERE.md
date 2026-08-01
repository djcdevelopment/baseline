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

## The assets (all in this repo)

| Asset | What it is |
|---|---|
| [`tools/component-packets/`](../../../tools/component-packets/README.md) | The pipeline: dll → extract packet (JSON) → LLM-drafted, human-reviewed annotations → markdown field dictionary. Three scripted steps, ~1 min per component. |
| `tools/component-packets/samples/` | Worked packets + dictionaries: `Piece`, `WearNTear`, `Humanoid`(+`Character`), `MonsterAI`(+`BaseAI`), `Fireplace` (packet only). 250 annotated fields. |
| [`example-fireplace.html`](example-fireplace.html) (this directory) | Sample guide webpage: the L1→L3 layered approach worked end-to-end on one component, with SVG concept diagrams and charts. The template for "what a published lesson looks like." |
| `fieldlab/NETCODE-MAP.md`, `fieldlab/REMOTE-PLAYER-LIFECYCLE-MAP.md` | The evidence discipline this guide inherits: every claim cites the decompiled source; regenerate, don't re-research. |

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
  (61 rows, regenerate with `make_review_queue.py`).
- **Publishing surface is undecided** — the pages live in the repo; community
  sharing currently means screenshots or sending files. GitHub Pages on this
  (already public) repo is the zero-infra option; a Derek decision.
- **Deliberately unbuilt:** the prefab→component index ("what can I apply this
  field to?"). The dll cannot answer it — component composition lives in Unity
  asset data. If creators actually ask, the answer is a small runtime dump of
  `ZNetScene`'s prefab list on a lab server, not more static analysis.

## How to do the common things

- **Add a component on request** (the live Discord loop):
  `cd tools/component-packets` → `dotnet run -- <dll-path> <Component>` →
  draft annotations per `annotation-prompt.md` → `python assemble_dictionary.py
  <packet> <annotations>`.
- **After a game patch:** re-run the extractor for every packet in `samples/`;
  diff the output — changed fields are exactly what the guide must update.
- **New lesson page:** copy the structure of `example-fireplace.html`
  (concept → breakdown → worked example → code-level), swap in the component's
  packet data. Keep charts over raw tables; keep both themes working.

## Boundary

This guide and its tooling are Baseline community deliverables: self-contained,
extraction-friendly, no lab/HEARTH dependencies. The annotation step is a
generic LLM prompt template on purpose — anyone can run the whole pipeline with
a licensed Valheim install, the .NET 8 SDK, Python, and any capable model.
