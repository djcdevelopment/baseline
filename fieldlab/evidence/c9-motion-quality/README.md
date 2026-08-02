# C9 motion quality — machine and artifact gates complete on AM4

**Status:** machine and retained-artifact gates complete on 2026-08-02; Derek's
subjective rendered-motion verdict remains pending. The accepted physical run is
`native-20260802-c9-motion6`, using two rendered Valheim clients (OMEN/Tugcorp and
i5/durracktu), the AM4 dedicated server and Gateway, and mod SHA-256
`a658af8bb39ac619cbf967dc9fa007745d042088c4ffaa500b119012c9085d55`.

The machine-readable result is
[`c9-motion-quality-summary.json`](c9-motion-quality-summary.json), regenerable with:

```powershell
python fieldlab/scripts/Write-C9MotionQualitySummary.py `
  --output fieldlab/evidence/c9-motion-quality/c9-motion-quality-summary.json `
  --run native-20260802-c9-motion6 `
  --source-commit same-commit-as-evidence `
  --mod-sha256 a658af8bb39ac619cbf967dc9fa007745d042088c4ffaa500b119012c9085d55 `
  --rendered-artifact fieldlab/runs/motion-clips/native-20260802-c9-motion6/c9-motion-quality-side-by-side.mp4
```

## Acceptance result

| C9 gate | Result | Retained evidence |
| --- | --- | --- |
| No unexplained hard correction | Passed | Three reliable-resync events, all inside the commanded `motion_*_gap` pair; zero `target_rejected` bursts and zero native fallback. |
| No persistent target divergence | Passed | Both 20 s ordinary observer probes completed with zero holds, gaps, resyncs, or failures. The injected-gap observer held once and recovered by reliable resync. |
| Bounded injected-loss recovery | Passed | OMEN withheld exactly sequences 1086–1105; i5 entered hold with `native_fallback=false` and applied the accepted reliable resync after 0.895 s. |
| No apply-attributable wall-clock hitch | Passed | The run-scoped perf windows contain 7 OMEN and 8 i5 lifecycle hitches. None has a `LumberjacksMotionRunner` section accounting for the frame; the largest are Valheim's own `Starting respawn` frames. |
| Retained rendered presentation | Passed | One 20.067 s, 2560×720, 30 fps side-by-side artifact contains both observer/driver role combinations. Both source receipts verify that the exact Valheim process window was maximized and foreground before capture. |
| Derek's subjective rendered-motion verdict | **Pending** | Review the retained side-by-side clip once and record `smooth`, `rough`, or `mixed`; no live KVM session or rerun is required. |

## Physical run result

- Both clients reached `scenario_complete`, stopped cleanly, and completed one
  fresh-process resume. Both final ledgers report `native_total=0`, `poison_trips=0`,
  and zero writer drops/faults while poison was armed. The server poison control was
  armed for the run and disarmed afterward.
- i5 observing OMEN east received 308 numbered frames, applied 1,696 presentation
  updates, suppressed 2,002 selected native transform-writer calls, and reported zero
  failures. OMEN observing i5 north received 349 frames, applied 1,464 updates,
  suppressed 2,000 selected native writer calls, and reported zero failures.
- During the loss cell, i5 received 275 frames, applied 1,096 updates, held once,
  recorded one gap and one reliable resync, and reported zero failures. OMEN's driver
  receipt records exactly 20 deliberately withheld frames and an accepted resync.
- The server readiness receipt remained green with the canonical server connected,
  a fresh heartbeat, and the descriptor for this exact run.

## Rendered artifact

The retained review artifact is
[`c9-motion-quality-side-by-side.mp4`](../../runs/motion-clips/native-20260802-c9-motion6/c9-motion-quality-side-by-side.mp4):

- 11,840,999 bytes; SHA-256
  `b419d17995cde00146a32c2a4ea9e5c7937458ff13c473c114292db68a3b2dee`;
- left panel: OMEN observing durracktu's northbound motion;
- right panel: i5 observing Tugcorp's eastbound motion;
- each panel is trimmed against its own machine clock and annotated from that
  machine's receipts; no cross-machine simultaneity is claimed or required;
- ffmpeg freeze detection reports no panel freeze of 0.5 s or longer at `-60 dB`;
- sampled-frame review by Codex shows each named remote avatar advancing across the
  framed path with no visible hard correction in the ordinary motion windows.

No `smooth`/`rough`/`mixed` verdict is attributed to Derek yet. That one-word review is
the remaining subjective C9 acceptance item; the machine and artifact gates above are
complete and do not need to be rerun to obtain it.

The two source capture receipts are retained beside the raw clips. They record exact
foreground-handle equality (OMEN PID 49912, handle 241437642; i5 PID 18320, handle
4065110), which rejects the terminal/loading-screen false positives encountered on the
earlier attempts.

## Rejected diagnostic attempts

- `native-20260802-c9-motion3` exposed a real harness defect: background execution was
  reasserted before the joined-peer boundary, then Unity reset it during scene change.
  The request now waits for the real player and peer before consuming that reassertion.
- `native-20260802-c9-motion4` passed machine checks, but its recordings showed a load
  screen and a terminal/partial game window. It was rejected, and capture now fails
  closed unless the actual Valheim window owns the Windows foreground handle.
- `native-20260802-c9-motion5` passed machine and foreground checks, but OMEN's remote
  avatar was behind the persisted camera. It was rejected. The bounded autotest-only
  observer probe now faces the midpoint of the declared remote path without moving the
  observer; normal gameplay never calls that seam.
- `native-20260802-c9-motion6` is the first accepted run because it passes the machine,
  foreground, framing, and retained-artifact gates together.

## Evidence reducer correction

This run also exposed that the older reducer read entire append-only perf logs and
could mix historical sessions into one run. It now bounds perf rows to the selected
scenario's completed-action window, accepts PowerShell's UTF-8 BOM, and only attributes
a C9 apply hitch to the actual `LumberjacksMotionRunner` section. Unrelated HUD or
scenario-controller work can explain a frame but cannot be mislabeled as motion apply.

## Prior C8 baseline and limits

The retained C8 pair `native-20260731-c8-full44` and `full45` remains the broader
composition baseline. It established that teleport/zone corrections were commanded,
target-rejection bursts were transient, and the once-per-session cold-join stall was
Valheim's own `WorldGenerator.Initialize`, not motion apply. C9 does not reopen those
boundaries.

C9's machine evidence proves motion correctness and retains visible presentation. It
does **not** substitute for Derek's pending subjective verdict, and it does **not**
close C10's 33 P1 admissions (29 instance plus four global), three `[VERIFY]` rows,
component-family gates, release alignment, P7 promotion, or fallback deletion.
