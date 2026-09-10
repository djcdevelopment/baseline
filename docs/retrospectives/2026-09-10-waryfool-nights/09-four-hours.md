# Chapter Nine: Four Hours

Late in the session, after the gallery is live and era ten is published and the
account contention is finally understood, Derek asks a quiet question.

Do you know how many hours I wasted because of the bug?

The agent can measure its own part. Two hours and eight minutes between the first
failure and the last eviction. Four failed capture attempts. Two rounds of
surgery on a state file. An edit that tripped an integrity check. A Steam
restart. A full excavation of a mod's source code. A reboot the operator
performed himself, because the agent had run out of ideas.

What it cannot measure is everything that happened before it arrived. The era ten
campaign was created at ten past five that evening. Era fourteen had run from
quarter past four in the morning until twenty past one in the afternoon. By the
time the agent saw its first failure, the operator had been at this for the
better part of twenty hours.

Probably four, he says.

Four hours. And the answer was one command against a log file that says, in
plain English, that you have been logged in elsewhere.

Before finding it, the agent had investigated memory pressure, a stale Steam
client, corrupt world data, build geometry, piece counts, altitude, map region,
camera distance, cold-start streaming, and the internals of a physics query.
Nine theories. Every one tested properly. Every one a real piece of engineering.
All of them downstream of a fact nobody had written down: two machines, one
account, and a silent eviction that disguises itself as a data problem.

What Derek says next is the reason this account exists at all.

It is a team effort. There is no I in blame.

Which is generous, and also, on checking, true.

What gets banked against those four hours is small and specific. A memory file
that now leads with the log line and names the misleading symptom, so the next
session recognises it in seconds instead of deriving it in hours. A written
closeout for six photographs nobody will ever take, with the mechanism explained,
so nobody re-runs those experiments at three in the morning. And one proposal not
yet built: teach the capture worker to read the Steam log when a batch fails, and
report kicked by another host instead of repeated failure.

Four hours becomes four seconds. That is the real return on a bad night. Not the
fix, which was trivial once found, but the note that stops it costing the same
again.
