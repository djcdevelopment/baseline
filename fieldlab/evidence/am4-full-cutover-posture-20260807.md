# AM4 runs Lumberjacks. Full cutover is the at-rest posture. (2026-08-07)

The lab's default changed tonight, deliberately and permanently: **native is now
the rollback, not the home state.** No bounded windows, no restore ceremony at
the end of a run.

## The posture

| Surface | At-rest state |
|---|---|
| AM4 server | `lumberjacksCutoverMode = lumberjacks-primary`, `zdoRedirectEnabled = true`, **`zdoRedirectPrefabs = *`** (full suppression), window/manifest `am4-handshake-async-20260730`, r42 mod (`08bf698b…`) |
| OMEN client | wary.fool's personalized pack config installed as the live config (the designed installer flow — extracted from `Comfy-P7-Mods-waryfool-r42.zip`); consumer armed, credentialed, correct window |
| i5 client | durracktu's personalized pack config installed via the deploy lane's new `-ValheimConfig` switch (hash-verified `c32c1070…`), gateway URL at OMEN's tailnet address — no tunnel dependency |
| Gateway | r42 pair image on OMEN, `restart: unless-stopped`, enrollment store on the persistent volume |

Verified: `Test-CutoverModeCoherence -ExpectedMode lumberjacks-primary` returns
**coherent, zero failures**, with the gateway reporting `admitted: true` on the
manifest. The same check found four divergences this morning.

**Playing the lab now means playing on Lumberjacks.** Launch Valheim normally on
either machine — no harness, no arming, no flags. That is what cutover means.

## What this puts live (fix-forward, not rehearse-and-retreat)

With `*` suppression, buildings/structures now ride the lane too — the ADR 0013
building-sharing case is no longer a scheduled test, it is the next play
session. If the second player can't see structures, the built fan-out is the
lever: `zdoCoPresenceFanoutEnabled` (hot-reloadable, runtime-control
allowlisted). We fix it live; we do not fall back to native to avoid finding out.

## Rollback (incident response, not ritual)

- Server: `cfg.bak-native-final-20260807` beside the live cfg + container restart.
- Clients: `*.bak-precutover-20260807` beside each live cfg (i5's pre-cutover
  bytes also retained in tonight's harness run backups under
  `C:\deploy\baseline\fieldlab\runs\...`).

## What "100% cutover" still means beyond the lab

P7 running this same posture on its credentialed public plane: promote
`m7-c10b-20260807-r42` with `-Execute`, restore P7's armed config, candidate 12,
and the human mod-zip→visible-world gate. Every artifact that window needs
exists and is rehearsed. The lab no longer waits for it.
