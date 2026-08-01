# Annotation review queue

Every field description the drafting model flagged low-confidence with `(?)`.
To clear a row: verify (or fix) the description in the matching
`tools/component-packets/samples/annotations-*.json` file and delete its `(?)`,
then re-run `python make_review_queue.py` and re-assemble the dictionaries.

## `annotations-humanoid.json` — 34 rows

- [ ] `Character.m_nViewOverride` — Overrides the default ZNetView component for networking.
- [ ] `Character.m_onDamaged` — Callback triggered whenever the character takes damage.
- [ ] `Character.m_onDeath` — Callback triggered when the character dies.
- [ ] `Character.m_onLevelSet` — Callback triggered when the character's star level changes.
- [ ] `Character.m_onLand` — Callback triggered when the character lands on the ground.
- [ ] `Character.m_group` — Group identifier used for faction and AI social behaviors.
- [ ] `Character.m_dontHideBossHud` — Prevents the boss health bar from hiding when far away.
- [ ] `Character.m_bossEvent` — The raid event associated with this boss character.
- [ ] `Character.m_aiSkipTarget` — If true, AI enemies will ignore this character.
- [ ] `Character.m_flying` — Determines if the character is currently flying.
- [ ] `Character.m_disableWhileSleeping` — Disables updates or AI routines while character is sleeping.
- [ ] `Character.m_pheromoneLoveEffect` — Effects played when tamed or in love.
- [ ] `Character.m_useAltStatusEffectScaling` — Enables alternative scaling calculations for status effects.
- [ ] `Character.m_tolerateFire` — If true, prevents damage from fire.
- [ ] `Character.m_tolerateTar` — If true, character is immune to tar slow.
- [ ] `Character.m_regenAllHPTime` — Time in seconds to regenerate full health.
- [ ] `Character.m_weakSpots` — Sub-objects where attacks deal extra damage.
- [ ] `Character.m_staggerDamageFactor` — Percentage of max health needed in one hit to stagger.
- [ ] `Character.m_enemyAdrenalineMultiplier` — Multiplies stats when enemies are nearby.
- [ ] `Character.m_heatBuildupBase` — Base rate of heat accumulation.
- [ ] `Character.m_heatCooldownBase` — Base rate of heat dissipation.
- [ ] `Character.m_heatBuildupWater` — Heat buildup rate while in water.
- [ ] `Character.m_heatWaterTouchMultiplier` — Heat cooldown multiplier when touching water.
- [ ] `Character.m_lavaDamageTickInterval` — Time between damage ticks when in lava.
- [ ] `Character.m_heatLevelFirstDamageThreshold` — Heat level threshold before damage begins.
- [ ] `Character.m_lavaFirstDamage` — Initial damage taken upon entering lava.
- [ ] `Character.m_lavaFullDamage` — Continuous damage taken when deep in lava.
- [ ] `Character.m_lavaAirDamageHeight` — Height limit above lava where heat damage still occurs.
- [ ] `Character.m_dayHeatGainRunning` — Heat accumulation rate while running in daytime.
- [ ] `Character.m_dayHeatGainStill` — Heat accumulation rate while standing in daytime.
- [ ] `Character.m_dayHeatEquipmentStop` — How much equipped gear blocks heat buildup.
- [ ] `Character.m_lavaSlowMax` — Maximum movement slow applied by lava.
- [ ] `Character.m_lavaSlowHeight` — Lava depth required to apply maximum slow.
- [ ] `Character.m_lavaHeatEffects` — Effects played when suffering heat damage from lava.

## `annotations-monsterai.json` — 5 rows

- [ ] `MonsterAI.m_fleePheromoneMin` — Minimum value for the pheromone system used during fleeing behavior
- [ ] `MonsterAI.m_fleePheromoneMax` — Maximum value for the pheromone system used during fleeing behavior
- [ ] `MonsterAI.m_privateAreaTriggerTreshold` — Number of private area triggers before the monster becomes hostile
- [ ] `BaseAI.m_takeoffTime` — How long the takeoff sequence takes before the creature is considered airborne.
- [ ] `BaseAI.m_flyAbsMinAltitude` — The absolute minimum altitude above sea level the creature must maintain.

## `annotations-piece.json` — 22 rows

- [ ] `Piece.m_targetNonPlayerBuilt` — Allows enemies to target this piece even if not player-built.
- [ ] `Piece.m_comfortObject` — The specific child object that defines the source of comfort.
- [ ] `Piece.m_allowAltGroundPlacement` — Allows placing the piece on imperfect or uneven ground.
- [ ] `Piece.m_onlyInTeleportArea` — Allows placing this piece only inside active teleport areas.
- [ ] `Piece.m_repairPiece` — If true, this piece represents the hammer's repair action.
- [ ] `Piece.m_removePiece` — If true, this piece represents the hammer's deconstruct action.
- [ ] `Piece.m_canRockJade` — Enables rocking or swaying physics behavior for the piece.
- [ ] `Piece.m_allowRotatedOverlap` — Allows the piece to overlap others when rotated.
- [ ] `Piece.m_vegetationGroundOnly` — Restricts placement to ground covered by vegetation.
- [ ] `Piece.m_mustConnectTo` — The target network object this piece must connect to.
- [ ] `Piece.m_noVines` — Prevents decorative vines from growing on this piece.
- [ ] `Piece.m_harvest` — Enables harvesting interactions on this piece.
- [ ] `Piece.m_harvestRadius` — The interaction radius for harvesting this piece.
- [ ] `Piece.m_harvestRadiusMaxLevel` — The maximum harvest radius at highest upgrade level.
- [ ] `WearNTear.m_ashDamageImmune` — Makes this piece immune to Ashlands environmental fire damage.
- [ ] `WearNTear.m_ashDamageResist` — Gives this piece resistance to Ashlands environmental damage.
- [ ] `WearNTear.m_comOffset` — Offset for the center of mass calculation.
- [ ] `WearNTear.m_forceCorrectCOMCalculation` — Forces high-precision center of mass calculations.
- [ ] `WearNTear.m_staticPosition` — Prevents physics forces from moving this object.
- [ ] `WearNTear.m_nonSolidRenderers` — Renderers that do not affect physical collisions.
- [ ] `WearNTear.m_triggerPrivateArea` — Triggers ward alerts if this piece is damaged inside one.
- [ ] `WearNTear.m_switchEffect` — Effects played when switching between wear states.

**61 rows pending.** Everything not listed here was drafted
without a flag — spot-check, but the flagged rows are the priority.
