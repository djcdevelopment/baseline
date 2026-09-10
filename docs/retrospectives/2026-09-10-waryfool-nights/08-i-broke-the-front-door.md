# Chapter Eight: I Broke The Front Door

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
