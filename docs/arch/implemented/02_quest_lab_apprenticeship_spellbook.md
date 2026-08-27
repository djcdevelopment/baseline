# Quest Lab --- Apprenticeship and the Creator Spellbook

## Role

Quest Lab should evolve from the original in-game teaching UI into the
apprenticeship layer of the creator ecosystem.

Arcane Sight asks: **What is the runtime doing?**

Quest Lab asks: **What am I experiencing, how does the system understand
it, and what useful ideas can I carry into my own creations?**

## Learning Gradient

`Player → Observer → Apprentice → Remixer → Creator`

A player experiences an Event without automatically seeing its
machinery. With creator permission, an apprentice can inspect selected
concepts, understand them, save useful constructs, and later reuse those
concepts in their own work.

## Preserve Suspense

Event internals should be hidden by default.

Start with simple semantic permissions: - Hidden: experience only. -
Explainable: conceptual explanation available. - Share selected
patterns: designated constructs may be saved. - Remixable: broader
artifact inspection/import allowed.

Do not build a complicated ACL system yet.

## Spellbook / Notebook

The notebook carries portable creator knowledge.

Examples: - Proximity ambush. - Shout within radius. - Wave-completion
gate. - Prolonged-combat relief. - Gate-destruction failure. -
Consume-item progression. - Timed survival. - Adaptive reinforcement.

A saved item need not copy the entire Event. It can contain stable
ID/version, attribution, explanation, required primitives, example
configuration, sharing permission, and an optional canonical
fragment/reference.

## Quest Lab Integration

The existing schools already teach the grammar: Combat, Harvest,
Inventory, Building, Crafting, Progression, World, Social.

Quest Lab can explain which events are bindable versus diagnostic, what
a current Quest listens for, why an objective advanced, what the player
just did that mattered, and which reusable pattern is present.

## Core Interaction

`Observe → Explain → Save to Spellbook`

Later:

`Studio → Open Spellbook → choose saved pattern → use directly or ask AI to compose from it`

Example: "Use the gate-failure pattern I saved, but start this encounter
when someone rings a bell."

## Creator Teaching Palette

Creator leads should be able to share a limited beginner palette without
exposing flagship Event internals: spawn this, say this, open/move this
gate, loot this item, eat this food, remain in combat this long, enter
this region, clear this wave, advance this Quest.

## First Implementation Slice

1.  Preserve school/event exploration.
2.  Give concepts/patterns stable identity.
3.  Add minimal Save to Spellbook for explicitly shareable examples.
4.  Persist notebook independently of an Event.
5.  Let Studio read the notebook.
6.  Let agents reference notebook items during authoring.
7.  Preserve attribution/version metadata from the beginning.

## Success Condition

A player can participate in another creator's Event, receive permission
to inspect a mechanic, understand it through Quest Lab, save it to a
portable notebook, and later use it while creating a different Event.
