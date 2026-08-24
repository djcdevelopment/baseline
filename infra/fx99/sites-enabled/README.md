# Adding something to the FX99 front door

Two ways, and only two. Which one you need depends on whether the thing is files
or a process.

## Files — no configuration at all

```bash
rsync -a --delete ./my-gallery/  fx99:/srv/sites/my-gallery/
```

It is now at `https://fx99.tail8e749c.ts.net/my-gallery/`. No file to edit, no
reload, nothing to remember. The slug is the directory name; it must match
`[a-z0-9][a-z0-9._-]*`.

This is the case that matters, because it is the one that happens constantly —
a gallery, a demo, a one-pager, a scratch report someone wants a link to. On AM4
each of those was a hand-added block in a shared 134-line file, which is how that
file ended up with seventeen backups.

## A process — one file, never shared

Create `<slug>.caddy` here:

```caddy
handle_path /steward/* {
	reverse_proxy 127.0.0.1:7080
}
```

Then deploy and reload:

```powershell
.\infra\fx99\deploy.ps1
```

`deploy.ps1` runs `caddy validate` first and refuses to reload a config that does
not parse, so a bad edit costs you an error message rather than the front door.

### Proxying something that lives on another host

Same file, tailnet address instead of localhost:

```caddy
handle_path /grafana/* {
	reverse_proxy am4.tail8e749c.ts.net:3000
}
```

Worth knowing what this costs: while the service still runs on AM4, every request
crosses AM4's wifi, which measured **0.56 MB/s** against FX99's 14 MB/s. Routing
it here does not make it faster — it makes it *addressable* from one place, so
that moving the service later is a one-line change to a file that already exists.
Migrate the route when the service is ready to follow, not before.

## Ordering

The main Caddyfile imports this directory **before** the static convention, inside
an explicit `route {}` block. So a service named `foo` always wins over a directory
named `foo`. That ordering is written down rather than inferred, because Caddy's
implicit specificity sorting is exactly what surprised someone on AM4 and got
explained in a comment instead of fixed.

## Seeing what is served

```bash
site list
```

Prints every URL this box answers on, static and proxied, with sizes and targets.
AM4 has no equivalent — you read the Caddyfile and hope.
