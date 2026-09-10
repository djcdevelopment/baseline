# Chapter Six: Knowing When To Stop

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
