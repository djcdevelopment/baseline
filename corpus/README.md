# Baseline corpus

This directory defines how Baseline's public knowledge is discovered. It does not own
that knowledge.

The contract is:

> Structured corpus, reconstructable indexes, replaceable projections.

## Three layers, three different jobs

1. **Authoritative artifacts** stay with the thing a person or agent would edit. A
   narrative has an `artifact.json` beside its HTML/template; the Workbench remains
   `Lumberjacks/docs/workbench/workbench.json`; the roadmap remains its append-only
   JSONL journal; a dispatch is the starter post and applied tags in Discord.
2. **Mirrors** make an external authority rebuildable offline. The dispatch capture is
   an exact, public-by-contract mirror of forum starter posts. It carries Discord IDs
   and links and never pretends to outrank Discord.
3. **Indexes and projections** under `site/corpus/`, `site/for/`, `site/explore/`, and
   `site/updates/` are disposable build products. Delete them and run the builder.

The normalized index is deliberately small-minded. It contains the fields needed for
the deterministic paths we use now: identity, kind, title, summary, audience, URL,
time, and provenance. Every adapter also preserves its domain record under `data`, so
the common schema does not have to predict the next useful interpretation.

## Discovery

[`sources.json`](sources.json) is a registry of source *families*, not a catalog of
every item. Sidecars are found by glob. Workbench and roadmap use explicit adapters
because they already have strong native schemas. The optional Discord mirror is read
when it exists.

An `artifact.json` is valid when:

- it validates against [`schemas/artifact.schema.json`](schemas/artifact.schema.json);
- every declared source file is inside the sidecar's own directory;
- every audience ID exists in [`audiences.json`](audiences.json); and
- its ID is globally unique.

That containment rule makes an artifact movable, locally understandable, and safe for
an agent to inspect without crawling the repository.

## Audience lenses

Audience IDs are discovery hints, not permissions and not identities. A person can use
several lenses in one visit. `curious` is always a valid way in; `contributor` is a
participation view across disciplines, not a claim that someone must become an owner.

The shared vocabulary lives in [`audiences.json`](audiences.json). Source artifacts
store only stable IDs. Renderers own ordering and presentation.

## Build and prove reconstruction

```powershell
python tools/corpus/build.py
python tools/corpus/build.py --check
python tools/corpus/test_corpus.py
```

`--check` rebuilds every byte in memory and compares it with the committed projection.
It also validates source containment, audience references, unique IDs, provenance
hashes, and feed shape.

To create a reviewed starter post through the existing bot, inspect the dry run and
then explicitly publish it:

```powershell
python tools/dispatches/dispatches.py publish
python tools/dispatches/dispatches.py publish --yes
```

The command is create-only. Once the starter exists, Discord owns subsequent edits.
To refresh the rebuildable mirror after people publish or edit dispatches:

```powershell
python tools/dispatches/dispatches.py capture
python tools/corpus/build.py
```

Only starter posts in the dedicated forum are syndicated. Replies stay conversation.
The forum guidelines state that starter posts are public feed entries before anyone
can create one.
