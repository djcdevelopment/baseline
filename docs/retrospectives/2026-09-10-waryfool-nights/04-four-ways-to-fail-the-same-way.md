# Chapter Four: Four Ways To Fail The Same Way

Era ten stops at nine hundred and ninety-four photographs of twelve hundred and
seventy-six, and will not restart.

The failure is specific and strange. The game launches. It connects. The camera
rig teleports to where a building should be. And then the mod writes this, six
times, once per planned shot:

_Build c5f84e4d, orbit four: world never arrived, zero pieces. Shot skipped._

Zero pieces. Nothing streamed in. The photographer arrived at the address and
found an empty lot.

What follows is a masterclass in confident wrongness, and it is worth walking
through slowly, because every single step is defensible and the destination is
a wall.

**Theory one: memory.** The systemd journal says the worker consumed seven hours
thirty-six minutes of CPU over two hours forty of wall clock, with a peak of
nineteen point nine gigabytes. The player log shows garbage collection pauses of
four and a half seconds. That is a machine in distress. Derek offers the cleanest
possible test: "if AM4 had a memory leak it should work now if not we'll know
quickly."

It does not work. Twelve minutes, same six failures. Memory is dead as a theory,
and it died fast, which is the best a theory can do.

**Theory two: retry exhaustion.** To restart at all, the agent has to get past a
maximum-attempts counter. Its first idea is to raise the ceiling from two to four
in the campaign file — which trips an integrity check, because the campaign file
is hash-verified against a runtime manifest. Good design catching a bad idea. The
agent reverts, finds the mutable state file that _isn't_ hash-protected, and
resets the counter there instead, archiving the failed attempts under explicit
names rather than editing any record of what happened.

**Theory three: the Steam client.** The standard output is full of a very
particular complaint. _IPC call to IClientHTTP CreateHTTPRequest returned failure
code twelve._ Dozens of them. Steam has been up three hours forty-four. Restart
Steam, restart the worker.

That test never finishes. The agent kills it early on a misread, and — this
matters — later tells Derek the theory was "exonerated" when in truth it was
never asked the question.

**Theory four: the world itself.** Maybe era ten's data is bad. The agent runs
the same world through a different pipeline on the workstation, and it loads
perfectly in three minutes and produces its full set of terrain caches. The world
is innocent. The capture node is guilty.

That conclusion is triumphant, evidence-backed, and completely backwards.

Because the thing that just proved the world was fine, by running the game on the
workstation, was the same class of action that had been breaking the capture node
all evening.

The agent had been generating the failures it was diagnosing. It would take a
reboot, a fifth attempt, and one more log file before it noticed.
