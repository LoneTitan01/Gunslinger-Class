# bg3-Gunslinger-Class
This is a mod for Baldur's Gate 3 implementing a Gunslinger class, the ability to craft firearms, etc.

## Requirements

- **Required:** [BG3 Script Extender](https://github.com/Norbyte/bg3se/releases), version 20 or newer. Persistent firearm modifications, misfire/broken state, per-hand Repair menus, volley cleanup, Violent Shot/Double or Nothing/Roll the Bones rolls, Cheat Death's Odds refunds, and Last Word's post-damage counterattack use server-side Lua. Install the extender through BG3 Mod Manager before enabling this version.
- **Required for Assembly/Disassembly Kits:** JWL Crafting Framework. The kits use its item-combination interface; firearms and the rest of the class can be used without it.
- **Optional:** [5e Spells](https://www.nexusmods.com/baldursgate3/mods/125), for the Arcane Gunsman spell options marked as coming from that mod.

## Modding Wiki

- [Baldur's Gate 3 Modding Wiki](https://wiki.bg3.community/Tutorials)

## Firearms

Each firearm replaces the default ranged attack with its own **Shoot Flintlock**, **Shoot Blunderbuss**, or **Shoot Musket** weapon attack. Shots fire the vanilla crossbow bolt projectile along a flat, straight line (the bolt's lobbed arc is removed) with crossbow firing animations, weapon damage, and weapon attack rolls; they are not spell attacks or piercing line-area attacks. Each basic shot consumes one bullet, and the engine prevents the attack when its ammo pool is empty. Flintlocks hold 3 bullets in each hand, blunderbusses hold 2, and muskets hold 1. Main-hand and offhand flintlocks use separate ammo pools and separate attack buttons; automatic bundled dual-wield shots are disabled so an offhand shot cannot bypass its ammunition cost.

Reload actions are granted by the equipped gun, not by Gunslinger class level:

- **Primary Reload:** bonus action, or an action if no bonus action remains; appears with a main-hand flintlock, blunderbuss, or musket and refills that gun.
- **Secondary Reload:** bonus action, or an action if no bonus action remains; appears with an offhand flintlock and refills its separate pool.
- **Full Reload:** action; with the Quick Reload feat, a bonus action, or an action if no bonus action remains. Appears with an off-hand flintlock (greyed out unless a flintlock is also in the main hand) and refills both pools.

Reloading (including Quickload) doesn't break Hide/sneaking or invisibility, like vanilla Hide and Dash. The hotbar and tooltips show each reload's current cost. The server toggles hidden statuses (`GSL_RELOAD_NO_BONUS_ACTION`, `GSL_QUICK_FULL_RELOAD`) whose `UnlockSpellVariant`/`ModifyUseCosts` boosts swap the cost between bonus action and action as the bonus action is spent or restored.

**Scattershot** (blunderbuss only) costs an action and one blunderbuss bullet, and can be used once per short rest. It blasts a 15-foot cone; each creature in it makes a Dexterity saving throw (DC 8 + Dexterity modifier + proficiency bonus), taking half weapon damage on a failed save and none on a success. Special Scattershots have a 20-foot cone (5 feet longer); Poison Mist still leaves its cloud. Each variant has its own once-per-short-rest cooldown, like vanilla weapon actions. It appears only while a working blunderbuss is in the main hand.

Firearms do not grant the inherited vanilla crossbow weapon actions (Piercing Shot, Mobile Shooting, Brace). Their only equipment-granted actions are the shots, reloads, and Scattershot listed above. They are granted through the weapons' `BoostsOnEquipMainHand` / `BoostsOnEquipOffHand` (`UnlockSpell(...)`) so they are listed as actions on the weapon tooltip, like vanilla weapon actions. The off-hand flintlock grants Secondary Reload, the off-hand shot, and Full Reload; Full Reload is greyed out unless a flintlock is also in the main hand. The hidden per-hand equip passives only add the ammo pools and swap the default ranged attack for the firearm shot (`AttackSpellOverride`).

Ammo refills on a short or long rest. Hand/type resource pools remain the combat UI, while Script Extender stores ammunition, modifications, misfires, and destruction against each physical firearm and restores its state when equipped or transferred. A natural 1 on an attack roll causes that gun to misfire: it can still fire, but its attack rolls take a -2 penalty until it's repaired or you take a long rest. While misfired, that gun gets its own **Repair** class-action menu (**Repair: Main Hand** or **Repair: Off Hand**). **Repair** costs an action and a DC 15 Sleight of Hand check; once you know Rapid Repair, it appears in the same menu next to Repair. A failed check spends its costs but leaves the misfire in place. A natural 1 with a gun that has already misfired breaks it: the Misfired condition is replaced by **Broken**, which stops that gun firing until a long rest. Broken guns cannot be field-repaired (Rapid Repair also cannot fix them).

| Firearm | Hands | Capacity | Base damage | Damage type | Range |
| --- | --- | --- | --- | --- | --- |
| Flintlock | One-handed | 3 bullets | 2d4 | Piercing | 45 ft |
| Blunderbuss | Two-handed | 2 bullets | 1d12 | Bludgeoning | 25 ft |
| Musket | Two-handed | 1 bullet | 2d6 | Piercing | 80 ft |

Weapon range values are **1350 / 750 / 2400**, respectively, using the game's shortbow scale of 1800 = 60 feet. Main-hand shooting spells use the equipped weapon's range, extended by a hidden spell-variant status (`ModifyTargetRadius`) while the main-hand gun has Tinkerer's range modification; the secondary flintlock uses 13.5 metres, or a 19.5-metre override with Tinkerer's range modification. The modified secondary attack is also explicitly unlocked as a selectable action. High-ground range extensions remain inherited from vanilla ranged attacks.

Blunderbuss and Musket use BG3's exact `Twohanded` weapon-property token, matching Heavy and Light Crossbows. The display-style spelling `Two-Handed` is not a valid stats property.

### Crafting

Starting at level 2, the Gunslinger has three **Craft** charges per day. Spend one charge to create one of the following:

- A base Flintlock
- A base Musket
- A base Blunderbuss
- An Assembly Kit, used to fuse a magical weapon to a firearm
- A Disassembly Kit, used to defuse a fused firearm and magical weapon

Use a kit's item-combination action to open the crafting interface. The supported recipes fuse an Assembly Kit, a magical weapon, and a base firearm; the kit and magical weapon are consumed and the firearm is transformed. Disassembly returns the base firearm and its original magical weapon, and consumes the Disassembly Kit. Implemented recipes include forty-four Flintlock combinations, forty-nine Musket combinations, and 54 Blunderbuss combinations. Every implemented recipe has a matching disassembly recipe. Blunderbuss adaptations include Revitalizing Shot, Corrosive Shot, Poison Mist Scattershot, Sorrowful Lash, Gargantuan Scattershot, Thunderous Scattershot, and firearm-compatible Undead Bane, Blooded, Unseen Menace, Punch-Drunk, Defender Flail, Psionic Weapon, Woundseeker, Fortune's Favor, Commander's Strike, and Undead Slayer effects. Other source abilities are retained where their effects support firearm attacks.

The following compatibility mapping includes weapons from the BG3 Wiki's [uncommon](https://bg3.wiki/wiki/List_of_uncommon_weapons), [rare](https://bg3.wiki/wiki/List_of_rare_weapons), and [very rare](https://bg3.wiki/wiki/List_of_very_rare_weapons) lists. Weapons whose only feature is a +1, +2, or +3 Enchantment are omitted. Flintlocks are matched to Light or Finesse weapons, shortbows, and hand crossbows; Muskets to Versatile or Thrown weapons, longbows, and light crossbows; and Blunderbusses to all remaining weapons, including two-handed weapons and heavy crossbows. When properties overlap, the priority is Flintlock > Musket > Blunderbuss, and each weapon appears only once. Weapon names link to their individual wiki pages. The Special ability column records the source property; Firearm Ability is the proposed adaptation. The first forty-four Flintlock and forty-nine Musket conversions listed below are implemented, along with 54 Blunderbuss conversions whose source item stats and templates were verified in the extracted reference. Damage of a weapon's bludgeoning, piercing, or slashing type is converted to the firearm's base damage type where applicable; resistance ignoring is adapted to the firearm's damage type. Recast melee weapon actions as firearm shots; close-area effects become Blunderbuss Scattershot abilities with the noted extended area or added effect. Some firearm ability proposals remain unimplemented.

### Firearm upgrade paths

Use the Assembly Kit with the current firearm and its listed material; the kit and material are consumed while the firearm is transformed. The Disassembly Kit restores the previous firearm and material. Flintlocks progress from Quickshot (+1, +1 Grit, Quick Reload) to Run-and-Gun (+1, Dash and Gun), then Diamond (+2, piercing-resistance bypass and one extra bonus action). Diamond Flintlocks can be upgraded with either a Black Diamond (+3, improved critical range and advantage in dim light or darkness) or an Infernal Diamond (+3, +2d6 Fire damage per shot).

Blunderbusses progress through Infernal Iron (+1, +1 Fire damage), Infernal Alloy (+1, fire resistance and +1d4 Fire damage), Soul Coin (+2, +1 critical range, +1d6 Fire on regular shots and +1d4 on Scattershot), and Enriched Infernal Iron (+3, +2d4 Fire on regular shots and Scattershot, which also ignites the ground). Muskets progress through Silver (+1, +2 to hit), Advanced Musket Components (+1d4 weapon damage), Karabasan's Gift (+2 and Paralyzing Shot once per short rest), and Mithral (+3, +1d6 weapon damage and piercing-resistance bypass). Craft Advanced Musket Components from Adamantine Slag and Rune Powder.

<details>
<summary>Flintlock-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Artificial Leech (+1)](https://bg3.wiki/wiki/Artificial_Leech_(%2B1)) | +1 | Bloodletting weapon action can cause Bleeding. | Bloodletting Shot: once per short rest, a hit can inflict Bleeding. |
| [Assassin's Shortsword](https://bg3.wiki/wiki/Assassin's_Shortsword) | +1 | Advantage on Stealth checks. | While equipped, gain Advantage on Stealth checks. |
| [Assassin's Touch](https://bg3.wiki/wiki/Assassin's_Touch) | +1 | Deals 1d4 Necrotic damage to sleeping or knocked-out targets. | Shots deal 1d4 Necrotic damage to Sleeping or Knocked Out targets. |
| [Club of Hill Giant Strength](https://bg3.wiki/wiki/Club_of_Hill_Giant_Strength) | None | Sets the wielder's Strength to 19. | While equipped, your Strength score becomes 19. |
| [Dragon's Grasp](https://bg3.wiki/wiki/Dragon's_Grasp) | None | Deals +1d4 weapon damage to Burning targets. | Shots deal +1d4 firearm damage to Burning targets. |
| [Firestoker](https://bg3.wiki/wiki/Firestoker) | None | Deals +1d4 weapon damage to Burning targets. | Shots deal +1d4 firearm damage to Burning targets. |
| [Hunter's Dagger](https://bg3.wiki/wiki/Hunter's_Dagger) | +1 | Hits inflict Ruptured for 3 turns. | Hits can inflict Ruptured for 3 turns. |
| [Murderous Cut](https://bg3.wiki/wiki/Murderous_Cut) | +1 | Deals +1d4 Piercing damage to targets at or below half HP. | Shots deal +1d4 firearm damage to targets at or below half HP. |
| [Ritual Axe](https://bg3.wiki/wiki/Ritual_Axe) | None | Can penalize a target's attack rolls and saves by 1d4; may deal 1d6 Piercing damage to the wielder if they have at least half HP. | A hit can penalize the target's attack rolls and saves by 1d4; at or above half HP, a shot can cost you 1d6 firearm damage. |
| [Ritual Dagger](https://bg3.wiki/wiki/Ritual_Dagger) | None | On hit, grants +1d4 to attack rolls and saves until the end of the wielder's next turn. Blood Sacrifice trades 1d4 Slashing damage to the wielder for the same bonus. | A hit grants +1d4 to your attack rolls and saves until the end of your next turn; Blood Sacrifice costs you 1d4 firearm damage for the same bonus. |
| [Ritual Dagger of Shar](https://bg3.wiki/wiki/Ritual_Dagger_of_Shar) | +1 | Deals +1d4 Necrotic damage. | Shots deal +1d4 Necrotic damage. |
| [Shining Staver-of-Skulls](https://bg3.wiki/wiki/Shining_Staver-of-Skulls) | +1 | Deals +1d4 Radiant damage and sheds light in a 25-foot radius. | Shots deal +1d4 Radiant damage; while equipped, shed light in a 25-foot radius. |
| [Shortsword of First Blood](https://bg3.wiki/wiki/Shortsword_of_First_Blood) | None | Deals +1d8 Piercing damage to targets at full HP. | Shots deal +1d8 firearm damage to targets at full HP. |
| [Skybreaker](https://bg3.wiki/wiki/Skybreaker) | +1 | Can cast Searing Smite at level 1 once per long rest. | Once per long rest, a hit can trigger Searing Smite (level 1). |
| [Speedy Reply](https://bg3.wiki/wiki/Speedy_Reply) | None | Hitting a target grants 2 turns of Momentum. | Hitting a target grants you 2 turns of Momentum. |
| [Sword of Screams](https://bg3.wiki/wiki/Sword_of_Screams) | None | Deals +1d4 Psychic damage. | Shots deal +1d4 Psychic damage. |
| [Sylvan Scimitar](https://bg3.wiki/wiki/Sylvan_Scimitar) | +1 | Uses the wielder's spellcasting modifier instead of Dexterity for attack rolls. | Use your spellcasting ability modifier instead of Dexterity for firearm attack rolls. |
| [Syringe (+1)](https://bg3.wiki/wiki/Syringe_(%2B1)) | +1 | Inject Nostrum adds 1d6 Necrotic damage and can Poison the target on a failed Dexterity save. | Nostrum Shot: once per short rest, deal firearm damage plus your Proficiency Bonus and 1d6 Necrotic; on a failed Dexterity save, Poison the target for 2 turns. |
| [Trepan (+1)](https://bg3.wiki/wiki/Trepan_(%2B1)) | +1 | Trephination adds 1d6 Necrotic damage and can knock the target Prone on a failed Dexterity save. | Trephination Shot: once per short rest, deal firearm damage plus your Proficiency Bonus and 1d6 Necrotic; on a failed Dexterity save, knock the target Prone for 2 turns. |
| [Worgfang](https://bg3.wiki/wiki/Worgfang) | None | Goblins have Disadvantage on attack rolls against the wielder. | Goblins have Disadvantage on attack rolls against you while this firearm is equipped. |
| [Wulbren's Hammer](https://bg3.wiki/wiki/Wulbren's_Hammer) | +1 | Deals 2d4 Force damage against objects and world objects. | Deals 2d4 Force damage to objects and world objects. |
| [Bow of Awareness](https://bg3.wiki/wiki/Bow_of_Awareness) | +1 | Grants +1 to Initiative rolls. | Gain +1 to Initiative while equipped. |
| [Hunting Shortbow](https://bg3.wiki/wiki/Hunting_Shortbow) | +1 | Advantage against Monstrosities; can cast Hunter's Mark at level 1 once per long rest. | Gain Advantage on attacks against Monstrosities; once per long rest, mark a target with Hunter's Mark (level 1). |

**Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Adamantine Scimitar](https://bg3.wiki/wiki/Adamantine_Scimitar) | +1 | Adamantine hits against objects are critical hits; the scimitar ignores Slashing resistance. | Hits against objects are critical hits; shots ignore resistance to firearm damage. |
| [Ambusher](https://bg3.wiki/wiki/Ambusher) | +1 | +1 Initiative, Advantage on Perception checks, and +1d6 Necrotic damage against creatures that have not taken a turn yet. | Gain +1 Initiative and Advantage on Perception checks; your first hit against a creature that has not taken a turn deals +1d6 Necrotic damage. |
| [Cold Snap](https://bg3.wiki/wiki/Cold_Snap) | None | Deals 1d4 cold damage. Chilling Counter can inflict Chilled on a creature that misses an attack; grants +1 AC while off-hand. | While equipped, deals an extra 1d4 cold damage; when a creature misses you, your next hit can inflict Chilled; gain +1 AC while the firearm is held in your off hand. |
| [Dolor Amarus](https://bg3.wiki/wiki/Dolor_Amarus) | +2 | Critical hits deal 7 additional damage. | Critical hits deal 7 additional firearm damage. |
| [Dread Iron Dagger](https://bg3.wiki/wiki/Dread_Iron_Dagger) | +1 | Deals +1d6 Necrotic damage while its wielder is hidden. | Shots deal +1d6 Necrotic damage while you are Hidden. |
| [Fleshrender](https://bg3.wiki/wiki/Fleshrender) | +2 | Part the Flesh weapon action can prevent the target from healing. | Part the Flesh Shot can prevent a hit target from healing. |
| [Gleamdance Dagger](https://bg3.wiki/wiki/Gleamdance_Dagger) | +2 | Sheds light; grants +1 AC when wielded off-hand. | Shed light while equipped; gain +1 AC while held in your off hand. |
| [Harmonic Dueller](https://bg3.wiki/wiki/Harmonic_Dueller) | +1 | Mellow Harmony: pass a DC 15 Performance check to add Charisma modifier (minimum 1) to melee weapon damage for a duration. | After passing a DC 15 Performance check, add your Charisma modifier (minimum 1) to firearm damage for the duration. |
| [Ne'er Misser](https://bg3.wiki/wiki/Ne'er_Misser) | +1 | Deals Force damage; can cast Magic Missile at level 3 once per short rest. | Shots deal Force damage; once per short rest, fire Magic Missile as a level 3 spell. |
| [Salty Scimitar (rrr)](https://bg3.wiki/wiki/Salty_Scimitar(rrr)) | +2 | Can cast Command at level 1 once per long rest. | Can cast Command at level 1 once per long rest. |
| [Sickle of BOOOAL](https://bg3.wiki/wiki/Sickle_of_BOOOAL) | None | Deals 2d4 Slashing damage; grants Advantage against Bleeding creatures while Kuo-toa worship BOOOAL. | Shots deal 2d4 firearm damage; gain Advantage against Bleeding targets while BOOOAL is worshipped. |
| [Slicing Shortsword](https://bg3.wiki/wiki/Slicing_Shortsword) | +1 | Attacks made with Advantage inflict Bleeding. | Hits made with Advantage can inflict Bleeding. |
| [Sussur Dagger](https://bg3.wiki/wiki/Sussur_Dagger) | +1 | Hits can Silence targets that fail a DC 12 Constitution save. | Hits can Silence targets that fail a DC 12 Constitution save. |
| [Sussur Sickle](https://bg3.wiki/wiki/Sussur_Sickle) | +1 | Hits can Silence targets that fail a DC 12 Constitution save. | Hits can Silence targets that fail a DC 12 Constitution save. |
| [Sword of Clutching Umbra](https://bg3.wiki/wiki/Sword_of_Clutching_Umbra) | +1 | Shadowsoaked Blow adds proficiency bonus and 1d6 Psychic damage without breaking concealment. | Shadowsoaked Shot adds your proficiency bonus and 1d6 Psychic damage without breaking concealment. |
| [The Baneful](https://bg3.wiki/wiki/The_Baneful) | +1 | Favoured Weapon adds +1 to attack and damage; hits can inflict Bane. | Favoured Firearm grants +1 to attack and damage rolls; hits can inflict Bane. |
| [Wavemother's Sickle](https://bg3.wiki/wiki/Wavemother's_Sickle) | +2 | Deals +1d4 Cold damage and has Advantage against Wet creatures. | Shots deal +1d4 Cold damage and have Advantage against Wet targets. |
| [Larethian's Wrath](https://bg3.wiki/wiki/Larethian's_Wrath) | +1 | Razor Gale weapon action damages all enemies in range. | Razor Gale: fire a ranged shot that damages all creatures in a 20-foot line. |
| [Phalar Aluve](https://bg3.wiki/wiki/Phalar_Aluve) | +1 | +1 Performance; Phalar Aluve: Melody lets the wielder Sing or Shriek once per short rest. | Once per short rest, Sing to grant nearby allies +1d4 to attack rolls, or Shriek to deal 1d4 Thunder damage to nearby enemies and weaken them. |
| [Bow of the Banshee](https://bg3.wiki/wiki/Bow_of_the_Banshee) | +1 | Hits can Frighten (DC 12 Wisdom); gains +1d4 to attack and damage against Frightened targets. | Hits can Frighten (DC 12 Wisdom); gain +1d4 to firearm attack and damage rolls against Frightened targets. |
| [Darkfire Shortbow](https://bg3.wiki/wiki/Darkfire_Shortbow) | +2 | Grants Fire and Cold resistance; can cast Haste at level 3 once per long rest. | Gain Fire and Cold resistance; cast Haste (level 3) once per long rest. |
| [Least Expected](https://bg3.wiki/wiki/Least_Expected) | +2 | While obscured, +1d4 to ranged attacks; Blinding Shot can Blind a target. | While Obscured, gain +1d4 to firearm attack rolls; Blinding Shot can Blind a target. |
| [Vicious Shortbow](https://bg3.wiki/wiki/Vicious_Shortbow) | +2 | Critical hits deal 7 additional damage. | Critical hits deal 7 additional firearm damage. |

**Very Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Hellfire Hand Crossbow](https://bg3.wiki/wiki/Hellfire_Hand_Crossbow) | +2 | Can Burn targets when attacking from Hide or Invisible; Scorching Ray Shot casts level 3 Scorching Ray once per short rest. | Hits made from Hide or while Invisible can Burn targets; once per short rest, fire Scorching Ray (level 3). |
| [Infernal Rapier](https://bg3.wiki/wiki/Infernal_Rapier) | +2 | +1 spell save DC; uses spellcasting modifier for attacks; can summon a Cambion at level 6 once per long rest. | Gain +1 spell save DC; use your spellcasting ability modifier for firearm attack rolls; summon a Cambion (level 6) once per long rest. |
| [Justiciar's Scimitar](https://bg3.wiki/wiki/Justiciar's_Scimitar) | +2 | Attacks with Advantage can Blind; Advantage against obscured targets; Shadowsoaked Blow adds proficiency bonus and 1d6 Psychic damage without breaking concealment. | Hits made with Advantage can Blind; gain Advantage against Obscured targets; Shadowsoaked Shot adds your proficiency bonus and 1d6 Psychic damage without breaking concealment. |
| [Knife of the Undermountain King](https://bg3.wiki/wiki/Knife_of_the_Undermountain_King) | +2 | Lowers critical-hit threshold by 1, rerolls damage dice of 2 or less, and grants Advantage against obscured targets. | Critical hit threshold is reduced by 1; reroll firearm damage dice of 2 or less and gain Advantage against Obscured targets. |
| [Pelorsun Blade](https://bg3.wiki/wiki/Pelorsun_Blade) | +1 | Deals +1d4 Radiant damage and grants Advantage against Undead. | Shots deal +1d4 Radiant damage and gain Advantage against Undead. |
| [Rhapsody](https://bg3.wiki/wiki/Rhapsody) | +1 | Kills stack +1 to attacks, damage, and spell save DC up to +3; hidden attacks can cause Bleeding; Scarlet Feast consumes 3 stacks. | Kills grant up to +3 to attack rolls, damage and spell save DC; Hidden hits can inflict Bleeding; consume all 3 stacks to empower a shot. |
| [Stillmaker](https://bg3.wiki/wiki/Stillmaker) | +2 | Can cast Hold Person at level 3 once per long rest. | Once per long rest, fire Hold Person (level 3) at a target. |
| [Sword of Life Stealing](https://bg3.wiki/wiki/Sword_of_Life_Stealing) | +2 | Critical hits deal 10 Necrotic damage and grant 10 temporary HP against non-Construct, non-Undead targets. | Critical hits deal 10 additional Necrotic damage and grant 10 temporary HP against non-Construct, non-Undead targets. |
| [The Dancing Breeze](https://bg3.wiki/wiki/The_Dancing_Breeze) | +2 | Whirlwind Attack strikes all nearby foes as a short-rest action. | Whirlwind Shot sweeps a 20-foot cone, hitting multiple creatures; once per short rest. |
| [Blightbringer](https://bg3.wiki/wiki/Blightbringer) | +1 | +1d4 to attack and damage against Gnomes and Dwarves; critical hits Slow the target. | Gain +1d4 to attack and damage against Gnomes and Dwarves; critical hits can Slow the target. |

</details>

<details>
<summary>Musket-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Bonesaw (+1)](https://bg3.wiki/wiki/Bonesaw_(%2B1)) | +1 | Incise Ligaments weapon action can Slow the target. | Incise Ligaments Shot can Slow the target; damage uses the firearm's base damage type. |
| [The Watcher's Guide](https://bg3.wiki/wiki/The_Watcher's_Guide) | None | A missed attack grants True Strike against that target on the next attack. | A missed attack grants True Strike against that target on your next attack. |
| [Corellon's Grace](https://bg3.wiki/wiki/Corellon's_Grace) | None | Grants +1 to unarmed attack rolls and damage, and +2 to saves while the wielder wears no armour. | While wearing no armour, gain +1 to firearm attack rolls and damage and +2 to saving throws. |
| [Faithbreaker](https://bg3.wiki/wiki/Faithbreaker) | +1 | Absolute Power weapon action adds 1d6 Force damage and can push the target. | Absolute Power Shot deals +1d6 Force damage and can push the target. |
| [Intransigent Warhammer](https://bg3.wiki/wiki/Intransigent_Warhammer) | None | Killing a target or landing a critical hit can knock nearby creatures Prone. | A kill or critical hit can knock creatures nearby the target Prone. |
| [Jagged Spear](https://bg3.wiki/wiki/Jagged_Spear) | None | Tortured targets may have Disadvantage on Constitution saves. | Tortured targets have Disadvantage on Constitution saves against your shots. |
| [Melf's First Staff](https://bg3.wiki/wiki/Melf's_First_Staff) | +1 | Grants +1 to spell attack rolls and spell save DC; can cast Melf's Acid Arrow at level 2 once per long rest. | Gain +1 to spell attack rolls and spell save DC; cast Melf's Acid Arrow (level 2) once per long rest. |
| [Nature's Snare](https://bg3.wiki/wiki/Nature's_Snare) | None | Hits can Ensnare targets that are not Plants or Beasts. | Hits can Ensnare targets that are not Plants or Beasts. |
| [Rain Dancer](https://bg3.wiki/wiki/Rain_Dancer) | None | Can cast Create Water at level 1 once per short rest. | Cast Create Water (level 1) once per short rest. |
| [Staff of a Mumbling Wizard](https://bg3.wiki/wiki/Staff_of_a_Mumbling_Wizard) | None | Can cast Fire Bolt at will; has a 1-in-20 chance to cause a Fireball explosion. | Fire Bolt at will; each shot has a 1-in-20 chance to trigger a Fireball explosion. |
| [Staff of Arcane Blessing](https://bg3.wiki/wiki/Staff_of_Arcane_Blessing) | None | Can cast Bless at level 1 once per long rest; blessed creatures also gain +1d4 to spell attack rolls. | Cast Bless (level 1) once per long rest; blessed allies also gain +1d4 to spell attack rolls. |
| [Staff of Crones](https://bg3.wiki/wiki/Staff_of_Crones) | None | Can cast Ray of Sickness at level 1 once per short rest. | Fire Ray of Sickness (level 1) once per short rest. |
| [Witchbreaker](https://bg3.wiki/wiki/Witchbreaker) | +1 | Advantage on attacks against concentrating targets; Hush You weapon action can Silence a target. | Gain Advantage on attacks against concentrating targets; Hush You Shot can Silence a target. |
| [Hellrider Longbow](https://bg3.wiki/wiki/Hellrider_Longbow) | +1 | Grants +3 Initiative and Advantage on Perception checks; once per turn, a hit can inflict Faerie Fire. | Gain +3 Initiative and Advantage on Perception checks; once per turn, a hit can inflict Faerie Fire. |
| [Spellthief](https://bg3.wiki/wiki/Spellthief) | None | A critical hit restores a level 1 spell slot once per short rest. | A critical hit restores one level 1 spell slot once per short rest. |

**Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Despair of Athkatla](https://bg3.wiki/wiki/Despair_of_Athkatla) | +2 | Grants +1 to spell attack rolls and spell save DC. | Gain +1 to spell attack rolls and spell save DC. |
| [Adamantine Longsword](https://bg3.wiki/wiki/Adamantine_Longsword) | +1 | Adamantine hits against objects are critical hits; the sword ignores Slashing resistance. | Hits against objects are critical hits; shots ignore resistance to firearm damage. |
| [Bigboy's Chew Toy](https://bg3.wiki/wiki/Bigboy's_Chew_Toy) | +1 | Can cast Enlarge on the wielder once per long rest. | Cast Enlarge on yourself once per long rest. |
| [Blackguard's Sword](https://bg3.wiki/wiki/Blackguard's_Sword) | +2 | Dazing Smite can Daze a target hit by a Smite spell if it fails a Constitution save. | Dazing Smite Shot can Daze a creature hit by a Smite spell if it fails a Constitution save. |
| [Blade of Oppressed Souls](https://bg3.wiki/wiki/Blade_of_Oppressed_Souls) | +1 | Deals +1d4 Psychic damage; Crowning Strike can inflict Crown of Madness. | Shots deal +1d4 Psychic damage; Crowning Shot can inflict Crown of Madness. |
| [Cacophony](https://bg3.wiki/wiki/Cacophony) | +1 | Can cast Thunderous Smite at level 1 once per short rest. | Once per short rest, fire a Thunderous Smite (level 1) round. |
| [Caitiff Staff](https://bg3.wiki/wiki/Caitiff_Staff) | +2 | Grants +1 to spell attack rolls and spell save DC; restores one expended Warlock spell slot once per long rest. | Gain +1 to spell attack rolls and spell save DC; restore one expended Warlock spell slot once per long rest. |
| [Charge-Bound Warhammer](https://bg3.wiki/wiki/Charge-Bound_Warhammer) | +1 | When bound to an Eldritch Knight or used as a Pact/Hexed weapon, gains +1 attack and damage and deals +1d6 Lightning damage. | When bound or Pact/Hexed, gain +1 to attack and damage and deal +1d6 Lightning damage. |
| [Clown Hammer](https://bg3.wiki/wiki/Clown_Hammer) | +2 | On a critical hit, the wielder and target must pass Wisdom saves or fall down laughing. | On a critical hit, you and the target must pass Wisdom saves or fall down laughing. |
| [Creation's Echo](https://bg3.wiki/wiki/Creation's_Echo) | None | Dealing Acid, Fire, Lightning, Radiant, or Necrotic damage grants resistance to that type for 2 turns. | Dealing Acid, Fire, Lightning, Radiant or Necrotic damage grants resistance to that type for 2 turns. |
| [Gold Wyrmling Staff](https://bg3.wiki/wiki/Gold_Wyrmling_Staff) | +1 | Deals +1d4 Fire damage and can cast Fire Bolt at will. | Shots deal +1d4 Fire damage; Fire Bolt at will. |
| [Hammer of the Just](https://bg3.wiki/wiki/Hammer_of_the_Just) | +2 | Deals +1d4 Radiant damage and +1d6 Bludgeoning damage to Fiends and Undead; can cast Detect Thoughts at level 2 once per long rest. | Shots deal +1d4 Radiant damage and +1d6 firearm damage to Fiends and Undead; cast Detect Thoughts (level 2) once per long rest. |
| [Harper Sacredstriker](https://bg3.wiki/wiki/Harper_Sacredstriker) | +1 | Can cast Spiritual Weapon at level 6 once per long rest. | Once per long rest, summon a level 6 Spiritual Weapon that attacks your target. |
| [Hollow's Staff](https://bg3.wiki/wiki/Hollow's_Staff) | +1 | Deals +1d4 Necrotic damage; targets have Disadvantage on saves against the wielder's Necromancy spells; can cast Arms of Hadar at level 3 once per long rest. | Shots deal +1d4 Necrotic damage; Necromancy targets have Disadvantage on saves against your spells; cast Arms of Hadar (level 3) once per long rest. |
| [Ketheric's Warhammer](https://bg3.wiki/wiki/Ketheric's_Warhammer) | +1 | Deals +1d4 Psychic damage. | Shots deal +1d4 Psychic damage. |
| [Pale Oak](https://bg3.wiki/wiki/Pale_Oak) | None | Faithwarden's Vines cannot Entangle the wielder; can cast Faithwarden's Vines at level 1 once per long rest. | You cannot be Entangled by Faithwarden's Vines; cast Faithwarden's Vines (level 1) once per long rest. |
| [The Sparky Points](https://bg3.wiki/wiki/The_Sparky_Points) | None | Dealing damage with the trident grants 2 Lightning Charges. | Dealing firearm damage grants 2 Lightning Charges. |
| [The Spellsparkler](https://bg3.wiki/wiki/The_Spellsparkler) | None | Dealing damage with a spell or cantrip grants 2 Lightning Charges. | Dealing spell or cantrip damage grants 2 Lightning Charges. |
| [Staff of Interruption](https://bg3.wiki/wiki/Staff_of_Interruption) | +2 | Can cast Counterspell at level 5 once per long rest. | Cast Counterspell (level 5) once per long rest. |
| [Staff of the Emperor](https://bg3.wiki/wiki/Staff_of_the_Emperor) | +2 | Grants +1 to spell attack rolls and spell save DC; succeeding on a save can force the source to save or be Stunned for 1 turn. | Gain +1 to spell attack rolls and spell save DC; succeeding on a save can force the source to save or be Stunned for 1 turn. |
| [Sword of the Emperor](https://bg3.wiki/wiki/Sword_of_the_Emperor) | +2 | Deals +1d4 damage to shapeshifters/polymorphed creatures and grants +2 to saves against spells. | Deal +1d4 firearm damage to shapeshifters or polymorphed creatures; gain +2 to saves against spells. |
| [Vicious Battleaxe](https://bg3.wiki/wiki/Vicious_Battleaxe) | +2 | Critical hits deal 7 additional damage. | Critical hits deal 7 additional firearm damage. |
| [The Joltshooter](https://bg3.wiki/wiki/The_Joltshooter) | None | Dealing damage with the longbow grants 2 Lightning Charges. | Dealing firearm damage grants 2 Lightning Charges. |
| [Titanstring Bow](https://bg3.wiki/wiki/Titanstring_Bow) | +1 | Adds the wielder's Strength modifier to damage; Pushing Attack can push a target 15 feet. | Add your Strength modifier to firearm damage; Pushing Shot can push a target 15 feet. |

**Very Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Dwarven Thrower](https://bg3.wiki/wiki/Dwarven_Thrower) | +2 | Returns when thrown; a dwarf deals +1d8 Bludgeoning damage on a throw, or +2d8 against Large or larger targets. | Dwarves deal +1d8 firearm damage with shots, or +2d8 against Large or larger targets; the returning-throw effect does not apply to firearms. |
| [Incandescent Staff](https://bg3.wiki/wiki/Incandescent_Staff) | None | +1 ranged spell attack, Fire resistance, Fire Bolt at will, and Fireball at level 3 once per long rest. | Gain +1 ranged spell attack, Fire resistance and Fire Bolt at will; cast Fireball (level 3) once per long rest. |
| [Mourning Frost](https://bg3.wiki/wiki/Mourning_Frost) | +1 | Deals +1d4 Cold damage; Cold damage gains +1, and Cold spells can Chill targets. | Shots deal +1d4 Cold damage; Cold damage gains +1, and Cold spells can Chill targets. |
| [Staff of Cherished Necromancy](https://bg3.wiki/wiki/Staff_of_Cherished_Necromancy) | +2 | Deals +1d4 Necrotic damage; Necromancy targets have save Disadvantage; spell kills grant Life Essence until long rest. | Shots deal +1d4 Necrotic damage; Necromancy targets have Disadvantage on saves; spell kills grant Life Essence until long rest. |
| [Staff of Spellpower](https://bg3.wiki/wiki/Staff_of_Spellpower) | +2 | +1 spell attack and spell save DC; Arcane Battery makes the next spell cost no slot. | Gain +1 spell attack and spell save DC; Arcane Battery makes your next spell cost no slot. |
| [Staff of the Ram](https://bg3.wiki/wiki/Staff_of_the_Ram) | +2 | Once per turn, a hit can push a target and Stun it, except Dragons and Huge creatures. | Once per turn, a hit can push a target and Stun it, except Dragons and Huge creatures. |
| [Trident of the Waves](https://bg3.wiki/wiki/Trident_of_the_Waves) | +1 | Hits make the target Wet and create a water surface. | Hits make the target Wet and create a water surface. |
| [Voss' Silver Sword](https://bg3.wiki/wiki/Voss'_Silver_Sword) | +2 | +1d4 to attack and damage against Githyanki, Aberrations, Fiends, and Elementals; can cast Wrathful Smite at level 1 once per short rest. | Gain +1d4 to firearm attack and damage rolls against Githyanki, Aberrations, Fiends, and Elementals; fire a Wrathful Smite Shot (firearm damage +1d6 Psychic, can Frighten) once per short rest. |
| [Woe](https://bg3.wiki/wiki/Woe) | +2 | +1 spell attack and spell save DC; failed saves against spells restore 1d4 HP; can cast Blight at level 4 once per long rest. | Gain +1 spell attack and spell save DC; failed saves against your spells restore 1d4 HP; cast Blight (level 4) once per long rest. |
| [The Dead Shot](https://bg3.wiki/wiki/The_Dead_Shot) | +2 | Lowers the critical-hit threshold by 1 and doubles proficiency bonus on ranged attacks with this bow. | Critical hit threshold is reduced by 1; when you do not have Disadvantage, firearm attacks gain an additional Proficiency Bonus to attack rolls. |

</details>

<details>
<summary>Blunderbuss-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Deep Delver](https://bg3.wiki/wiki/Deep_Delver) | None | Hits inflict Shattered. | Hits inflict Shattered. |
| [Hoppy](https://bg3.wiki/wiki/Hoppy) | +1 | Revitalising Strike weapon action damages a target and heals the wielder. | Revitalising Shot damages the target and heals you; once per short rest. |
| [Infernal Mace (Uncommon)](https://bg3.wiki/wiki/Infernal_Mace_(Uncommon)) | +1 | Deals 3 Poison damage on hit and can Poison the target. | Shots deal 3 Poison damage and can Poison the target. |
| [Xyanyde](https://bg3.wiki/wiki/Xyanyde) | +1 | Once per short rest, a missed attack can inflict Faerie Fire for 2 turns. | Once per short rest, a missed shot can inflict Faerie Fire for 2 turns. |
| [Argument Solver](https://bg3.wiki/wiki/Argument_Solver) | +1 | Poison Mist weapon action adds Poison damage equal to proficiency bonus and creates a Poison cloud. | Poison Mist Scattershot: blast a 15-foot cone, adding Poison damage equal to your proficiency bonus and leaving a Poison cloud. |
| [Doom Hammer](https://bg3.wiki/wiki/Doom_Hammer) | None | Hits inflict Bone Chilled, preventing HP recovery; undead targets also have Disadvantage on attacks. | Hits inflict Bone Chilled, preventing HP recovery; Undead targets also have Disadvantage on attacks. |
| [Everburn Blade](https://bg3.wiki/wiki/Everburn_Blade) | None | Deals an additional 1d4 Fire damage. | Shots deal an additional 1d4 Fire damage. |
| [Exterminator's Axe](https://bg3.wiki/wiki/Exterminator's_Axe) | None | Deals +1d6 Fire damage to Plants, Myconids, and Small creatures. | Shots deal +1d6 Fire damage to Plants, Myconids and Small creatures. |
| [Githyanki Greatsword (Psionic)](https://bg3.wiki/wiki/Githyanki_Greatsword_(Psionic)) | +1 | When wielded by a Githyanki, deals +1d4 Psychic damage. | When wielded by a Githyanki, shots deal +1d4 Psychic damage. |
| [Hamarhraft](https://bg3.wiki/wiki/Hamarhraft) | None | Landing from a jump deals 1d4 Thunder damage in a 10-foot radius. | Landing from a jump triggers a 10-foot Scattershot that deals 1d4 Thunder damage. |
| [Light of Creation](https://bg3.wiki/wiki/Light_of_Creation) | +1 | Deals +1d6 Lightning damage; each successful attack has a chance to Stun the wielder unless they are a Construct. | Shots deal +1d6 Lightning damage; each hit has a chance to Stun you unless you are a Construct. |
| [Svartlebee's Woundseeker](https://bg3.wiki/wiki/Svartlebee's_Woundseeker) | +1 | Grants +1d4 to attack rolls against creatures that have already taken damage. | Gain +1d4 to attack rolls against creatures that have already taken damage. |
| [Sword of Justice](https://bg3.wiki/wiki/Sword_of_Justice) | +1 | Can cast Tyr's Protection once per short rest. | Cast Tyr's Protection once per short rest. |
| [The Skinburster](https://bg3.wiki/wiki/The_Skinburster) | +1 | Dealing melee damage grants 2 turns of Force Conduit. | Dealing firearm damage grants 2 turns of Force Conduit. |
| [The Undead Bane](https://bg3.wiki/wiki/The_Undead_Bane) | +1 | Deals +1d6 Slashing damage to Fiends and Undead; Profane Scourge adds proficiency bonus damage and can add 2d6 Slashing damage and Bane against those targets. | Deal +1d6 firearm damage to Fiends and Undead; Profane Scourge adds your proficiency bonus and can add 2d6 firearm damage and Bane against those targets. |
| [Very Heavy Greataxe](https://bg3.wiki/wiki/Very_Heavy_Greataxe) | +1 | Gargantuan Cleave attacks multiple targets for +1d6 Slashing damage, but leaves the wielder Off Balance. | Gargantuan Scattershot: blast a 20-foot cone, hitting multiple targets for +1d6 firearm damage; leaves you Off Balance. |
| [Crossbow of Arcane Force](https://bg3.wiki/wiki/Crossbow_of_Arcane_Force) | +1 | Once per short rest, infuses bolts as a bonus action; ranged weapon attacks deal +1d4 Force damage for the turn. | Once per short rest, infuse rounds as a bonus action; firearm attacks deal +1d4 Force damage for the turn. |
| [Gandrel's Aspiration](https://bg3.wiki/wiki/Gandrel's_Aspiration) | +1 | Advantage against Monstrosities; Sacred Munitions can Turn undead for the rest of the turn. | Gain Advantage against Monstrosities; Sacred Munitions can Turn Undead for the rest of the turn. |

**Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Adamantine Mace](https://bg3.wiki/wiki/Adamantine_Mace) | +1 | Adamantine hits against objects are critical hits; the mace ignores Bludgeoning resistance. | Hits against objects are critical hits; shots ignore resistance to the firearm's damage type. |
| [Corrosive Flail](https://bg3.wiki/wiki/Corrosive_Flail) | +1 | Corrosive Strike adds Acid damage equal to proficiency bonus and creates acid that reduces target AC by 2. | Corrosive Shot adds Acid damage equal to your proficiency bonus and creates acid that reduces target AC by 2. |
| [Defender Flail](https://bg3.wiki/wiki/Defender_Flail) | +1 | Reduces incoming Bludgeoning, Piercing, and Slashing damage by 1; grants +1 AC. | While equipped, reduce incoming damage of the firearm's type by 1 and gain +1 AC. |
| [Flail of Ages](https://bg3.wiki/wiki/Flail_of_Ages) | +1 | Adds an elemental condition based on its damage type; can cast Elemental Age at level 3 once per long rest. | Shots add an elemental condition matching their damage type; cast Elemental Age (level 3) once per long rest. |
| [Infernal Mace](https://bg3.wiki/wiki/Infernal_Mace) | +2 | Deals 3 Poison damage on hit and can Poison the target. | Shots deal 3 Poison damage and can Poison the target. |
| [Ravengard's Scourger](https://bg3.wiki/wiki/Ravengard's_Scourger) | +2 | Can use Commander's Strike to direct an ally to make a weapon attack as a reaction. | Commander's Shot lets you direct an ally to make a weapon attack as a reaction. |
| [Shattered Flail](https://bg3.wiki/wiki/Shattered_Flail) | +2 | Hits heal the wielder for 1d6 HP; failing to keep hitting each turn can cause Madness. | Hits restore 1d6 HP; failing to hit a creature on each turn can cause Madness. |
| [Twist of Fortune](https://bg3.wiki/wiki/Twist_of_Fortune) | +1 | Reroll weapon damage dice of 2 or less; Blood Money adds damage based on the target's gold and consumes that gold. | Reroll firearm damage dice of 2 or less; Blood Money adds damage based on the target's gold and consumes that gold. |
| [Blooded Greataxe](https://bg3.wiki/wiki/Blooded_Greataxe) | +1 | Deals +1d4 Slashing damage while the wielder is at or below half HP. | Shots deal +1d4 firearm damage while you are at or below half HP. |
| [Breaching Pikestaff](https://bg3.wiki/wiki/Breaching_Pikestaff) | +2 | Deals an additional 1d4 Force damage. | Shots deal an additional 1d4 Force damage. |
| [Corpsegrinder](https://bg3.wiki/wiki/Corpsegrinder) | +2 | Deals +1d4 Thunder damage; Grand Slam adds Thunder damage equal to proficiency bonus and can push nearby foes. | Shots deal +1d4 Thunder damage; Grand Slam Scattershot blasts a 15-foot radius, adding Thunder damage equal to your proficiency bonus and pushing nearby foes. |
| [Defender Greataxe](https://bg3.wiki/wiki/Defender_Greataxe) | +2 | Can reduce its Enchantment by 1 on the first attack each round for +1 AC and +1 to saves. | Once per round, reduce the firearm's Enchantment by 1 on your first attack to gain +1 AC and +1 to saves. |
| [Drakethroat Glaive](https://bg3.wiki/wiki/Drakethroat_Glaive) | +2 | Draconic Elemental Weapon can imbue a weapon with an element; improves Dragonborn breath save difficulty. | Draconic Elemental Weapon can imbue the firearm with an element; improves Dragonborn breath save difficulty. |
| [Harmonium Halberd](https://bg3.wiki/wiki/Harmonium_Halberd) | +1 | Increases Strength by 2 (maximum 23), but decreases Intelligence and Wisdom by 1. | Increase Strength by 2 (maximum 23), but decrease Intelligence and Wisdom by 1 while equipped. |
| [Hellbeard Halberd](https://bg3.wiki/wiki/Hellbeard_Halberd) | +2 | Deals 6 Poison damage on hit; target can be Poisoned (DC 12 Constitution save). | Shots deal 6 Poison damage; target can be Poisoned (DC 12 Constitution save). |
| [Jorgoral's Greatsword](https://bg3.wiki/wiki/Jorgoral's_Greatsword) | +1 | Colossal Onslaught attacks creatures in a line and adds Slashing damage equal to proficiency bonus. | Colossal Onslaught fires through creatures in a 20-foot line, dealing firearm damage and bonus damage equal to your proficiency bonus. |
| [Monster Slayer Glaive](https://bg3.wiki/wiki/Monster_Slayer_Glaive) | +1 | Deals +1d4 damage to Monstrosities; increases jump distance by 5 feet. | Deal +1d4 firearm damage to Monstrosities; increase jump distance by 5 feet. |
| [Moonlight Glaive](https://bg3.wiki/wiki/Moonlight_Glaive) | +2 | Deals +1d4 Radiant damage and sheds light; Moonlight Butterflies grants Advantage against its target. | Shots deal +1d4 Radiant damage and shed light; Moonlight Butterflies grants Advantage against its target. |
| [Punch-Drunk Bastard](https://bg3.wiki/wiki/Punch-Drunk_Bastard) | +1 | While Drunk, grants Advantage on attacks and melee hits deal 1d4 Thunder damage in a 10-foot radius. | While Drunk, gain Advantage on firearm attacks and shots deal 1d4 Thunder damage in a 15-foot Scattershot cone. |
| [Rat Bat](https://bg3.wiki/wiki/Rat_Bat) | +1 | Deals +1d6 Piercing damage and grants Advantage on attacks against Beasts. | Shots deal +1d6 firearm damage and grant Advantage against Beasts. |
| [Soulbreaker Greatsword](https://bg3.wiki/wiki/Soulbreaker_Greatsword) | +1 | Githyanki gain +1d4 Psychic damage; +2 Initiative; Soulbreaker adds proficiency-bonus Psychic damage and can Stun. | Githyanki shots deal +1d4 Psychic damage; gain +2 Initiative; Soulbreaker Shot adds proficiency-bonus Psychic damage and can Stun. |
| [Sorrow](https://bg3.wiki/wiki/Sorrow) | +1 | Sorrowful Lash cantrip is available as a bonus action. | Sorrowful Lash becomes a bonus-action shot that lashes a target. |
| [Sussur Greatsword](https://bg3.wiki/wiki/Sussur_Greatsword) | +1 | Hits can Silence targets that fail a DC 12 Constitution save. | Hits can Silence targets that fail a DC 12 Constitution save. |
| [Unseen Menace](https://bg3.wiki/wiki/Unseen_Menace) | +1 | Invisible while equipped and grants Advantage on attacks; a miss removes invisibility for 2 rounds; critical hit threshold is 19. | Invisible while equipped and gain Advantage on attacks; a miss removes invisibility for 2 rounds; critical hit threshold is 19. |
| [Giantbreaker](https://bg3.wiki/wiki/Giantbreaker) | +1 | Heavy Hitter can make targets Reeling for 2 turns. | Heavy Hitter rounds can make targets Reeling for 2 turns. |
| [Harold](https://bg3.wiki/wiki/Harold) | +1 | Ranged weapon hits can Bane a target for 2 turns on a failed Charisma save. | Ranged hits can Bane a target for 2 turns on a failed Charisma save. |
| [The Long Arm of the Gur](https://bg3.wiki/wiki/The_Long_Arm_of_the_Gur) | +2 | Against Undead, gains +1d4 to attack and damage rolls. | Against Undead, gain +1d4 to attack and damage rolls. |

**Very Rare:**

| Weapon | Enchantment | Special ability | Firearm Ability |
| --- | --- | --- | --- |
| [Handmaiden's Mace](https://bg3.wiki/wiki/Handmaiden's_Mace) | +2 | Sets Strength to 18, deals +1d6 Poison damage, and can Poison targets. | Strength becomes 18; shots deal +1d6 Poison damage and can Poison targets. |
| [The Sacred Star](https://bg3.wiki/wiki/The_Sacred_Star) | +2 | Deals +1d4 Radiant damage and applies Radiating Orb; can Turn Undead; Dawnburst Strike deals proficiency-bonus Radiant damage and can Blind nearby foes. | Shots deal +1d4 Radiant damage and apply Radiating Orb; can Turn Undead; Dawnburst Scattershot blasts a 15-foot radius, dealing proficiency-bonus Radiant damage and possibly Blinding nearby foes. |
| [Foebreaker](https://bg3.wiki/wiki/Foebreaker) | +2 | Ignores resistance to Bludgeoning damage. | Shots ignore resistance to the firearm's damage type. |
| [Halberd of Vigilance](https://bg3.wiki/wiki/Halberd_of_Vigilance) | +2 | +1 Initiative, Advantage on Perception checks, and Advantage on reaction attacks. | Gain +1 Initiative and Advantage on Perception checks; gain Advantage on firearm reaction attacks. |
| [Hellfire Greataxe](https://bg3.wiki/wiki/Hellfire_Greataxe) | +2 | Deals +1d6 Fire damage; damage grants Heat; Hellflame Cleave is a short-rest action. | Shots deal +1d6 Fire damage and grant Heat; Hellflame Scattershot hits multiple targets in a 15-foot cone once per short rest. |
| [Sethan](https://bg3.wiki/wiki/Sethan) | +2 | Can summon a spiritual greataxe; can Reduce a creature, lowering its weapon damage and imposing Strength-check/save Disadvantage. | Summon a spiritual blunderbuss; Reduce a creature, lowering its firearm damage and imposing Disadvantage on Strength checks and saves. |
| [Sword of Chaos](https://bg3.wiki/wiki/Sword_of_Chaos) | +2 | Deals +1d4 Necrotic damage and restores 1d6 HP when it deals damage. | Shots deal +1d4 Necrotic damage and restore 1d6 HP when they deal damage. |
| [Fabricated Arbalest](https://bg3.wiki/wiki/Fabricated_Arbalest) | +2 | Dazzling Ray can Blind creatures in its path; Illuminating Shot can inflict Radiating Orb. | Dazzling Ray fires through a line of creatures and can Blind them; Illuminating Shot can inflict Radiating Orb. |
| [Hellfire Engine Crossbow](https://bg3.wiki/wiki/Hellfire_Engine_Crossbow) | +2 | Can cast Lightning Arrow at level 4 once per long rest and pull a creature 30 feet closer. | Cast Lightning Arrow (level 4) once per long rest; a hit pulls a creature up to 30 feet closer. |

</details>

## Gunslinger

The Gunslinger is a firearm-focused class built around precision, timing, and specialized shots. Gunslingers use **grit points** to fuel trick shots and other combat actions, letting them adapt their attacks to the situation. At level 3, a Gunslinger's maximum becomes 3 grit points; it increases by 1 at levels 7, 11, 15, and 18. Gunslingers regain a spent grit point when they kill a creature by any means or land a firearm critical hit, once per attack (a critical kill, or several kills from one attack, restore only 1 grit). The class has a maximum level of 20. Gunslingers start with 8 + their Constitution modifier hit points and gain 5 + their Constitution modifier hit points per level.

At level 3, Gunslingers choose two grit abilities, then choose one additional ability at levels 5, 9, 13, and 17 (a base Gunslinger feature shared by every subclass). Desperados also choose an extra grit ability at levels 7, 11, 15, and 19, so they gain a grit ability every other level after level 3 (levels 3, 5, 7, 9, 11, 13, 15, 17, and 19). The level 3 and Desperado-only picks offer the Desperado's exclusive abilities alongside the shared ones; the base-class picks at 5, 9, 13, and 17 offer only shared abilities. Desperados increase their maximum grit by 1 every three levels starting at level 6 (levels 6, 9, 12, 15, and 18). Subclasses are selected at level 3, before the level 3 grit abilities, so each subclass's grit pool can be offered. Desperados' exclusive grit abilities join their pool at the levels listed below (the levels of the Desperado's own picks); they're chosen like other grit abilities rather than granted automatically.

### Character Creation

- **Default ability scores:** Strength 10, Dexterity 15 (+2 bonus), Constitution 13, Intelligence 14 (+1 bonus), Wisdom 8, Charisma 12.
- **Saving throw proficiencies:** Dexterity and Constitution.
- **Fighting Style (level 1):** choose one of Archery, Two-Weapon Fighting, Dueling, Close Quarters or Defense. Close Quarters (`GSL_FightingStyle_CloseQuarters`) is custom: +1 to ranged weapon attack rolls, and no Disadvantage on ranged attacks with ammunition weapons (firearms, bows, crossbows and slings) while a hostile creature is within 5 feet.
- **Armour and weapon proficiencies:** Light armour, shields, firearms (via the Slings proficiency group), all bows and crossbows (shortbows, longbows, hand, light and heavy crossbows), and light melee weapons (clubs, daggers, handaxes, light hammers, sickles, scimitars and shortswords).
- **Starting equipment (`EQP_GunslingerClass`):** Leather Armour, a Dagger, Leather Boots and a Light Crossbow, equipped with the ranged weapon set active. The kit also includes two Potions of Healing, a Scroll of Revivify, camp clothes and shoes, a keychain, an alchemy pouch and a camp supplies backpack.
- **Skill proficiencies:** choose 2 from Sleight of Hand, Acrobatics, Athletics, Deception, Insight, Intimidation, Perception, Persuasion, and Stealth. Sleight of Hand and Perception are selected by default.

### Gunslinger Progression

| Level | Gunslinger features | Grit Abilities | Max Grit Points | Misc |
| --- | --- | --- | --- | --- |
| 1 | Start with 8 + Constitution modifier HP; Fighting Style; **Gunslinger's Draw** | - | - |
| 2 | Gain 5 + Constitution modifier HP | - | - | Ability to craft firearms |
| 3 | Gain 5 + Constitution modifier HP; choose a subclass | Choose 2 | 3 |
| 4 | Gain 5 + Constitution modifier HP; **Tinkerer** | - | 3 | Feat |
| 5 | Gain 5 + Constitution modifier HP | Choose 1 | 3 |
| 6 | Gain 5 + Constitution modifier HP; **Second Attack**; **Expertise** (1 skill) | - | 3 |
| 7 | Gain 5 + Constitution modifier HP | - | 4 |
| 8 | Gain 5 + Constitution modifier HP | - | 4 | Feat |
| 9 | Gain 5 + Constitution modifier HP | Choose 1 | 4 |
| 10 | Gain 5 + Constitution modifier HP; **Master Tinkerer** | - | 4 |
| 11 | Gain 5 + Constitution modifier HP | - | 5 |
| 12 | Gain 5 + Constitution modifier HP | - | 5 | Feat |
| 13 | Gain 5 + Constitution modifier HP | Choose 1 | 5 |
| 14 | Gain 5 + Constitution modifier HP; **Improved Critical** | - | 5 |
| 15 | Gain 5 + Constitution modifier HP | - | 6 |
| 16 | Gain 5 + Constitution modifier HP | - | 6 | Feat |
| 17 | Gain 5 + Constitution modifier HP | Choose 1 | 6 |
| 18 | Gain 5 + Constitution modifier HP | - | 7 |
| 19 | Gain 5 + Constitution modifier HP | - | 7 | Feat |
| 20 | Gain 5 + Constitution modifier HP; **Deadeye** | - | 7 |

**Second Attack (level 6, all subclasses):** attack twice, instead of once, when you take the Attack action with a firearm or other weapon. It uses the same Extra Attack logic as vanilla classes, so it doesn't stack with Extra Attack from multiclassing.

**Expertise (level 6):** choose one skill you're proficient in and double your proficiency bonus for it.

**Tinkerer (level 4):** as an action (no grit cost), add a modification to an equipped firearm until your next long rest. Choose one: increase its capacity by 2 bullets; increase its damage dice (Flintlock: 2d4 becomes 1d10, Blunderbuss: 1d12 becomes 2d6, or Musket: 2d6 becomes 3d4); or increase its range (Flintlock +20 feet, Blunderbuss +10 feet, or Musket +40 feet). Each firearm tracks its modifications separately, so a main-hand and offhand Flintlock can be modified independently. A new modification replaces the previous one on that firearm.

**Master Tinkerer (level 10):** each firearm can hold two different Tinkerer modifications at once. Applying a third replaces the oldest; reapplying one the gun already has changes nothing.

**Gunslinger's Draw (level 1):** +3 to Initiative. BG3 stats can't grant Advantage on Initiative, so this uses a flat bonus close to the average gain from Advantage on a d20.

**Improved Critical (level 14):** your critical hit range increases by 1, so attacks crit on a 19 or 20 (same boost as the Champion's Improved Critical). It stacks with other crit-range reductions.

**Deadeye (level 20):** a Critical Hit with a firearm deals an extra 5d10 Piercing damage.

### Feats

| Feat | Effect |
| --- | --- |
| **Gunner** | Gain proficiency with firearms. Firearms are grouped under BG3's Slings weapon category. Increase Dexterity by 1. |
| **Quick Reload** | When dual-wielding two Flintlocks, Full Reload costs a bonus action instead of an action (an action if no bonus action remains). Increase Dexterity by 1. |
| **Grit Adept** | Increase your maximum grit points by 2 and choose one grit ability available to a level 3 Gunslinger. |
| **Close-Quarters Gunner** | Firearm attacks no longer have Disadvantage against targets within 5 feet. Increase Dexterity by 1. |
| **Longarm Specialist** | Musket attacks gain 20 feet (6m) of range. Increase Dexterity by 1. |
| **Called Shot** | Once per turn, when you hit a creature with a firearm from at least 30 feet away, choose one: reduce its movement speed by 10 feet, prevent it from making reactions, or impose Disadvantage on its next attack before the end of its next turn. Increase Dexterity by 1. |
| **Spellshot Adept** | Your firearm attacks count as magical. Once per turn after casting a spell, your next firearm hit deals an extra 1d4 damage of the spell's elemental type. Increase Intelligence by 1. |

### Grit Abilities

| Name | Lvl available | Description | Cost (grit and actions) |
| --- | --- | --- | --- |
| Merciless Shot | 3 | Make a firearm attack; each grit spent adds 1d4 damage with a Flintlock or 1d6 with a Blunderbuss or Musket. | 1-3 grit; Action; 1 bullet |
| Line 'em Up | 3 | Deal half weapon damage to enemies and neutral creatures, but not allies, in a 20-foot line. Targets make a Dexterity save (DC 8 + Dexterity modifier + proficiency bonus) and take half damage on a successful save. | 2 grit; Action; 1 bullet |
| Rapid Shot | 3 | Fire one additional firearm attack. | 1 grit; Bonus Action; 1 bullet |
| Bite the Bullet | 3 | Gain temporary hit points equal to grit spent multiplied by your proficiency bonus. | Up to 3 grit; Bonus Action |
| Shot in the Dark | 3 | Gain 60-foot darkvision and ignore blindness for 10 turns. | 1 grit; Bonus Action |
| Rapid Repair | 3 | Make a DC 18 Sleight of Hand check to clear a misfire. Appears next to Repair in a misfired gun's Repair menu. | 1 grit; Bonus Action |
| Disarming Shot | 3 | On a hit, the target must pass a Strength save or drop its weapon. | 1 grit; Action; 1 bullet |
| Winging Shot | 3 | On a hit, the target must pass a Constitution save or be knocked Prone. | 1 grit; Action; 1 bullet |
| Forceful Shot | 3 | On a hit, the target must pass a Strength save or be pushed back 4.5 m. | 1 grit; Action; 1 bullet |
| Bullying Shot | 3 | On a hit, the target must pass a Wisdom save or be Frightened for 1 turn. | 1 grit; Action; 1 bullet |
| Quickload | 3 | Fully reload your main-hand firearm or off-hand Flintlock, or reload both. | 1 grit; no action for one gun, or Bonus Action for both |
| Flash Powder | 3 | Target a point on the ground or a creature within 9 m. Creatures in a 1.5 m radius must pass a Constitution save or be Blinded for 1 turn. | 1 grit; Action |
| Fanning Fire | 7 (Desperado); 9 (others) | Make 2-4 firearm attacks against up to 1 + grit spent targets. Each shot takes a penalty of 1 + grit spent: -2 for 1 grit, -3 for 2, or -4 for 3. | 1-3 grit; Action; 2-4 bullets |
| Violent Shot | 9 | Add damage per grit spent: 1d8 with a Flintlock, 2d6 with a Blunderbuss, or 3d4 with a Musket. Then roll a d20; the gun misfires on a result at or below grit spent. | 1-3 grit; Action; 1 bullet |
| Dazing Shot | 9 | On a hit, the target must pass a Constitution save or be Dazed for 1 turn. | 2 grit; Action; 1 bullet |
| Piercing Round | 9 | Fire through an 18 m line, making an attack roll against each enemy and neutral creature, but not allies, in it. | 2 grit; Action; 1 bullet |
| Hair Trigger | 9 | When an enemy within 9 m attacks an ally, shoot the attacker. | 1 grit; Reaction; 1 bullet |
| Grit and Steel | 13 | When you fail a saving throw, reroll it. Once per short rest. | 2 grit; interrupt on failed save |
| Bullet Time | 17 | Gain an extra action this turn. Once per short rest. | 4 grit; no action |
| Hail of Lead | 17 | Make a weapon attack against every enemy within 18 m. Once per long rest. | 5 grit; Action; 1 bullet |
| Final Judgement | 17 | If the hit leaves the target below 25% of its hit points, it takes weapon damage again and must pass a Constitution save or die. | 4 grit; Action; 1 bullet |

#### Desperado Grit Abilities

| Name | Lvl available | Description | Cost (grit and actions) |
| --- | --- | --- | --- |
| Desperado's Luck | 3 | Once per turn, when a firearm attack would miss, add 1d4 to the roll, potentially turning it into a hit. Does not spend a Reaction point. | 1 grit; no action |
| Ante Up | 3 | Gain Advantage on your next firearm attack before the end of your next turn. If it misses, attacks against you have Advantage until your next turn. | 1 grit; Bonus Action |
| Lucky Draw | 3 | Reroll 1s and 2s on your firearm damage dice until the end of your turn. Once per turn. | 1 grit; no action |
| Two-Gun Tango | 3 | Fire your off-hand Flintlock. | 1 grit; no action; 1 off-hand bullet |
| Double Load | 7 | Make an attack with two bullets, dealing an extra 1d4 damage with a Flintlock or 1d6 with a Blunderbuss or Musket. A natural 1 destroys the weapon until a long rest restores it; it cannot be repaired. | 1 grit; Action; 2 bullets |
| Roll the Bones | 7 | Roll a d6: 1 gives -1d4 to firearm attack rolls; 2-5 adds 1d6 damage on the next firearm hit; 6 adds 2d6 damage and restores 1 grit. Lasts until your next attack or 2 turns. | 1 grit; Bonus Action |
| Duck and Weave | 7 | When a ranged weapon attack is about to damage you, resist its physical damage, then Disengage and gain 3 m of movement. | 1 grit; Reaction |
| Close Call | 7 | Gain +2 AC against an attack. If it misses, automatically make a firearm attack against the attacker. | 2 grit; Reaction; 1 bullet if counterattacking |
| Cheat Death's Odds | 7 | While below half your hit points, grit abilities that cost 2 or more grit refund 1 grit when used. | Passive; no action or grit cost |
| Hot Hand | 7 | When you hit with a firearm attack, your next firearm attack scores a Critical Hit on an 18-20. | 2 grit; Reaction |
| Double or Nothing | 11 | After you hit with a firearm attack, roll a d20. On 11 or higher, deal the weapon's damage again; otherwise the gun misfires. | 2 grit; Reaction |
| Last Word | 11 | Arm Last Word until your next long rest. The next time you would be downed, stay at 1 HP and immediately make one firearm attack against your attacker. Once per long rest. | 3 grit; Bonus Action |
| Quick on the Draw | 11 | When an enemy within 9 m starts an attack, cancel it and shoot first. The enemy gets its attack back (an extra weapon attack, or its action for spell attacks). | 2 grit; Reaction; 1 bullet |
| Ricochet Shot | 11 | Shoot an enemy; the shot ricochets to up to three additional enemies. The first hit deals full weapon damage and each ricochet deals half. | 3 grit; Action; 1 bullet |
| Dead Man's Hand | 15 | While below 25% of your hit points, make your next firearm attack before the end of your next turn a Critical Hit if it hits. Once per turn. | 3 grit; no action |
| All In | 19 | Fire a number of shots equal to all your current grit (3-10) at enemies, each at -2 to hit. The matching option is the only one that can be cast. | All current grit; Action; 1 bullet |
| Desperado's Fortune | 19 | Replaces Desperado's Luck. Once per turn, add 1d8 to a firearm attack roll or a saving throw. | 1 grit; no action |
| High Noon | 19 | Call out an enemy for 3 turns. Your firearm attacks against it gain +20 to hit (only a natural 1 misses), crit on 17-20, and deal an extra 1d8 damage. Once per long rest. | 5 grit; Bonus Action |

### Subclasses

#### Marksman

The Marksman specializes in accurate, high-range attacks that deal heavy damage. This subclass is strongest when it can keep enemies at a distance, with few options for close-quarters combat.

| Level | Gunslinger features | Marksman features |
| --- | --- | --- |
| 1 | **Gunslinger's Draw** | — |
| 2 | — | — |
| 3 | Choose a subclass; choose 2 grit abilities | **Lock-on:** As a bonus action, once per short rest, lock on to a creature (concentration). Your firearm attacks deal extra damage equal to your proficiency bonus to it. If it dies while you concentrate, you can lock on to a new target for a bonus action without using another short rest use, like Hunter's Mark. |
| 4 | **Tinkerer** | — |
| 5 | Choose 1 shared grit ability | — |
| 6 | **Second Attack**; **Expertise** (1 skill) | — |
| 7 | — | **Long Shot:** Once per turn, deal additional damage based on the distance to your target (see range damage table below). |
| 8 | — | — |
| 9 | Choose 1 shared grit ability | — |
| 10 | **Master Tinkerer** | — |
| 11 | — | **Stable Shot:** Without spending an action, sacrifice 20 feet of movement to gain Advantage on your next firearm attack. |
| 12 | — | — |
| 13 | Choose 1 shared grit ability | — |
| 14 | **Improved Critical** | — |
| 15 | — | **Pinpoint Accuracy:** Gain +1 to hit at 50 feet or more, and +2 to hit at 70 feet or more. |
| 16 | — | — |
| 17 | Choose 1 shared grit ability | — |
| 18 | — | **Headshot:** Spend 5 grit for an automatic critical hit. |
| 19 | — | — |
| 20 | **Deadeye** | — |

**Long Shot Damage** (90-120 ft damage values are provisional)

| Target distance | Additional damage |
| --- | --- |
| 20 feet or more | 1d4 |
| 30 feet or more | 1d6 |
| 40 feet or more | 1d8 |
| 50 feet or more | 1d10 |
| 60 feet or more | 2d6 |
| 70 feet or more | 2d8 |
| 80 feet or more | 2d10 |
| 90 feet or more | 2d12 |
| 100 feet or more | 3d8 |
| 110 feet or more | 3d10 |
| 120 feet or more | 3d12 |

#### Desperado

The Desperado makes greater use of grit, spending it on special effects and versatile combat techniques. This subclass turns grit into its defining resource, rewarding bold and adaptable play.

| Level | Desperado features | Grit ability progression | Maximum grit |
| --- | --- | --- | --- |
| 3 | Choose Desperado; Desperado's Luck, Ante Up, Lucky Draw and Two-Gun Tango join the grit pool | Choose 2 | 3 |
| 4 | - | - | 3 |
| 5 | - | Choose 1 (Gunslinger, shared pool) | 3 |
| 6 | - | - | 4 |
| 7 | Double Load, Roll the Bones, Duck and Weave, Close Call, Cheat Death's Odds and Hot Hand join the grit pool | Choose 1 | 4 |
| 8 | - | - | 4 |
| 9 | - | Choose 1 (Gunslinger, shared pool) | 5 |
| 10 | - | - | 5 |
| 11 | Last Word, Double or Nothing and Quick on the Draw join the grit pool; Ricochet Shot joins the Desperado pool | Choose 1 | 5 |
| 12 | - | - | 6 |
| 13 | - | Choose 1 (Gunslinger, shared pool) | 6 |
| 14 | - | - | 6 |
| 15 | Dead Man's Hand joins the grit pool | Choose 1 | 7 |
| 16 | - | - | 7 |
| 17 | - | Choose 1 (Gunslinger, shared pool) | 7 |
| 18 | - | - | 8 |
| 19 | All In, Desperado's Fortune and High Noon join the grit pool | Choose 1 | 8 |
| 20 | - | - | 8 |

#### Arcane Gunsman

The Arcane Gunsman combines firearms and magic. It can imbue shots with magical effects, use special ammunition, and gain spellcasting benefits through its firearm. Intelligence is the Arcane Gunsman's spellcasting ability. Its spell slots follow the D&D 5e half-caster progression, keyed to Gunslinger level; spell selection, ammunition, and firearm bonuses are still to be defined.

| Level | Gunslinger features | Arcane Gunsman features |
| --- | --- | --- |
| 1 | **Gunslinger's Draw** | — |
| 2 | — | — |
| 3 | Choose a subclass; choose 2 grit abilities | Gain Arcane Gunsman spellcasting (see spell slot table): learn 2 cantrips and 3 1st-level spells. **Infused Rounds:** Spend a bonus action to infuse your rounds for 10 turns with Fire, Thunder, Lightning, Acid, Cold, or Poison; firearm attacks deal an extra 1d4 damage of that type. |
| 4 | **Tinkerer** | — |
| 5 | Choose 1 shared grit ability | — |
| 6 | **Second Attack**; **Expertise** (1 skill) | — |
| 7 | — | **Improved Infused Rounds:** Damage increases to 2d4 and Force is added to the element choices. **Arcane Reload:** Bonus action, concentration; your main-hand firearm reloads one bullet at the start of each of your turns. |
| 8 | — | — |
| 9 | Choose 1 shared grit ability | — |
| 10 | **Master Tinkerer** | — |
| 11 | — | **Mastered Infused Rounds:** Damage increases to 3d4; add Radiant and Necrotic choices. **Smart Shooting:** Add your Intelligence modifier to firearm attack and damage rolls. |
| 12 | — | — |
| 13 | Choose 1 shared grit ability | — |
| 14 | **Improved Critical** | — |
| 15 | — | **Unstable Infused Rounds:** Toggleable; while active with an infusion, rounds deal 5d4 of their element, but each firearm attack has a 25% chance to backfire for 3d4 Force damage in a 5-foot radius. |
| 16 | — | — |
| 17 | Choose 1 shared grit ability | — |
| 18 | — | **Spellstrike Shooter:** When you cast a leveled spell using your action, you can make one weapon attack without spending an action. |
| 19 | — | — |
| 20 | **Deadeye** | — |

**Arcane Gunsman Spell Slots**

| Gunslinger level | 1st | 2nd | 3rd | 4th | 5th |
| --- | --- | --- | --- | --- | --- |
| 3 | 3 | - | - | - | - |
| 4 | 3 | - | - | - | - |
| 5 | 4 | 2 | - | - | - |
| 6 | 4 | 2 | - | - | - |
| 7 | 4 | 3 | - | - | - |
| 8 | 4 | 3 | - | - | - |
| 9 | 4 | 3 | 2 | - | - |
| 10 | 4 | 3 | 2 | - | - |
| 11 | 4 | 3 | 3 | - | - |
| 12 | 4 | 3 | 3 | - | - |
| 13 | 4 | 3 | 3 | 1 | - |
| 14 | 4 | 3 | 3 | 1 | - |
| 15 | 4 | 3 | 3 | 2 | - |
| 16 | 4 | 3 | 3 | 2 | - |
| 17 | 4 | 3 | 3 | 3 | - |
| 18 | 4 | 3 | 3 | 3 | - |
| 19 | 4 | 3 | 3 | 3 | 1 |
| 20 | 4 | 3 | 3 | 3 | 1 |

**Arcane Gunsman Spells**

The 5e Spells column refers to the [5e Spells mod](https://www.nexusmods.com/baldursgate3/mods/125). With the 5e Spells compatibility add-on enabled, both columns are offered together in one pool.

Like the vanilla casters, each level-up offers a single pick from a cumulative list containing every spell of a level the Arcane Gunsman has slots for, and nothing higher:

| Gunslinger level | New spells learned | Pool |
| --- | --- | --- |
| 3 | 2 cantrips, 3 spells | Cantrips; 1st |
| 5 | 2 spells | 1st-2nd |
| 7 | 1 spell | 1st-2nd |
| 9 | 1 cantrip, 1 spell | Cantrips; 1st-3rd |
| 11 | 1 spell | 1st-3rd |
| 13, 15, 17 | 1 spell | 1st-4th |
| 19 | 1 spell | 1st-5th |

| Spell level | BG3 base game | 5e Spells mod |
| --- | --- | --- |
| Cantrips | Fire Bolt, Ray of Frost, Shocking Grasp | Control Flames, Mind Sliver |
| 1st | Chromatic Orb, Magic Missile, Color Spray | Absorb Elements, Catapult, Chaos Bolt, Zephyr Strike |
| 2nd | Magic Weapon, Misty Step, Scorching Ray, Shatter, Gust of Wind | Dragon's Breath, Kinetic Jaunt, Rime's Binding Ice |
| 3rd | Counterspell, Haste, Fireball, Protection from Energy, Fear, Lightning Bolt | Ashardalon's Stride, Erupting Earth, Flame Arrows, Thunder Step |
| 4th | Fire Shield, Ice Storm, Resilient Sphere, Dimension Door | Shadow of Moil, Storm Sphere, Vitriolic Sphere |
| 5th | Cone of Cold, Hold Monster, Telekinesis | Steel Wind Strike, Synaptic Static, Far Step |

The level-up screen lists the spell slots gained at each level through the subclass's `ActionResource` progression descriptions (`0:SpellSlot;1:1` for Spellcasting at level 3, `0:SpellSlot` afterwards), matching the vanilla Eldritch Knight and Arcane Trickster entries.

## Implementation Notes / Known Limitations

### Grit ability visuals

Grit abilities reuse base-game animations and prepare/cast effects copied from vanilla spells with similar effects. Weapon variants inherit them from their first variant. Non-projectile abilities also copy those spells' sounds; grit abilities that fire a projectile set no `CastSound`/`TargetSound`, so, like the basic firearm attack, they play the firing weapon's own sounds.

Gunshots use the firing sounds from **Immersive Firearms**: the Flintlock and Musket play IF's flintlock/musket shot (`Projectiles_Grn_Impact_Bomb`), and the Blunderbuss plays IF's blunderbuss blast (`Gale_Explosion_Boom` + `ThunderousPunch`). These are all base-game sound events, so no audio files are packed. Because grit shots can be fired from any equipped gun, the sound is picked by the weapon rather than the spell. Each gun's hand passive list includes a hidden `OnCast` passive (`GSL_Firearm_ShotSound_MainHand`, `GSL_Firearm_BlunderbussSound_MainHand` or `GSL_Firearm_ShotSound_OffHand`) whose `SpellId(...)` condition lists every spell that fires that hand's gun. It covers basic attacks, grit shots, Scattershot and the other weapon zones. The passive applies a 0-turn `EFFECT` status (`GSL_FIREARM_SHOT_SOUND` / `GSL_BLUNDERBUSS_SHOT_SOUND`) whose `StatusEffect` is a sound-only effect ported from IF (`Assets/Effects/Effects_Banks/GSL_*_Shot_SoundFX.lsx`, `Content/[PAK]_GSL_Firearm_Sounds/_merged.lsx`, `MultiEffectInfos/`). IF's muzzle-flash visuals are not included. `tests/test_spell_data.py` checks that the passive spell lists match every gunshot spell.

| Ability | Vanilla visual source |
| --- | --- |
| Merciless Shot | Sneak Attack (ranged) |
| Line 'em Up | Piercing Shot |
| Rapid Shot | Horde Breaker (ranged) |
| Bite the Bullet | Second Wind |
| Shot in the Dark | Darkvision |
| Rapid Repair, Tinkerer | Mending |
| Fanning Fire | Volley |
| Double Load | Hamstring Shot |
| Close Call | Shield reaction animation |
| Last Word | Death Ward |
| Stable Shot | Brace (crossbow) |
| Headshot | Hunter's Mark |
| Infused Rounds | Divine Favor |
| Disarming / Winging / Forceful / Bullying Shot | Disarming / Trip / Pushing / Menacing Attack (ranged) |
| Dazing Shot | Distracting Strike (ranged) |
| Violent Shot | Pin Down |
| Flash Powder | Faerie Fire |
| Bullet Time | Action Surge |
| Hail of Lead, All In | Volley |
| Final Judgement, Double or Nothing | Sneak Attack (ranged); Final Judgement adds Power Word Kill's target effect |
| Ante Up | Bless |
| Dead Man's Hand | Bane |
| High Noon | Hunter's Mark |

Unstable Backfire is an instant sub-effect with no cast animation.

### Custom icon artwork

See [To-do.md](To-do.md) for the complete artwork checklist, exact export paths and formats, atlas slots, and stat consumers. All custom actions, passives and statuses now reference registered `GSL_*` ability icons. The ability atlas, tooltip/controller exports and six action-resource image sets now contain the ComfyUI-generated artwork, converted by `python artwork/comfyui/export_icons.py`. The exporter rebuilds the atlas from each key's UV cell, derives the Highlight, Used and Missing resource states, and writes the resource PNG/DDS variants plus `Mods/GunslingerClass/GUI/metadata.lsx`. Re-run it after regenerating or editing any generated PNG. When packing with `stage_packages.py --divine`, the GUI texture metadata is compiled to `metadata.lsf` alongside the visual banks and root templates. Shooting artwork is separate from the existing firearm inventory icons. Resource images are looked up by resource `Name` under the mod's GUI folders, not by a speculative `Icon` attribute in the resource definitions. The optional 5e compatibility PAK needs no duplicate artwork.

Character creation and level-up use separate resource icons at `Mods/GunslingerClass/GUI/Assets/CC/icons_resources/<ResourceName>.DDS`, with PNG counterparts and `AssetsLowRes` copies. The resource exporter creates all six at 128x128 from the master artwork (falling back to the resource PNG), registers their dimensions in GUI metadata, and preserves the existing 48x48 combat-panel icons. `validate_xml.py` checks these level-up paths and metadata before staging. Rebuild the PAK with `stage_packages.py --divine` and reinstall it to pick up the icons; their appearance still needs an in-game level-up check.

The Gunslinger class icon is `Public/Game/GUI/Assets/ClassIcons/Gunslinger.DDS` (300x300, level-up screen and character sheet) and `ClassIcons/hotbar/Gunslinger.DDS` (140x140, hotbar class button). Both are DXT5 with full mipmaps and are found through the class `Name`, like vanilla classes. `Class/ico_class_m_gunslinger.DDS` (72x72, single level) is the small class badge shown in the inventory and party panels. Every class texture ships with a matching `.png` because the UI resolves PNG paths. The Marksman, Desperado and ArcaneGunsman subclasses each have their own emblem, written under their `Name` to `ClassIcons/`, `ClassIcons/hotbar/` and `Class/ico_class_m_<name>.DDS`. Once a subclass is chosen, the UI looks up the class icon by the subclass name, so a missing subclass badge leaves the inventory class icon empty. All of these are generated with the ComfyUI `classes` prompt group and exported by `artwork/comfyui/export_icons.py --group classes` (via `export_class_icons.py`).

This mod is implemented entirely through BG3's stats/.lsx data format (no custom Script Extender (BG3SE) scripting or Osiris story scripts). A few parts of the design above don't have a clean 1:1 vanilla equivalent, so they were implemented as documented, best-effort approximations. These are called out below so they're easy to find and revisit.

**Firearms, ammo and misfires**

- Firearm weapons (`WPN_GSL_Flintlock`, `WPN_GSL_Blunderbuss`, `WPN_GSL_Musket`) use the 3D models, textures and inventory icons from **Immersive Firearms by maradi** (used with the author's permission). Weapon stats and firing animations inherit from vanilla crossbows (Flintlock → Hand Crossbow, one-handed; Musket → Light Crossbow, two-handed; Blunderbuss → Heavy Crossbow, two-handed). Their custom shooting spells and the weapons' `Projectile` field use two mod projectile root templates in `RootTemplates/_merged.lsx`: `GSL_Projectile_Bullet_Straight` (`9c0f6a51-3b7e-4d2a-8f61-2e4b7c9d1a05`, main hand) and `GSL_Projectile_Bullet_Straight_OffHand` (`d4e2b8a7-6c13-4f9e-a5b0-7e1f3c2d8b96`, off-hand flintlock). These are standalone copies of vanilla `VFX_Projectile_Arrow_Normal_01` / `VFX_Projectile_Arrow_Normal_OffHand_01` that keep the original bolt trail, impact and sound effects but omit `ProjectilePath`, `OffsetMin_Bezier3` and `ShiftMin_Bezier3`, the fields that create the lobbed arc. This is the same way straight vanilla projectiles such as Eldritch Blast and Fire Bolt are defined. IF's own stats, spells and statuses are **not** included, and IF does not need to be installed. The imported assets were given new resource UUIDs and icon names (`GSL_*`) to avoid conflicts with Immersive Firearms. Equipment types use crossbow-compatible one-/two-handed animation mappings. The item root templates inherit vanilla `BASE_WEAPON` rather than the crossbow bases, because the tooltip's weapon-type label comes from the item's tag `DisplayName`s and child templates add to (rather than replace) their parent's tags; inheriting a crossbow base would keep the `WPN_HAND_CROSSBOW`/`WPN_LIGHT_CROSSBOW`/`WPN_HEAVY_CROSSBOW` labels. Each firearm template instead carries one mod tag from `Public/GunslingerClass/Tags` (`WPN_GSL_FLINTLOCK`, `WPN_GSL_BLUNDERBUSS`, `WPN_GSL_MUSKET`, labelled Flintlock, Blunderbuss and Musket) and keeps the crossbow `PhysicsTemplate`. Asset locations:
  - meshes: `Generated/Public/GunslingerClass/Firearms/`
  - textures: `Public/GunslingerClass/Assets/Firearms/`
  - visual/material/texture banks: `Public/GunslingerClass/Content/Assets/[PAK]_GSL_Firearms/_merged.lsx`
  - icon atlas: `Public/GunslingerClass/Assets/Textures/Icons/`, `GUI/Icons_GunslingerFirearms.lsx`, `Content/UI/[PAK]_UI/_merged.lsx`
  - tooltip/controller icons: `Public/Game/GUI/Assets/`
  - gunshot sound effects: `Public/GunslingerClass/Assets/Effects/Effects_Banks/`, `Content/[PAK]_GSL_Firearm_Sounds/_merged.lsx`, `MultiEffectInfos/`
  - The `Content` banks, `MultiEffectInfos`, `Tags` and `RootTemplates/_merged.lsx` must be converted to `.lsf`, and the effect sources under `Assets/Effects` to `.lsfx`, before packing (`stage_packages.py --divine` does this). Root-template conversion is required for crafted firearms and kits to be available to the game; leaving the item templates as source XML in the PAK can allow Craft to spend its charge without creating an item.
- Misfire: each firearm's visible **Misfire** passive fires on a critical miss with that gun. It applies the character-side `GSL_MISFIRE` trigger and, like Tinkerer, puts `GSL_FIREARM_ITEM_MISFIRED` directly on the gun with `ApplyEquipmentStatus` (main or off hand, via `IsOffHandAttack()`). The gun's tooltip then shows Misfired like an enchantment. The -2 itself stays on the per-hand character status, so it is named in the hit-chance breakdown and never counted twice. The server reconciles the gun status on repair, on breaking (Broken replaces Misfired) and on long rest.
- Firearm-only conditions use vanilla `IsRangedWeaponAttack()` and `IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())`. The imported weapons use the otherwise-unused Slings proficiency group. They do not call Immersive Firearms' custom `IsFirearmAttack()` helper or require that mod's scripts.
- The shared critical-miss passive notifies the server runtime, which records the exact gun and projects hand-specific attack locks. Double Load has a separate destruction trigger; destroyed guns offer no Rapid Repair option. Ordinary repair remains outside this grit update.
- Ammo capacity (3/2/1 bullets) is granted by equipment passives. Direct grit attacks pay ammunition through `UseCosts`; reaction shots spend one bullet through native resource functors, without a second action/reaction charge. The server adds conditional ammunition costs and readiness checks to Line 'em Up and native spells with ranged weapon attack rolls. Those conditional checks leave non-firearm weapons' existing actions/costs intact. Reloads still refill their matching pools; the runtime snapshots the result to the physical gun. Primary/Secondary Reload cost `BonusActionPoint:1`; while the character has no bonus action left, the server applies `GSL_RELOAD_NO_BONUS_ACTION`, whose spell variant replaces that cost with `ActionPoint:1`. Full Reload costs `ActionPoint:1`; with Quick Reload and a bonus action available, `GSL_QUICK_FULL_RELOAD` replaces it with `BonusActionPoint:1`. The server re-checks the bonus action on casts, turn start, equipment changes and every few ticks. The reload and Quickload spells carry `SpellFlags` `Stealth;Invisible` (the vanilla `Shout_Hide`/`Shout_Dash` flags), so casting them keeps the character hidden or invisible and doesn't alert enemies.

**Crafting**

- Starting at level 2, the Gunslinger gets a single **Craft** class action (`Shout_GSL_Craft`), a linked spell container that opens five options: Flintlock, Musket, Blunderbuss, Assembly Kit, and Disassembly Kit (`Shout_GSL_Craft*`). Each option spends one Gunsmithing Charge (`GunslingerCraftCharges`, restores on long rest) and an action to place the item directly into the caster's inventory via `SummonInInventory`.
- The Assembly Kit (`OBJ_GSL_AssemblyKit`) and Disassembly Kit (`OBJ_GSL_DisassemblyKit`) use JWL Crafting Framework's item-combination interface. The first supported pairing is the Artificial Leech (+1) and a Flintlock: assembly consumes the kit and Artificial Leech, transforms the Flintlock into an enchanted variant, and disassembly consumes its kit and returns both original items. The Leech's +1 enchantment transfers; its Bloodletting action is NPC-only in the base game and is not granted to player characters. Additional pairings need their own explicit `ItemCombos.txt` recipes and firearm variants; arbitrary magical weapons are not fused dynamically.

**Grit abilities**

- Level-up grit choices reuse the unlocked spell or reaction's name, description, and icon, so the selection tooltip shows the same rules text as the ability itself. Cheat Death's Odds is a passive-only choice and uses its own descriptor.
- See [Grit-Ability-Report.md](Grit-Ability-Report.md) for the before/README/after comparison, exact costs, implementation references, and in-game acceptance checklist. Source tests and mocked Lua lifecycle tests are not proof of BG3 reaction timing.
- Level 3 grants two selected grit abilities (from the subclass's pool); later selections grant one, on the class/subclass schedules listed above. Fanning Fire is in the level 7+ pools, so it's first offered at level 7 to Desperados (their own extra pick) and at the level 9 base-class pick to everyone. Tinkerer is no longer a grit pick; it's a level 4 class feature. Grit Adept uses the level-3 pool.
- Merciless Shot, Rapid Shot, Double Load, and Fanning Fire now execute weapon attacks directly, rather than spending an action on a buff followed by a second attack. Linked menus expose only tiered abilities (Merciless/Bite/Fanning/Violent Shot/All In). Single-cost shots (Rapid Shot, Double Load, Disarming, Winging, Forceful, Bullying, Dazing, Final Judgement) are one hotbar spell each, not a group; like Merciless Shot's options they work with any equipped firearm and spend that firearm's bullet(s).
- Each firearm's basic attack is granted once, through the weapon passive's AttackSpellOverride (replacing the vanilla ranged attack). Weapons no longer also UnlockSpell it, which had shown the attack twice (one copy using the class casting ability). The attack therefore isn't listed on the weapon tooltip. Line 'em Up uses half weapon damage on every non-allied creature, quarter damage on a successful Dexterity save.
- Tinkerer has six choices: capacity/damage/range for primary or secondary firearms, each costing an action and no grit. The server stores up to one modification per physical gun (two distinct ones with Master Tinkerer at level 10), replaces the oldest when full, and clears them on long rest. Saves that stored the older single-modification format are migrated automatically. Each active modification is applied to the modified weapon by the Tinkerer spell itself with `ApplyEquipmentStatus(RangedMainHand/RangedOffHand, ...)`, the same mechanism as Magic Weapon and Shillelagh. It shows as an enchantment-style status (Tinkered: Capacity, Tinkered: Damage, Tinkered: Range) on the gun's tooltip, even when the gun is unequipped; the server then reconciles the statuses with its per-gun record (replacing the oldest past the limit). Damage is a `WeaponDamageDieOverride` boost on the gun itself; capacity and range are applied to the wielder by the server while that gun is equipped. Increasing capacity does not conjure bullets; reload to fill the new space.
- Repair uses one class-action container per hand (`Shout_GSL_Repair_Main`/`_Off`, or the `_Rapid` variants once `GSL_RapidRepairUnlock` is known). The server unlocks only the misfired, unbroken hand's menu through the hidden `GSL_REPAIR_MENU_*` statuses. DCs are fixed (Repair 15, Rapid Repair 18) instead of scaling with rarity, which would have needed a separate spell per rarity and hand. A failed check still spends the costs.
- Fanning Fire uses 2/3/4 target selections, matching ammunition costs and -2/-3/-4 attack penalties. The penalty is a `RollBonus(RangedWeaponAttack,-N)` on the Fanning Fire passive, gated by `SpellId(...)` (the vanilla Agonizing Blast pattern), so it is part of the roll and the hit-chance preview rather than a status applied around the cast. Shots require enough loaded ammunition for the entire volley: even a capacity-modified Musket holds only three bullets.
- Shot in the Dark grants native 18-metre darkvision and blindness-group immunity for 10 turns (attacking no longer ends it). Whether this suppresses an already-active Blind status exactly as the design intends still needs an in-game check.
- **Stable Shot** now spends 6 metres (20 feet) of movement when activated; learning the feature no longer permanently removes that movement from every turn.
- Desperado's exclusive abilities are grit picks, added to Desperado-only grit pools offered by the Desperado's own picks at levels 3/7/11/15/19. The base-class picks at 5/9/13/17 use the shared pools for every subclass. The level 3 grit pick lives on each subclass's level 3 progression row, so it's offered after the subclass is chosen. Grit Adept still uses the shared level-3 pool.
  - **Desperado's Luck:** native post-roll prompt, one grit, +1d4, once-per-turn marker, no Reaction cost.
  - **Double Load:** action attack, one grit, two bullets, +1d4 (Flintlock) or +1d6 (Blunderbuss/Musket) damage; natural 1 marks that physical gun destroyed until long rest.
  - **Close Call:** native post-roll prompt costing a Reaction and two grit. Subtracting two from the incoming roll is equivalent to +2 AC for that attack. The prompt also applies a hidden `GSL_CLOSE_CALL_COUNTER` marker. When the attack resolves, the marker's `OnAttacked` passive fires a loaded, usable main-hand firearm at the attacker only on a miss (the vanilla Riposte `IsMiss()` / `UseSpell(SWAP, ...)` pattern). A companion passive clears the marker on a hit.
  - **Last Word:** a prepared bonus action (three grit, once per long rest) that grants a `DownedStatus` replacement, the same mechanism as vanilla Relentless Endurance. When it triggers, you regain 1 HP and the server fires the counterattack at the most recent attacker. `IsKillingBlow()` is never set during `OnPreDamage`, so a lethal-damage interrupt can't work.
- **Expanded grit pools.** Fifteen shared abilities unlock at levels 3/9/13/17. Fifteen more Desperado abilities unlock at levels 3/7/11/15/19, giving 19 Desperado-only abilities. Every subclass grit pick offers every ability unlocked at that level or lower. Approximations and deviations from the suggestion list:
  - **Violent Shot:** the misfire chance is a server-side d20 roll after the cast, on a result at or below the grit tier. The gun receives the normal Misfired state; a gun that has already misfired breaks.
  - **Double or Nothing:** a reaction (Interrupt_GSL_DoubleOrNothing, Reaction + 2 grit) after a non-lethal firearm hit casts a free follow-up (Projectile_GSL_DoubleOrNothing). The server rolls a d20 when it starts; on 11 or higher the follow-up deals weapon damage again, otherwise the gun misfires. Cheat Death's Odds refunds through the interrupt.
  - **Roll the Bones:** a bust is a -1d4 attack penalty rather than lost grit. Results last 12 seconds (2 turns) or until your next attack; Jackpot restores 1 grit when applied.
  - **Cheat Death's Odds:** a refund rather than a cost reduction. The server refunds 1 grit after a qualifying cast of 2 or more grit while below half HP. Interrupts costing 2 or more (Grit and Steel, Quick on the Draw, Double or Nothing) apply the refund through their own functors; Last Word is now a spell, so the cast refund covers it.
  - **Quick on the Draw:** triggers when an enemy within 9 m declares an attack, not on initiative. Interrupt `UseSpell` always resolves after the interrupted action, so it follows the vanilla Instinctive Charm pattern: `Counterspell()` cancels the attack, the attacker gets `EXTRA_ATTACK`/`EXTRA_ATTACK_Q` (weapon attacks) or `GSL_QUICK_ON_THE_DRAW_REFUND` (restores 1 action for spell attacks), and then the reaction shot fires.
  - **All In:** one firearm-agnostic option per grit total (3-10). Each option can only be cast when your grit exactly matches it, so casting always empties your grit. It costs one bullet, and every shot is at -2 to hit.
  - **Dead Man's Hand:** a guaranteed crit on the next hit, without the two-gun attack.
  - **Two-Gun Tango:** spends off-hand ammunition.
  - **Piercing Round:** makes an attack roll against each non-allied creature in the line rather than a save.
  - **Desperado's Fortune:** replaces Desperado's Luck (the Luck prompt is suppressed while you have Fortune or High Noon).
  - **High Noon:** uses `RollBonus(Attack,20)` as an "only a natural 1 misses" approximation; its 1d8 is passive bonus firearm damage, not an attack-roll or saving-throw bonus.
  - **Duck and Weave:** physical `SetDamageResistance` has no vanilla precedent; it needs an in-game check.
- The new abilities use 29 new custom ability icons, registered in the existing ability atlas.
- New menu tiers, repair options, and interrupts reuse existing custom icons. No additional artwork is required. Lua files and the extender config are included automatically by `stage_packages.py`.

**Feats**

- **Close-Quarters Gunner**: uses the native `IgnorePointBlankDisadvantage(Ammunition)` boost (the same mechanism as Crossbow Expert's point-blank feature), so firearm attacks against targets within 5 feet are not made at Disadvantage.
- **Longarm Specialist**: BG3 has no long-range disadvantage to ignore, so the feat only adds range. Script Extender applies a hidden status adding 6m to main-hand weapon-attack targeting while a musket is equipped; it stacks with Tinkerer's range modification.
- **Called Shot**: the README's 3-way choice (reduce speed / deny reactions / impose disadvantage) has no in-combat UI hook to let the player pick an option per use, so this always applies the "disadvantage on the target's next attack" option.
- **Spellshot Adept**: the bonus damage rider is simplified to a fixed Force-damage bonus instead of matching "the school of the spell just cast," since that needs per-school damage-type tracking with no simple functor equivalent.

**Arcane Gunsman**

- **Arcane Reload** (level 7) is a concentration bonus action that applies the `GSL_ARCANE_RELOAD` equipment status to the main-hand firearm (Magic Weapon pattern). At the start of each of the wielder's turns, the server adds one bullet to any equipped, unbroken firearm carrying that status, up to its capacity.
- **Infused Rounds** is a bonus-action spell group (Divine Favor visuals). Each element applies a 10-turn status whose conditional `CharacterWeaponDamage` boosts add 1d4/2d4/3d4 (5d4 while Unstable) of that element to ranged weapon attacks made with Slings-proficiency firearms; choosing a new element replaces the old one (shared `StackId`). Force needs Improved, Radiant/Necrotic need Mastered. Unstable is a toggleable passive (vanilla `IsToggled`/`ToggleOnFunctors` pattern) whose status only takes effect while an infusion is active; it grants a passive that rolls a native d4 (4 = 25%) on each firearm attack to trigger an immediate, caster-centred 1.5-metre radius Force backfire, whether it hits or misses.
- Every Arcane Gunsman spell ID was checked against the vanilla and 5e Spells stats. The 4th- and 5th-level lists previously held placeholder entries (an upcast Gust of Wind variant and the Mephit fire-breath zone); these are replaced with real 4th- and 5th-level spells.

**5e Spells compatibility addon**

- `GunslingerClass_5eSpellsCompat` has no progression rows of its own. Its `SpellLists.lsx` redefines the base Arcane Gunsman cantrip and cumulative level 1-5 lists under the same UUIDs, holding the base-game and 5e Spells options of every included level. The add-on depends on GunslingerClass, so it loads afterwards and its lists replace the base ones. Each level-up then offers a single pick from the combined list instead of separate base and 5e picks. Without the add-on, the lists contain only base-game spells.

**General**

- This repository contains the unpacked mod source tree under `GunslingerClass/`, alongside reference mods in `examples/`. `stage_packages.py` runs `validate_xml.py`, then copies the files for each PAK into `Main_Staging/` (base mod, `Generated/` meshes, `Public/Game/` icons, plus `Localization/English/`) and `5e_Compat_Staging/` (5e Spells compat add-on). Pass `--divine <path to LSLib Divine.exe>` to convert the localization `.xml` to `.loca` and the `Content` bank, `RootTemplates` and `Tags` `.lsx` files to `.lsf`, then pack both folders into `Packages/GunslingerClass.pak` and `Packages/GunslingerClass_5eSpellsCompat.pak` (LZ4, verified against the staged file list). Add `--no-pack` to convert and stage without packing. Without `--divine`, convert the files with LSLib ConverterApp, remove the originals, and pack each staging folder with ConverterApp (Create Package, V18 Baldur's Gate 3 Release, LZ4).
- `validate_xml.py` checks XML, the main module/localization folder layout, and public `TranslatedString` localization, then runs `validate_stats.py` to check local stats references, spell inheritance, effective cast animations/events, projectile trajectories, zone geometry, reload effects, and separate offhand attack wiring. Vanilla animation/trajectory inheritance is checked against `examples/BG3 Reference` when available; without that cache, validation explicitly reports that external fields were not checked. These checks do not parse stats in the game engine or verify behaviour in-game.
- Run the focused regression suite with `python -m unittest discover -s tests -p test_spell_data.py -v`. After installing a rebuilt PAK and restarting the game, test all five Craft choices; empty/refill each basic firearm ammo pool; fire and reload both flintlocks separately; then check class actions, field repair, Rapid Repair, Infused Rounds, and unstable backfire in combat. Verify resource costs on misses as well as hits.
- Run `python -m unittest discover -s tests -p test_staging_resources.py -v` to check root-template and visual-bank conversion, manual-conversion reporting, and conversion failure handling.
