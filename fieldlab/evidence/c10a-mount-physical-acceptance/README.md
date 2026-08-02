# C10a mount physical acceptance

Status: **selected two-client saddle boundary accepted on the AM4 local lane**
on 2026-08-02. P7, Workbench, and HEARTH were not started or changed.

Exact paired candidate `m7-c10a-20260802-r27` ran on the real OMEN and i5
Valheim clients against the AM4 dedicated server. All three loaded mod version
`0.5.66` with DLL SHA-256
`337b942a64eb5632ef0bced863b9295f89269e7e928ed516404072cbac1933bc`.
The local Gateway ran the exact pinned image
`sha256:66ddf62515ca127f2e023f5b90e6afa174f20d16eb1182f17b4bf83a8276ea13`.

Accepted run `native-20260802-c10a-mount-r27-1` created one non-persistent,
run-tagged tamed Lox with a real `Sadle`, instantiated it on both clients, and
proved the typed saddle contract in both rider directions. i5 drove 8.789 m
while OMEN independently observed 9.161 m; after forced OMEN Gateway
disconnect/reconnect and authoritative reclaim to live i5, OMEN drove 9.605 m
while i5 independently observed 9.775 m. Both observer-side rider attachment
offset distributions were exactly zero in the retained sample.

The canonical owner epochs advanced 1→2→3→4→5. The disconnect path reclaimed
to the exact live i5 peer at epoch 4, both native releases retained the expected
simulation owner, and both clients rejected deliberately stale transfer,
snapshot, and real-rider-edge frames. AM4 accepted canonical snapshots across
epochs 2–5. Both clients completed every action, each resumed once in a fresh
process, and OMEN/i5/AM4 native totals and poison trips remained zero. Cleanup
destroyed exactly the one tagged Lox.

The machine receipt is
[`verification-summary.json`](verification-summary.json). Full logs remain in
the ignored run directory
`fieldlab/runs/native-valheim/native-20260802-c10a-mount-r27-1/`.

Runs r17–r26 remain falsifiers. They exposed, in sequence, incomplete saddle
target discrimination, grant/owner ordering, replica rider-parent handling,
disconnect reclaim identity, stale epoch fencing, missing logical character
reauthorization, stale snapshot/rider cleanup, synthetic stale-rider
construction, and one previously unadmitted ward RPC (`FlashShield`). They are
retained because each failure changed the implementation or the proof.

This closes the selected physical **saddle control/ownership canary**, not full
netcode. It does not prove arbitrary existing untagged Lox, a third distant
recipient, AoI enter/leave, or relevance-scoped snapshot delivery; the current
canary fan-out still uses `Everybody`. Those generalization gates remain C10,
along with container/station, AI/creature, fallback deletion, and P7 promotion.
