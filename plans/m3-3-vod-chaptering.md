# M3-3 — VOD Chaptering Pipeline

## Objective
Turn stream VODs of white-glove sessions into a searchable training library:
timestamped chapters + a short summary per session, so onboarding material
accumulates for free from work already being done.

## Context
Sessions cover integration, training, and demos ("config signing setup",
"quest hookup", "first event captured"). Summarization is a designated offload
lane: use `mcp__hearth__local_generate` with `backend="gcp-gemini"` for drafts;
the builder edits, never ships raw model output. Transcripts may need to be
fetched/generated first — auto-captions are acceptable input.

## Steps
1. Create `docs/training-library/README.md`: index table — date, GM/topic,
   VOD link, chapter list, one-line summary.
2. Define the per-session file format
   `docs/training-library/{yyyy-mm-dd}-{topic}.md`: chapter timestamps with
   plain-language titles (player vocabulary, not internals), a 3–5 sentence
   summary, and "referenced docs" links (data-trust note, workbooks, cards).
3. Build the offload recipe: `recipes/vod-chapters.md` documenting the exact
   prompt shape for gcp-gemini (input: transcript chunk + instruction to emit
   timestamped chapters + summary; the brief must stand alone — the model has
   no conversation context). Include the ok/text/backend metadata check rule.
4. Process whatever transcripts are currently available (even one proves the
   pipeline). If none are retrievable, process a placeholder transcript and
   mark the entry `pipeline-proof`.

## Acceptance
- Index + format + recipe exist; at least one real or proof entry processed
  end-to-end through the offload lane.
- Chapter titles are understandable by a GM with no codebase knowledge.

## Out of scope
Video hosting/editing; automatic transcript fetching on a schedule.
