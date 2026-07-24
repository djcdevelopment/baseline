# m7-e04-native-candidate-capture / native-candidate-v1

- Run: `fixture-normalizer-smoke`
- Driver: `replay`
- Classification: `supported`

## Native normalization

- Candidate events: `2`
- Raw evidence: `normalized-input.json`, `raw/native-source.jsonl`, `raw/events.jsonl`, `raw/anomalies.jsonl`, `raw/ignored.jsonl`, `raw/normalized-decisions.json`

## Invariants

- PASS `native_source_readable`: read 4 source line(s)
- PASS `native_candidate_rows_normalized`: normalized 2 candidate row(s)
- PASS `native_rows_not_silently_dropped`: ignored=2; malformed=0; raw source and sidecars retained
- PASS `native_source_is_malformed_free`: malformed=0
