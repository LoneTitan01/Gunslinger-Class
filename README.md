# bg3-Gunslinger-Class
This is a mod for Baldur's Gate 3 implementing a Gunslinger class, the ability to craft firearms, etc.

## Requirements

- **Required:** [BG3 Script Extender](https://github.com/Norbyte/bg3se/releases), version 20 or newer. Persistent firearm modifications, misfire/broken state, rarity-based Rapid Repair, volley cleanup, and Last Word's post-damage counterattack use server-side Lua. Install the extender through BG3 Mod Manager before enabling this version.
- **Optional:** [5e Spells](https://www.nexusmods.com/baldursgate3/mods/125), for the Arcane Gunsman spell options marked as coming from that mod.

## Modding Wiki

- [Baldur's Gate 3 Modding Wiki](https://wiki.bg3.community/Tutorials)

## Firearms

Each firearm replaces the default ranged attack with its own **Shoot Flintlock**, **Shoot Blunderbuss**, or **Shoot Musket** weapon attack. Shots fire the vanilla crossbow bolt projectile along a flat, straight line (the bolt's lobbed arc is removed) with crossbow firing animations, weapon damage, and weapon attack rolls; they are not spell attacks or piercing line-area attacks. Each basic shot consumes one bullet, and the engine prevents the attack when its ammo pool is empty. Flintlocks hold 3 bullets in each hand, blunderbusses hold 2, and muskets hold 1. Main-hand and offhand flintlocks use separate ammo pools and separate attack buttons; automatic bundled dual-wield shots are disabled so an offhand shot cannot bypass its ammunition cost.

Reload actions are granted by the equipped gun, not by Gunslinger class level:

- **Primary Reload:** bonus action; appears with a main-hand flintlock, blunderbuss, or musket and refills that gun.
- **Secondary Reload:** bonus action; appears with an offhand flintlock and refills its separate pool.
- **Full Reload:** action; appears with two equipped flintlocks and refills both pools.

**Scattershot** (blunderbuss only) costs an action and one blunderbuss bullet. It blasts a 10-foot cone; each creature in it makes a Dexterity saving throw (DC 8 + Dexterity modifier + proficiency bonus), taking full weapon damage on a failed save or half on a success. It appears only while a working blunderbuss is in the main hand.

Firearms do not grant the inherited vanilla crossbow weapon actions (Piercing Shot, Mobile Shooting, Brace). Their only equipment-granted actions are the shots, reloads, and Scattershot listed above. They are granted through the weapons' `BoostsOnEquipMainHand` / `BoostsOnEquipOffHand` (`UnlockSpell(...)`) so they are listed as actions on the weapon tooltip, like vanilla weapon actions. The off-hand flintlock grants Secondary Reload, the off-hand shot, and Full Reload; Full Reload is greyed out unless a flintlock is also in the main hand. The hidden per-hand equip passives only add the ammo pools and swap the default ranged attack for the firearm shot (`AttackSpellOverride`).

Ammo refills on a short or long rest. Hand/type resource pools remain the combat UI, while Script Extender stores ammunition, modifications, misfires, and destruction against each physical firearm and restores its state when equipped or transferred. A natural 1 on an attack roll causes that gun to misfire, disabling its firearm attacks until repaired or a long rest. Rapid Repair is implemented; the separate ordinary action/DC 10 + rarity repair described by the original design is still not implemented.

| Firearm | Hands | Capacity | Base damage | Range |
| --- | --- | --- | --- | --- |
| Flintlock | One-handed | 3 bullets | 2d4 | 45 ft |
| Blunderbuss | Two-handed | 2 bullets | 1d12 | 25 ft |
| Musket | Two-handed | 1 bullet | 2d6 | 80 ft |

Weapon range values are **1350 / 750 / 2400**, respectively, using the game's shortbow scale of 1800 = 60 feet. Main-hand shooting spells use the equipped weapon's range; the secondary flintlock uses 13.5 metres, or a 19.5-metre override with Tinkerer's range modification. The modified secondary attack is also explicitly unlocked as a selectable action. High-ground range extensions remain inherited from vanilla ranged attacks.

Blunderbuss and Musket use BG3's exact `Twohanded` weapon-property token, matching Heavy and Light Crossbows. The display-style spelling `Two-Handed` is not a valid stats property.

### Crafting

Starting at level 2, the Gunslinger has three **Craft** charges per day. Spend one charge to create one of the following:

- A base Flintlock
- A base Musket
- A base Blunderbuss
- An Assembly Kit, used to fuse a magical weapon to a firearm
- A Disassembly Kit, used to defuse a fused firearm and magical weapon

The following compatibility mapping includes weapons from the BG3 Wiki's [uncommon](https://bg3.wiki/wiki/List_of_uncommon_weapons), [rare](https://bg3.wiki/wiki/List_of_rare_weapons), and [very rare](https://bg3.wiki/wiki/List_of_very_rare_weapons) lists. Weapons whose only feature is a +1, +2, or +3 Enchantment are omitted. Flintlocks are matched to one-handed weapons, Blunderbusses to two-handed melee weapons, and Muskets to ranged weapons. Versatile weapons are listed with Blunderbusses. These are proposed fusion targets; how each property's effect transfers to a firearm remains to be defined.

<details>
<summary>Flintlock-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Artificial Leech (+1) | +1 | Bloodletting weapon action can cause Bleeding. |
| Assassin's Shortsword | +1 | Advantage on Stealth checks. |
| Assassin's Touch | +1 | Deals 1d4 Necrotic damage to sleeping or knocked-out targets. |
| Bonesaw (+1) | +1 | Incise Ligaments weapon action can Slow the target. |
| Club of Hill Giant Strength | None | Sets the wielder's Strength to 19. |
| Deep Delver | None | Hits inflict Shattered. |
| Dragon's Grasp | None | Deals +1d4 weapon damage to Burning targets. |
| Firestoker | None | Deals +1d4 weapon damage to Burning targets. |
| Hoppy | +1 | Revitalising Strike weapon action damages a target and heals the wielder. |
| Hunter's Dagger | +1 | Hits inflict Ruptured for 3 turns. |
| Infernal Mace (Uncommon) | +1 | Deals 3 Poison damage on hit and can Poison the target. |
| Murderous Cut | +1 | Deals +1d4 Piercing damage to targets at or below half HP. |
| Ritual Axe | None | Can penalize a target's attack rolls and saves by 1d4; may deal 1d6 Piercing damage to the wielder if they have at least half HP. |
| Ritual Dagger | None | On hit, grants +1d4 to attack rolls and saves until the end of the wielder's next turn. Blood Sacrifice trades 1d4 Slashing damage to the wielder for the same bonus. |
| Ritual Dagger of Shar | +1 | Deals +1d4 Necrotic damage. |
| Shining Staver-of-Skulls | +1 | Deals +1d4 Radiant damage and sheds light in a 25-foot radius. |
| Shortsword of First Blood | None | Deals +1d8 Piercing damage to targets at full HP. |
| Skybreaker | +1 | Can cast Searing Smite at level 1 once per long rest. |
| Speedy Reply | None | Hitting a target grants 2 turns of Momentum. |
| Sword of Screams | None | Deals +1d4 Psychic damage. |
| Sylvan Scimitar | +1 | Uses the wielder's spellcasting modifier instead of Dexterity for attack rolls. |
| Syringe (+1) | +1 | Inject Nostrum weapon action can Poison the target. |
| The Watcher's Guide | None | A missed attack grants True Strike against that target on the next attack. |
| Trepan (+1) | +1 | Trephination weapon action can knock the target Prone. |
| Worgfang | None | Goblins have Disadvantage on attack rolls against the wielder. |
| Wulbren's Hammer | +1 | Deals 2d4 Force damage against objects and world objects. |
| Xyanyde | +1 | Once per short rest, a missed attack can inflict Faerie Fire for 2 turns. |

**Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Adamantine Mace | +1 | Adamantine hits against objects are critical hits; the mace ignores Bludgeoning resistance. |
| Adamantine Scimitar | +1 | Adamantine hits against objects are critical hits; the scimitar ignores Slashing resistance. |
| Ambusher | +1 | +1 Initiative, Advantage on Perception checks, and +1d6 Necrotic damage against creatures that have not taken a turn yet. |
| Cold Snap | None | Off-hand only: Chilling Counter can inflict Chilled on a creature that misses an attack; grants +1 AC while off-hand. |
| Corrosive Flail | +1 | Corrosive Strike adds Acid damage equal to proficiency bonus and creates acid that reduces target AC by 2. |
| Defender Flail | +1 | Reduces incoming Bludgeoning, Piercing, and Slashing damage by 1; grants +1 AC. |
| Despair of Athkatla | +2 | Grants +1 to spell attack rolls and spell save DC. |
| Dolor Amarus | +2 | Critical hits deal 7 additional damage. |
| Dread Iron Dagger | +1 | Deals +1d6 Necrotic damage while its wielder is hidden. |
| Flail of Ages | +1 | Adds an elemental condition based on its damage type; can cast Elemental Age at level 3 once per long rest. |
| Fleshrender | +2 | Part the Flesh weapon action can prevent the target from healing. |
| Gleamdance Dagger | +2 | Sheds light; grants +1 AC when wielded off-hand. |
| Harmonic Dueller | +1 | Mellow Harmony: pass a DC 15 Performance check to add Charisma modifier (minimum 1) to melee weapon damage for a duration. |
| Infernal Mace | +2 | Deals 3 Poison damage on hit and can Poison the target. |
| Ne'er Misser | +1 | Deals Force damage; can cast Magic Missile at level 3 once per short rest. |
| Ravengard's Scourger | +2 | Can use Commander's Strike to direct an ally to make a weapon attack as a reaction. |
| Salty Scimitar (rrr) | +2 | Can cast Command at level 1 once per long rest. |
| Shattered Flail | +2 | Hits heal the wielder for 1d6 HP; failing to keep hitting each turn can cause Madness. |
| Sickle of BOOOAL | None | Deals 2d4 Slashing damage; grants Advantage against Bleeding creatures while Kuo-toa worship BOOOAL. |
| Slicing Shortsword | +1 | Attacks made with Advantage inflict Bleeding. |
| Sussur Dagger | +1 | Hits can Silence targets that fail a DC 12 Constitution save. |
| Sussur Sickle | +1 | Hits can Silence targets that fail a DC 12 Constitution save. |
| Sword of Clutching Umbra | +1 | Shadowsoaked Blow adds proficiency bonus and 1d6 Psychic damage without breaking concealment. |
| The Baneful | +1 | Favoured Weapon adds +1 to attack and damage; hits can inflict Bane. |
| Twist of Fortune | +1 | Reroll weapon damage dice of 2 or less; Blood Money adds damage based on the target's gold and consumes that gold. |
| Wavemother's Sickle | +2 | Deals +1d4 Cold damage and has Advantage against Wet creatures. |

**Very Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Belm | +2 | Perfectly Balanced Strike grants an extra bonus-action attack; Whirlwind Attack strikes nearby foes. |
| Handmaiden's Mace | +2 | Sets Strength to 18, deals +1d6 Poison damage, and can Poison targets. |
| Hellfire Hand Crossbow | +2 | Can Burn targets when attacking from Hide or Invisible; Scorching Ray Shot casts level 3 Scorching Ray once per short rest. |
| Infernal Rapier | +2 | +1 spell save DC; uses spellcasting modifier for attacks; can summon a Cambion at level 6 once per long rest. |
| Justiciar's Scimitar | +2 | Attacks with Advantage can Blind; Advantage against obscured targets; Shadowsoaked Blow adds proficiency bonus and 1d6 Psychic damage without breaking concealment. |
| Knife of the Undermountain King | +2 | Lowers critical-hit threshold by 1, rerolls damage dice of 2 or less, and grants Advantage against obscured targets. |
| Pelorsun Blade | +1 | Deals +1d4 Radiant damage and grants Advantage against Undead. |
| Rhapsody | +1 | Kills stack +1 to attacks, damage, and spell save DC up to +3; hidden attacks can cause Bleeding; Scarlet Feast consumes 3 stacks. |
| Stillmaker | +2 | Can cast Hold Person at level 3 once per long rest. |
| Sword of Life Stealing | +2 | Critical hits deal 10 Necrotic damage and grant 10 temporary HP against non-Construct, non-Undead targets. |
| The Sacred Star | +2 | Deals +1d4 Radiant damage and applies Radiating Orb; can Turn Undead; Dawnburst Strike deals proficiency-bonus Radiant damage and can Blind nearby foes. |

</details>

<details>
<summary>Blunderbuss-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Argument Solver | +1 | Poison Mist weapon action adds Poison damage equal to proficiency bonus and creates a Poison cloud. |
| Corellon's Grace | None | Grants +1 to unarmed attack rolls and damage, and +2 to saves while the wielder wears no armour. |
| Doom Hammer | None | Hits inflict Bone Chilled, preventing HP recovery; undead targets also have Disadvantage on attacks. |
| Everburn Blade | None | Deals an additional 1d4 Fire damage. |
| Exterminator's Axe | None | Deals +1d6 Fire damage to Plants, Myconids, and Small creatures. |
| Faithbreaker | +1 | Absolute Power weapon action adds 1d6 Force damage and can push the target. |
| Githyanki Greatsword (Psionic) | +1 | When wielded by a Githyanki, deals +1d4 Psychic damage. |
| Hamarhraft | None | Landing from a jump deals 1d4 Thunder damage in a 10-foot radius. |
| Intransigent Warhammer | None | Killing a target or landing a critical hit can knock nearby creatures Prone. |
| Jagged Spear | None | Tortured targets may have Disadvantage on Constitution saves. |
| Light of Creation | +1 | Deals +1d6 Lightning damage; each successful attack has a chance to Stun the wielder unless they are a Construct. |
| Melf's First Staff | +1 | Grants +1 to spell attack rolls and spell save DC; can cast Melf's Acid Arrow at level 2 once per long rest. |
| Nature's Snare | None | Hits can Ensnare targets that are not Plants or Beasts. |
| Rain Dancer | None | Can cast Create Water at level 1 once per short rest. |
| Staff of a Mumbling Wizard | None | Can cast Fire Bolt at will; has a 1-in-20 chance to cause a Fireball explosion. |
| Staff of Arcane Blessing | None | Can cast Bless at level 1 once per long rest; blessed creatures also gain +1d4 to spell attack rolls. |
| Staff of Crones | None | Can cast Ray of Sickness at level 1 once per short rest. |
| Svartlebee's Woundseeker | +1 | Grants +1d4 to attack rolls against creatures that have already taken damage. |
| Sword of Justice | +1 | Can cast Tyr's Protection once per short rest. |
| The Skinburster | +1 | Dealing melee damage grants 2 turns of Force Conduit. |
| The Undead Bane | +1 | Deals +1d6 Slashing damage to Fiends and Undead; Profane Scourge adds proficiency bonus damage and can add 2d6 Slashing damage and Bane against those targets. |
| Very Heavy Greataxe | +1 | Gargantuan Cleave attacks multiple targets for +1d6 Slashing damage, but leaves the wielder Off Balance. |
| Witchbreaker | +1 | Advantage on attacks against concentrating targets; Hush You weapon action can Silence a target. |

**Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Adamantine Longsword | +1 | Adamantine hits against objects are critical hits; the sword ignores Slashing resistance. |
| Bigboy's Chew Toy | +1 | Can cast Enlarge on the wielder once per long rest. |
| Blackguard's Sword | +2 | Dazing Smite can Daze a target hit by a Smite spell if it fails a Constitution save. |
| Blade of Oppressed Souls | +1 | Deals +1d4 Psychic damage; Crowning Strike can inflict Crown of Madness. |
| Blooded Greataxe | +1 | Deals +1d4 Slashing damage while the wielder is at or below half HP. |
| Breaching Pikestaff | +2 | Deals an additional 1d4 Force damage. |
| Cacophony | +1 | Can cast Thunderous Smite at level 1 once per short rest. |
| Caitiff Staff | +2 | Grants +1 to spell attack rolls and spell save DC; restores one expended Warlock spell slot once per long rest. |
| Charge-Bound Warhammer | +1 | When bound to an Eldritch Knight or used as a Pact/Hexed weapon, gains +1 attack and damage and deals +1d6 Lightning damage. |
| Clown Hammer | +2 | On a critical hit, the wielder and target must pass Wisdom saves or fall down laughing. |
| Corpsegrinder | +2 | Deals +1d4 Thunder damage; Grand Slam adds Thunder damage equal to proficiency bonus and can push nearby foes. |
| Creation's Echo | None | Dealing Acid, Fire, Lightning, Radiant, or Necrotic damage grants resistance to that type for 2 turns. |
| Defender Greataxe | +2 | Can reduce its Enchantment by 1 on the first attack each round for +1 AC and +1 to saves. |
| Drakethroat Glaive | +2 | Draconic Elemental Weapon can imbue a weapon with an element; improves Dragonborn breath save difficulty. |
| Gold Wyrmling Staff | +1 | Deals +1d4 Fire damage and can cast Fire Bolt at will. |
| Hammer of the Just | +2 | Deals +1d4 Radiant damage and +1d6 Bludgeoning damage to Fiends and Undead; can cast Detect Thoughts at level 2 once per long rest. |
| Harmonium Halberd | +1 | Increases Strength by 2 (maximum 23), but decreases Intelligence and Wisdom by 1. |
| Harper Sacredstriker | +1 | Can cast Spiritual Weapon at level 6 once per long rest. |
| Hellbeard Halberd | +2 | Deals 6 Poison damage on hit; target can be Poisoned (DC 12 Constitution save). |
| Hollow's Staff | +1 | Deals +1d4 Necrotic damage; targets have Disadvantage on saves against the wielder's Necromancy spells; can cast Arms of Hadar at level 3 once per long rest. |
| Jorgoral's Greatsword | +1 | Colossal Onslaught attacks creatures in a line and adds Slashing damage equal to proficiency bonus. |
| Ketheric's Warhammer | +1 | Deals +1d4 Psychic damage. |
| Larethian's Wrath | +1 | Razor Gale weapon action damages all enemies in range. |
| Monster Slayer Glaive | +1 | Deals +1d4 damage to Monstrosities; increases jump distance by 5 feet. |
| Moonlight Glaive | +2 | Deals +1d4 Radiant damage and sheds light; Moonlight Butterflies grants Advantage against its target. |
| Pale Oak | None | Faithwarden's Vines cannot Entangle the wielder; can cast Faithwarden's Vines at level 1 once per long rest. |
| Phalar Aluve | +1 | +1 Performance; Phalar Aluve: Melody lets the wielder Sing or Shriek once per short rest. |
| Punch-Drunk Bastard | +1 | While Drunk, grants Advantage on attacks and melee hits deal 1d4 Thunder damage in a 10-foot radius. |
| Rat Bat | +1 | Deals +1d6 Piercing damage and grants Advantage on attacks against Beasts. |
| Shadow Lantern | None | Provides Moonshield protection from the Shadow Curse; can summon a Shadow Lantern wraith at level 6 once per long rest. |
| Soulbreaker Greatsword | +1 | Githyanki gain +1d4 Psychic damage; +2 Initiative; Soulbreaker adds proficiency-bonus Psychic damage and can Stun. |
| Sorrow | +1 | Sorrowful Lash cantrip is available as a bonus action. |
| Spear of Night | +1 | Shar's Blessing allows it to kill the Nightsong if Shar permits. |
| The Sparky Points | None | Dealing damage with the trident grants 2 Lightning Charges. |
| The Spellsparkler | None | Dealing damage with a spell or cantrip grants 2 Lightning Charges. |
| Staff of Interruption | +2 | Can cast Counterspell at level 5 once per long rest. |
| Staff of the Emperor | +2 | Grants +1 to spell attack rolls and spell save DC; succeeding on a save can force the source to save or be Stunned for 1 turn. |
| Sussur Greatsword | +1 | Hits can Silence targets that fail a DC 12 Constitution save. |
| Sword of the Emperor | +2 | Deals +1d4 damage to shapeshifters/polymorphed creatures and grants +2 to saves against spells. |
| Unseen Menace | +1 | Invisible while equipped and grants Advantage on attacks; a miss removes invisibility for 2 rounds; critical hit threshold is 19. |
| Vicious Battleaxe | +2 | Critical hits deal 7 additional damage. |

**Very Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Dwarven Thrower | +2 | Returns when thrown; a dwarf deals +1d8 Bludgeoning damage on a throw, or +2d8 against Large or larger targets. |
| Foebreaker | +2 | Ignores resistance to Bludgeoning damage. |
| Halberd of Vigilance | +2 | +1 Initiative, Advantage on Perception checks, and Advantage on reaction attacks. |
| Hellfire Greataxe | +2 | Deals +1d6 Fire damage; damage grants Heat; Hellflame Cleave is a short-rest action. |
| Incandescent Staff | None | +1 ranged spell attack, Fire resistance, Fire Bolt at will, and Fireball at level 3 once per long rest. |
| Mourning Frost | +1 | Deals +1d4 Cold damage; Cold damage gains +1, and Cold spells can Chill targets. |
| Sethan | +2 | Can summon a spiritual greataxe; can Reduce a creature, lowering its weapon damage and imposing Strength-check/save Disadvantage. |
| Staff of Cherished Necromancy | +2 | Deals +1d4 Necrotic damage; Necromancy targets have save Disadvantage; spell kills grant Life Essence until long rest. |
| Staff of Spellpower | +2 | +1 spell attack and spell save DC; Arcane Battery makes the next spell cost no slot. |
| Staff of the Ram | +2 | Once per turn, a hit can push a target and Stun it, except Dragons and Huge creatures. |
| Sword of Chaos | +2 | Deals +1d4 Necrotic damage and restores 1d6 HP when it deals damage. |
| The Dancing Breeze | +2 | Whirlwind Attack strikes all nearby foes as a short-rest action. |
| Trident of the Waves | +1 | Hits make the target Wet and create a water surface. |
| Voss' Silver Sword | +2 | +1d4 to attack and damage against Githyanki, Aberrations, Fiends, and Elementals; can cast Wrathful Smite at level 1 once per short rest. |
| Woe | +2 | +1 spell attack and spell save DC; failed saves against spells restore 1d4 HP; can cast Blight at level 4 once per long rest. |

</details>

<details>
<summary>Musket-compatible weapons</summary>

**Uncommon:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Bow of Awareness | +1 | Grants +1 to Initiative rolls. |
| Crossbow of Arcane Force | +1 | Once per short rest, infuses bolts as a bonus action; ranged weapon attacks deal +1d4 Force damage for the turn. |
| Gandrel's Aspiration | +1 | Advantage against Monstrosities; Sacred Munitions can Turn undead for the rest of the turn. |
| Hellrider Longbow | +1 | Grants +3 Initiative and Advantage on Perception checks; once per turn, a hit can inflict Faerie Fire. |
| Hunting Shortbow | +1 | Advantage against Monstrosities; can cast Hunter's Mark at level 1 once per long rest. |
| Spellthief | None | A critical hit restores a level 1 spell slot once per short rest. |

**Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Bow of the Banshee | +1 | Hits can Frighten (DC 12 Wisdom); gains +1d4 to attack and damage against Frightened targets. |
| Darkfire Shortbow | +2 | Grants Fire and Cold resistance; can cast Haste at level 3 once per long rest. |
| Giantbreaker | +1 | Heavy Hitter can make targets Reeling for 2 turns. |
| Harold | +1 | Ranged weapon hits can Bane a target for 2 turns on a failed Charisma save. |
| Least Expected | +2 | While obscured, +1d4 to ranged attacks; Blinding Shot can Blind a target. |
| The Joltshooter | None | Dealing damage with the longbow grants 2 Lightning Charges. |
| The Long Arm of the Gur | +2 | Against Undead, gains +1d4 to attack and damage rolls. |
| Titanstring Bow | +1 | Adds the wielder's Strength modifier to damage; Pushing Attack can push a target 15 feet. |
| Vicious Shortbow | +2 | Critical hits deal 7 additional damage. |

**Very Rare:**

| Weapon | Enchantment | Special ability |
| --- | --- | --- |
| Blightbringer | +1 | +1d4 to attack and damage against Gnomes and Dwarves; critical hits Slow the target. |
| The Dead Shot | +2 | Lowers the critical-hit threshold by 1 and doubles proficiency bonus on ranged attacks with this bow. |
| Fabricated Arbalest | +2 | Dazzling Ray can Blind creatures in its path; Illuminating Shot can inflict Radiating Orb. |
| Hellfire Engine Crossbow | +2 | Can cast Lightning Arrow at level 4 once per long rest and pull a creature 30 feet closer. |

</details>

## Gunslinger

The Gunslinger is a firearm-focused class built around precision, timing, and specialized shots. Gunslingers use **grit points** to fuel trick shots and other combat actions, letting them adapt their attacks to the situation. At level 3, a Gunslinger's maximum becomes 3 grit points; it increases by 1 at levels 7, 11, 15, and 19. Gunslingers regain a spent grit point on critical hits or kills. The class has a maximum level of 20. Gunslingers start with 8 + their Constitution modifier hit points and gain 5 + their Constitution modifier hit points per level.

At level 3, Gunslingers choose two grit abilities, then choose one additional ability at levels 5, 9, 13, and 17. Desperados instead choose one additional grit ability every three levels starting at level 5 (levels 5, 8, 11, 14, 17, and 20), and increase their maximum grit by 1 every three levels starting at level 6 (levels 6, 9, 12, 15, and 18). Subclasses are selected at level 3.

### Character Creation

- **Default ability scores:** Strength 10, Dexterity 15 (+2 bonus), Constitution 13, Intelligence 14 (+1 bonus), Wisdom 12, Charisma 8.
- **Skill proficiencies:** choose 2 from Acrobatics, Arcana, Athletics, Intimidation, Perception, Sleight of Hand, and Survival. Sleight of Hand and Athletics are selected by default.

### Gunslinger Progression

| Level | Gunslinger features | Grit Abilities | Max Grit Points | Misc |
| --- | --- | --- | --- | --- |
| 1 | Start with 8 + Constitution modifier HP | - | - |
| 2 | Gain 5 + Constitution modifier HP | - | - | Ability to craft firearms |
| 3 | Gain 5 + Constitution modifier HP; choose a subclass | Choose 2 | 3 |
| 4 | Gain 5 + Constitution modifier HP | - | 3 | Feat |
| 5 | Gain 5 + Constitution modifier HP | Choose 1 | 3 |
| 6 | Gain 5 + Constitution modifier HP | - | 3 |
| 7 | Gain 5 + Constitution modifier HP | - | 4 |
| 8 | Gain 5 + Constitution modifier HP | - | 4 | Feat |
| 9 | Gain 5 + Constitution modifier HP | Choose 1 | 4 |
| 10 | Gain 5 + Constitution modifier HP | - | 4 |
| 11 | Gain 5 + Constitution modifier HP | - | 5 |
| 12 | Gain 5 + Constitution modifier HP | - | 5 | Feat |
| 13 | Gain 5 + Constitution modifier HP | Choose 1 | 5 |
| 14 | Gain 5 + Constitution modifier HP | - | 5 |
| 15 | Gain 5 + Constitution modifier HP | - | 6 |
| 16 | Gain 5 + Constitution modifier HP | - | 6 | Feat |
| 17 | Gain 5 + Constitution modifier HP | Choose 1 | 6 |
| 18 | Gain 5 + Constitution modifier HP | - | 6 |
| 19 | Gain 5 + Constitution modifier HP | - | 7 |
| 20 | Gain 5 + Constitution modifier HP | - | 7 | Feat |

### Feats

| Feat | Effect |
| --- | --- |
| **Gunner** | Gain proficiency with firearms. Firearms are grouped under BG3's Slings weapon category. Increase Dexterity by 1. |
| **Quick Reload** | When dual-wielding two Flintlocks, reload both as a bonus action instead of an action. Increase Dexterity by 1. |
| **Grit Adept** | Increase your maximum grit points by 2 and choose one grit ability available to a level 3 Gunslinger. |
| **Close-Quarters Gunner** | Blunderbuss attacks do not suffer penalties from nearby enemies. Once per turn, hitting a creature within 15 feet can push it 5 feet. Increase Dexterity by 1. |
| **Longarm Specialist** | Musket attacks ignore long-range penalties and gain 20 feet of normal range. Increase Dexterity by 1. |
| **Called Shot** | Once per turn, when you hit a creature with a firearm from at least 30 feet away, choose one: reduce its movement speed by 10 feet, prevent it from making reactions, or impose Disadvantage on its next attack before the end of its next turn. Increase Dexterity by 1. |
| **Spellshot Adept** | Your firearm attacks count as magical. Once per turn after casting a spell, your next firearm hit deals an extra 1d4 damage of the spell's elemental type. Increase Intelligence by 1. |

### Grit Abilities

- **Merciless Shot:** Spend up to 3 grit points and make an attack as an action. For each grit point spent, add half of one base weapon attack to the damage roll.
- **Line 'em Up:** Spend 2 grit points to deal half damage to all enemies in a 20-foot line. Targets make a saving throw with a DC of 8 + your Dexterity modifier + your proficiency bonus, taking half damage on a successful save.
- **Rapid Shot:** Spend 1 grit point to fire again as a bonus action.
- **Bite the Bullet:** As a bonus action, spend up to 3 grit points to gain temporary hit points equal to the grit spent multiplied by your proficiency bonus.
- **Shot in the Dark:** As a bonus action, spend 1 grit point to gain darkvision out to 60 feet and ignore blindness for one shot.
- **Rapid Repair:** Spend 1 grit point and make a Sleight of Hand check against a DC of 12 + the weapon's rarity: common (0), uncommon (1), rare (2), very rare (3), or legendary (4).
- **Fanning Fire (level 7+):** Spend 1-3 grit points as an action to make 2-4 firearm attacks against 1 + the grit spent number of enemies. Each shot takes an attack-roll penalty equal to the grit spent: 1 grit gives two attacks at -1 each; 3 grit gives four attacks at -3 each.
- **Tinkerer (level 5+):** Spend 1 grit point to add one modification to an equipped firearm until your next long rest. Choose one: increase its capacity by 2 bullets; increase its damage dice (Flintlock: 2d4 becomes 1d10, Blunderbuss: 1d12 becomes 2d6, or Musket: 2d6 becomes 3d4); or increase its range (Flintlock +20 feet, Blunderbuss +10 feet, or Musket +40 feet). Each firearm tracks its modification separately, so a main-hand and offhand Flintlock can be modified independently. A new modification replaces the previous one on that firearm.

#### Desperado Grit Abilities

- **Desperado's Luck (level 3+):** Once per turn, when a firearm attack would miss, spend 1 grit point to add 1d4 to the roll, potentially turning it into a hit. This interrupt does not spend a Reaction point.
- **Double Load (level 5+):** Spend 1 grit point and two bullets to deal 1.5 times damage. A natural 1 destroys the weapon until a long rest restores it; it cannot be repaired by any other means. "The gun has been damaged beyond a simple field repair. Several hours at the workbench are needed for it to fire again."
- **Close Call (level 8+):** As a reaction, spend 1 grit point to increase AC by 2 against an attack. If it misses, make a firearm attack against the attacker.
- **Last Word (level 11+):** Once per long rest, when damage would reduce you to 0 HP, spend 3 grit points to stay at 1 HP using Death Ward, then immediately make one firearm attack.

### Subclasses

#### Marksman

The Marksman specializes in accurate, high-range attacks that deal heavy damage. This subclass is strongest when it can keep enemies at a distance, with few options for close-quarters combat.

| Level | Marksman features |
| --- | --- |
| 3 | **Lock-on:** Add your proficiency bonus to damage against one targeted enemy. |
| 7 | **Long Shot:** Deal additional damage based on the distance to your target (see range damage table below). |
| 11 | **Stable Shot:** As a class action, sacrifice 20 feet of movement to gain advantage on your shot. |
| 15 | **Pinpoint Accuracy:** Gain +1 to hit at 50 feet or more, and +2 to hit at 70 feet or more. |
| 19 | **Headshot:** Spend 5 grit for an automatic critical hit. |

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
| 3 | Choose Desperado; Desperado's Luck becomes available | Choose 2 (Gunslinger progression) | 3 |
| 4 | - | - | 3 |
| 5 | Double Load becomes available | Choose 1 | 3 |
| 6 | - | - | 4 |
| 7 | Second Attack (one additional attack when taking the Attack action) | - | 4 |
| 8 | Close Call becomes available: spend 1 grit and your reaction for +2 AC against an attack; if it misses, immediately counterattack with a firearm | Choose 1 | 4 |
| 9 | - | - | 5 |
| 10 | - | - | 5 |
| 11 | Last Word becomes available | Choose 1 | 5 |
| 12 | - | - | 6 |
| 13 | - | - | 6 |
| 14 | - | Choose 1 | 6 |
| 15 | - | - | 7 |
| 16 | - | - | 7 |
| 17 | - | Choose 1 | 7 |
| 18 | - | - | 8 |
| 19 | - | - | 8 |
| 20 | - | Choose 1 | 8 |

#### Arcane Gunsman

The Arcane Gunsman combines firearms and magic. It can imbue shots with magical effects, use special ammunition, and gain spellcasting benefits through its firearm. Intelligence is the Arcane Gunsman's spellcasting ability. Its spell slots follow the D&D 5e half-caster progression, keyed to Gunslinger level; spell selection, ammunition, and firearm bonuses are still to be defined.

| Level | Arcane Gunsman features |
| --- | --- |
| 3 | Gain Arcane Gunsman spellcasting (see spell slot table)<br>**Infused Rounds:** Spend a bonus action to shoot an elementally-infused round, dealing 1d4 elemental damage |
| 7 | **Improved Infused Rounds:** Infused Rounds damage increases to 2d4<br>**Arcane Reload:** Your weapon reloads one bullet per round |
| 11 | **Mastered Infused Rounds:** Infused Rounds damage increases to 3d4<br>**Smart Shooting:** Add your intelligence modifier to your to-hit |
| 15 | **Unstable Infused Rounds:** Adds the option to use unstable infused rounds, dealing 5d4 elemental damage with a 25% chance to blow up in your face, dealing 3d4 elemental damage in a 5-foot radius centered on you. |
| 19 | When you use your action to cast a spell, you can make a ranged attack as part of the same action. |

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

These are thematic recommendations, not a finalized class spell list. The 5e Spells column refers to the [5e Spells mod](https://www.nexusmods.com/baldursgate3/mods/125).

| Spell level | BG3 base game | 5e Spells mod |
| --- | --- | --- |
| Cantrips | Fire Bolt, Ray of Frost, Shocking Grasp | Control Flames, Mind Sliver |
| 1st | Chromatic Orb, Magic Missile, Shield | Absorb Elements, Catapult, Chaos Bolt, Zephyr Strike |
| 2nd | Magic Weapon, Misty Step, Scorching Ray, Shatter | Dragon's Breath, Kinetic Jaunt, Rime's Binding Ice, Tasha's Mind Whip |
| 3rd | Counterspell, Haste, Lightning Bolt, Protection from Energy | Ashardalon's Stride, Erupting Earth, Flame Arrows, Thunder Step |
| 4th | Fire Shield, Ice Storm | Shadow of Moil, Storm Sphere, Vitriolic Sphere |
| 5th | Cone of Cold, Conjure Volley | Holy Weapon, Swift Quiver, Synaptic Static |

## Implementation Notes / Known Limitations

### Grit ability visuals

Grit abilities reuse base-game animations, prepare/cast effects and sounds copied from vanilla spells with similar effects. Weapon variants inherit them from their first variant.

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
| Infused Rounds | Branding Smite (ranged) |

Unstable Backfire is an instant sub-effect with no cast animation.

### Custom icon artwork

See [To-do.md](To-do.md) for the complete artwork checklist, exact export paths and formats, atlas slots, and stat consumers. All custom actions, passives and statuses now reference registered `GSL_*` ability icons. The new ability atlas, tooltip/controller exports, and six action-resource image sets contain temporary firearm artwork; replace those images with final art while retaining their names and atlas positions. Shooting artwork is separate from the existing firearm inventory icons. Resource images are looked up by resource `Name` under the mod's GUI folders, not by a speculative `Icon` attribute in the resource definitions. The optional 5e compatibility PAK needs no duplicate artwork.

This mod is implemented entirely through BG3's stats/.lsx data format (no custom Script Extender (BG3SE) scripting or Osiris story scripts). A few parts of the design above don't have a clean 1:1 vanilla equivalent, so they were implemented as documented, best-effort approximations. These are called out below so they're easy to find and revisit.

**Firearms, ammo and misfires**

- Firearm weapons (`WPN_GSL_Flintlock`, `WPN_GSL_Blunderbuss`, `WPN_GSL_Musket`) use the 3D models, textures and inventory icons from **Immersive Firearms by maradi** (used with the author's permission). Weapon stats and firing animations inherit from vanilla crossbows (Flintlock → Hand Crossbow, one-handed; Musket → Light Crossbow, two-handed; Blunderbuss → Heavy Crossbow, two-handed). Their custom shooting spells and the weapons' `Projectile` field use two mod projectile root templates in `RootTemplates/_merged.lsx`: `GSL_Projectile_Bullet_Straight` (`9c0f6a51-3b7e-4d2a-8f61-2e4b7c9d1a05`, main hand) and `GSL_Projectile_Bullet_Straight_OffHand` (`d4e2b8a7-6c13-4f9e-a5b0-7e1f3c2d8b96`, off-hand flintlock). These are standalone copies of vanilla `VFX_Projectile_Arrow_Normal_01` / `VFX_Projectile_Arrow_Normal_OffHand_01` that keep the original bolt trail, impact and sound effects but omit `ProjectilePath`, `OffsetMin_Bezier3` and `ShiftMin_Bezier3`, the fields that create the lobbed arc. This is the same way straight vanilla projectiles such as Eldritch Blast and Fire Bolt are defined. IF's own stats, spells and statuses are **not** included, and IF does not need to be installed. The imported assets were given new resource UUIDs and icon names (`GSL_*`) to avoid conflicts with Immersive Firearms. Equipment types use crossbow-compatible one-/two-handed animation mappings. Asset locations:
  - meshes: `Generated/Public/GunslingerClass/Firearms/`
  - textures: `Public/GunslingerClass/Assets/Firearms/`
  - visual/material/texture banks: `Public/GunslingerClass/Content/Assets/[PAK]_GSL_Firearms/_merged.lsx`
  - icon atlas: `Public/GunslingerClass/Assets/Textures/Icons/`, `GUI/Icons_GunslingerFirearms.lsx`, `Content/UI/[PAK]_UI/_merged.lsx`
  - tooltip/controller icons: `Public/Game/GUI/Assets/`
  - The `Content` banks and `RootTemplates/_merged.lsx` must be converted to `_merged.lsf` before packing (`stage_packages.py --divine` does this). Root-template conversion is required for crafted firearms and kits to be available to the game; leaving the item templates as source XML in the PAK can allow Craft to spend its charge without creating an item.
- Firearm-only conditions use vanilla `IsRangedWeaponAttack()` and `IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())`. The imported weapons use the otherwise-unused Slings proficiency group. They do not call Immersive Firearms' custom `IsFirearmAttack()` helper or require that mod's scripts.
- The shared critical-miss passive notifies the server runtime, which records the exact gun and projects hand-specific attack locks. Double Load has a separate destruction trigger; destroyed guns offer no Rapid Repair option. Ordinary repair remains outside this grit update.
- Ammo capacity (3/2/1 bullets) is granted by equipment passives. Direct grit attacks pay ammunition through `UseCosts`; reaction shots spend one bullet through native resource functors, without a second action/reaction charge. The server adds conditional ammunition costs and readiness checks to Line 'em Up, Infused Rounds, and native spells with ranged weapon attack rolls. Those conditional checks leave non-firearm weapons' existing actions/costs intact. Reloads still refill their matching pools; the runtime snapshots the result to the physical gun.

**Crafting**

- Starting at level 2, the Gunslinger gets a single **Craft** class action (`Shout_GSL_Craft`), a linked spell container that opens five options: Flintlock, Musket, Blunderbuss, Assembly Kit, and Disassembly Kit (`Shout_GSL_Craft*`). Each option spends one Gunsmithing Charge (`GunslingerCraftCharges`, restores on long rest) and an action to place the item directly into the caster's inventory via `SummonInInventory`.
- The Assembly Kit (`OBJ_GSL_AssemblyKit`) and Disassembly Kit (`OBJ_GSL_DisassemblyKit`) are craftable inventory items with their own root templates (based on the vanilla Forgery Kit's visuals), but they **do not fuse or defuse weapons yet**. BG3's native item-fusion mechanism (`ItemCombos.txt`) requires the two specific source/result stat entries to be known ahead of time, which doesn't generalize to "any magical weapon the player happens to find." Implementing this properly would need per-weapon combos or Script Extender scripting to read and re-apply an arbitrary weapon's boosts at runtime.

**Grit abilities**

- See [Grit-Ability-Report.md](Grit-Ability-Report.md) for the before/README/after comparison, exact costs, implementation references, and in-game acceptance checklist. Source tests and mocked Lua lifecycle tests are not proof of BG3 reaction timing.
- Level 3 grants two selected base grit abilities; later selections grant one, on the class/subclass schedules listed above. Tinkerer enters the level-5 pool and Fanning Fire the level-7 pool. Grit Adept uses the level-3 pool.
- Merciless Shot, Rapid Shot, Double Load, and Fanning Fire now execute weapon attacks directly, rather than spending an action on a buff followed by a second attack. Linked menus expose Merciless/Bite/Fanning's 1-3 grit tiers. Line 'em Up uses half weapon damage on enemies only, quarter damage on a successful Dexterity save.
- Tinkerer has six choices: capacity/damage/range for primary or secondary firearms. The server stores one modification per physical gun, replaces the previous choice, and clears it on long rest. Increasing capacity does not conjure bullets; reload to fill the new space.
- Rapid Repair exposes primary/secondary choices at DC 12-16, filtered by the equipped gun's rarity and repairable misfire state. It keeps the previous bonus-action timing and costs one grit. A failed check still spends those costs.
- Fanning Fire uses 2/3/4 target selections, matching ammunition costs and -1/-2/-3 attack penalties. Its penalty is removed on cast completion or cancellation. Shots require enough loaded ammunition for the entire volley: even a capacity-modified Musket holds only three bullets.
- Shot in the Dark grants native 18-metre darkvision and blindness-group immunity for the next attack. Whether this suppresses an already-active Blind status exactly as the design intends still needs an in-game check.
- **Stable Shot** now spends 6 metres (20 feet) of movement when activated; learning the feature no longer permanently removes that movement from every turn.
- Desperado's exclusive features are automatic at levels 3/5/8/11, in addition to its selected grit abilities.
  - **Desperado's Luck:** native post-roll prompt, one grit, +1d4, once-per-turn marker, no Reaction cost.
  - **Double Load:** action attack, one grit, two bullets, 1.5x weapon damage; natural 1 marks that physical gun destroyed until long rest.
  - **Close Call:** native post-roll prompt costing a Reaction and one grit. Subtracting two from the incoming roll is equivalent to +2 AC for that attack. Its resolution interrupt checks for a miss, fires a loaded usable firearm counterattack, and clears its marker on either hit or miss.
  - **Last Word:** native lethal-damage prompt costing three grit, Death Ward and a long-rest cooldown; the server requests its firearm attack after the incoming damage event, not before survival. Its lethal-prompt timing and Death Ward/1-HP interaction are high-priority in-game checks, not engine-verified claims.
- New menu tiers, repair options, and interrupts reuse existing custom icons. No additional artwork is required. Lua files and the extender config are included automatically by `stage_packages.py`.

**Feats**

- **Close-Quarters Gunner**: BG3 has no literal "disadvantage on ranged attacks while an enemy is within 5 ft" penalty to cancel, so only the push-on-hit rider is implemented (`Force(1.5, OriginToTarget)` on a firearm hit).
- **Longarm Specialist**: similarly, there's no built-in long-range disadvantage to ignore; approximated as Advantage on firearm attacks beyond 60 ft, which produces the same practical benefit.
- **Called Shot**: the README's 3-way choice (reduce speed / deny reactions / impose disadvantage) has no in-combat UI hook to let the player pick an option per use, so this always applies the "disadvantage on the target's next attack" option.
- **Spellshot Adept**: the bonus damage rider is simplified to a fixed Force-damage bonus instead of matching "the school of the spell just cast," since that needs per-school damage-type tracking with no simple functor equivalent.

**Arcane Gunsman**

- **Arcane Reload** (level 7) remains a flavor-only marker spell/passive and does not automatically replenish ammunition each round.
- **Infused Rounds** inherits vanilla ranged attack animations, range, and projectile trajectories, requires a main-hand firearm, and overrides the inherited physical/offhand damage effects and tooltip damage with its Force damage. Unstable rounds use a native d4 roll (4 = 25%) to trigger an immediate, caster-centred 1.5-metre radius backfire on a shot, whether it hits or misses.
- The recommended Arcane Gunsman spell lists substitute a small number of spells that could not be confirmed to exist under the exact vanilla/5e-mod names in the README (e.g. Shield, Lightning Bolt, Fire Shield, Ice Storm, Cone of Cold, Conjure Volley, Tasha's Mind Whip, Holy Weapon, Swift Quiver, and Synaptic Static), in favor of grep-verified alternatives of a similar level and theme (for example Color Spray, Fireball, Fear, Gust of Wind, and the Mephit fire-breath zone spell in place of the base-game spells above). These spell lists are explicitly marked in the README as "thematic recommendations, not a finalized class spell list," so this substitution is intended to be revisited/tuned rather than treated as final.

**5e Spells compatibility addon**

- `GunslingerClass_5eSpellsCompat` ships its own `Progressions.lsx` rows sharing the same `TableUUID`/`Level` as the base Arcane Gunsman progression table, on the assumption that BG3 merges same-table/same-level Progression rows contributed by separate mods (adding their `Selectors`/spell options together) when both mods are enabled. This is a common community modding pattern but was not verified in-engine in this environment; if it doesn't merge as expected, the compat addon's extra spell options may not appear without manually combining the two Progression rows.

**General**

- This repository contains the unpacked mod source tree under `GunslingerClass/`, alongside reference mods in `examples/`. `stage_packages.py` runs `validate_xml.py`, then copies the files for each PAK into `Main_Staging/` (base mod, `Generated/` meshes, `Public/Game/` icons, plus `Localization/English/`) and `5e_Compat_Staging/` (5e Spells compat add-on). Pass `--divine <path to LSLib Divine.exe>` to convert the localization `.xml` to `.loca` and the `Content` bank and `RootTemplates` `.lsx` files to `.lsf`, then pack both folders into `Packages/GunslingerClass.pak` and `Packages/GunslingerClass_5eSpellsCompat.pak` (LZ4, verified against the staged file list). Add `--no-pack` to convert and stage without packing. Without `--divine`, convert the files with LSLib ConverterApp, remove the originals, and pack each staging folder with ConverterApp (Create Package, V18 Baldur's Gate 3 Release, LZ4).
- `validate_xml.py` checks XML, the main module/localization folder layout, and public `TranslatedString` localization, then runs `validate_stats.py` to check local stats references, spell inheritance, effective cast animations/events, projectile trajectories, zone geometry, reload effects, and separate offhand attack wiring. Vanilla animation/trajectory inheritance is checked against `examples/BG3 Reference` when available; without that cache, validation explicitly reports that external fields were not checked. These checks do not parse stats in the game engine or verify behaviour in-game.
- Run the focused regression suite with `python -m unittest discover -s tests -p test_spell_data.py -v`. After installing a rebuilt PAK and restarting the game, test all five Craft choices; empty/refill each basic firearm ammo pool; fire and reload both flintlocks separately; then check class actions, Rapid Repair, Infused Rounds, and unstable backfire in combat. Verify resource costs on misses as well as hits.
- Run `python -m unittest discover -s tests -p test_staging_resources.py -v` to check root-template and visual-bank conversion, manual-conversion reporting, and conversion failure handling.
