# Gunslinger grit implementation audit

## Scope and evidence

This audit compares the class design in [README.md](README.md) with the actual
spells, statuses, passives, progression tables, resource definitions, and
localization. It covers all eight selected grit abilities, the four automatic
Desperado features, grit acquisition/recovery, and the related Marksman actions.

**Important:** "implemented" below means authored and regression-tested, not
tested in a running BG3 game. Native interrupt ordering, item-stat recalculation,
multi-target attack timing, and reaction UI still require the acceptance checks
at the end. In particular, Last Word and suppression of existing blindness must
not be treated as certified full parity yet.

BG3 Script Extender is now **required**, with the declared minimum version 20.
It is not a PAK dependency with a fabricated module UUID: the requirement is
declared in [Config.json](GunslingerClass/Mods/GunslingerClass/ScriptExtender/Config.json)
and documented in the README.

## Ability comparison

| Ability | Previous implementation | README contract | Implementation after this audit |
|---|---|---|---|
| Merciless Shot | Action + 2 grit applied a flat +1d8 buff; firing still needed another attack. | Action attack; spend 1-3 grit, adding half a weapon attack per point. | Linked 1/2/3-grit weapon attacks, costing one action and one bullet. Native weapon damage multipliers are 1.5/2/2.5. No preparatory buff/action. |
| Line 'em Up | Action + 2 grit; fixed 2d6 piercing, half on save; could target allies. | Half firearm damage to enemies in a 20-foot line; half again on a Dexterity save, DC 8 + Dex modifier + proficiency. | Enemy-only 6-metre line; `MainRangedWeapon/2`, or `/4` on save, using the weapon damage type and specified DC. Server wiring requires and consumes one primary-gun bullet. |
| Rapid Shot | Bonus action + 1 grit unlocked vanilla Piercing Shot instead of firing. | One-grit bonus-action shot. | Direct firearm weapon attack with bonus action + 1 grit + 1 appropriate bullet. |
| Bite the Bullet | Fixed 2 grit, temporary HP = 2 x proficiency. | Bonus action; spend 1-3 grit; temporary HP = spent grit x proficiency. | Three spend choices; native TemporaryHP statuses with 1/2/3 x proficiency and the shared TEMPORARY_HP stack. No invented HP functor. |
| Shot in the Dark | A DARKVISION tag did not grant an actual vision distance. | Bonus action + 1 grit; 60-foot darkvision and ignore blindness for one shot. | Native `DarkvisionRangeMin(18)` and blindness-group immunity, removed on attack. Suppression of an already-active Blind status remains an explicit engine test/gap. |
| Rapid Repair | Bonus action + 1 grit; fixed DC 12; removed a character-wide misfire. | One grit; Sleight of Hand DC 12 + rarity; repair the gun, not all equipped guns. | Primary/secondary options, each gated to the physical gun's repairable state and DC 12-16. Success clears only that gun's ordinary misfire. Native checks retain proficiency/expertise handling. Failed rolls retain the misfire and spend the costs. Existing bonus-action timing is preserved because the README did not specify another timing. |
| Tinkerer | Bonus action + 1 grit; character-wide +1d4 rather than a choice. | One modification per physical gun until long rest: capacity +2; specified replacement dice; or specified range bonus. Hands independent; replacement, not stacking. | Six hand/mode choices. Persistent item-keyed state drives capacity boosts, item damage-die statuses, and item range. Flintlock/Blunderbuss/Musket damage becomes 1d10/2d6/3d4; range increases by 6/3/12 metres. Changing capacity does not create bullets. |
| Fanning Fire | Action + 2 grit; -2 attack buff refunded one normal action, not a volley. | Action + 1-3 grit; 2-4 shots at -1/-2/-3, selecting up to 1 + grit enemies. | 2/3/4 projectile selections and matching bullet/grit costs. Native penalties are applied before the volley and cleaned on completion/cancellation. No action refund. Repeated-target selection and multi-roll timing require game tests. |
| Desperado's Luck | Free static +1d4 firearm bonus; not a paid post-miss decision. | Once/turn after a miss: pay 1 grit for +1d4; no Reaction. | Native OnPostRoll decision, `AdjustRoll(1d4)`, grit cost 1 and a turn-reset marker. Offers only potentially useful roll adjustments. Natural-1/critical handling needs a game check. |
| Double Load | One-grit +1d8 preparatory buff; later shot used one bullet; "broken" only imposed disadvantage. | One grit + two bullets; 1.5x damage; natural 1 destroys the physical gun until long rest, not field-repairable. | Direct action attack, one grit, two bullets, 1.5x weapon damage. Its critical-miss passive records destruction against that gun. Hand-specific locks prevent gun attacks; repair choices exclude destroyed guns. |
| Close Call | Manually activated Reaction + 1 grit, granting +2 AC without a counterattack. | Reaction + 1 grit; +2 AC for the triggering attack; counterattack if it misses. | Native post-roll prompt subtracts 2 from the incoming roll, equivalent to +2 AC for that attack. Resolution conditionally fires a usable loaded primary gun on a miss, and clears its marker on either result. Counterattack spends one bullet but not a second action/reaction. |
| Last Word | Manually activated Death Ward + cooldown; no lethal prompt or counter. | Lethal-damage interrupt, 3 grit, once/long rest; Death Ward leaves 1 HP, then a firearm counterattack. | Native OnPreDamage lethal predicate applies Death Ward, cooldown, and a pending marker. Server AttackedBy handling correlates the story action and requests the shot after incoming damage, rather than before survival or on unrelated damage. Prompt availability, damage-event ordering, and actual 1-HP survival are not engine-verified. |

Grit attack choices currently use the primary firearm. Independent secondary
choices exist for Tinkerer and Rapid Repair, and the normal secondary shooting
action retains its separate ammunition pool.

## Progression and grit recovery

The progression data already matched the design; it was not changed to mask an
ability defect:

- All subclasses: two selected abilities and three maximum grit at level 3.
- Marksman/Arcane Gunsman: one additional choice at 5/9/13/17; maximum increases
  at 7/11/15/19, reaching seven.
- Desperado: one additional choice at 5/8/11/14/17/20; maximum increases at
  6/9/12/15/18, reaching eight.
- Tinkerer is absent from the level-3 pool and enters at level 5; Fanning Fire
  enters the level-7 pool. Selection opportunities still follow each subclass's
  schedule, so not every subclass can newly select Fanning Fire at level 7.
- Grit Adept gives +2 maximum grit and a level-3-pool choice.
- Desperado's Luck/Double Load/Close Call/Last Word are automatic subclass
  features at 3/5/8/11, in addition to selected base abilities.
- `GSL_GritRecovery` uses native firearm-hit/critical/killing-blow conditions to
  restore one grit. A hit that is both critical and lethal satisfies one OR
  condition, not two independent recovery branches.
- The resource replenishes on long rest. Recovery at maximum, damage riders,
  and multiple kills in a volley still need engine checks.

See [Progressions.lsx](GunslingerClass/Public/GunslingerClass/Progressions/Progressions.lsx),
[PassiveLists.lsx](GunslingerClass/Public/GunslingerClass/Lists/PassiveLists.lsx),
and [ActionResourceDefinitions.lsx](GunslingerClass/Public/GunslingerClass/ActionResourceDefinitions/ActionResourceDefinitions.lsx).

## Related Marksman actions

- **Stable Shot:** action + 6 metres of movement to grant Advantage on the next
  firearm attack. No grit cost. The movement is spent on activation, not removed
  permanently when the feature is learned. This is consistent with the design's
  class-action interpretation.
- **Headshot:** spends five grit to apply a one-shot native always-critical
  boost. The following firearm attack still pays its ordinary action/ammo costs.
  Natural-1 interaction and consuming the status with a different attack need
  an engine check.
- Lock-on targeting, Long Shot distance bands, Pinpoint Accuracy, and unrelated
  feat/Arcane Gunsman approximations are not expanded by this grit update.

## Physical-gun state and ammunition

[BootstrapServer.lua](GunslingerClass/Mods/GunslingerClass/ScriptExtender/Lua/BootstrapServer.lua)
stores persistent state keyed by physical item, not by shared weapon stat entry.
[GritRules.lua](GunslingerClass/Mods/GunslingerClass/ScriptExtender/Lua/GritRules.lua)
contains the capacity, rarity, modification/replacement, repair/destruction, and
long-rest rules.

The runtime:

1. Tracks equipped primary/secondary firearms using Osiris's actual slot names,
   `Ranged Main Weapon` and `Ranged Offhand Weapon`.
2. Snapshots ammunition on cast completion and before unequipping.
3. Restores item-specific ammunition when a gun is equipped/transferred, without
   filling newly added capacity for free.
4. Applies replacement damage dice to the item itself; range mutations are
   replicated to clients.
5. Uses a 19.5-metre secondary Flintlock spell/override for the range upgrade.
   This avoids vanilla offhand spells' use of the **main-hand** range scalar.
   The extended secondary spell is also explicitly unlocked.
6. Exposes only the correct hand/rarity Rapid Repair options, excluding broken
   guns. Native rarity codes differ from design bonuses: Common/Unique map to
   +0, Uncommon/Rare/Epic/Legendary to +1/+2/+3/+4. Unsupported higher rarity
   codes raise an explicit error rather than silently using DC 12.
7. Adds firearm-conditional costs/readiness locks to native ranged-weapon
   attack spells, preserving their existing effects and ordinary bow costs.
8. Clears modifications, ordinary misfires, and destruction on long rest,
   including tracked unequipped guns when their entities are available.

These hooks recognize this mod's three firearm root templates; arbitrary
third-party firearms and hypothetical fused weapon templates are not silently
treated as supported Gunslinger guns.

**Capacity constraints are intentional:** Double Load needs two loaded bullets,
so a base one-shot Musket cannot use it without a capacity upgrade. Fanning Fire
requires 2/3/4 bullets up front. A capacity-modified Musket holds three, so its
four-shot option remains unavailable. No free reload is inserted into a volley.

## Implementation references

- [GunslingerSpells.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerSpells.txt):
  entry-point menus, line attack, existing Marksman actions, basic shots/reloads.
- [GunslingerGritSpells.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerGritSpells.txt):
  spend tiers, direct weapon attacks, per-hand repair/modification choices,
  reaction shot, extended secondary shot.
- [GunslingerInterrupts.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerInterrupts.txt):
  Luck, Close Call and its resolution, Last Word.
- [GunslingerGritStatuses.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerGritStatuses.txt):
  variable temporary HP, volley penalties, cooldowns, hand locks and repair
  eligibility, item damage replacements.
- [GunslingerPassives.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerPassives.txt):
  ability unlocks, recovery and critical-miss notifications.
- [English localization](GunslingerClass/Localization/English/GunslingerClass.xml):
  spend-tier, hand-choice and corrected ability descriptions.

New grit choices reuse existing icon keys and add no artwork-catalog entries. The packaging script copies the extender configuration and Lua alongside
the mod metadata; Lua needs no Divine conversion.

API grounding used Norbyte's [Script Extender API](https://github.com/Norbyte/bg3se/blob/main/Docs/API.md)
and component definitions, working Osiris slot/event examples in existing mods,
and cached vanilla Bardic Inspiration/Bend Luck, Shield, Riposte, Shillelagh,
resource-spending, and multi-projectile stat patterns. This supports the authored
mechanisms; it does not replace observing them in this game's engine.

## Validation and required game checks

Automated coverage includes [grit stat tests](tests/test_grit_data.py),
[Lua rule tests](tests/test_grit_rules.lua), and
[mocked server lifecycle tests](tests/test_grit_runtime.lua), plus the existing
spell, icon, XML, localization, and staging suites. Mocks verify adapter logic,
not actual engine event timing, stat recalculation, or combat UI.

Validation completed for this update:

- 51 Python regression tests passed.
- Both Lua rule and mocked runtime suites passed.
- XML/layout/localization checks passed for 23 XML files; local stats/reference
  validation passed for 82 custom spells.
- Editor diagnostics reported no errors in the changed Python files.
- Divine converted the localization and resource banks, rebuilt both PAKs,
  and verified every staged file against each package's file list. The main
  package includes the extender configuration and Lua runtime.

Before treating the new build as gameplay-certified:

1. Confirm Script Extender loads the server bootstrap without errors. For an
   older save, take a long rest before comparing old buff/status behavior.
2. Check selection counts and grit maxima for all subclass schedules and Grit
   Adept; verify crit/kill recovery never exceeds the maximum.
3. For each gun, verify exact action/grit/bullet costs and damage on every
   Merciless, Rapid, Double Load, and Fanning tier. Confirm Fanning allows
   repeated target selections as intended and each attack has the correct
   penalty; then fire a normal shot to check cleanup.
4. Check Line 'em Up length, enemy-only targeting, save DC, half/quarter damage,
   and single-bullet consumption.
5. Check all Bite tiers at different proficiency bonuses and with existing temp
   HP. Test Shot in the Dark while already Blinded and while in magical darkness;
   verify it does not permanently cure a pre-existing blindness effect.
6. Modify two physical Flintlocks independently; replace each modification;
   reload after capacity upgrade; swap hands, unequip, transfer between
   characters, save/load, and long rest. Verify dice and range tooltips and
   actual hit targeting, including the default secondary attack override.
7. Force an ordinary natural 1 and a Double Load natural 1. Confirm only the
   offending gun is disabled, no inherited special attack bypasses its lock,
   Rapid Repair uses the correct hand/DC, and destruction survives transfers
   and cannot be field-repaired.
8. Check Luck asks only after a potentially recoverable firearm miss, spends
   one grit/no Reaction, and resets at the intended turn boundary.
9. Check Close Call against single/multi-attack casts: exactly one incoming
   attack receives the adjustment, only a miss causes the counter, one bullet
   is spent, no extra Reaction is charged, and no marker leaks to a later attack.
   Verify counterattack range/line of sight as well.
10. Check Last Word against lethal weapon/spell/environmental damage, multiple
    damage packets, existing Death Ward, and an empty/broken gun. It must leave
    exactly 1 HP, counter only after survival when a valid loaded gun/attacker
    exists, spend three grit only once, and reset only on long rest.

The separate ordinary DC 10 + rarity repair action and weapon-fusion kits remain
known non-grit implementation gaps. The original class design is not rewritten
to claim those features now work.
