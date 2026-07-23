# M5-2 — Quest Content Contribution Pipeline

## Objective
The first real community-contribution lane — content, not code. A GM authors a
quest on the config site → it gets reviewed → smoke-tested in fieldlab →
signed → shipped, with the author credited visibly. Designed for two people
now, shaped to scale to twenty.

## Context
The quest configuration website exists (designed and implemented). Config
signing exists (alpha). Fieldlab exists (`fieldlab/`). Adoption-strategy lever
#4: amplify the author — credit is the durable power on offer. Quest slice
architecture: `docs/quest-vertical-slice-architecture.md`.

## Steps
1. Trace the current path of a quest config from the site's output to the
   client mod's input (files, formats, where signing happens). Document it as
   found — this becomes the pipeline doc's "how it works today" section.
2. Write `docs/quest-contribution-pipeline.md`: stages Author → Review →
   Smoke-test → Sign → Ship → Credit. For each: who acts (GM / operator),
   entry/exit criteria, and the exact command or click. Review checklist:
   does it load, does it reference only existing prefabs/events, is the
   reward within agreed bounds (note: bounds TBD with GMs — mark as open,
   don't invent numbers).
3. Fieldlab smoke test: define the minimal scenario — load quest config on the
   lab/test server, trigger its event path, confirm capture fires. Script what
   can be scripted into `fieldlab/`; manual steps get a checklist.
4. Credit: identify where the author's name can surface (quest text in-game,
   dashboard, changelog entry). Implement the cheapest one now; list the rest.
5. Run one real quest through the full pipeline end-to-end (an existing GM
   quest or a test quest) and record the pass in the doc as the worked example.

## Acceptance
- The worked example completed the whole pipeline including a visible credit.
- Every stage has an exit criterion a non-developer can evaluate.
- Open questions (reward bounds, approval authority as GMs multiply) are
  listed explicitly, not silently decided.

## Out of scope
Code contributions (CONTRIBUTING.md is separate); multi-reviewer workflow;
automated moderation.
