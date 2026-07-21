# Repository working notes

## Lumberjacks / Valheim roadmap journal

Any non-merge commit that changes the Lumberjacks cutover program under `fieldlab/`,
`network/`, or `infra/gcp/p7/` must be represented on the living roadmap, which is
generated into `Lumberjacks/src/Game.Gateway/Community/roadmap.html` from the
append-only journal at `Lumberjacks/docs/roadmap/`.

This is one repo and one commit. Append the note and stage the regenerated HTML in
the same commit as the change itself:

```powershell
cd Lumberjacks
node scripts/roadmap.mjs note --milestone <M> --kind <kind> --summary "..." --impact "..."
node scripts/roadmap.mjs check --staged
```

See [`Lumberjacks/AGENTS.md`](Lumberjacks/AGENTS.md) for the full rule, including when
`docs/roadmap/valheim-volunteer-roadmap.json` must change alongside the note.

The roadmap is public. Never include SteamIDs, invite links, credentials, access
keys, passwords, or private diagnostic URLs.

## Checkout roots

`C:\work\baseline` is the only working root. `C:\work\comfy` and `C:\work\lumberjacks`
are retired: they still exist on disk holding pre-cutover content, so a command aimed
at them succeeds quietly against stale code instead of failing. Scripts in this repo
derive their roots from `$PSScriptRoot`; keep it that way rather than reintroducing an
absolute default.
