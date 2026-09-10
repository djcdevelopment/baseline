# Chapter Seven: Seven Thousand Invisible Pictures

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
