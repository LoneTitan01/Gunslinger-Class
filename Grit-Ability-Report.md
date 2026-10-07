# Gunslinger grit implementation audit

## Scope and evidence

This audit compares the class design in [README.md](README.md) with the actual
spells, statuses, passives, progression tables, resource definitions, and
localization. It covers all eight base grit abilities, the four Desperado-only
grit abilities, grit acquisition/recovery, and the related Marksman actions.

**Important:** "implemented" below means authored and regression-tested, not
tested in a running BG3 game. Native interrupt ordering, item-stat recalculation,
multi-target attack timing, and reaction UI still require the acceptance checks
at the end. In particular, Last Word and suppression of existing blindness must
not be treated as certified full parity yet.

BG3 Script Extender is now **required**, with the declared minimum version 29 for the Fortune chooser's read-only native row wrapper.
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
| Rapid Repair | Bonus action + 1 grit; fixed DC 12; removed a character-wide misfire. | One grit; Sleight of Hand DC 12 + rarity; repair the gun, not all equipped guns. | Primary/secondary options, each gated to the physical gun's repairable state and DC 12-16. Success clears only that gun's ordinary misfire (a -2 ranged to-hit penalty that no longer blocks firing; a second misfire before repair breaks the gun until long rest). Native checks retain proficiency/expertise handling. Failed rolls retain the misfire and spend the costs. Existing bonus-action timing is preserved because the README did not specify another timing. |
| Fanning Fire | Action + 2 grit; -2 attack buff refunded one normal action, not a volley. | Action + 1-3 grit; 2-4 shots at -2/-3/-4, selecting up to 1 + grit enemies. | 2/3/4 projectile selections and matching bullet/grit costs. Native penalties are applied before the volley and cleaned on completion/cancellation. No action refund. Repeated-target selection and multi-roll timing require game tests. |
| Desperado's Luck | Free static +1d4 firearm bonus; not a paid post-miss decision. | Once/turn after a miss: pay 1 grit for +1d4; no Reaction. | Native OnPostRoll decision, `AdjustRoll(1d4)`, grit cost 1 and a turn-reset marker. Offers only potentially useful roll adjustments. Natural-1/critical handling needs a game check. |
| Double Load | One-grit +1d8 preparatory buff; later shot used one bullet; "broken" only imposed disadvantage. | One grit + two bullets; 1.5x damage; natural 1 destroys the physical gun until long rest, not field-repairable. | Direct action attack, one grit, two bullets, 1.5x weapon damage. Its critical-miss passive records destruction against that gun. Hand-specific locks prevent gun attacks; repair choices exclude destroyed guns. |
| Close Call | Manually activated Reaction + 1 grit, granting +2 AC without a counterattack. | Reaction + 1 grit; +2 AC for the triggering attack; counterattack if it misses. | Native post-roll prompt subtracts 2 from the incoming roll, equivalent to +2 AC for that attack. Resolution conditionally fires a usable loaded primary gun on a miss, and clears its marker on either result. Counterattack spends one bullet but not a second action/reaction. |
| Last Word | Manually activated Death Ward + cooldown; no lethal prompt or counter. | Lethal-damage interrupt, 3 grit, once/long rest; Death Ward leaves 1 HP, then a firearm counterattack. | Native OnPreDamage lethal predicate applies Death Ward, cooldown, and a pending marker. Server AttackedBy handling correlates the story action and requests the shot after incoming damage, rather than before survival or on unrelated damage. Prompt availability, damage-event ordering, and actual 1-HP survival are not engine-verified. |

Grit attack choices currently use the primary firearm. Independent secondary
choices exist for Tinkerer and Rapid Repair, and the normal secondary shooting
action retains its separate ammunition pool.

### Expanded abilities (suggestion list)

| Ability | Unlock | Implementation | Approximation / open question |
|---|---|---|---|
| Trick Shot (Disarming / Winging / Forceful / Bullying Shot) | 3 | One class-action group of four action firearm attacks, each costing 1 grit and a bullet; on hit Str save Disarm / Con save Prone / Str save 4.5 m push / Wis save Frightened 1 turn. | Save DCs are 8 + proficiency + Dexterity modifier. |
| Quickload | 3 | Bonus action, 1 grit; refills every wielded gun's loaded ammunition. | - |
| Flash Powder | 3 | Action, 1 grit; 1.5 m radius Con save or Blinded 1 turn. | - |
| Violent Shot | 9 | Linked 1/2/3-grit attacks usable with any main-hand firearm, adding 1d8/2d6/3d4 per grit by gun. | Server rolls d20 after the cast; d20 <= tier misfires the gun through the normal Misfired/broken path. |
| Stunning Shot | 9 | 2 grit attack; Con save or Stunned 1 turn. | - |
| Piercing Round | 9 | 2 grit, 1 bullet; 18 m line, one attack roll per creature. | Attack roll per target instead of a save. |
| Hair Trigger | 9 | Native interrupt, Reaction + 1 grit, when an enemy within 9 m attacks an ally. | Ally-attack trigger ordering needs a game check. |
| Grit and Steel | 13 | Native failed-save reroll interrupt, 2 grit, once per short rest. | - |
| Bullet Time | 17 | 4 grit, extra action, once per short rest. | - |
| Hail of Lead | 17 | Action, 5 grit, 1 bullet; weapon attack on every enemy within 18 m; once per long rest. | - |
| Final Judgement | 17 | 4 grit attack; below 25% HP after the hit, repeat weapon damage plus Con save or die. | - |
| Ante Up | D3 | Bonus action, 1 grit; Advantage on the next firearm attack; on a miss, attackers gain Advantage. | - |
| Lucky Draw | D3 | 1 grit; reroll 1s and 2s on firearm damage dice this turn. | - |
| Two-Gun Tango | D3 | Bonus action, 1 grit, off-hand bullet; off-hand shot adds Dex to damage. | Spends off-hand ammunition. |
| Roll the Bones | D7 | Bonus action, 1 grit; server d6 picks Bust/Hit/Jackpot status for 12 s. | Bust is -1d4 to hit, not lost grit. Jackpot restores 1 grit. |
| Duck and Weave | D7 | Reaction + 1 grit when a ranged attack would damage you: physical resistance, Disengage, +3 m. | Physical `SetDamageResistance` has no vanilla precedent. |
| Cheat Death's Odds | D7 | Passive. Below half HP, grit abilities costing 2+ refund 1 grit. | Refund rather than discount. Lua handles casts; costly interrupts refund via their own functors. |
| Hot Hand | D7 | Once-per-turn native `OnCastHit` interrupt, 2 grit and no Reaction cost, on your own firearm hit: next firearm attack crits on 18-20. | Independent used marker resets on turn; consuming the buff does not refresh the ability. Cheat Death's Odds refunds through the interrupt functor. |
| Double or Nothing | D11 | Once per turn, 2 grit; on a server d20 result of 11+, makes a free firearm attack against the original target; otherwise the gun misfires. | Independent used marker resets on turn, even after a failed roll. The additional attack has its own attack roll and spends one bullet, but no action, grit, or Reaction. |
| Quick on the Draw | D11 | Native interrupt, Reaction + 2 grit, when an enemy within 9 m attacks. Cancels the attack (`Counterspell()`), refunds it to the attacker, then shoots. | Triggers on an attack, not on initiative. |
| Ricochet Shot | D11 | Action, 3 grit and 1 bullet; weapon attack chains from the first enemy to up to three more, dealing half damage on each ricochet. | Follows the vanilla Arrow of Ricochet projectile chain. |
| Dead Man's Hand | D15 | Below 25% HP, 3 grit: next firearm hit this turn is a crit. | No two-gun attack. |
| Desperado's Fortune | D15 | If Desperado's Luck is known, it upgrades automatically after completing level 15 and replaces Luck with the highlighted Fortune class feature; shows as taken in level-15+ pools only while that feature is owned; once per turn, 1 grit: +1d8 after a missed firearm attack or failed saving throw. | No grit selection or cost for the upgrade. Without Luck, Fortune is an untaken grit selection. Respec rebuilds the conditional upgrade; the Luck interrupt is suppressed while Fortune or High Noon is active. |
| High Noon | D18 | Bonus action, 5 grit, 3 turns: +20 to hit and crit on 17-20 against the target; firearm attacks deal +1d8 damage. Once per long rest. | `RollBonus(Attack,20)` approximates "only a natural 1 misses". |


"D" marks Desperado-only unlock levels.

## Progression and grit recovery

The progression data already matched the design; it was not changed to mask an
ability defect:

- All subclasses: two selected abilities and three maximum grit at level 3. The
  level 3 pick is on each subclass's level 3 row, so it follows subclass choice.
- Marksman and Arcane Gunsman: one additional choice at 5/9/13/17 from the
  shared pools. Their maximum increases at 7/11/15/18, reaching seven.
- Desperado: an extra subclass choice at 7/11/15/18, so it picks a grit ability
  every other level from 3 to 18; maximum increases at 6/9/12/15/18, reaching
  eight. The Desperado uses merged shared and subclass-specific pools at
  3/5/7/9/11/13/15/17/18, including Desperado abilities available at the time.
- Tinkerer is no longer in any grit pool (it's a level 4 class feature). Fanning Fire
  is in the level 7+ pools, so it's first offered at level 7 (Desperado) or 9
  (Marksman/Arcane Gunsman).
- Grit Adept gives +2 maximum grit and a level-3-pool choice.
- There are no optional grit-ability replacement choices on level-up.
- Shared pools add new abilities at 3/9/13/17. Desperado-only pools add Luck
  plus three new abilities at 3; Double Load, Close Call plus four more at 7;
  Last Word plus two at 11; Dead Man's Hand at 15 (Fortune upgrades Luck
  automatically if known); and High Noon at 18. These remain
  selectable unlock choices.
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
  entry-point menus, line attack, existing Marksman actions, basic shots/reloads,
  spend tiers, direct weapon attacks, per-hand repair/modification choices,
  reaction shot, extended secondary shot.
- [GunslingerInterrupts.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerInterrupts.txt):
  Luck, Close Call and its resolution, Last Word.
- [GunslingerStatuses.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerStatuses.txt):
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

- 75 Python regression tests passed.
- Both Lua rule and mocked runtime suites passed, including the new gamble
  rolls, Violent Shot misfires, Roll the Bones and Cheat Death refunds.
- XML/layout/localization checks passed for 23 XML files; local stats/reference
  validation passed for 157 custom spells.
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
11. Check each new save-on-hit shot (Disarming, Winging, Forceful, Bullying,
    Dazing) applies only on a hit, and that Quickload refills both hands.
12. Violent Shot and Double or Nothing: confirm the server roll misfires the
    correct gun, a second misfire breaks it, the Double or Nothing success
    attacks the original target with its own roll, and the damage tiers match
    tooltips.
13. Hair Trigger, Duck and Weave, Quick on the Draw and Grit and Steel: verify
    the prompts appear on the intended trigger, spend one Reaction/grit cost,
    and Duck and Weave's physical resistance actually reduces the hit.
14. Roll the Bones: all three results appear over repeated casts, statuses
    clear after the next attack, and Jackpot never exceeds maximum grit.
15. Cheat Death's Odds: refunds once for 2+ grit casts and interrupts while
    below half HP, and never for 1-grit abilities or above half HP.
16. Piercing Round and Hail of Lead: check targeting, per-shot rolls, and
    ammunition spent.
17. Final Judgement, Dead Man's Hand and High Noon: check HP
    thresholds, guaranteed/expanded crits, and
    that Desperado's Luck is hidden while Fortune or High Noon is active.

Ordinary field repair is separate from the grit ability: while a firearm is
misfired, its owner can spend an action on a Sleight of Hand check at DC 10 +
rarity. Success clears only that gun's misfire; failure spends the action but
leaves the misfire in place. Destroyed guns remain unrepairable until a long
rest. Weapon-fusion kits remain a known non-grit implementation gap.
