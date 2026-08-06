# How this repo got its shape

Background for anyone confused by the directory layout or by a doc that references a
path which no longer exists. None of this is needed to use or build the project.

## The merge

`baseline` merges the `comfy` repo and its mods with the Lumberjacks network
implementation, per [`fieldlab/plan-baseline-cutover.md`](../../fieldlab/plan-baseline-cutover.md).

`comfy`'s content lives at the repo root, history preserved unmodified — original commit
SHAs still resolve (e.g. `git show 433f1cc3`). The Lumberjacks service tree lives under
[`Lumberjacks/`](../../Lumberjacks/README.md), landed via `git subtree`, with its full
original history preserved as the second parent of the merge commit.

If `git log --follow` on a `Lumberjacks/`-prefixed path stops at the merge boundary,
that is expected subtree behavior, not lost history. Use:

```bash
git log <merge-commit>^2 -- <path>
```

## Repository family

[`baseline`](https://github.com/djcdevelopment/baseline) is the canonical, integrated
repository for current development. The original
[`Lumberjacks`](https://github.com/djcdevelopment/Lumberjacks) and
[`comfy`](https://github.com/djcdevelopment/comfy) repositories preserve public source
lineage. Their still-existing local checkouts are **retired** and must not be mistaken
for the current working tree.

## The July 2026 prune

Roughly 280 of 1,045 tracked files were deliberately removed in July 2026: the handoff
tree, community and strategy essays, a generated repo-map snapshot, a Discord/Sheets
data-harvest side project, a second Valheim mod (`comfy-control-surface`), a camera
flythrough exploration, rank-ladder recipes, a community-systems kit, and a large set of
finished fieldlab experiment plans, scenarios and evidence. None of it was load-bearing.

That included `comfy`'s original README, which the root README used to carry verbatim — a
statement of the project's community mission ("enable caring to look like art instead of
labor") and a session-by-session history of how the repo grew. It was removed because
nearly every path it pointed at is gone. It is worth reading; it is just no longer an
accurate index of this repo.

All pruned content remains recoverable from this repo's git history and from the two
still-existing source repos, `C:\work\comfy` and `C:\work\lumberjacks`. If you are
looking for something a doc references and cannot find it here, that is where it went.
