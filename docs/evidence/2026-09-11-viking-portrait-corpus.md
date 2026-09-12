# Evidence — Viking portrait corpus, catalog and categorization (2026-09-11)

Boundary artifact record for the portrait corpus the DMos image lane produced and the
catalog baseline built over it. Design record:
[`docs/design/valheim-portrait-picker-2026-09/`](../design/valheim-portrait-picker-2026-09/README.md).
Labels per PD-4: **VERIFIED** = measured on the files this session; **INFERRED** = derived
from receipts without an independent check.

## The corpus (input, never copied into a repo)

| | |
|---|---|
| path | `E:\omen\DMos\artifacts\corpus-viking-profiles-20260910\` |
| `receipts.ndjson` | sha256 `163320de32bbf5d6090041d22164fc902b4fd6c988693d07ba06785191174550` · 2,063,320 bytes · 1,375 lines |
| `assets/*.png` | 1,375 files · 1,983,495,147 bytes · every file's sha256 matches its receipt (VERIFIED) |
| dimensions | 1,373 decode as 1024×1024 RGB; 2 do not decode (VERIFIED) |
| corrupt pair | `viking_carpenter_m_veteran_s1`, `viking_miner_m_prospector_s1` — one blob, 1,655,768 bytes, sha256 `80f7986c68b23de2d200485573472006643a6a079848c7d810e244e4f81d946e`, both receipts 355 s (VERIFIED identical bytes; job collision INFERRED from the receipts) |
| render window | 2026-09-10T23:10:55Z → 2026-09-11T03:11:49Z · lanes `b70@bus4` 686, `b70@bus9` 689 · 18 steps · 26,272 GPU-seconds (INFERRED from `duration_seconds`) |
| `viking_gallery.html` | 2,405,233 bytes; the lane's own local viewer, embeds the receipts with `file://` paths; not used by the catalog |

## Outputs beside the corpus

| file | sha256 | bytes | produced by |
|---|---|---|---|
| `catalog.json` | `1102106f42a128cffa0cacb8759f77cb90ca17f0188c7b6877761a88c2953502` | 1,416,890 | `tools/portrait-corpus/build_catalog.py` |
| `face_qa.json` | `e042720465225a820228dc725ff291867a57075e50cb5d9a46303e15a2d40883` | 541,529 | `tools/portrait-corpus/face_qa.py` (opencv 4.14.0, mediapipe 0.10.14) |
| `attributes.json` | `7a5f4035cd4585bdba4ca488a70e85b1294691b937d013695ba6708e767942e9` | 45,451 | `tools/portrait-corpus/extract_attributes.py` ingest |
| `attributes-work/batch-{1..8}.{prompt.txt,result.json}` | — | — | the door's raw replies with `ok/backend/model/job_id` |
| `qa/contact-<concept>.jpg` × 96 | — | — | `tools/portrait-corpus/contact_sheets.py review` |

## Outputs in this repo

| file | sha256 | bytes |
|---|---|---|
| `docs/design/valheim-portrait-picker-2026-09/concepts.json` | `e05a373de1a521288312010592e9c9b2431fd062aeb95f7bbd2bfdbeac44b808` | 206,738 |
| `docs/design/valheim-portrait-picker-2026-09/picks.json` | `858499e90dbc9558be8464afe70133fd56a3d0cc316e618f7a1175abe91412f0` | 921 |
| `tools/portrait-corpus/vocab.json` | `ee788fd42a477245e963175704e45f5ea399f6d214f1aa0cda8af4f7d8c75e20` | 4,573 |
| `docs/design/valheim-portrait-picker-2026-09/contact-sheets/*.jpg` | six sheets, each ≤ 245,032 bytes | |

`concepts.json` carries `catalog_sha256` and the catalog carries `receipts_sha256`, so the
chain corpus → catalog → concepts is checkable from the repo alone.

## Counts (VERIFIED)

| | |
|---|---|
| concepts | 96 (24 roles × woman/man × 2 variants); themes builders 48 · trades 20 · warriors-mystics 12 · hunters-reavers 8 · lore-hearth 8 |
| takes per concept | 15 × 31 concepts, 14 × 65 |
| usable assets | 1,358 of 1,375 — rejects: `corrupt` 2, `bg_dropped` 7 (all seed `s5`/`s11`), `rejected_by_eye` 8 (`berserker_m_wolfskin`) |
| curated takes | 384 (4 per concept); 1 concept reviewed by eye (`picks.json`), 95 auto-ranked and awaiting the contact-sheet pass |
| face signals | 3-detector consensus: 862 assets with 3 votes, 353 with 2, 139 with 1, 19 with 0; `face_small` 75, `face_off_centre` 10 — advisory only |
| attribute extraction | 8 batches × 12 prompts through HEARTH `gcp-gemini` / `gemini-3.5-flash`, job ids `job_38835c8a…`, `job_b4d4a55f…`, `job_dbd682b9…`, `job_e16d2a55…`, `job_2f2534db…`, `job_f95901c2…`, `job_1df57588…`, `job_e29bb4b2…` (full ids in `attributes.json`); 96/96 rows, 0 off-vocabulary |
| tests | `python -m pytest tools/portrait-corpus/test_portrait_corpus.py -q` → 7 passed |

## What was tried and not kept

- A per-concept corner-luminance z-score as the background-defect gate: caught 1 of 7. Replaced
  by whole-frame near-white excess over the concept median (threshold 0.08), which caught all 7
  and nothing else (VERIFIED against the sheet `contact-sheets/defects-bg-dropped.jpg`).
- Haar, BlazeFace (both ranges), gemini-3.5-flash (15-up and 4-up sheets) and gemini-3.1-pro
  (4-up) as a face gate: each wrong on the wolfskin concept (README Finding 3). Kept as ranking
  signals only.
- Hair colour measured from the pixels beside the face box: agreed with the prompt on 24 of 67
  concepts. Discarded; the prompt classification with the beard-colour rule is the source.
- A "mojibake repair" for `Groa the Seið-Kona`: the receipt already holds U+00F0; the console
  was at fault. Removed.
