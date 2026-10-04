# In-Game Testing Checklist

Features that pass the local data tests (`python -B -m unittest discover -s tests`, the Lua tests and `validate_xml.py`) but still need to be checked in Baldur's Gate 3. Rebuild with `python stage_packages.py --divine` before testing.

Mark each item `[x]` when it works, or add a note under it describing what went wrong.

## High-risk items

These rely on engine behaviour that the local tests can't confirm.

- [ ] **Nat-1 misfire:** a natural 1 on a basic firearm shot counts as a critical miss and misfires the gun (-2 to its attack rolls). A second natural 1 with that gun breaks it.
- [ ] **Nat-1 misfire on grit shots:** same check with a grit shot such as Disarming Shot or Rapid Shot.
- [ ] **Projectile grit sounds:** grit shots (Merciless, Rapid, Disarming, Winging, Forceful, Bullying, Dazing, Violent, Fanning Fire, Double Load, Final Judgement, Double or Nothing, All In) play the firing weapon's gunshot sound, not silence or a maneuver sound. Check Flintlock, Blunderbuss and Musket.
- [ ] **Immersive Firearms gun sounds:** basic shots, grit shots and Scattershot play IF's flintlock/musket shot (Flintlock, off-hand Flintlock, Musket) or blunderbuss blast (Blunderbuss). Each shot should play the sound once, in time with the shot, with no doubled or missing sounds. Non-shot abilities (reloads, Lock-on, Flash Powder) should not play a gunshot.
- [ ] **Infused Rounds damage:** the extra element damage (`CharacterWeaponDamage` in a status) shows on firearm hits in the combat log, and doesn't apply to melee or non-firearm attacks.
- [ ] **Spellshot Adept:** after casting a spell, the next firearm hit deals the extra 1d4. The status may be removed `OnAttack` before the damage is added; if the bonus never appears, report it.
- [ ] **Next-attack buffs last until used:** cast each buff and confirm it survives into your next turn when you don't attack, then is removed by the next firearm attack. The buffs are Stable Shot, Headshot, Ante Up, Hot Hand, Dead Man's Hand and the Spellshot charge. Also try casting them out of combat and then starting combat.
- [ ] **Level 5 level-up:** the level-up screen no longer goes black at level 5. Level a Gunslinger of each subclass from 1 to 20.

## Class, progression and UI

- [ ] Class, subclass and inventory/character-sheet icons appear for Gunslinger, Marksman, Desperado and Arcane Gunsman.
- [ ] Grit, ammo and other resource icons show on the hotbar and level-up screen.
- [ ] The subclass name reads "Arcane Gunsman" (with a space).
- [ ] The level 3 subclass choice appears before the grit ability choice, and each subclass offers its own grit pool.
- [ ] Grit ability choices appear at the right levels (base class: 3, 5, 9, 13, 17; Desperado: 3, 5, 8, 11, 14, 17, 20).
- [ ] Maximum grit matches the README tables for each subclass.
- [ ] Hit points: level 1 gives 8 + Constitution modifier, and each later level adds 5 + Constitution modifier. Check with a Constitution 14 (+2) character: 10 HP at level 1, 17 at level 2.
- [ ] Gunslinger's Draw, Second Attack, Expertise, Tinkerer, Master Tinkerer, Improved Critical and Deadeye apply at their levels.
- [ ] Lists of grit options show descriptions and icons, with no blank entries.

## Firearms and reloads

- [ ] Shoot Flintlock, Shoot Blunderbuss and Shoot Musket use weapon attack rolls, consume one bullet each, and are blocked when empty.
- [ ] The main-hand and off-hand flintlocks keep separate ammo pools and separate attack buttons.
- [ ] Primary and Secondary Reload use a bonus action, or an action when no bonus action remains.
- [ ] Full Reload costs an action, or a bonus action with the Quick Reload feat. It's greyed out unless both hands hold flintlocks.
- [ ] Ammo, Tinkerer modifications, misfires and destruction persist per gun across unequipping, re-equipping, trading and save/load.
- [ ] Field repair (action plus Sleight of Hand) clears a misfire, but can't fix a destroyed gun.
- [ ] **Scattershot:** the blunderbuss cone deals half damage on a failed Dexterity save and none on a success. Check the Poison Mist, Gargantuan and Thunderous variants too; Poison Mist leaves its cloud even on a save.

## Feats

- [ ] **Gunner:** the description no longer mentions the Sling proficiency group; it grants firearm proficiency and +1 Dexterity.
- [ ] **Quick Reload:** it's named "Quick Reload", its description mentions the +1 Dexterity, and it turns Full Reload into a bonus action.
- [ ] **Close-Quarters Gunner:** firearm attacks at 5 ft or closer no longer have Disadvantage, and nothing gets pushed.
- [ ] **Grit Adept, Longarm Specialist, Called Shot:** apply as described in the README.

## Grit abilities (all subclasses)

- [ ] Single-shot grit abilities appear as individual actions, not spell groups: Rapid Shot, Double Load, Disarming, Winging, Forceful, Bullying and Dazing Shot, Ricochet, and Final Judgement. They work with any equipped firearm.
- [ ] Merciless Shot offers 1, 2 or 3 grit options, adding damage for each grit spent.
- [ ] Shot in the Dark lasts 10 turns.
- [ ] Line 'em Up, Piercing Round and Hail of Lead hit the correct targets and use the right saves or attack rolls.
- [ ] Violent Shot's misfire roll, Fanning Fire's multi-target shots, Hair Trigger and Grit and Steel all work.
- [ ] Grit is regained on critical hits and kills.

## Marksman

- [ ] **Lock-on:** a bonus action and concentration, adding proficiency-bonus damage to firearm hits on the target. When the target dies, Lock-on: New Target is offered without spending another short-rest use.
- [ ] **Long Shot:** bonus damage scales with distance, once per turn.
- [ ] Stable Shot, Pinpoint Accuracy and Headshot apply as described.

## Desperado

- [ ] **Double or Nothing:** offered as a reaction after a firearm hit (not a killing blow). On 11 or higher it deals weapon damage again; otherwise the gun misfires.
- [ ] Desperado's Luck/Fortune, Duck and Weave, Close Call, Quick on the Draw and Last Word trigger as reactions or interrupts.
- [ ] Cheat Death's Odds refunds 1 grit for abilities that cost 2 or more grit while you're below half HP.
- [ ] Roll the Bones, Lucky Draw, Two-Gun Tango, Last Stand, All In and High Noon apply as described.

## Arcane Gunsman

- [ ] At level 3, the level-up screen offers real spell lists, not cantrip picks over empty lists. Spell slots match the README table.
- [ ] **Infused Rounds:** a bonus-action container with Fire, Thunder, Lightning, Acid, Cold and Poison options. Each lasts 10 turns and adds 1d4. Choosing a new element replaces the old one.
- [ ] **Improved Infused Rounds (level 7):** adds Force and raises the damage to 2d4.
- [ ] **Mastered Infused Rounds (level 11):** adds Radiant and Necrotic and raises the damage to 3d4.
- [ ] **Unstable Infused Rounds (level 15):** only usable while infused. Damage becomes 5d4, and there's a 25% backfire chance per firearm attack (3d4 Force in a 5 ft radius).
- [ ] **Smart Shooting (level 11):** a passive that adds your Intelligence modifier to firearm attack and damage rolls.
- [ ] Arcane Reload and Spellstrike Shooter apply as described.

## Crafting

- [ ] Firearms and ammunition can be crafted from level 2, and the crafted items have the correct stats and icons.
