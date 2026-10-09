# In-Game Testing Checklist

Features that pass the local data tests (`python -B -m unittest discover -s tests`, the Lua tests and `validate_xml.py`) but still need to be checked in Baldur's Gate 3. Rebuild with `python stage_packages.py --divine` before testing.

Mark each item `[x]` when it works, or add a note under it describing what went wrong.

## High-risk items

These rely on engine behaviour that the local tests can't confirm.

- [x] **Nat-1 misfire:** a natural 1 on a basic firearm shot counts as a critical miss and misfires the gun (-2 to its attack rolls). A second natural 1 with that gun breaks it. The Misfire passive should now be visible in the firearm's tooltip, and a misfired or destroyed gun should show a Misfired / Broken status on the weapon itself. *Retest: the 100% hit chance was the nautiloid tutorial (vanilla, unchanged). Misfires silently failed on every magical firearm because the script only recognised the four base firearm templates; it now maps every firearm template from the weapon stats.*
- [x] **Nat-1 misfire on grit shots:** same check with a grit shot such as Disarming Shot or Rapid Shot.
- [x] **Projectile grit sounds:** grit shots (Merciless, Rapid, Disarming, Winging, Forceful, Bullying, Dazing, Violent, Fanning Fire, Double Load, Final Judgement, Double or Nothing) play the firing weapon's gunshot sound, not silence or a maneuver sound. Check Flintlock, Blunderbuss and Musket.
- [x] **Immersive Firearms gun sounds:** basic shots, grit shots and Scattershot play IF's flintlock/musket shot (Flintlock, off-hand Flintlock, Musket) or blunderbuss blast (Blunderbuss). Each shot should play the sound once, in time with the shot, with no doubled or missing sounds. Non-shot abilities (reloads, Lock-on, Flash Powder) should not play a gunshot.
- [x] **Infused Rounds damage:** the extra element damage (`CharacterWeaponDamage` in a status) shows on firearm hits in the combat log, and doesn't apply to melee or non-firearm attacks.
- [x] **Spellshot Adept:** after casting a spell, the next firearm hit deals the extra 1d4 Force. The status may be removed `OnAttack` before the damage is added; if the bonus never appears, report it. *Retest: only real spells (`IsSpell()`) charge it now; grit abilities no longer count as spells.*
- [ ] **Hot Streak:** starting the class action costs one bonus action and 6 Grit and shows the native once-per-short-rest indicator. After a miss ends the chain, starting again is blocked until a short rest. Each recast costs one weapon attack and one bullet, with no further Grit cost; confirm Extra Attack allows two shots with one action. Regular firearm attacks (including off-hand) and recast shots share the +1d4 through +10d4 bonus and advance the same chain once per attack, without double damage or multi-projectile advancement. Only the current recast is available. The tenth firearm hit, any attack miss, or a long rest removes all recast shots. Reloading, ending a turn, and short rests do not end the chain. Check all three firearm types, firing sounds, misfires, and save/load persistence.
- [x] **Next-attack buffs last until used:** cast each buff and confirm it survives into your next turn when you don't attack, then is removed by the next firearm attack. The buffs are Stable Shot, Headshot, Ante Up, Hot Hand, Dead Man's Hand and the Spellshot charge. Also try casting them out of combat and then starting combat. *Retest: every next-attack buff now lasts 2 turns.*
- [x] **Level 5 level-up:** the level-up screen no longer goes black at level 5. Level a Gunslinger of each subclass from 1 to 20.

## Class, progression and UI

- [x] Class, subclass and inventory/character-sheet icons appear for Gunslinger, Marksman, Desperado and Arcane Gunsman.
- [x] Grit, ammo and other resource icons show on the hotbar and level-up screen.
- [x] The subclass name reads "Arcane Gunsman" (with a space).
- [x] The level 3 subclass choice appears before the grit ability choice, and each subclass offers its own grit pool.
- [x] Grit ability choices appear at the right levels: Marksman and Arcane Gunsman at 3 (choose 2), 5, 9, 13 and 17; Desperado at 3 (choose 2), 5, 7, 9, 11, 13, 15, 17 and 18. The level 5/9/13/17 picks appear on each subclass's progression; Desperado's pools include shared abilities and its unlocked abilities, while the other subclasses use shared-only pools. Desperado gets its final pick and maximum-grit increase at level 18; there is no grit pick at level 19. Confirm no "Replace a Grit Ability" option appears.
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
- [x] **Tinkerer statuses:** upgrades show on the modified gun's tooltip as Tinkered: Capacity/Damage/Range or Tinker Master: Ammo/Damage/Range, stay on the gun when it's unequipped, and persist through long rests. With Master Tinkerer, two upgrades can coexist. Rest still repairs misfires/destruction and refills upgraded capacity.
- [x] **Tinkerer effects:** Ammo doubles base capacity; applying Ammo again with Master Tinkerer triples it (Flintlock 9, Blunderbuss 6, Musket 3). Damage adds 1d4 to the modified firearm's damage rolls; Master Damage adds 2d4 instead. Verify the added Piercing damage in the combat log for main-hand and off-hand shots, preserves existing weapon bonuses, does not affect the other gun, and persists after a long rest. Main-hand Range adds 20/10/40 ft; Master Range doubles that bonus. Secondary Range extends the off-hand flintlock to 19.5 m, and Master Range to 25.5 m. Capacity upgrades do not conjure bullets; reload to fill the new space.
- [x] **Remove Modification:** the Tinkerer menu has primary and secondary Remove Modification choices, each costing an action and no grit. Each clears all ordinary/master upgrades on that gun only, removes the corresponding capacity/range bonuses from the wielder, and discards bullets above base capacity. It does not repair a misfire. Cancelled casts leave upgrades intact; removed upgrades stay removed after save/load and long rests.
- [x] **Misfire on the gun:** the firearm's Misfire passive reads as a rules description. After a natural 1, the gun's own tooltip shows a Misfired effect (like Tinkered: Damage), the attack penalty is -2 (not -4), and it clears on repair or long rest and turns into Broken on a second natural 1. Off-hand misfires mark the off-hand gun only.
- [x] **Repair menu:** a misfired gun shows one class action for its hand only (**Repair: Main Hand** or **Repair: Off Hand**). It holds **Repair** (action, DC 15 Sleight of Hand), plus **Rapid Repair** next to it once you know Rapid Repair. A success clears the misfire and removes the menu; a broken gun shows no menu.
- [x] **Scattershot:** the blunderbuss cone deals half damage on a failed Dexterity save and none on a success. Check the Poison Mist, Gargantuan and Thunderous variants too; Poison Mist leaves its cloud even on a save. Each can be used once per short rest and comes back after a short or long rest.
- [x] **Scattershot range:** base Scattershot has a 15-foot cone; Poison Mist, Gargantuan and Thunderous Scattershot each have a 20-foot cone.

## Feats

- [x] **Gunner:** the description no longer mentions the Sling proficiency group; it grants firearm proficiency and +1 Dexterity.
- [x] **Quick Reload:** it's named "Quick Reload", its description mentions the +1 Dexterity, and Full Reload shows and costs a bonus action while one is available, switching to an action once the bonus action is spent.
- [x] **Close-Quarters Gunner:** firearm attacks at 5 ft or closer no longer have Disadvantage, and nothing gets pushed.
- [x] **Grit Adept, Called Shot:** apply as described in the README.
- [x] **Longarm Specialist:** with a musket in the main hand, the attack range is 6m (20 ft) longer, and it stacks with Tinkerer: Range. Long shots no longer get Advantage. Flintlocks and Blunderbusses get no extra range. *Retest: the range bonus never applied; it is now a hidden status the script applies while a musket is equipped.*
- [x] **Feat Dexterity passives:** Long Range Training (Longarm Specialist), Steady Hands (Close-Quarters Gunner) and the Gunner and Called Shot Dexterity passives only say "Increase your Dexterity score by 1, to a maximum of 20." Only Quick Reload's mentions Full Reload.

## Grit abilities (all subclasses)

For each ability, also check that it appears under Class Actions on the hotbar (Line 'em Up and Shot in the Dark excepted), spends the listed grit, uses the listed action type, and is greyed out when you don't have enough grit.

- [x] Single-shot grit abilities appear as individual actions, not spell groups: Rapid Shot, Double Load, Disarming, Winging, Forceful, Bullying and Stunning Shot, and Final Judgement. They work with any equipped firearm. *Retest: the grit abilities were in stats files that load before the spells and statuses they inherit from, so the engine dropped them. They're now merged into the main files.*
- [x] Grit is regained on firearm critical hits and on kills by any means (firearm, melee, spell, Scattershot), once per attack: a critical kill gives 1 grit, and an area attack that kills several creatures gives 1 grit. Destroying objects gives none.
- [x] **Merciless Shot (action, 1-3 grit):** offers 1, 2 or 3 grit options. Each grit adds 1d4 damage with a Flintlock, or 1d6 with a Blunderbuss or Musket (e.g. 3 grit = weapon damage + 3d6 with a Musket). *Retest: replaced the half-weapon-attack bonus that didn't deal damage.*
- [x] **Line 'em Up (2 grit):** hits every enemy and neutral creature (but not allies) in a 20 ft (6 m) line. The save DC is 8 + Dexterity modifier + proficiency bonus; a successful save halves the damage.
- [x] **Rapid Shot (bonus action, 1 grit):** fires the equipped firearm again.
- [x] **Bite the Bullet (bonus action, 1-3 grit):** grants temporary HP equal to the grit spent * proficiency bonus. *Retest: the tooltip now shows the base-game warning that temporary HP from different sources doesn't stack.*
- [x] **Shot in the Dark (bonus action, 1 grit):** grants 18 m darkvision and ignores Blindness for 10 turns. Doesn't show status affect in tooltip.
- [x] **Rapid Repair (bonus action, 1 grit):** has no separate hotbar entry. It appears next to Repair in a misfired gun's Repair menu and makes a DC 18 Sleight of Hand check. On a success, the misfire clears.
- [x] **Fanning Fire (level 7+, action, 1-3 grit):** 1 grit gives 2 attacks at -2 against up to 2 enemies; 2 grit gives 3 attacks at -3 against up to 3 enemies; 3 grit gives 4 attacks at -4 against up to 4 enemies. *Retest: now one Fanning Fire group with 1, 2 and 3 grit options that works with any main-hand firearm, instead of separate per-firearm actions. Each shot spends a bullet. Retest: the to-hit penalty didn't apply; it is now part of the roll itself, so the hit chance shown when targeting should drop by 2/3/4 and the roll breakdown should list it.*
- [x] **Trick Shot (level 3+):** one class-action group contains Disarming Shot (Strength save or drop weapon), Winging Shot (Constitution save or Prone), Forceful Shot (Strength save or 4.5 m push), and Bullying Shot (Wisdom save or Frightened for 1 turn). Each option costs an action, 1 grit, and one bullet; its effect applies only on a hit.
- [x] **Quickload (level 3+, 1 grit):** a group with three options: reload the main hand (no bonus action), reload the off-hand flintlock (no bonus action), or reload both (bonus action). Each option only appears when the matching firearms are equipped.
- [x] **Flash Powder (level 3+, action, 1 grit):** can be aimed at an empty spot on the ground as well as at a creature within 9 m. Every creature within 1.5 m of that point rolls a Constitution save or is Blinded for 3 turns; barrels and other objects aren't affected.
- [x] **Violent Shot (level 9+, 1-3 grit):** adds 1d8 (Flintlock), 2d6 (Blunderbuss) or 3d4 (Musket) damage per grit. Afterwards, a d20 roll at or below the grit spent makes the gun misfire. Retest: the linked menu shows exactly three entries (1/2/3 grit) that work with any equipped firearm.
- [x] **Stunning Shot (level 9+, 2 grit):** on a hit, the target makes a Constitution save or is Stunned for 1 turn. Verify the description links to the Stunned condition and saving throw tooltips.
- [x] **Piercing Round (level 9+, 2 grit, 1 bullet):** makes an attack roll against every enemy and neutral creature (but not allies) in an 18 m line. *Retest: it used to skip neutral creatures.*
- [x] **Hair Trigger (level 9+, reaction, 1 grit):** offered when an enemy within 9 m attacks an ally (hit or miss), and shoots the attacker. 
- [x] **Grit and Steel (level 13+, 2 grit):** offered when you fail a saving throw, and rerolls it. Once per short rest.
- [x] **Bullet Time (level 17+, 4 grit):** grants an extra action this turn. Once per short rest.
- [x] **Hail of Lead (level 17+, action, 5 grit, 1 bullet):** makes a weapon attack against every enemy within 18 m. Once per long rest.
- [x] **Final Judgement (level 17+, 4 grit):** if the hit leaves the target below 25% HP, it takes weapon damage again and makes a Constitution save or dies.
- [x] **Last Man Standing (level 18 Desperado):** only appears in the level-18 Desperado Grit Ability pool. It is not offered to other subclasses or in the level-17 pool. Verify there is a single **Last Man Standing** action on the hotbar (no per-firearm variants). It stays visible but disabled until a firearm kill (including an off-hand kill), then becomes enabled, costs 2 grit and 1 main-hand bullet, needs no action, and can target any enemy in range. Its tooltip shows the base-game once-per-short-rest indicator; after it is used it shows the short-rest-required warning and stays disabled until a short rest. Casting Start applies the chain condition, which lasts 2 turns and ends early when you hit with any weapon attack other than a Last Man Standing attack. Each kill by a Start or Chain attack while the condition is active should add a separate **Last Man Standing** chain button in the recast spells area (Start stays in place, disabled) for another 2-grit free attack. Test Flintlock, Blunderbuss and Musket main hands, ignoring the button, a shot that fails to kill, exhausting grit or bullets, and short-rest reset.

## Marksman

- [x] **Lock-on:** a bonus action and concentration, adding proficiency-bonus damage to firearm hits on the target. When the target dies, Lock-on: New Target is offered without spending another short-rest use.
- [x] **Long Shot:** bonus damage scales with distance, once per turn.
- [x] Stable Shot and Pinpoint Accuracy apply as described. *Retest: Stable Shot no longer needs an action; it costs only its movement.*
- [x] **Headshot (level 18, 5 grit):** the next firearm hit is an automatic critical hit. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*

## Desperado

- [x] Desperado picks at levels 5, 9, 13 and 17 include shared choices and previously unlocked Desperado abilities, without offering abilities from later levels. Its level-15+ pools omit Desperado's Luck and include Desperado's Fortune, displayed as already taken when automatically converted from Luck. A Desperado who knows Desperado's Luck automatically gains Fortune at level 15 without a grit cost or selection, and Luck is removed; a Desperado who does not know Luck does not gain Fortune. Its level 18 pick includes High Noon and all other selectable abilities unlocked by then. Confirm this is the final Desperado grit pick and there is no pick at level 19. Desperado's picks at levels 3, 7 and 11 offer the corresponding unlocked pool. Marksman and Arcane Gunsman picks at 5/9/13/17 remain shared-only. Fanning Fire is first offered to Desperado at level 7 and other subclasses at level 9.
- [x] **Desperado's Luck (level 3+, 1 grit):** an interrupt offered when a firearm attack would miss, at most once per turn. It adds 1d4 to the roll and doesn't use your reaction.
- [x] **Ante Up (level 3+, bonus action, 1 grit):** gives Advantage on your next firearm attack before the end of your next turn. If that attack misses, attacks against you have Advantage until your next turn. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*
- [x] **Lucky Draw (level 3+, 1 grit):** rerolls 1s and 2s on firearm damage dice until the end of your turn. Once per turn.
- [x] **Two-Gun Tango (level 3+, 1 grit, 1 off-hand bullet):** fires the off-hand flintlock for normal off-hand weapon damage. *Retest: no longer costs a bonus action and no longer adds your Dexterity modifier.*
- [x] **Double Load (level 7+, 1 grit, 2 bullets):** deals weapon damage + 1d4 with a Flintlock, or + 1d6 with a Blunderbuss or Musket. A natural 1 breaks the gun until a long rest, even if it hadn't misfired before: it shows the Broken condition, and Rapid Repair can't fix it. *Retest: a Double Load natural 1 only misfired the gun; the script now applies the Double Load state before the roll and treats any misfire during Double Load as a break.*
- [x] **Roll the Bones (level 7+, bonus action, 1 grit):** rolls a d6. On a 1, firearm attack rolls get -1d4. On a 2-5, the next firearm hit deals +1d6. On a 6, it deals +2d6 and you regain 1 grit. The effect lasts until your next attack or 2 turns.
- [x] **Duck and Weave (level 7+, reaction, 1 grit):** offered when a ranged weapon attack is about to damage you. You resist its physical damage, then Disengage and gain 3 m of movement. *Retest: the movement status now lasts 2 turns so the extra 3 m is still there on your turn.*
- [x] **Close Call (level 7+, reaction, 2 grit):** gives +2 AC against an attack; if the attack then misses, you automatically shoot the attacker (main-hand firearm must be loaded). *Retest: no counter-shot when the attack still hits, and an automatic counter-shot with no extra prompt when it misses.*
- [x] **Cheat Death's Odds (level 7+, passive):** below half HP, abilities that cost 2 or more grit refund 1 grit. Abilities that cost 1 grit, and any ability used at or above half HP, get no refund.
- [x] **Hot Hand (level 7+, 2 grit, no reaction required):** offered as a prompt when you hit with a firearm attack, even if your reaction is unavailable. Your next firearm attack crits on 18-20. Retest that the triggering attack doesn't consume the buff. Once used, the prompt must not return that turn even after the buff is consumed; it becomes available next turn.
- [x] **Last Word (level 11+, 3 grit):** a bonus action that prepares you for 2 turns. If you would be downed while prepared, you stay at 1 HP and make a firearm attack against your attacker. Once per long rest. *Retest: the old 0-HP reaction never triggered, so it now uses the same downed-replacement mechanism as Relentless Endurance. Test it as the last party member standing too.*
- [x] **Double or Nothing (level 11+, 2 grit, no reaction required):** offered after a firearm hit (not a killing blow), even if your reaction is unavailable. On 11 or higher, it makes a free firearm attack with its own attack roll against the original target and spends one bullet; otherwise the gun misfires. Confirm the extra attack costs no action, grit, or Reaction, and that it can miss independently. The d20 roll should play only the Second Wind gesture, with no projectile; only a successful bonus attack should fire another shot. Check with both a single firearm and dual-wielded flintlocks.
- [x] **Independent once-per-turn limits:** after accepting Double or Nothing, no further prompt should appear that turn whether the roll succeeds or misfires. It becomes available next turn. Using Double or Nothing must not lock out Hot Hand, or vice versa. Declining either prompt must not consume its use.
- [x] **Quick on the Draw (level 11+, reaction, 2 grit):** offered when an enemy within 9 m starts an attack, and shoots it first. *Retest:* the enemy attack should be cancelled, the Gunslinger shot should resolve, and the enemy should get the attack back (free weapon attack or a restored action for spell attacks).
- [x] **Ricochet Shot (level 11+, Desperado, 3 grit):** costs one bullet and fires at an enemy, then ricochets to up to three more enemies. Check separate attack rolls, full weapon damage on the first target, half damage on ricochets, and that only one bullet is spent.
- [x] **Dead Man's Hand (level 15+, 3 grit):** only usable below 25% HP. Your next firearm attack before the end of your next turn crits if it hits. Once per turn. *Retest: the status now lasts 2 turns and is only removed by a weapon attack.*
- [x] **Desperado's Fortune (level 15 upgrade, 1 grit):** only characters who know Desperado's Luck receive the free upgrade after completing level 15. Luck is removed; Fortune shows as taken only when its class feature is actually owned. Without Luck, Fortune remains an untaken grit selection. Retest subsequent levels, delayed progression updates, save/load with no equipped or tracked firearm, completed respecs with and without Luck, and cancelled respecs. Conversion must stay paused while the respec UI is open. Once per turn, it offers +1d8 only after a missed firearm attack or failed saving throw. Characters affected by the old unconditional grant need to respec after installing the rebuilt mod.
- [x] **High Noon (unlocked at level 18, bonus action, 5 grit):** marks an enemy for 3 turns. Your firearm attacks against it get +20 to hit (only a natural 1 misses) and crit on 17-20; firearm attacks also deal an extra 1d8 damage. Confirm the extra damage appears only on firearm hits and does not add to attack rolls or saving throws. There's no reaction prompt. Once per long rest. *Retest: changed the High Noon 1d8 from an attack-roll and saving-throw bonus to bonus firearm damage.*

- [x] **Removed All In:** no longer offered in the level 18 Desperado chooser. Loading an existing save removes its old unlock passive, dynamic boosts and ready marker. Verify the retired group disappears and Fanning Fire still works normally.

For Fortune/save-load recovery, confirm the Script Extender console has no `Attempted to call Osiris function in restricted context` error. Restoration runs on the first server tick after loading, not inside `SessionLoaded`. Confirm the level-15 screen displays **Desperado's Luck: Evolution** and explains the free conditional upgrade. Confirm Luck disappears from both the passive features and the reactions tab after native progression removal; existing affected saves need a respec to rebuild the progression. Fortune's reaction must remain available. Cancelling a respec must restore Fortune without leaving Luck's passive or reaction behind. If removal fails, a single `[Gunslinger] WARNING: Luck remains owned` warning remains; debug snapshots and passive-source dumps are no longer emitted.

### Fortune level-up owned indicator

Rebuild/install the mod with Script Extender v29 or newer, restart the game, and load a save immediately before Desperado level 15. Test keyboard/mouse and controller:

- Repeat with Luck picked at each of levels **5, 7, 9, 11, and 13**. Open the level-15 grit chooser and wait for Fortune ownership to replicate. The preview temporarily substitutes Fortune's passive stat ID for that earlier Luck pick, without changing the passive-list UUID. Fortune must show the taken checkmark and reject selection without a Tick error. The newly earned grit choice remains available for another ability. Confirm and inspect earlier selections for unintended changes; also cancel and confirm the original Luck selection/passive/reaction remains intact.
- Without Luck, Fortune must remain an ordinary selectable grit choice; it must not be granted free.
- Cancel and reopen the chooser, then confirm level 15. Cancellation removes temporary Fortune; confirmation keeps it and removes Luck's passive and reaction.
- During respec, omit Luck and confirm that Fortune is selectable again. Repeat save/load and switching characters.
- Confirm there are no Fortune preview dumps, `Luck cleanup` source dumps, or runtime-loaded messages in the extender log, and no new preview diagnostic file is written.
- Leave the chooser open and scroll/reopen its list. Confirm no sustained slow-Tick warning spam. The native row is matched by its captured type `ls.VMCharacterCreationPassive`, localization handle `h00000027g0000g4000g8000g000000000001`, and icon. A wrapper overrides read-only `Value`/`Enabled` to the already-owned state. Discovery is bounded to 24 nodes and a 500-microsecond elapsed-time budget per pass; stable rows are checked by cached index path rather than recurring whole-tree traversal. Cancellation must restore the original row and widget.
- Test two characters with different Luck-selection levels, including one without Luck. Their preview histories must not affect each other. Changing the original pick during respec must not be overwritten by restoration.

### Manual Fortune chooser inspection

The native passive templates read the row model's `Value` and `Enabled`: `Value = 1` shows a current selection; `Enabled = false` shows a previously selected checkmark. The compiled calculation that supplies these values is not exposed by the templates. Do not assume changing a passive or selection array refreshes that model, or that `ChangeId`/`NeedsSync` are safe refresh controls without runtime evidence.

The live capture confirmed Fortune's unchecked row has `Value = 0`, `Enabled = true`, and all its properties are read-only, whereas previously owned choices have `Value = 1`, `Enabled = false`. `Name` contains an untranslated localization handle. Character ownership and preview-history substitution both succeeded without changing the row; `NeedsSync` was already true. The fix overrides the row through a supported Noesis wrapper, without guessing at a refresh flag or modifying the selector's chosen-count calculation.

Only elements declaring both `DataContext` and `IsEnabled` are wrapped. The `IsEnabled` dependency property's getter can return nil even when declared; its value is not read, saved, or written. Ownership uses the row model's verified `Value`/`Enabled` bindings instead. Presentation-only elements with the same Fortune context are traversed without being changed. Test both mouse clicks and controller acceptance to confirm the owned row cannot spend another grit choice.

Hover the owned Fortune row and focus it with a controller. Its tooltip must describe Desperado's Fortune, not `se::GSL_OwnedFortuneBindings`. The row retains the ownership wrapper while tooltip content/context receives the original native passive model. Repeat after scrolling/recreating the row and cancelling/reopening the chooser.

To capture the live model without adding Tick-based UI scans:

1. Rebuild/install and restart. Open the level-15 grit chooser with Fortune still unchecked.
2. In the Script Extender console, press Enter, type `client`, then run `!gsl_fortune_chooser`.
3. Attach `%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\Script Extender\GunslingerFortuneChooser.json`.

The command runs only when invoked. It records passive row values/property writability, selector counts, preview/current/character choices, Luck/Fortune ownership on the character and dummy, and `ChangeId`/`NeedsSync`. It does not modify any state. Traversal stops after 20,000 nodes or one second and explicitly reports an incomplete capture. Ordinary Lua/scalar contexts are tolerated; generic Script Extender type introspection does not identify Noesis proxies, so callable Noesis reflection is checked separately. Normal gameplay emits no diagnostic dumps or files.

## Arcane Gunsman

- [x] **Arcane Gunsman spells:** each level-up offers one spell pick from a single pool. It holds the base-game spells plus the 5e Spells options when the add-on is loaded, and only spells of a level you have slots for: level 3 offers 2 cantrips and 3 1st-level spells; level 5, 2 spells of 1st-2nd level; level 9 adds a cantrip and 3rd-level spells; level 13, 4th-level spells; level 19, 5th-level spells. Fire Breath no longer appears. The level-up screen shows the spell slots gained (Spellcasting at level 3, then Spell Slots at 5, 7, 9, 11, 13, 15, 17 and 19), and they match the README table.
- [x] With 5e Spells and the compat add-on enabled, each spell pick shows the base-game and 5e spells in one combined list, with no separate 5e pick.
- [x] **Infused Rounds:** a bonus-action container with Fire, Thunder, Lightning, Acid, Cold and Poison options. Each lasts 10 turns and adds 1d4. Choosing a new element replaces the old one.
- [x] **Improved Infused Rounds (level 7):** adds Force and raises the damage to 2d4.
- [x] **Mastered Infused Rounds (level 11):** adds Radiant and Necrotic and raises the damage to 3d4.
- [x] **Unstable Infused Rounds (level 15):** a toggleable passive on the hotbar, no longer an Infused Rounds option. While it's on and an infusion is active, damage becomes 5d4 and each firearm attack has a 25% backfire chance (3d4 Force in a 5 ft radius). With no infusion active, it does nothing. Check that toggling it off removes the effect.
- [x] **Smart Shooting (level 11):** a passive that adds your Intelligence modifier to firearm attack and damage rolls.
- [x] **Arcane Reload (level 7):** a bonus action with concentration. The main-hand firearm shows an Arcane Reload status, and one bullet is reloaded at the start of each of your turns (up to capacity) until concentration ends. Breaking concentration removes the status from the gun.
- [x] **Spellstrike Shooter:** after casting a leveled spell that costs an action, a free weapon attack is queued. Verify that cantrips, bonus-action spells, and spells cast without spending a spell slot do not trigger it.

## Crafting

- [x] Firearms and ammunition can be crafted from level 2, and the crafted items have the correct stats and icons.
- [x] Using an Assembly Kit opens a combine window with exactly two slots (firearm + magic weapon) and makes the combined firearm. Using a Disassembly Kit opens one slot, and disassembling a combined firearm returns the firearm and the magic weapon.
- [ ] Craft and disassemble each Flintlock, Blunderbuss, and Musket upgrade. Verify the two alternative Flintlock +3 recipes both require the Diamond Flintlock, and Advanced Musket Components combine Adamantine Slag with Rune Powder.
- [x] Verify Quick Reload spends 1 Grit and no bonus action; Dash and Gun unlocks one free Flintlock attack after Dash; Paralyzing Shot consumes one musket cartridge and applies Paralyzed only on a failed Constitution save.
- [ ] Verify each upgrade's enchantment, attack bonus, critical range, bonus action, damage, fire resistance, piercing-resistance bypass, and Scattershot fire surface effect in-game.
