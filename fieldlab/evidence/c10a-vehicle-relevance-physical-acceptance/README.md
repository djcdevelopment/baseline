# C10a untagged vehicle relevance physical acceptance

**Accepted on AM4:** 2026-08-02

`native-20260802-c10a-relevance-r41-1` closes the last local C10a functional
gate. The exact `m7-c10a-20260802-r41` DLL was deployed with the same SHA256 to
AM4, OMEN, and i5, and the local Gateway ran the exact paired r41 image.

Both rendered clients completed the 41-action manifest and one fresh-process
resume. One ordinary untagged tamed Lox was discovered independently by the
server, owner, and observer; ownership traversed both players, disconnect
reclaim, and the dedicated server through canonical epochs 1-6. Both physical
drive/observe directions passed, attachment error remained zero, and AM4
continued publishing the idle mount from its ZDO-only representation.

The run also physically exercised the defect exposed by r40. Valheim's
`ReleaseNearbyZDOS` sweep attempted to assign the server-owned mount to both
clients before resume and to the replacement sessions after resume. r41 logged
and suppressed all four attempts. i5 then moved outside relevance and back in;
the server recorded `snapshot_relevance_left` followed by
`snapshot_relevance_entered` while direct per-observer fan-out continued.

The corrected fail-closed reducer passes all 27 checks. The same reducer still
rejects retained r40, so the evidence fix did not erase the earlier functional
failure. Native-network use and poison trips remained zero, both clients stopped
cleanly, runtime controls were restored, and cleanup destroyed exactly the one
in-memory-tracked untagged mount. P7 was not contacted or changed.

The compact receipt is
[`verification-summary.json`](verification-summary.json). The full raw bundle
remains in the ignored local evidence store at
`fieldlab/runs/native-valheim/native-20260802-c10a-relevance-r41-1/`; the
single-use manifest and coverage receipt are committed under
`fieldlab/scenarios/`.

This accepts the local untagged mount/vehicle relevance boundary. It does not
claim a third physical Valheim client; M7-E04 is the retained three-recipient
policy proof. C9's subjective clip verdict, P7 candidate promotion, fallback
deletion, and the final post-deletion P7 proof remain open.
