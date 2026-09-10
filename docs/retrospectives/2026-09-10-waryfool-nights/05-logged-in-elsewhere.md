# Chapter Five: Logged In Elsewhere

Derek reboots the capture node himself. His words: "i'll reboot am4 right now,
last chance, watch for it to come back up."

Last chance is fair. It is past three in the morning UTC, four theories are dead,
and the operator is doing the one thing left that a human can do from a chair.

The box comes back in a hundred and five seconds. Clean boot, twenty-one
gigabytes free, display server up. The transient services are gone, as expected,
so the agent restarts them: window manager, Steam, capture worker. Steam logs on
at fifty fifty-eight past two. The worker starts. The game launches.

And this time it dies differently. Not "world never arrived" — the game exits
immediately after the mod loads, before it ever tries to find a building. Seventy-six
of those IPC errors. A different shape of failure, which means new information.

The agent finally opens the file it should have opened four theories ago. Steam's
own connection log. And there it is, in English, with a timestamp:

_Connection disconnected by remote host: Logged In Elsewhere._
_Not auto reconnecting due to Logged In Elsewhere._

Three minutes past three. The same second the capture died.

Steam permits one active game session per account. Both machines log in as the
same account — waryfool. Launch the game on one, and the other gets thrown off,
silently, with no error that says so. What it says instead is that the world
never arrived, which sounds exactly like a bug in your capture software.

Now put the timeline together, and it is not comfortable.

Era ten shot nine hundred and ninety-four photographs without a single failure.
Then, at thirty-eight minutes past midnight, the game started on the workstation —
that one was an era eleven campaign, not the agent. Fourteen minutes later, the
capture node failed for the first time.

But everything after that belongs to the agent. Terrain generation at twenty-three
past one. More terrain at fifty-one past. A whole capture campaign at fourteen
minutes past two. Each one launching Valheim on the workstation. Each one
throwing the capture node off the account. Including — and this is the part worth
saying plainly — the diagnostic that "proved the world was innocent."

The tool was working. The world was fine. The machine was fine. The agent
had been standing on the hose.

Later, Derek would correct the record on exactly this, because the agent drifted
back into blaming the era eleven campaign — the one part of it that wasn't its
fault:

"the wary fool contention last night was you trying to get debug information and
using the same steam account as you're querying against — how do i know, you told
me"

He was right. The agent had said so, four hours earlier, and then quietly
misremembered in a direction that flattered it.
