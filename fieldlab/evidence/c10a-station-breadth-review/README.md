# C10a station-family breadth review — 2026-08-02

This closes the bounded **source and admission** review for vanilla station
components. It does not claim that a player manually clicked every station in
one physical run.

The repository's extractor-v2 tool was rerun against the installed pinned
`assembly_valheim.dll` (sha256
`3b26c8512778f6e0664b5af2a26f3c30993a00f584c1e76d9123a742b67e2004`). It
reproduced 19 routed, 21 direct, and 120 instance RPC names, 122 ZNetView-bearing
components, and zero unresolved registrations. The eight station registrants
below account for exactly 19 instance-RPC names:

- `Beehive.Awake`
- `CookingStation.Awake`
- `Fermenter.Awake`
- `Fireplace.Awake`
- `Incinerator.Awake`
- `SapCollector.Awake`
- `ShieldGenerator.Start`
- `Smelter.Awake`

Seven names were already exact P1 routes: `RPC_AddFuel`,
`RPC_AddFuelAmount`, `RPC_AddItem`, `RPC_AddOre`, `RPC_EmptyProcessed`,
`RPC_Extract`, and `RPC_RemoveDoneItem`.

Pinned-source review showed that the other 12 are also emitted during ordinary
play, so leaving them unadmitted would turn a valid station interaction into an
unadmitted-send poison failure after native fallback deletion. They are now
exact P2 instance routes shared by the mod and Gateway:

- owner mutation/request: `RPC_Attack`, `RPC_RequestIncinerate`,
  `RPC_SetFuel`, `RPC_SetFuelAmount`, `RPC_Tap`, `RPC_ToggleOn`;
- directed result: `RPC_IncinerateRespons`;
- presentation broadcast: `RPC_AnimateLever`,
  `RPC_AnimateLeverReturn`, `RPC_HitNow`, `RPC_SetSlotVisual`, and
  `RPC_UpdateEffects`.

Every row is bounded to the extracted zero-, integer-, float-, or string-bearing
payload and a complete target ZDO. None transfers ownership, admits an untyped
blob, creates a new multi-writer transaction, or introduces a method-name
collision. The source shape is therefore the already-proven reliable
target-ZDO route, not a new station-specific authority lane. Per the landscape's
reopen rule, no separate physical station gate was created: source showed no
distinct ownership/mutation shape, and no station poison trip was recorded.
The retained r4 physical composition already proves generic target-ZDO dispatch;
the selected r34 chest remains the physical container transaction canary.

`StationFamilies_AllExtractedRpcsHaveExactSharedRoutes` derives the complete
station set from `synthetic_baseline_v2.json`, compares all 19 names and payload
signatures to the shared catalog, and fails if a later pinned game assembly adds
an unclassified station registration. The mod suite passes 182/182. The
canonical .NET 9 non-performance solution passes 625/625 (17 companion, 126
contracts, 250 simulation, 232 Gateway). The mod Release build completes with
zero warnings and zero errors.

Machine-readable receipt: `verification-summary.json`.
