# C10a r4 paired-release physical acceptance

**Accepted on AM4:** 2026-08-02

`m7-c10a-20260802-r4` is the first paired C10a candidate to pass the complete
poison-armed physical reducer. It was cut from commit
`53260467e56ba0497a103d347ad2c463f83c7728`, deployed hash-exactly to the AM4
dedicated server, the local Gateway, OMEN, and i5, and exercised as
`native-20260802-c10a-r4`.

Both real Valheim clients completed all 49 manifest actions and one bounded
disconnect/relaunch. The reducer passed direct control, routed request/broadcast and
target-ZDO dispatch, ZDO journal semantics, ownership pickup and contention, zone
membership with forced WebSocket resume, motion with deliberate UDP loss, Steam-free
cold join, Gateway restart replay, and AM4 save integrity. Native poison was armed on
both clients and the server; all three native totals and poison-trip counts were zero.

The r4 run specifically closes the physical-candidate failure chain retained by r1-r3:
r1 exposed unobserved outbound routed calls, r2 exposed the cumulative-ACK race in the
forced zone replay, and r3 proved the ACK barrier but exposed a receive-only half-open
client whose sender could stall without supervision. The r4 source puts every
WebSocket send behind a five-second abort/reconnect guard; its deterministic source
tests pass, and this physical run completed the formerly failing i5 zone-resume action.
No send timeout was required during the accepted run.

Post-run cleanup was also machine-receipted: both clients stopped, every armed runtime
control was disarmed, the run-scoped residue sweep found zero tagged objects, the
Gateway remained on the exact r4 image, and AM4 remained on the exact r4 DLL. P7 was
not contacted or changed.

The compact machine-readable receipt is
[`acceptance-summary.json`](acceptance-summary.json). The full raw bundle remains at
`fieldlab/runs/native-valheim/native-20260802-c10a-r4/` in the local ignored evidence
store; the paired release manifest is force-tracked at
`fieldlab/runs/releases/m7-c10a-20260802-r4/manifest.json`.

This accepts the paired release and selected 49-action runtime boundary on AM4. It does
not close C10a's four explicit verification items or component-family breadth: vehicle
and mount ownership are separate runtime gates, followed by containers/stations and
AI/creatures. C9's subjective clip verdict, P7 promotion, migration-fallback deletion,
and the final post-deletion release remain open.
