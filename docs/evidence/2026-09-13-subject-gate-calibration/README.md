# Subject gate calibration -- 2026-09-13

**Question.** Can whole-build geometry, computed before any shutter, name the subjects the
judge called not worth a photograph (debris, a bare floor) without rejecting a build the eye kept?

**First attempt (rejected).** One threshold per feature, fitted to the 77 labelled detail-tier
builds of 2026-09-12 (all >= 529 pieces, median ~3,000) at zero keepers lost. It caught 6 of
33 `neither` builds there -- and then rejected 50 of 170 builds in era 1's full coverage queue
for being under 6.2 m tall. Those are single-storey houses: a Valheim wall is 2 m, a roofed
hut is 4-6 m, and the labelled sample had simply never contained one. Fitted extremes do not
transfer from the detail tier to a coverage queue.

**What ships.** Two rules, each a conjunction with limits that mean something physically,
declared in `thresholds.json` and applied by `tools/selfie-stick/subject_gate.py gate`:

| rule | clauses | meaning |
|---|---|---|
| bare-floor | height < 3 m AND floorShare > 0.5 | a floor, path or fence line with nothing standing on it |
| debris | density < 0.02 pieces/m2 AND largestMassShare < 0.35 | thin scatter with no coherent mass |

On the 77 labelled builds they catch 0 of 33 `neither` and reject 0 keepers (there are no
bare floors among 500-piece builds). On era 1's coverage queue they remove 5 of 170: lots of
2-51 pieces, 0-2 m tall, 57-100 % floor. `calibration-era11.json` records the per-class
feature distributions the limits were checked against.

**Recalibrate** when light-table sessions on the new eras accumulate `neither`/`reshoot`
verdicts on coverage-queue builds: `subject_gate.py calibrate --thresholds thresholds.json`
reports each rule's catch and loss on the labelled set; move a limit only with that in hand.
