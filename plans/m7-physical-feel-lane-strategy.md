# M7 physical feel lane strategy

Status: ready for a bounded live run after the two physical clients are joined.

## Purpose

Use the three-account, three-machine topology to separate two questions that are
currently easy to conflate:

1. Does the distributed transport produce the expected evidence and counters?
2. Does the movement look and feel acceptable to a human watching two clients?

The dedicated server identity remains a server concern. The two player identities
are assigned to the existing physical clients: OMEN is player A and i5 is player B.
No server GUI login is required, and no Steam credential is stored in the repository,
passed to a script, or printed in a receipt.

## Human-light operating model

The physical clients must be joined and fully loaded once. After that, the agent owns
the loop through the Companion HTTP surfaces and the existing i5 SSH lane:

```text
readiness
  -> capture starts on OMEN and i5
  -> one client is set APPLY and the other OBSERVE
  -> named movement pattern runs for a bounded duration
  -> capture closes and evidence is retained
  -> optional role reversal repeats without relogging
  -> agent reports counters and asks for felt result
```

Run the coordinator from the repository root:

```powershell
tools\i5\Start-TwoClientFeelWindow.ps1 `
  -Pattern straight_north `
  -MotionDurationSeconds 10 `
  -CaptureDurationSeconds 25 `
  -ApplyClient omen `
  -RoleReversal `
  -Label sprint-role-reversal `
  -CollectBundles `
  -OutputJson .\captures\physical-feel\sprint-role-reversal.json
```

The command does not launch or close Valheim and does not simulate keyboard input.
The intended interaction is to watch both screens, then answer three small questions:

- smooth, rough, or mixed;
- did the visible effect follow the APPLY role;
- where was the first correction, glide, teleport, or stop-response anomaly?

If a user has not joined both clients yet, stop before the coordinator and ask for
one join window. Do not turn a missing peer into repeated relogs or repeated motion
runs.

## Experiment matrix

| Window | Pattern | APPLY role | Human input | Evidence question |
|---|---|---|---|---|
| A | `straight_north` | OMEN | Watch sprint and stop | Does the visual result have a machine/account-independent transport signature? |
| B | `straight_north` | i5 | Watch sprint and stop | Does the result follow the APPLY role after reversal? |
| C | `stutter_north` | OMEN then i5 | Watch short corrections | Are stutter steps more stable or more discontinuous than continuous motion? |
| D | `circle` | OMEN then i5 | Watch turns | Does correction behavior appear at direction changes rather than cadence changes? |

Start with A+B. Only run C or D if the first pair produces usable telemetry and the
human can describe a distinct visual difference. The named patterns are test stimuli,
not claims about the final movement equation.

## Evidence contract

Each run retains:

- the read-only Wave 0 readiness receipt;
- the OMEN/i5 concurrent capture comparison;
- the apply/observe command receipt;
- the movement command receipt;
- child-process stdout/stderr paths;
- optional local copies of both Companion evidence bundles;
- the exact pattern, duration, interval, apply sequence, and UTC timestamps.

Interpretation rules:

- peers above zero with zero Lumberjacks motion deltas means the visible movement is
  native Valheim evidence for that run;
- advancing Lumberjacks motion counters means the motion transport was observed;
- bad samples or missing readiness fields invalidate the transport conclusion but do
  not invalidate a human visual note;
- if the visual effect follows the APPLY role after reversal, that is evidence about
  the selected application path, not proof that all ZDO authority has cut over;
- no result promotes P7 authority or changes the current M7 gate by itself.

## Why this is the right use of the accounts and hardware

The physical lane provides the missing human signal that headless clients cannot:
perceived glide, correction, stop latency, teleporting, and whether the result feels
deterministic. OMEN and i5 also expose different local runtime, display, and network
conditions while sharing the same server and release. The APPLY reversal controls for
machine-specific bias without asking for another Steam login.

The disposable headless lane remains useful for synthetic generation, replay, and
authority experiments. It must use separate seeded client volumes or an alternate
account assignment; a Steam identity cannot be treated as both a physical client and
a headless client at the same time. Seeding is a one-time UI operation, not part of
every experiment.

## Stop rules and next decisions

Stop the window if either Companion command fails, either capture is incomplete, a
client leaves the server, or a movement command remains pending after its bounded
duration. Retain the receipt and change the failing seam before repeating.

After A+B, compare:

1. human observation against APPLY role;
2. motion counter deltas against the visual window;
3. server-ping age/jitter and peer/player-name evidence;
4. role-reversal consistency between OMEN and i5.

If only the visual result changes while transport evidence stays stable, investigate
client interpolation/rendering. If transport counters change with the role and the
visual result follows them, investigate the motion publish/apply seam. If both are
stable but the result feels rough, the next experiment should isolate cadence versus
prediction using the synthetic E03 fingerprints before changing production equations.
