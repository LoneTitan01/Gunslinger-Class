# In-Game Testing Checklist

Features that pass the local data tests (`python -B -m unittest discover -s tests`, the Lua tests and `validate_xml.py`) but still need to be checked in Baldur's Gate 3. Rebuild with `python stage_packages.py --divine` before testing.

Mark each item `[x]` when it works, or add a note under it describing what went wrong.

## High-risk items

These rely on engine behaviour that the local tests can't confirm.

- [x] **Nat-1 misfire:** a natural 1 on a basic firearm shot counts as a critical miss and misfires the gun (-2 to its attack rolls). A second natural 1 with that gun breaks it. The Misfire passive should now be visible in the firearm's tooltip, and a misfired or destroyed gun should show a Misfired / Broken status on the weapon itself. *Retest: the 100% hit chance was the nautiloid tutorial (vanilla, unchanged). Misfires silently failed on every magical firearm because the script only recognised the four base firearm templates; it now maps every firearm template from the weapon stats.*
- [x] **Nat-1 misfire on grit shots:** same check with a grit shot such as Disarming Shot or Rapid Shot.
- [x] **Projectile grit sounds:** grit shots (Merciless, Rapid, Disarming, Winging, Forceful, Bullying, Dazing, Violent, Fanning Fire, Double Load, Final Judgement, Double or Nothing, All In) play the firing weapon's gunshot sound, not silence or a maneuver sound. Check Flintlock, Blunderbuss and Musket.
- [x] **Immersive Firearms gun sounds:** basic shots, grit shots and Scattershot play IF's flintlock/musket shot (Flintlock, off-hand Flintlock, Musket) or blunderbuss blast (Blunderbuss). Each shot should play the sound once, in time with the shot, with no doubled or missing sounds. Non-shot abilities (reloads, Lock-on, Flash Powder) should not play a gunshot.
- [x] **Infused Rounds damage:** the extra element damage (`CharacterWeaponDamage` in a status) shows on firearm hits in the combat log, and doesn't apply to melee or non-firearm attacks.
- [ ] **Spellshot Adept:** after casting a spell, the next firearm hit deals the extra 1d4 Force. The status may be removed `OnAttack` before the damage is added; if the bonus never appears, report it. *Retest: only real spells (`IsSpell()`) charge it now; grit abilities no longer count as spells.*
- [ ] **Next-attack buffs last until used:** cast each buff and confirm it survives into your next turn when you don't attack, then is removed by the next firearm attack. The buffs are Stable Shot, Headshot, Ante Up, Hot Hand, Dead Man's Hand and the Spellshot charge. Also try casting them out of combat and then starting combat. *Retest: every next-attack buff now lasts 2 turns.*
- [x] **Level 5 level-up:** the level-up screen no longer goes black at level 5. Level a Gunslinger of each subclass from 1 to 20.

## Class, progression and UI

- [x] Class, subclass and inventory/character-sheet icons appear for Gunslinger, Marksman, Desperado and Arcane Gunsman.
- [x] Grit, ammo and other resource icons show on the hotbar and level-up screen.
- [x] The subclass name reads "Arcane Gunsman" (with a space).
- [x] The level 3 subclass choice appears before the grit ability choice, and each subclass offers its own grit pool.
- [ ] Grit ability choices appear at the right levels (base class: 3, 5, 9, 13, 17; Desperado: 3, 5, 7, 9, 11, 13, 15, 17, 19). *Retest: the 5/9/13/17 picks moved back to the base Gunslinger class, and the Desperado gets its own extra picks at 7, 11, 15 and 19. Marksman and Arcane Gunsman should still get exactly 3 (x2), 5, 9, 13 and 17.*
- [x] Maximum grit matches the README tables for each subclass.
- [x] Hit points: level 1 gives 8 + Constitution modifier, and each later level adds 5 + Constitution modifier. Check with a Constitution 14 (+2) character: 10 HP at level 1, 17 at level 2.
- [x] Gunslinger's Draw, Second Attack, Expertise, Tinkerer, Master Tinkerer, Improved Critical and Deadeye apply at their levels. *Retest: the grit abilities were in stats files that load before the spells and statuses they inherit from, so the engine dropped them. They're now merged into the main files.*
- [x] Lists of grit options show descriptions and icons, with no blank entries.

## Firearms and reloads

- [x] **Firearm type names:** tooltips (and dropped/crafted guns) show the weapon type as Flintlock, Blunderbuss and Musket, not Hand Crossbow, Heavy Crossbow and Light Crossbow. The guns still equip in the right hands, animate correctly and drop onto the ground normally.
- [x] Shoot Flintlock, Shoot Blunderbuss and Shoot Musket use weapon attack rolls, consume one bullet each, and are blocked when empty.
- [x] The main-hand and off-hand flintlocks keep separate ammo pools and separate attack buttons.
- [x] Primary and Secondary Reload use a bonus action, or an action when no bonus action remains. The hotbar/tooltip cost shows the bonus action, then switches to an action once the bonus action is spent (and back at the start of your next turn).
- [x] Reloading (Primary, Secondary and Full Reload, and Quickload) while hidden or invisible keeps you hidden or invisible and doesn't alert nearby enemies. *Retest: reloads now carry the vanilla Hide/Dash `Stealth;Invisible` flags.*
- [x] Full Reload appears only with an off-hand flintlock and costs an action. It's greyed out unless both hands hold flintlocks.
- [x] Tinkerer modifications, misfires and destruction persist per gun across unequipping, re-equipping, trading and save/load.
- [x] **Tinkerer statuses:** each modification shows on the modified gun's tooltip as Tinkered: Capacity, Tinkered: Damage or Tinkered: Range, stays on the gun when it's unequipped, and is removed on long rest. With Master Tinkerer, two of them show at once. *Retest: the spells now apply the status straight onto the gun (like Magic Weapon) instead of relying only on the script, and a script error can no longer silently stop the gun from updating for the rest of the session.*
- [x] **Tinkerer effects:** Capacity raises the gun's maximum ammo by 2 (reload to fill). Damage changes the weapon's damage dice on the tooltip and in rolls (Flintlock 1d10, Blunderbuss 2d6, Musket 3d4). Main-hand Range adds 20/10/40 ft to Shoot and to grit shots (check the targeting circle). Secondary Range lets the off-hand flintlock shoot out to 19.5 m. *Retest: range used to edit the weapon at runtime, which may not have reached the client or survived a reload. It now uses a spell-variant status like vanilla Distant Spell.*
- [x] **Misfire on the gun:** the firearm's Misfire passive reads as a rules description. After a natural 1, the gun's own tooltip shows a Misfired effect (like Tinkered: Damage), the attack penalty is -2 (not -4), and it clears on repair or long rest and turns into Broken on a second natural 1. Off-hand misfires mark the off-hand gun only.
- [ ] **Repair menu:** a misfired gun shows one class action for its hand only (**Repair: Main Hand** or **Repair: Off Hand**). It holds **Repair** (action, DC 15 Sleight of Hand), plus **Rapid Repair** next to it once you know Rapid Repair. A success clears the misfire and removes the menu; a broken gun shows no menu.
- [x] **Scattershot:** the blunderbuss cone deals half damage on a failed Dexterity save and none on a success. Check the Poison Mist, Gargantuan and Thunderous variants too; Poison Mist leaves its cloud even on a save. Each can be used once per short rest and comes back after a short or long rest.

## Feats

- [x] **Gunner:** the description no longer mentions the Sling proficiency group; it grants firearm proficiency and +1 Dexterity.
- [x] **Quick Reload:** it's named "Quick Reload", its description mentions the +1 Dexterity, and Full Reload shows and costs a bonus action while one is available, switching to an action once the bonus action is spent.
- [x] **Close-Quarters Gunner:** firearm attacks at 5 ft or closer no longer have Disadvantage, and nothing gets pushed.
- [x] **Grit Adept, Called Shot:** apply as described in the README.
- [x] **Longarm Specialist:** with a musket in the main hand, the attack range is 6m (20 ft) longer, and it stacks with Tinkerer: Range. Long shots no longer get Advantage. Flintlocks and Blunderbusses get no extra range. *Retest: the range bonus never applied; it is now a hidden status the script applies while a musket is equipped.*
- [x] **Feat Dexterity passives:** Long Range Training (Longarm Specialist), Steady Hands (Close-Quarters Gunner) and the Gunner and Called Shot Dexterity passives only say "Increase your Dexterity score by 1, to a maximum of 20." Only Quick Reload's mentions Full Reload.

## Grit abilities (all subclasses)

For each ability, also check that it appears under Class Actions on the hotbar (Line 'em Up and Shot in the Dark excepted), spends the listed grit, uses the listed action type, and is greyed out when you don't have enough grit.

- [x] Single-shot grit abilities appear as individual actions, not spell groups: Rapid Shot, Double Load, Disarming, Winging, Forceful, Bullying and Dazing Shot, and Final Judgement. They work with any equipped firearm. *Retest: the grit abilities were in stats files that load before the spells and statuses they inherit from, so the engine dropped them. They're now merged into the main files.*
- [x] Grit is regained on firearm critical hits and on kills by any means (firearm, melee, spell, Scattershot), once per attack: a critical kill gives 1 grit, and an area attack that kills several creatures gives 1 grit. Destroying objects gives none.
- [x] **Merciless Shot (action, 1-3 grit):** offers 1, 2 or 3 grit options. Each grit adds 1d4 damage with a Flintlock, or 1d6 with a Blunderbuss or Musket (e.g. 3 grit = weapon damage + 3d6 with a Musket). *Retest: replaced the half-weapon-attack bonus that didn't deal damage.*
- [x] **Line 'em Up (2 grit):** hits every enemy and neutral creature (but not allies) in a 20 ft (6 m) line. The save DC is 8 + Dexterity modifier + proficiency bonus; a successful save halves the damage.
- [x] **Rapid Shot (bonus action, 1 grit):** fires the equipped firearm again.
- [x] **Bite the Bullet (bonus action, 1-3 grit):** grants temporary HP equal to the grit spent * proficiency bonus. *Retest: the tooltip now shows the base-game warning that temporary HP from different sources doesn't stack.*
- [x] **Shot in the Dark (bonus action, 1 grit):** grants 18 m darkvision and ignores Blindness for 10 turns. Doesn't show status affect in tooltip.
- [ ] **Rapid Repair (bonus action, 1 grit):** has no separate hotbar entry. It appears next to Repair in a misfired gun's Repair menu and makes a DC 18 Sleight of Hand check. On a success, the misfire clears.
- [ ] **Fanning Fire (level 7+, action, 1-3 grit):** 1 grit gives 2 attacks at -2 against up to 2 enemies; 2 grit gives 3 attacks at -3 against up to 3 enemies; 3 grit gives 4 attacks at -4 against up to 4 enemies. *Retest: now one Fanning Fire group with 1, 2 and 3 grit options that works with any main-hand firearm, instead of separate per-firearm actions. Each shot spends a bullet. Retest: the to-hit penalty didn't apply; it is now part of the roll itself, so the hit chance shown when targeting should drop by 2/3/4 and the roll breakdown should list it.*
- [x] **Disarming Shot (level 3+, 1 grit):** on a hit, the target makes a Strength save or drops its weapon.
- [x] **Winging Shot (level 3+, 1 grit):** on a hit, the target makes a Constitution save or falls Prone.
- [x] **Forceful Shot (level 3+, 1 grit):** on a hit, the target makes a Strength save or is pushed back 4.5 m.
- [x] **Bullying Shot (level 3+, 1 grit):** on a hit, the target makes a Wisdom save or is Frightened for 1 turn.
- [x] **Quickload (level 3+, 1 grit):** a group with three options: reload the main hand (no bonus action), reload the off-hand flintlock (no bonus action), or reload both (bonus action). Each option only appears when the matching firearms are equipped.
- [x] **Flash Powder (level 3+, action, 1 grit):** can be aimed at an empty spot on the ground as well as at a creature within 9 m. Every creature within 1.5 m of that point rolls a Constitution save or is Blinded for 1 turn; barrels and other objects aren't affected.
- [ ] **Violent Shot (level 9+, 1-3 grit):** adds 1d8 (Flintlock), 2d6 (Blunderbuss) or 3d4 (Musket) damage per grit. Afterwards, a d20 roll at or below the grit spent makes the gun misfire. Retest: the linked menu shows exactly three entries (1/2/3 grit) that work with any equipped firearm.
- [x] **Dazing Shot (level 9+, 2 grit):** on a hit, the target makes a Constitution save or is Dazed for 1 turn. *Retest: in the description, hovering "Dazed" shows the Dazed condition tooltip and "saving throw" shows the saving throw tooltip.*
- [x] **Piercing Round (level 9+, 2 grit, 1 bullet):** makes an attack roll against every enemy and neutral creature (but not allies) in an 18 m line. *Retest: it used to skip neutral creatures.*
- [x] **Hair Trigger (level 9+, reaction, 1 grit):** offered when an enemy within 9 m attacks an ally (hit or miss), and shoots the attacker. 
- [x] **Grit and Steel (level 13+, 2 grit):** offered when you fail a saving throw, and rerolls it. Once per short rest.
- [x] **Bullet Time (level 17+, 4 grit):** grants an extra action this turn. Once per short rest.
- [x] **Hail of Lead (level 17+, action, 5 grit, 1 bullet):** makes a weapon attack against every enemy within 18 m. Once per long rest.
- [x] **Final Judgement (level 17+, 4 grit):** if the hit leaves the target below 25% HP, it takes weapon damage again and makes a Constitution save or dies.

## Marksman

- [x] **Lock-on:** a bonus action and concentration, adding proficiency-bonus damage to firearm hits on the target. When the target dies, Lock-on: New Target is offered without spending another short-rest use.
- [x] **Long Shot:** bonus damage scales with distance, once per turn.
- [x] Stable Shot and Pinpoint Accuracy apply as described. *Retest: Stable Shot no longer needs an action; it costs only its movement.*
- [x] **Headshot (level 18, 5 grit):** the next firearm hit is an automatic critical hit. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*

## Desperado

- [ ] The Desperado's own picks (3, 7, 11, 15, 19) offer its exclusive abilities at the levels listed in the README, and the base-class picks (5, 9, 13, 17) offer only shared abilities. Fanning Fire is first offered at the level 7 pick. *Retest: Desperado ability levels changed to 3/7/11/15/19.*
- [x] **Desperado's Luck (level 3+, 1 grit):** an interrupt offered when a firearm attack would miss, at most once per turn. It adds 1d4 to the roll and doesn't use your reaction.
- [x] **Ante Up (level 3+, bonus action, 1 grit):** gives Advantage on your next firearm attack before the end of your next turn. If that attack misses, attacks against you have Advantage until your next turn. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*
- [x] **Lucky Draw (level 3+, 1 grit):** rerolls 1s and 2s on firearm damage dice until the end of your turn. Once per turn.
- [x] **Two-Gun Tango (level 3+, 1 grit, 1 off-hand bullet):** fires the off-hand flintlock for normal off-hand weapon damage. *Retest: no longer costs a bonus action and no longer adds your Dexterity modifier.*
- [x] **Double Load (level 7+, 1 grit, 2 bullets):** deals weapon damage + 1d4 with a Flintlock, or + 1d6 with a Blunderbuss or Musket. A natural 1 breaks the gun until a long rest, even if it hadn't misfired before: it shows the Broken condition, and Rapid Repair can't fix it. *Retest: a Double Load natural 1 only misfired the gun; the script now applies the Double Load state before the roll and treats any misfire during Double Load as a break.*
- [x] **Roll the Bones (level 7+, bonus action, 1 grit):** rolls a d6. On a 1, firearm attack rolls get -1d4. On a 2-5, the next firearm hit deals +1d6. On a 6, it deals +2d6 and you regain 1 grit. The effect lasts until your next attack or 2 turns.
- [x] **Duck and Weave (level 7+, reaction, 1 grit):** offered when a ranged weapon attack is about to damage you. You resist its physical damage, then Disengage and gain 3 m of movement. *Retest: the movement status now lasts 2 turns so the extra 3 m is still there on your turn.*
- [x] **Close Call (level 7+, reaction, 2 grit):** gives +2 AC against an attack; if the attack then misses, you automatically shoot the attacker (main-hand firearm must be loaded). *Retest: no counter-shot when the attack still hits, and an automatic counter-shot with no extra prompt when it misses.*
- [x] **Cheat Death's Odds (level 7+, passive):** below half HP, abilities that cost 2 or more grit refund 1 grit. Abilities that cost 1 grit, and any ability used at or above half HP, get no refund.
- [ ] **Hot Hand (level 7+, reaction, 2 grit):** offered as a reaction prompt when you hit with a firearm attack. Your next firearm attack crits on 18-20. *Retest: it was a 2-grit action usable after a hit; it's now a reaction on the hit itself, with no hotbar spell. Check that the attack that triggered it doesn't consume the buff.*
- [x] **Last Word (level 11+, 3 grit):** a bonus action that prepares you for 2 turns. If you would be downed while prepared, you stay at 1 HP and make a firearm attack against your attacker. Once per long rest. *Retest: the old 0-HP reaction never triggered, so it now uses the same downed-replacement mechanism as Relentless Endurance. Test it as the last party member standing too.*
- [ ] **Double or Nothing (level 11+, reaction, 2 grit):** offered after a firearm hit (not a killing blow). On 11 or higher it deals weapon damage again; otherwise the gun misfires. *Retest: the misfire path worked but a win dealt no damage. The follow-up shot has no attack roll, so its damage moved from SpellSuccess (which never resolved) to SpellProperties.*
- [ ] **Quick on the Draw (level 11+, reaction, 2 grit):** offered when an enemy within 9 m starts an attack, and shoots it first. *Retest:* the enemy attack should be cancelled, the Gunslinger shot should resolve, and the enemy should get the attack back (free weapon attack or a restored action for spell attacks).
- [ ] **Ricochet Shot (level 11+, Desperado, 3 grit):** costs one bullet and fires at an enemy, then ricochets to up to three more enemies. Check separate attack rolls, full weapon damage on the first target, half damage on ricochets, and that only one bullet is spent.
- [x] **Dead Man's Hand (level 15+, 3 grit):** only usable below 25% HP. Your next firearm attack before the end of your next turn crits if it hits. Once per turn. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*
- [ ] **All In (level 19+, all grit (3-10), 1 bullet):** one All In group, usable with any main-hand firearm. Only the option matching your current grit (3-8) is available; it fires one shot per grit at enemies, each at -2 to hit, and leaves you with 0 grit.
- [ ] **Desperado's Fortune (level 19+, 1 grit):** replaces Desperado's Luck. Once per turn, it adds 1d8 to a firearm attack roll or a saving throw.
- [ ] **High Noon (level 19+, bonus action, 5 grit):** marks an enemy for 3 turns. Your firearm attacks against it get +20 to hit (only a natural 1 misses) and crit on 17-20; firearm attacks also deal an extra 1d8 damage. Confirm the extra damage appears only on firearm hits and does not add to attack rolls or saving throws. There's no reaction prompt. Once per long rest. *Retest: changed the High Noon 1d8 from an attack-roll and saving-throw bonus to bonus firearm damage.*

## Arcane Gunsman

- [x] **Arcane Gunsman spells:** each level-up offers one spell pick from a single pool. It holds the base-game spells plus the 5e Spells options when the add-on is loaded, and only spells of a level you have slots for: level 3 offers 2 cantrips and 3 1st-level spells; level 5, 2 spells of 1st-2nd level; level 9 adds a cantrip and 3rd-level spells; level 13, 4th-level spells; level 19, 5th-level spells. Fire Breath no longer appears. The level-up screen shows the spell slots gained (Spellcasting at level 3, then Spell Slots at 5, 7, 9, 11, 13, 15, 17 and 19), and they match the README table.
- [x] With 5e Spells and the compat add-on enabled, each spell pick shows the base-game and 5e spells in one combined list, with no separate 5e pick.
- [x] **Infused Rounds:** a bonus-action container with Fire, Thunder, Lightning, Acid, Cold and Poison options. Each lasts 10 turns and adds 1d4. Choosing a new element replaces the old one.
- [x] **Improved Infused Rounds (level 7):** adds Force and raises the damage to 2d4.
- [x] **Mastered Infused Rounds (level 11):** adds Radiant and Necrotic and raises the damage to 3d4.
- [ ] **Unstable Infused Rounds (level 15):** a toggleable passive on the hotbar, no longer an Infused Rounds option. While it's on and an infusion is active, damage becomes 5d4 and each firearm attack has a 25% backfire chance (3d4 Force in a 5 ft radius). With no infusion active, it does nothing. Check that toggling it off removes the effect.
- [x] **Smart Shooting (level 11):** a passive that adds your Intelligence modifier to firearm attack and damage rolls.
- [ ] **Arcane Reload (level 7):** a bonus action with concentration. The main-hand firearm shows an Arcane Reload status, and one bullet is reloaded at the start of each of your turns (up to capacity) until concentration ends. Breaking concentration removes the status from the gun.
- [ ] **Spellstrike Shooter:** after casting a leveled spell that costs an action, a free weapon attack is queued. Verify that cantrips, bonus-action spells, and spells cast without spending a spell slot do not trigger it.

## Crafting

- [x] Firearms and ammunition can be crafted from level 2, and the crafted items have the correct stats and icons.
- [x] Using an Assembly Kit opens a combine window with exactly two slots (firearm + magic weapon) and makes the combined firearm. Using a Disassembly Kit opens one slot, and disassembling a combined firearm returns the firearm and the magic weapon.
- [ ] Craft and disassemble each Flintlock, Blunderbuss, and Musket upgrade. Verify the two alternative Flintlock +3 recipes both require the Diamond Flintlock, and Advanced Musket Components combine Adamantine Slag with Rune Powder.
- [ ] Verify Quick Reload spends 1 Grit and no bonus action; Dash and Gun unlocks one free Flintlock attack after Dash; Paralyzing Shot consumes one musket cartridge and applies Paralyzed only on a failed Constitution save.
- [ ] Verify each upgrade's enchantment, attack bonus, critical range, bonus action, damage, fire resistance, piercing-resistance bypass, and Scattershot fire surface effect in-game.
