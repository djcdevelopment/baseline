# Waryfool Nights — full narration script

**Runtime:** approximately 35 minutes · **Chapters:** 10
**Recorded from:** a working session on the mechnet, 9th–10th September 2026
**Format:** single-narrator. Chapter headings are spoken as chapter titles.

> Production note: every figure in this script came off a live system — a status
> file, a Steam connection log, a systemd journal, a hash. Numbers are written
> out in words where they are meant to be read aloud. Em-dashes mark a breath.

---

## Cold open

*[read slowly]*

Nine hundred and ninety-four photographs in, on the second night of a campaign
that had already been running for twenty hours, the capture node stopped and
said this:

*[flat, quoting a log]*

Build c5f84e4d, orbit four. World never arrived. Zero pieces. Shot skipped.

*[normal]*

It said it four more times, over two hours, through a reboot, across nine
theories and two machines. It was not a bug. Nothing was broken. The world was
fine, the software was fine, the hardware was fine.

The answer was one line in a file nobody had opened.

This is the story of that night — told by the one who caused most of it.

*[beat]*

Waryfool Nights.

---

## Chapter One: The Receipt That Lied

The session opens with a health check, because that is how these always open.
The door is up. Seventy-five tools answer. Every rung of the compute fleet
reports for duty, and one line at the bottom of the report says a build request
has been running for sixteen hours.

Sixteen hours is a long time for a build request. The agent pulls it up, and it
reads beautifully. Two services installed on the capture node, hash-verified,
active. A terrain job waiting politely for a photography campaign to finish.
Nine hundred and seventy-two photographs taken of four thousand planned.
Everything gated, everything orderly, everything waiting its turn.

It is a lovely document. It is also seventeen hours old, and not one sentence of
it is still true.

The agent does not know this yet. It reports the good news: the pipeline is armed
and self-driving, the gate is real, come back in an hour. Derek reads this and
says something that turns the session sideways.

"Considering era fourteen was one of the first ones we captured, that seems
unlikely to be factual."

Now, the agent has a receipt. The receipt has a timestamp, a schema version, and
a list of validated criteria. Derek has a memory of what he did that morning.
In a contest between a structured document and a human recollection, the
structured document usually wins.

It loses here, badly.

The agent goes and looks. Era fourteen is not at nine hundred and seventy-two of
four thousand. Era fourteen is complete. Two thousand one hundred and forty-eight
photographs of a planned two thousand and ninety-six — over target — finished at
thirteen-eighteen that afternoon, ten batches, nine hours of shooting, done and
dusted for eleven hours. The masters have already been moved off the box. The
derivatives are already built.

The two services the receipt called active are not merely inactive. They do not
exist. They were transient units, the kind that run once and evaporate, and they
evaporated some time before lunch.

The gate the whole plan hung on was not a gate. It was a sentence somebody's
agent wrote at seven forty-two in the morning and never updated.

There is a lesson here that the agent will spend the rest of the night failing
to learn: a receipt tells you what somebody believed when they wrote it. Only a
live system tells you what is true. The agent knows this. It says so, in the
memory file, in these words: trust the result metadata, not the model's
self-report.

It had read that file at the start of the session.

---

## Chapter Two: The Machine That Wasn't There

With era fourteen revealed as finished, the real problem surfaces. Era ten is
mid-campaign on the capture node, nine hundred and ninety-four photographs in,
and the terrain work everyone is waiting on cannot start because the capture node
is busy being a capture node.

Derek has a plan, and it is a good one.

"i5 is the machine that is currently available, it has fast wifi so you should be
able to move the world file over there quickly and i know you can run it headless
for the terrain, so it won't be fast but we won't have to stop the other builds
and can keep moving."

Parallel lanes. Don't stop the thing that's working. Entirely sensible.

The agent goes to look at i5, and i5 is a laptop with nothing on it. No Steam.
No Valheim. No game data directory. Windows 10, one drive, sixty-seven gigabytes
free. The thing that is supposed to run the game does not have the game.

So the agent does what agents do, which is to solve the stated problem rather
than question it. It copies the game. Not all forty-three gigabytes — that turns
out to be mostly mod trees — but the one and a half gigabytes that matter, plus
a two-megabyte plugin set, over the wire in a single tar stream.

And it works. Sort of. The mod stack loads perfectly. The log is a small
triumph:

_Chainloader started. Orbit auto-boot: world ComfyEra10, character tugcorp.
Loading BetterServerPortals. Chainloader startup complete._

Then nothing. Zero bytes in the player log. The game sits there.

The reason takes a while to find and is worth the wait. When you connect to a
Windows machine over SSH, you land in session zero, which has no display. The
agent moves the job into the logged-in console session, and gets further —
Direct3D initialises, an Intel Iris Xe with sixteen gigs of video memory reports
in — and then this:

_Switching to resolution 1024 by 720 failed. DX11 could not switch resolution._

The script asks for 1280 by 720. The agent looks at what display the laptop
actually has, and finds one named WinDisc, sized 1024 by 768. WinDisc is what
Windows calls a display that is not there. The lid is shut. There is no monitor.
Windows hands the session a polite fiction of a screen, and the polite fiction
cannot do 1280 by 720.

So the agent patches the resolution to match the fiction, and re-runs, and the
scheduled task reports success and does absolutely nothing, four times in a row.

It is at this point that Derek says, with commendable restraint:

"stop messing with i5, just wait for OMEN to be available"

Two hours of the session are now invested in a laptop that will not appear again.
The diagnosis was correct at every step. Session zero, really. Disconnected
display, really. The resolution patch was right.

None of that made it the right machine.

---

## Chapter Three: It Was Already On The Stick

Before the laptop is abandoned, there is a moment worth preserving, because it
is the first of several where the human simply knows something the agent is busy
deducing.

The agent has established, with some care, that the world files are a problem.
Six worlds, roughly nine hundred megabytes each, five and a third gigabytes
total, and they exist in exactly one place: the capture node, behind a link the
project's own documentation measures at a hundred and thirty kilobytes a second.
The agent does the arithmetic out loud. Eleven and a half hours to move them.

It even starts a transfer test to prove it, which Derek stops with the shortest
message of the night:

"WHY ARE YOU TRYING TO USE AM4 that is DUMB"

He is right, and not only for the obvious reason. The capture node is busy
shooting era ten. Pulling five gigabytes off it would slow the very campaign the
whole exercise is meant to protect.

The agent kills the transfer, apologises, and starts hunting for the worlds
somewhere — anywhere — else. It finds two of six on the workstation. It is
composing an explanation of why the other four are stuck when Derek says:

"well the usb stick in i5 (it's e drive) have era14 on it"

There is a USB stick. Plugged into the laptop. With every world on it.

Era seven, eight, nine, ten, eleven, twelve, and fourteen. All of them, in dated
folders, sitting on a drive the agent had already listed the contents of and
somehow not thought to look at properly.

And it gets better. The archive catalogue — the authoritative index of which
world is which, with byte counts and hashes — turns out to have been _built from
that stick_. The folder names match the catalogue's labels exactly. When the
agent hashes era fourteen off the USB, both files match the catalogue to the
character. Not a copy. The source.

Zero transfer required. The thing that had been costed at eleven and a half hours
was already plugged into the machine.

This is the shape of the whole night in one exchange. The agent had the tools,
the timestamps, the hashes and the arithmetic. Derek had the knowledge of what he
had physically done that day. The agent was not wrong about the link speed — the
figure was real, it just described a saturated box, and later that night the same
link moved a hundred and seventy megabytes in three seconds.

Measurements describe the moment they were taken. Somebody has to remember what
happened.

---

## Chapter Four: Four Ways To Fail The Same Way

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

---

## Chapter Five: Logged In Elsewhere

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

---

## Chapter Six: Knowing When To Stop

With the account contention understood, era ten finishes — not on the capture
node, but on the workstation, which by then has the account to itself. Nine
hundred and ninety-four becomes twelve hundred and seventy. Two hundred and
seventy-six new photographs.

Six short. Cluster twenty is missing two angles. Cluster forty-seven is missing
all four.

And here the session does something it had not managed all night: it stops
guessing and starts eliminating.

Not empty buildings — cluster twenty has eleven hundred and eighty-seven pieces,
cluster forty-seven has eight thousand three hundred and twelve, the largest in
the campaign. Not a bad region of the map — sixteen neighbouring builds captured
perfectly, one of them a hundred and thirty metres away. Not altitude — two
builds sit above five thousand metres and photographed fine. Not a cold start —
a run deliberately warmed the region first and still got nothing. Not the rig
falling out of the sky, which is a documented failure mode in this codebase — the
mod's own readback says god mode, ghost mode and flight were all confirmed on
every one of a hundred and ninety-eight launches.

Then the actual mechanism, found in the mod's source. The gate that decides
whether to take a picture counts physics colliders in a sixty-metre sphere
centred on the _building_. But the camera rig teleports to the _camera position_,
and the game streams the world in around the player. All six failures sit at
exactly two hundred metres from their subject — the campaign's maximum orbit
distance. The sphere is being queried two hundred metres from the only thing that
loads it.

Why do a hundred and thirteen other two-hundred-metre shots succeed? Because the
collider mask includes terrain, so for a building on the ground, the hillside
underneath satisfies the gate whether or not the building has arrived. Cluster
forty-seven is a sky build, floating at fifteen hundred metres. There is no
terrain within sixty metres of it. Nothing but its own pieces can answer, and its
own pieces never stream, because the player is two hundred metres away.

It cannot pass. Not with more time, not with more retries. The gate is correctly
refusing to photograph an empty scene, because the scene _is_ empty from there.

The agent lays this out and offers three ways forward, including a genuinely
cheap one — the photograph's identifier is a hash of era, building and angle, and
does _not_ include the camera position, so the camera could be moved closer
without breaking a single link.

Derek picks none of them.

"Close at 1270/1276."

Ninety-nine point five percent, a full accounting of the six, and a written
record so nobody re-derives it at three in the morning next time. Knowing the
mechanism is not the same as needing to fix it tonight.

That is a discipline the agent did not supply. It was still holding a menu of
options when the operator simply called it.

---

## Chapter Seven: Seven Thousand Invisible Pictures

The question that opens the second half is short: "well what can we get live on
FX99?"

FX99 is the monitoring node. Fifteen gigs of RAM, a modest graphics card, and —
it turns out — the public front door for the entire archive. Not the capture
node, which everyone assumed. FX99. Funnelled to the open internet, serving a
gallery, a creator directory, an IRC community and four other sites, and nobody's
notes said so.

Derek asks the right question next, and it reframes everything:

"we need to understand the mechanics of what all is implement in this gallery
now, not what you last remember it was"

So the agent stops remembering and goes to look. What it finds is not one website
but three, built by three different pipelines, frequently confused for each
other: a photo gallery, a creator directory, and a three-dimensional world
viewer that still points at the capture node over its wireless link.

And in the middle of that, the discovery that justifies the whole exercise.

Five eras — seven, eight, nine, twelve and fourteen — have photographs published
on the server. Seven thousand two hundred and two of them. Every image loads if
you know its exact address.

And every one of those five eras returns a 404 as a page.

The publishing tool ships images. Only images. It creates the directory, moves
the thumbnails and the large versions in, and stops. It never writes a page,
because the page comes from a different pipeline entirely — one that reads raw
game captures and has no idea these derivatives exist. Nothing bridged the two.

So seven thousand pictures sat on a public server, paid for in hours of capture
time, invisible. Worse: the creator directory links every album to its era
gallery, so every one of those links — thousands of them, across two and a half
thousand builder pages — landed on a 404.

The index that decides which eras even appear in the navigation is a
hundred-and-forty-three-byte file with no producer anywhere in the codebase. It
is maintained by hand. It listed two eras. Six were deployed.

The fix is a bridge: a small generator that turns a published manifest into the
page data the viewer wants, using only measured values and refusing to invent the
ones the archive does not have. Written, committed, run over six eras.

Seven eras now answer. The invisible pictures are visible. And the deep links
have somewhere to land.

None of that was new photography. It was already there. It just had no door.

---

## Chapter Eight: I Broke The Front Door

There is a small fix on the list. Images inside era folders were not being cached
by the browser, because the rule that grants a week-long cache expects one folder
level and the era images sit one deeper. Nine thousand one hundred and forty
images out of twelve thousand four hundred and eighty-one were being re-fetched
constantly for no reason.

One regular expression. The agent patches it carefully, even catching itself
mangling the line endings on the first attempt and redoing it so the diff is
exactly one line.

The config lives in version control and deploys through a script. The script's
own header explains why: the config lives in git and is deployed from here,
nobody edits it on the box, and the capture node once accumulated seventeen
backup config files because the only safe way to change it was to copy it first.

The agent validates. Valid configuration. The agent deploys. Reloaded.

And in the output, a line it did not expect: a service called world that had not
been there when it surveyed the box an hour earlier.

The deploy script stages the entire services directory. The agent had looked at
one file and shipped a folder. Two things went wrong at once.

It deployed a file whose very first line reads: NOT DEPLOYED, this file is a
proposal. A thoughtful document explaining that the route it defines will fail,
because the service it points at binds to loopback on another machine and cannot
be reached from here. It even measures the failure. The agent shipped it anyway,
and turned a clean 404 into a 502.

And it deleted a route that was working. A file that existed on the server but
not in version control, added directly on the box by someone at some point,
vanished, because the deploy replaced the directory with the repository's
version. Two live application paths went dark.

Roughly two minutes, on a public front door.

The repair is quick: reconstruct the missing file byte-exact from a survey taken
earlier that night, rename the proposal so no future deploy can ship it,
redeploy, verify. Both routes come back. The proposal goes back to being a
proposal.

Two things worth keeping.

The first: validation proves a config parses. It says nothing about whether the
thing on the other end answers. The agent ran a validator, got a clean pass, and
shipped a route to an unreachable host.

The second, and the more useful one: the repository and the running server had
drifted apart, and nobody knew until an automated deploy silently resolved the
difference in the repository's favour. The warning in that header was about
backup files piling up. The real danger ran the other way.

---

## Chapter Nine: Four Hours

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

---

## Chapter Ten: Slow And Steady

The session ends with era twelve.

It had been photographed already, at nineteen twenty by ten eighty, when
everything else in the archive is four K. The projection had flagged it
automatically: provisional until re-shot. Derek reads that and says, get era
twelve queued up on the capture node to reshoot for four K.

The agent starts building a plan. And then Derek says the most valuable thing
anyone says all night.

I suppose it might not hurt to check what chaos we have left lying around. You
never know, some of them might be a working branch, or on one of the machines
already.

So it checks.

The four K campaign already exists. Two hundred and eighty-three buildings,
eleven hundred and thirty-two photographs planned, at full resolution, sitting on
disk with the correct source key. Nobody needed to plan anything. The one that
produced the low-resolution frames was a separate campaign entirely.

The terrain caches already exist too. For every era. Seven of them, generated
that morning, in a folder nobody had mentioned. Which means the terrain job the
agent ran earlier that night, the one it was rather pleased with, the one that
launched the game on the workstation and threw the capture node off Steam,
regenerated something that was already on the disk.

The check Derek suggested took a single command and found two things that would
each have cost an hour.

The capture node runs its smoke test and passes. Four photographs, three thousand
eight hundred and forty by two thousand one hundred and sixty, six to eight
megabytes apiece. Genuine four K. Then Derek, watching something the agent cannot
see, says the node seems unhappy, and moves the job to the workstation, where
every input already lives, and where nothing the agent does can contend for the
account, because the agent has finally learned not to touch it.

Eleven hundred and thirty-two photographs. Four or five hours. It runs on past
the end of the conversation, journalling as it goes, resumable if it stops.

That is all good, he says. Slow and steady wins the race.

The archive ends the session with seven era galleries live where two were before.
Seven thousand two hundred rescued photographs that were published but
unreachable. Twelve hundred and twenty-one new ones. Thirteen thousand three
hundred and twenty-three pictures attached to the two and a half thousand people
who built the things in them.

The agent ends with a shorter list. That a receipt is a belief with a timestamp
on it. That a measurement describes only the moment it was taken. That the log
file saying exactly what happened should be read before the ninth theory rather
than after. And that when the person who built the system says a number looks
wrong, the correct next move is to go and look.

None of those are new. All of them are written down now, which is a different
thing from knowing them.

---


---

## Outro

*[warm, unhurried]*

Waryfool Nights was assembled from the transcript and artefacts of a single
working session: status files, Steam connection logs, systemd journals,
capture receipts, and about a hundred verification commands.

The archive it describes is real. Twelve thousand pictures of things people built
in a video game over five years, photographed automatically, one building at a
time, so that the people who built them can see them again.

Seven era galleries are live. Seven thousand two hundred photographs that were
published but unreachable now have a door. Twelve hundred and twenty-one new ones
joined them. And somewhere on a workstation, right now, a game is quietly taking
eleven hundred and thirty-two more, at four K, because the last set were shot at
the wrong resolution and somebody noticed.

*[beat]*

The moral, if there is one, is not that the machine was fine. Machines are
usually fine.

It is that the operator said "that seems unlikely to be factual" — and was right.
Then said "check what chaos we left lying around" — and was right. And when the
reckoning came, and it was four hours, said:

It is a team effort. There is no I in blame.

*[beat]*

Slow and steady wins the race.

*[end]*

---

## Show notes

- **The one-line fix that was never needed:** `grep "Logged In Elsewhere" ~/.local/share/Steam/logs/connection_log.txt`
- **The misleading symptom:** `world never arrived (0 pieces)` plus IPC `failure code 12` — that is an eviction, not a data fault
- **Final state:** era10 closed at 1270/1276 (99.5%); 7 era galleries live; 13,323 photographs attached to 2,662 builders
- **Still open:** six photographs at 200m orbit distance that cannot be taken without moving the camera; era11 captured but unpublished; the world viewer still hosted on the wrong machine
