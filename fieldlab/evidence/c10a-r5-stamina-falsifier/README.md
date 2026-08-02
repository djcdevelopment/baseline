# C10a r5 `UseStamina` physical falsifier

**Retained:** 2026-08-02

Candidate `m7-c10a-20260802-r5` was built from
`5b34acf18fbe9cf5d9020a1bceca46c79bb2f244`, deployed hash-exactly to the
local Gateway, AM4, OMEN, and i5, and opened both real Windows Valheim clients.
It is not accepted.

The first focused attempt, `native-20260802-c10a-stamina-r5`, armed broad client
poison without entering the retained Steam-free composition. Both clients
correctly blocked the intentionally retained native peer bootstrap before join
(`native_peer_connection=1`, `poison_trips=1`). That was a harness-shape
falsifier, not a `UseStamina` result.

The second attempt, `native-20260802-c10a-stamina-r5-full`, entered the complete
C2-C6 Steam-free composition. Both clients joined through logical peers with
native poison armed, and OMEN, i5, and AM4 each retained zero native uses and
zero poison trips. OMEN then sent `UseStamina(1.25)` to i5 through Lumberjacks;
i5 receipted the real gameplay change `50 -> 48.75`, and OMEN received the
correlated success receipt.

The reverse direction exposed the release defect. i5's motion rendezvous had
already resolved OMEN's live player as `1059480882:1`, but the stamina probe's
unfiltered `Player.GetAllPlayers()` scan selected the aliased player-shaped ZDO
`1:2860948`, owned by peer `1059480882`. OMEN refused to dispatch it because
the target was not its live local player, so no ACK or success receipt was
issued and i5 reached `routed_probe_deadline_exceeded`. Weakening that receiver
check would have counted a debit on the wrong object as gameplay success.

r6 therefore requires a probe target's ZDO user component to equal its current
owner and chooses the nearest matching live player. The harness also replaces
the invalid standalone broad-poison shape with a named native-zero composition
switch. This directory retains the compact falsifier; the ignored raw bundles
remain under `fieldlab/runs/native-valheim/`.

Both failed attempts cleaned up: the games stopped, the i5 task returned to
`Ready`, every armed AM4 cutover control was disarmed without error, both client
Lab configs were restored, the residue sweep found zero tagged objects, and P7
was untouched.
