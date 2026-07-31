# PD-3 — Public community-data posture

Status: adopted 2026-07-29 (Derek); promoted from the decision queue
2026-07-30.

## Context

The public `djcdevelopment/comfy` archive contains real community material:
guild-tracker data, generated quest-picker data with member names, and player
handles. Removing those files from the current tree would not remove them from
Git history. Restricting Workbench links would reduce discovery but would not
change the data's existing public status.

The operator confirmed that everyone named had been consulted and knew the data
was public, that the source trackers were already shared publicly in multiple
forms, that reported misattributions were corrected, and that volunteer GMs
donated the live quest data.

## Decision

Retain the existing community data in the public archive. Workbench material may
link to the recipes and recovery handoffs without pretending the underlying
history is private.

This decision applies to the corpus reviewed in July 2026. It is not blanket
permission to publish new participant data.

## Operating boundaries

- A new dataset requires its own consent and exposure check before publication.
- Corrections or withdrawal requests are evaluated against the affected current
  artifact and its Git history; do not promise that deleting `HEAD` erases
  history.
- Never publish credentials, access tokens, private diagnostic URLs, or data that
  participants did not knowingly make available.
- If repository visibility or the participant cohort changes materially, review
  the affected dataset rather than reopening the entire historical corpus by
  default.

## Alternatives rejected

- **Prune from `HEAD`:** creates the appearance of removal while Git history
  continues to carry the data.
- **Link-only containment:** reduces discovery but does not change existing
  publication and obscures how the community artifacts were produced.
