# Baseline session notes

Read [AGENTS.md](AGENTS.md) first. Baseline is the knowledge/evidence/index hub; active
product implementation belongs to the sovereign repositories in
[REPO-MAP.md](REPO-MAP.md).

For a cold pickup, use [the fleet era map](docs/internal/START-HERE.md), then the
relevant report under `docs/internal/repo-split/reports/`. Do not repair a missing
product path by copying code back or reaching into a sibling checkout.

The landing protocol is one pass: an instruction to land/ship includes an intentional
commit, `git pull --ff-only`, and a direct push to `main`. Baseline has no roadmap-note
hook after the split; product repositories define their own ceremonies and gates.
