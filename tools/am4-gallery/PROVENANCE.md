# Provenance — vendored AM4 gallery source

## Why this directory exists

These files are the **live** gallery running on the AM4 host. Until 2026-08-06 they
existed in exactly one place: `~/gallery/` on that machine, in no git repository, with no
copy anywhere else. The only redundancy was a handful of `*.bak-<timestamp>` files sitting
in the same directory on the same disk.

The API that used to accompany them is a cautionary tale for exactly this: it stopped on
2026-06-25 and stayed stopped, and because nothing was versioned or supervised, working
out what it had even been took a search of the whole box. (It turned out to be
`~/am4bot/bot.py`, which serves the Discord bot and the gallery API from one process.)

This is a **vendored copy for durability and reference**, taken because the Valheim
gallery work is about to build on these files. It is not the deployment source.

## Origin

Copied from `am4:~/gallery/` on **2026-08-06**:

| file | what it is |
| --- | --- |
| `index.html` | the gallery front end — facets, sort, pagination, lightbox, starring |
| `build_index.py` | builds `index.json` from bench result sidecars; run by `gallery-refresh.timer` every 2 min |
| `request.html` | the request submission UI; posts to `/api/requests` |
| `gen_caddyfile.sh` | regenerates `/etc/caddy/Caddyfile` from `users.txt` |
| `users.sh` | add/remove/list gallery logins |
| `who_report.py` | access-log reporting |

## Deliberately not copied

- **`users.txt`** — the basic-auth store, `name:bcrypthash` per line. It is the secret and
  it stays on the host. Both `gen_caddyfile.sh` and `users.sh` read it at runtime; neither
  embeds a hash, which is why they are safe to vendor.
- **`index.json`, `now.json`, `status.json`, `stars.json`** — generated state, rewritten on
  a timer. `index.json` also carries user-submitted prompt text and requester names.
- **`*.bak-*`** — superseded snapshots.

## Do not run `gen_caddyfile.sh` from here (or anywhere)

It regenerates the **old** layout, in which the gallery is served at the site root of
`:8190`. The live `/etc/caddy/Caddyfile` has since grown a mech-commander proxy, a public
community storefront (`redir / /workbench 302`), and the gallery relocated under
`handle_path /gallery/*`. Running the generator would overwrite all of that.

It is vendored because it documents the original intent and the `users.txt` contract — not
because it is still safe to execute. Edit `/etc/caddy/Caddyfile` directly, keeping a dated
backup alongside the existing `.bak-*` and `.pre-mech-*` files.

## Routing drift found on copying — and repaired 2026-08-06

Both of these were live faults, not theoretical ones. The gallery moved from the site root
to `/gallery/` when the public storefront took the root, and two paths were left behind.

**1. Thumbnails and full images 404'd.** `index.html` requests **relative**
`thumb/<id>.webp` and `img/<id>.webp`. Served from `/gallery/`, those resolve to
`/gallery/thumb/...`, which `handle_path /gallery/*` strips and roots at
`/home/derek/gallery` — a directory containing neither. The 3,315 real images live under
`/home/derek/bench/results_full/{thumb,img}`.

Fixed in `/etc/caddy/Caddyfile` by adding two handlers **before** the `/gallery/*` block
(Caddy evaluates `handle` blocks in written order):

```caddy
handle_path /gallery/thumb/* {
        root * /home/derek/bench/results_full/thumb
        file_server
}
handle_path /gallery/img/* {
        root * /home/derek/bench/results_full/img
        file_server
}
```

Verified by `caddy adapt`: the two image roots now each appear twice — once for the
original top-level `/thumb/*` and `/img/*`, once for the `/gallery/`-prefixed pair.
Backup kept at `/etc/caddy/Caddyfile.pre-gallery-thumbfix-20260806-091410`. The caddy user
can read the store, so no `setfacl` step was needed.

**2. The live status card was dead.** `request.html` fetched absolute `/now.json`, which
has no handler. Changed to relative `now.json`, which resolves to `/gallery/now.json`
(present, auth-gated). Fixed in both this copy and the host copy; host backup at
`~/gallery/request.html.bak-nowjson-*`.

Note the `/api/*` calls in both pages are correctly absolute — those are top-level Caddy
routes proxied to the bot on `127.0.0.1:8200` — and `index.json` is correctly relative.
`/now.json` was the only path on the wrong side of the move.

**Verification caveat:** every `/gallery/*` path returns `401` unauthenticated because
`basic_auth` runs before the handler, so a runtime probe cannot distinguish "fixed" from
"broken" without credentials. `401` replacing `404` proves a handler now matches; the
`caddy adapt` root check proves it matches the right one. Confirming the pixels render
still needs one logged-in look.

## Related risk, not yet addressed

`~/am4bot/` **is** a git repository but has **no remote configured**, and carries
uncommitted changes to `bot.py`. It is therefore also a single-disk copy. It is not
vendored here because it is AM4 imagegen infrastructure rather than Baseline, and because
`bot.env` lives beside it. Giving it a remote is the fix.
