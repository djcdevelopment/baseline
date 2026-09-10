# Chapter Two: The Machine That Wasn't There

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
