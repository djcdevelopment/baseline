# Weekly Rhythm

This weekly cycle exists to make it easier to keep caring. Turning community
maintenance into a short, predictable checklist protects the operator's time and
makes the work fully delegable later. We're not fixing a broken process — we're
lowering the standing cost of running the world so the people who build it can
enjoy it instead of drowning in it.

**Target: ~30 minutes, once a week.**

> _Optional pre-collect:_ before you start, `git log --since="1 week ago" --oneline`
> gives you the shipped changes for the changelog step, and a quick skim of the
> community Discord gives you the week's feedback. Keep it trivial — no tooling
> required.

## The checklist (~30 minutes)

### 1. Feedback sweep (~5 min)
- [ ] Read recent activity in the community Discord (ad hoc messages + anything
      raised during streams).
- [ ] Drop each raw item into a triage note (see
      [templates/feedback-triage.md](templates/feedback-triage.md)).

### 2. Roadmap update (~10 min)
This is the heart of the rhythm. The convention is explicit:
**"you said → we did / we won't / later."** Every swept item gets exactly one
disposition, each with a one-line reason:

| Disposition | Means | Always include |
|---|---|---|
| **did** | it's live | a link to the change |
| **won't** | we're not doing this | a gentle, structural one-line why |
| **later** | captured for a future wave | a one-line note on when it might fit |

- [ ] Move each triaged item onto the live **Volunteer Roadmap** with its
      disposition and reason. No item leaves the sweep undisposed.

### 3. Changelog post (~10 min)
- [ ] Identify which mod updates shipped this week (updates ship as Steam-bound
      downloads).
- [ ] Write 2–3 player-facing sentences per update using
      [templates/changelog-entry.md](templates/changelog-entry.md).
- [ ] Post to the community Discord and the roadmap.

### 4. GM touch-base (~5 min)
- [ ] A light, warm check-in with the absorbed Guild Masters — what repetitive
      work stole their time this week, what they enjoyed.
- [ ] If something worth keeping surfaces, capture it as a
      [session-residue](templates/session-residue.md) note. This is a steward's
      mirror to remove their toil and center their authorship — never an audit.

## Where things live
- **Feedback arrives** in the community Discord (ad hoc + during streams).
- **Dispositions are visible** on the live **Volunteer Roadmap**
  ("you said → we did / won't / later").
- **Changelog posts** go to the community Discord and the roadmap.
- **Working notes** (triage, residue) live under `docs/templates/`-derived files.
- **Tuning changes** need a [netcode tuning-ledger](../network/tuning-ledger.md)
  entry before they ship — no entry, no ship.
