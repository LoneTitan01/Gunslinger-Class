# In-Game Testing Checklist

Features that pass the local data tests (`python -B -m unittest discover -s tests`, the Lua tests and `validate_xml.py`) but still need to be checked in Baldur's Gate 3. Rebuild with `python stage_packages.py --divine` before testing.

Mark each item `[x]` when it works, or add a note under it describing what went wrong.

## Crafting

- [x] Firearms and ammunition can be crafted from level 2, and the crafted items have the correct stats and icons.
- [x] Using an Assembly Kit opens a combine window with exactly two slots (firearm + magic weapon) and makes the combined firearm. Using a Disassembly Kit opens one slot, and disassembling a combined firearm returns the firearm and the magic weapon.
- [x] With each optional weapon-copy compatibility add-on enabled after its dependencies, assemble every listed copied weapon with its base firearm; verify inherited abilities, ammunition, reload, and repair. Disassemble and check that the original modded weapon returns, not its vanilla equivalent. Retest vanilla assembly/disassembly and confirm unrelated modded weapons remain unsupported.
- [ ] Craft and disassemble each Flintlock, Blunderbuss, and Musket upgrade. Verify the two alternative Flintlock +3 recipes both require the Diamond Flintlock, and Advanced Musket Components combine Adamantine Slag with Rune Powder.
- [ ] Verify Quick Reload spends 1 Grit and no bonus action; Dash and Gun unlocks one free Flintlock attack after Dash; Paralyzing Shot consumes one musket cartridge and applies Paralyzed only on a failed Constitution save.
- [ ] Verify each upgrade's enchantment, attack bonus, critical range, bonus action, damage, fire resistance, piercing-resistance bypass, and Scattershot fire surface effect in-game.

## Native Ranged Attacks

- [x] **Empty gun disables vanilla ranged actions:** empty the main-hand gun; Sneak Attack (Ranged), Battle Master maneuvers and other vanilla ranged actions are greyed out, while Reload and the gun's own abilities stay available. Reload and they return. Empty the off-hand Flintlock and the vanilla off-hand ranged attack is greyed out. Unequip an empty gun and equip it on another character: it is not stuck disabled.
- [x] **Sneak Attack action:** the Sneak Attack (Ranged) action, not the on-hit reaction, spends one bullet from the main-hand gun. With 0 ammo the action is unavailable. The Sneak Attack reaction on an ordinary shot still spends only that shot's bullet.
- [x] **Battle Master ranged maneuvers:** Disarming, Distracting, Goading, Maneuvering, Menacing, Pushing and Trip Attack each spend one bullet when used with a gun and are unavailable at 0 ammo. Precision Attack does not spend an extra bullet.
- [ ] **Ranged smites and Ensnaring Strike:** ranged Branding Smite, Banishing Smite and Ensnaring Strike spend one bullet. *Check that Branding Smite does not spend more than one bullet.*
- [x] **Basic ranged attack with each gun:** the native ranged attack and Extra Attack shots spend one bullet from the main-hand Flintlock, Blunderbuss or Musket, and are unavailable when that gun is empty even if an off-hand Flintlock is loaded.
- [x] **Off-hand Flintlock:** a native off-hand ranged attack spends only the off-hand Flintlock's bullet and leaves the main-hand gun's ammo unchanged.
- [ ] **Hail of Thorns and Conjure Barrage:** each spends exactly one bullet per cast, even when Conjure Barrage hits several targets.
- [ ] **Volley and Slashing Flourish:** note how many bullets Volley (Hunter) and Slashing Flourish (College of Swords) spend. Expected is one per target attacked; report if this feels wrong.
- [x] **Special arrows:** Arrows of Slaying, Arrow of Fire, Ice, Lightning, Acid, Darkness, Detonation, Piercing, Antimagic, Wraith's Embrace, Barbed Arrow and Arrow of Many Targets (including its ricochets) fired from a gun do not spend a bullet and can be used at 0 ammo. A broken gun still cannot fire them.
- [x] **Broken gun:** with the main-hand gun broken, Sneak Attack, Battle Master maneuvers and other native ranged attacks are unavailable, while a working off-hand Flintlock can still make off-hand shots.
- [x] **Bows unaffected:** with a bow or crossbow equipped instead of a gun, all of the above work normally and are not blocked by Gunslinger ammo.

## Thorn Blade (main mod)

- [ ] **Assembly:** a vanilla Thorn Blade, an Assembly Kit and a Flintlock make the Thorn Blade Flintlock, with no other mods loaded. Disassembly returns the Flintlock and the original Thorn Blade.
- [ ] **Poison rider:** shots deal +1d4 Poison only while you are concentrating, and not otherwise.
- [ ] **Ensnaring Shot:** spends one bullet and is unavailable at 0 ammo. On a hit with a failed Strength save it Ensnares the target and starts concentration, and the Ensnare ends when concentration breaks. Once used, it stays unavailable until a long rest. It plays a gunshot sound.

## Weapon Compatibility Add-ons

Load each add-on after GunslingerClass and its source mod. For every item below, also check that the firearm shows the expected name, description, rarity and enchantment.

### Encounters Overhaul copies

- [x] **Hobgoblin's Render of Mind and Body:** the copy carried by Encounters Overhaul hobgoblins (`EO_Blindside_Shortsword`) combines into the Render of Mind and Body Flintlock, and disassembly returns the Encounters Overhaul shortsword.
- [x] **Other new copies:** Blightbringer, Thermodynamo Axe and Thorn Blade from Encounters Overhaul each assemble into their existing firearm and disassemble back to the Encounters Overhaul item.

### Encounters Overhaul originals

- [ ] **Nightwalker's Claw Flintlock:** a hit can reduce the target's maximum HP (Life Drain, DC 10 Constitution).
- [ ] **Ebonbone Scepter Musket:** grants Cone of Cold once per long rest, and Elemental Affinity boosts Cold spell damage.
- [ ] **Woe (Skull Lord variant) Musket:** shots deal +1d10 Necrotic damage and apply Decompose for 4 turns. *Decompose comes from Utut's Core Library; check it is applied rather than silently missing.*

### Act Two Expansion add-on

- [ ] **Assembly round trip:** at least one Flintlock, one Musket and one Blunderbuss conversion assembles and disassembles back to the exact Act Two Expansion weapon.
- [ ] **New firearm shots:** Ricochet Shot (Gnomish Tinkerer Crossbow), Mindcrush Shot (Silver Sword of the Comet), Hail of Thorns Shot (Ironvine Shortbow), Menacing Shot (Phasmid Longbow) and Scorching Shot (Ancient Warhammer) each:
  - spend one bullet of the right type and are unavailable at 0 ammo
  - can be used once per short rest
  - play a gunshot sound (the Blunderbuss sound for Mindcrush)
  - apply their save effect only on a failed save
- [ ] **Ricochet Shot:** the bullet ricochets to nearby creatures like an Arrow of Ricochet.
- [ ] **Assassin's Riposte (Gish Shortsword):** when an enemy misses you with a melee attack, you are offered a reaction shot that spends one bullet. It is not offered when the Flintlock is empty or broken, and it recharges on a short rest.
- [ ] **Firearm passives:**
  - Death Knight's Longsword grants Life Essence when a shot kills an enemy.
  - Sickle of Slicing deals +1d4 Piercing against Bleeding targets.
  - Silver Sword of the Comet and Gish Shortsword shots deal +1d4 Psychic.
  - Kara-Turan Katana shots ignore Piercing resistance and inflict Bleeding when made with Advantage.
- [ ] **Passives kept from the source weapons:** these still trigger from shots:
  - Faerie Fire (Firbolg Greataxe)
  - Phantasmal Force (Phasmid Longbow)
  - Ray of Enfeeblement (Enfeebling Rapier)
  - the critical-hit Cold damage (Hoarfrost Blade)
  - the shockwave (Gnomish War Pick)
  - Poison (Ironvine Shortbow)
  - the spell slot restored on a critical hit (Silver Sword of the Comet)
- [ ] **Spell unlocks still work while a gun is held:**
  - Zephyr Flash and Zephyr Break (Lance Pike)
  - Heroic Throw (The Breacher)
  - Lightning Whirlwind (Axe of Storms)
  - Gushing Air (Bow of the Thunder Lord)
  - the staff spells (Firefly Keeper, Still Wind and Sun Crystal staffs)
  - Mass Healing Word and Create Water (Trident of Healing Waters)
  - Razor Gale (Scimitar of Flowing Waters)
- [x] **Out of scope:** Dawnblade (Legendary) has no recipe and shows Invalid Combination.
