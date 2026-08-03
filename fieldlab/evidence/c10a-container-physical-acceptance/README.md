# C10a container physical acceptance

Status: **selected two-client container transaction accepted on the AM4 local
lane** on 2026-08-02. P7, Workbench, and HEARTH were not started or changed.

Exact paired candidate `m7-c10a-20260802-r34` ran on the real OMEN and i5
Valheim clients against the AM4 dedicated server. All three loaded mod version
`0.5.73` with DLL SHA-256
`6a076ce929b3d343883a88ba5e1f8a1601648299292b73ef1c1d37c815ec0635`.
The local Gateway ran exact pinned image
`sha256:7942aca93246505340822f939d3bab5a6236848e60f45874aa02ccbfafc55c51`.

Accepted run `native-20260802-c10a-container-r34-1` created a real
`piece_chest_wood` at deterministic generated terrain height and seeded its
real inventory with one Raspberry. Both physical clients reconstructed that
same chest, invoked the actual `Container.TakeAll` method, and sent an original
plus a byte-equivalent duplicate transaction. The server held all four copies
from the two distinct peers before mutating the chest.

OMEN won the revision-one contention and changed inventory 10 to 11. i5 lost
as stale and remained 23 to 23. The server committed one mutation, rejected one
stale contender, replayed both duplicate transaction IDs without another
mutation or credit, and serialized the real empty inventory inside the
revision-two journal batch. Native `TakeAll` was suppressed on both clients.

The actual chest stayed under canonical ownership. The scoped owner guard
blocked reassignment attempts from both original physical peers before commit
and from both new peer incarnations after the fresh-process boundary; unrelated
ZDO owner changes remain outside this guard. Both relaunched clients requested
a durable refresh, received an exact snapshot, and reconstructed the same chest
at revision 2 with metadata count 0, real inventory count 0, and owner 0.

Both clients completed the 23-action composition with one fresh-process resume,
and OMEN, i5, and AM4 native-use ledgers remained zero. Cleanup matched and
destroyed exactly the one tagged container. The compact machine receipt is
[`verification-summary.json`](verification-summary.json). Full logs remain in
the ignored run directory
`fieldlab/runs/native-valheim/native-20260802-c10a-container-r34-1/`.

The physical harness reached completed composition but returned nonzero because
its first reducer version required every owner-suppression row to have owner 0.
That was a false predicate: the intended proof has a server-owned phase before
commit and an owner-zero phase afterward. The reducer was corrected to require
two distinct attempted physical owners in both phases; rerunning it over the
same preserved evidence passed all 19 checks. No failed gameplay action was
relabelled and no evidence was edited.

Runs r29-r33 remain falsifiers. In order, they exposed an unsnapped chest being
tombstoned by structural wear, the Steam-free server's lack of a terrain
collider, a fixed-delay contention race, missing explicit inventory
serialization plus native owner reclaim, and a fresh-process durable-interest
refresh gap. Each failure changed the implementation or the acceptance proof.

This closes the selected physical **container transaction canary**, not every
station implementation. Smelter, cooking-station, and other station-specific
RPC semantics were not physically invoked here; they remain admitted/poisoned
breadth until exercised or contradicted. AI/creature, arbitrary untagged
vehicle/mount relevance, fallback deletion, and P7 promotion also remain.
