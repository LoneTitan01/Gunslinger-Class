# JWL Soul Smithing compatibility implementation plan

## Implemented scope

The optional module authors all 221 distinct tiers across 113 weapon families.
The 20 prerequisite families have base firearm conversions in the main
Gunslinger module, and their 36 JWL upgrade tiers are now included here.

Current implementation:

- `generate_jwl_compat.py` joins exact `JWL_<base-stat>_UP<n>` identities to
  main-module recipes, rather than traversing JWL's malformed recipe graph.
  Its pinned source hash, audited prerequisite families, and 113/221 count
  guards replace the proposed separate manifest.
- The optional module contains 221 firearms, 221 firearm templates, 442
  recipes, and 442 recipe-result records.
- UUIDv5 IDs are deterministic; Faithbreaker UP1 keeps its legacy stat,
  template, and recipe IDs.
- Tier rarity/enchantment, audited behavior overlays, and English weapon
  descriptions are generated. Firearm-aware effects and the prerequisite base
  conversions are supplied by the main package.
- `generate_base_conversions.py` generates 20 main-module conversions from
  exact base stat IDs found in the bundled JWL recipes. Their firearm root
  templates are derived from the corresponding base firearms.
- One additional source-template alias repairs Wavemother's Sickle UP1's
  missing root UUID without overriding JWL stats or smithing recipes.
- Ketheric's Warhammer and Xyanyde have conflicting duplicate declarations,
  not identical duplicates. The audited final Legendary declarations are
  explicitly selected. Their Very Rare variants cannot be represented as
  separate tiers because JWL reuses the same stat IDs.
- Cold Snap's omitted rarity resolves to Rare for both tiers; compatibility
  preserves that source value rather than silently assigning Legendary.

Regeneration and verification:

```powershell
python generate_base_conversions.py
python generate_base_conversions.py --check
python generate_jwl_compat.py
python generate_jwl_compat.py --check
python -m unittest tests.test_base_conversions
python -m unittest discover -s tests -p "test_*compat.py"
python validate_xml.py
python stage_packages.py --divine <path to Divine.exe> --weapon-compat
```

`tests/test_jwl_compat.py` covers scoped completeness, deterministic output,
rarity/enchantment, firearm chassis and equipment actions, exact-tier
round-trips, legacy identity, source aliases, behavior overlays, and
localization. Actual crafting UI, duplicate-stat engine behavior, and reaction
timing still require the in-game acceptance checks below.

## Compatibility behavior

`GunslingerClass_JWL_WeaponCopiesCompat` supports every weapon tier shipped in
`examples/JWL Soul Smithing`.

The completed optional add-on must:

- accept each exact JWL Soul Smithing weapon stat as an Assembly Kit material;
- combine it with the same Flintlock, Musket, or Blunderbuss used by the
  corresponding vanilla conversion;
- preserve the JWL tier's rarity, enchantment, and upgraded behavior while
  retaining the firearm-specific adaptation;
- disassemble back into the exact JWL item that was consumed;
- remain separate from the main Gunslinger PAK and require both
  `GunslingerClass` and `JWL_SoulSmithing`;
- preserve the existing Faithbreaker UP1 firearm identity for save
  compatibility.

This plan does not make the Gunslinger PAK override JWL's own recipes. JWL
continues to upgrade the original weapon, after which that exact upgraded item
can be assembled into a firearm. Directly applying a JWL smithing hammer to an
already assembled firearm is out of scope unless it is added as a separately
designed feature later.

## Source audit

The bundled source reports module `Version64` `36028797018963975`
(`1.0.0.7`). That audited version declares:

| Measure | Count |
| --- | ---: |
| Named weapons in `upgrades_list.txt` | 113 |
| Distinct JWL upgrade-tier stat IDs | 221 |
| JWL-prefixed weapon declarations | 223 |
| Duplicate declarations | 2 |
| Gunslinger base firearm conversions | 113 |
| Prerequisite conversions implemented in the main module | 20 |
| Compatibility tiers implemented now | 221 |
| Excluded tiers requiring new base conversions | 0 |

The final compatibility module therefore needs 221 firearm stats, 221 root
templates, 221 assembly recipes, and 221 disassembly recipes. Each recipe also
has its matching `ItemCombinationResult`, for 884 item-combination records in
total. The current Faithbreaker UP1 records count toward those totals.

The authoritative inputs are:

- `examples/JWL Soul Smithing/upgrades_list.txt`
- `examples/JWL Soul Smithing/Public/JWL_SoulSmithing/Stats/Generated/Data/Weapon.txt`
- `examples/JWL Soul Smithing/Public/JWL_SoulSmithing/Stats/Generated/ItemCombos.txt`
- `examples/JWL Soul Smithing/Public/JWL_SoulSmithing/RootTemplates/jwl-upgraded-gear.lsx`
- `GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/Weapon.txt`
- `GunslingerClass/Public/GunslingerClass/Stats/Generated/ItemCombos.txt`

JWL's item-combination graph is evidence, not a safe generation source by
itself. The checked-in compatibility manifest described below is the canonical
mapping.

## Source defects that must be handled

The audited JWL files contain valid weapon stats for the affected tiers, but
several recipe links are malformed:

| Weapon | Defect |
| --- | --- |
| Blood-Bound Blade | The first recipe consumes `JWL_MAG_Bonded_Lethal_Longsword_UP1` and produces the same stat instead of consuming the base weapon. |
| Cold Snap | The first recipe consumes `JWL_MAG_Frost_Offhand_Dagger_UP1` and produces the same stat instead of consuming the base weapon. |
| Deep Delver | The first recipe consumes `JWL_UND_KC_Elder_Warpick_UP1` and produces the same stat instead of consuming the base weapon. |
| Harold | Its Legendary recipe consumes Harmonium Halberd UP1. |
| The Joltshooter | Its Legendary recipe consumes Sylvan Scimitar UP1. |
| Vicious Battleaxe | Its Legendary recipe consumes Twist of Fortune UP1. |
| Xyanyde | `JWL_GOB_DrowCommander_Mace_UP1` is declared twice. |
| Ketheric's Warhammer | `JWL_MAG_Ketheric_Warhammer_UP1` is declared twice. |
| Wavemother's Sickle | UP1's stat points to `a4fbc198-0cf1-4e4c-96a1-22d3c3d15948`, but the source template uses `a3c1e1da-7633-49f5-b807-0ae53fbf238e`. |

Implementation rules:

1. Map tiers by explicit weapon family and stat ID, not by recursively walking
   `Object 2 -> Result 1`.
2. Pin the final Legendary declarations for the two known conflicting
   duplicate IDs. Reject any source-stat change until explicitly re-audited;
   never silently accept another duplicate or invent replacement source IDs.
3. Add a regression test that records these known anomalies and fails if a new
   self-link, cross-family link, duplicate stat, missing template, or missing
   tier appears. The known Wavemother root mismatch is covered by its template
   alias; JWL's own smithing links remain untouched.
4. Do not copy or repair JWL's own malformed smithing recipes in this add-on.
   Compatibility assembly consumes the resulting tier item by exact stat ID,
   regardless of how the player obtained it.

## Compatibility data model

Add a checked-in manifest, for example
`tools/jwl_compat_manifest.py`, with one record per named weapon:

```python
JwlWeapon(
    name="Faithbreaker",
    kind="Musket",
    base_source="GOB_GoblinKing_Warhammer",
    firearm_parent="WPN_GSL_Musket_Faithbreaker",
    tiers=(
        JwlTier("JWL_GOB_GoblinKing_Warhammer_UP1", "Rare"),
        JwlTier("JWL_GOB_GoblinKing_Warhammer_UP2", "VeryRare"),
        JwlTier("JWL_GOB_GoblinKing_Warhammer_UP3", "Legendary"),
    ),
)
```

Each tier record should also declare any semantic override needed beyond the
standard rarity/enchantment transfer:

- replacement adapted passive;
- replacement firearm spell or weapon action;
- changed numeric parameter;
- damage-type translation;
- a deliberate retained base-firearm behavior.

Generate and check in the three compatibility resources from this manifest:

- `GunslingerClass/Public/GunslingerClass_JWL_WeaponCopiesCompat/Stats/Generated/Data/Weapon.txt`
- `GunslingerClass/Public/GunslingerClass_JWL_WeaponCopiesCompat/Stats/Generated/ItemCombos.txt`
- `GunslingerClass/Public/GunslingerClass_JWL_WeaponCopiesCompat/RootTemplates/_merged.lsx`

Generation should be deterministic. Running it twice must produce no diff.
Generated files should contain a header identifying the generator and should
not be edited manually.

### Stat naming and save compatibility

Use:

```text
WPN_GSL_<Kind>_<BaseSlug>_JWL_UP<n>
```

Examples:

```text
WPN_GSL_Musket_Faithbreaker_JWL_UP2
WPN_GSL_Musket_Faithbreaker_JWL_UP3
WPN_GSL_Flintlock_Ambusher_JWL_UP1
```

Keep the existing `WPN_GSL_Musket_Faithbreaker_JWL` stat and
`803d4d12-1c23-4107-836a-2c783c967a11` root template as Faithbreaker UP1.
Changing that identity would invalidate existing saves and crafted items. The
manifest should allow this one legacy-name override.

Generate stable UUIDv5 root-template IDs from the compatibility module UUID and
the final weapon stat name. Record the algorithm in the generator and never
regenerate IDs randomly.

### Stat inheritance

Every compatibility firearm must inherit from the matching adapted Gunslinger
weapon, not from JWL's melee/ranged weapon:

```text
JWL tier source
  supplies: tier rarity, enchantment, and tier-specific delta

existing WPN_GSL_* conversion
  supplies: firearm chassis, ammunition, repair, misfire, visuals,
            firearm-safe passives, and adapted weapon actions
```

Do not blindly copy JWL's complete `Boosts`, `PassivesOnEquip`, or unlocked
spells. Those fields can restore melee-only actions, slashing/bludgeoning
assumptions, or the source weapon's chassis. Instead:

1. Compare each JWL tier with its original weapon and preceding tier.
2. Transfer `Rarity` and the effective `WeaponEnchantment`.
3. Preserve `WeaponProperty(Magical)`.
4. Translate only the tier delta onto the existing firearm adaptation.
5. Use or add a `GSL_*` passive/spell when the original effect assumes a melee
   attack, source damage type, melee range, or source weapon action.
6. Preserve unrelated technical fields already carried by the base firearm,
   including equipment statuses and weapon functors.

This requires relaxing the current compatibility test that permits only a
`RootTemplate` override. Tier firearms need explicit, audited fields when their
JWL upgrade changes behavior.

### Recipe behavior

For every tier:

```text
Assembly Kit + exact JWL tier + base firearm
    -> tier-specific JWL compatibility firearm

tier-specific JWL compatibility firearm + Disassembly Kit
    -> base firearm + exact JWL tier
```

Required invariants:

- assembly consumes the kit and JWL item and transforms the base firearm;
- disassembly consumes the kit and transforms the compatibility firearm;
- disassembly returns the exact tier stat, never its vanilla counterpart or a
  different JWL tier;
- Flintlock results support both ranged hands; Musket and Blunderbuss results
  remain main-hand weapons;
- the result stat keeps the `WPN_GSL_(Flintlock|Musket|Blunderbuss)_` prefix so
  the Script Extender runtime registers it and injects the correct Repair
  action;
- recipe and result names are globally unique across the main and all optional
  modules.

## Prerequisite base conversions

These 20 base firearm adaptations are implemented in the main Gunslinger
module. They intentionally remain prerequisites only: their JWL upgrade tiers
are not generated into the optional module yet.

| Weapon | JWL tiers | Required work |
| --- | ---: | --- |
| Adamantine Scimitar | 2 | Add the Flintlock conversion and translate adamantine resistance bypass to Piercing. |
| Belm | 1 | Add the Flintlock conversion and a firearm-safe bonus attack. |
| Blightbringer | 2 | Add the Flintlock conversion with ancestry bonuses and Slow-on-critical behavior. |
| Blood-Bound Blade | 2 | Add the appropriate firearm conversion and bonded-weapon damage behavior; ignore the malformed first JWL recipe link. |
| Cruel Sting | 2 | Add the Musket conversion and firearm-safe Ensnaring Strike/poison behavior. |
| Duke Ravengard's Longsword | 2 | Add the Musket conversion and its commander effects. |
| Hellfire Hand Crossbow | 1 | Add the Flintlock conversion, hidden/invisible Burning trigger, and Scorching Ray action. |
| Knife of the Undermountain King | 1 | Add the Flintlock conversion with critical, reroll, and obscured-target effects. |
| Kurwin's Cauterizer | 2 | Add the Flintlock conversion and translate its burning-on-hit behavior. |
| Least Expected | 1 | Add the Flintlock conversion with obscured attack bonus and Blinding Shot. |
| Loviatar's Scourge | 3 | Add the Blunderbuss conversion, Necrotic resistance, and splash damage. Include 1d6 necrotic damage to the weilder to simulate the original enchantment. |
| Pelorsun Blade | 1 | Add the Flintlock conversion with Radiant damage and Undead advantage. |
| Render of Mind and Body | 3 | Add the Flintlock conversion with Advantage-gated Psychic damage. |
| Returning Pike | 2 | Add the Blunderbuss conversion; replace throwing behavior with an intentional firearm adaptation. |
| Stillmaker | 1 | Add the Flintlock conversion and its Hold Person action. |
| The Dancing Breeze | 1 | Add the Flintlock conversion and replace Whirlwind Attack with the documented firearm shot. |
| Thermodynamo Axe | 2 | Add the Musket conversion with Heat generation on firearm damage. |
| Vicious Shortbow | 2 | Add the Flintlock conversion with critical bonus damage. |
| Vicious Shortsword | 2 | Add the Flintlock conversion with critical bonus damage. |
| Vision of the Absolute | 3 | Add the Musket conversion with its multi-eyed-target effect and firearm-safe special action. |

The normal main-module assembly/disassembly recipes and firearm root templates
are generated by `generate_base_conversions.py`; focused structural and
round-trip tests live in `tests/test_base_conversions.py`. These base
conversions stay out of the optional JWL module so owners of the source items
can use the normal Gunslinger recipe without installing JWL.

## Complete tier inventory

The lists below account for all 113 names in JWL's `upgrades_list.txt`. The
source spells “Adamantine Scimitar” and “Sylvan Scimitar” as “Scimtar”; use the
correct display spelling in documentation and generated manifest labels while
retaining exact internal stat IDs.

### One JWL tier (26 weapons / 26 results)

Belm; Corpsegrinder; Drakethroat Glaive; Dwarven Thrower; Foebreaker; Halberd
of Vigilance; Handmaiden's Mace; Hellfire Engine Crossbow; Hellfire Greataxe;
Hellfire Hand Crossbow; Ketheric's Warhammer; Knife of the Undermountain King;
Least Expected; Moonlight Glaive; Mourning Frost; Pelorsun Blade; Ravengard's
Scourger; Sethan; Staff of Spell Power; Stillmaker; Sword of the Emperor; The
Dancing Breeze; The Dead Shot; Trident of the Waves; Wavemother's Sickle;
Xyanyde.

### Two JWL tiers (66 weapons / 132 results)

Adamantine Longsword; Adamantine Mace; Adamantine Scimitar; Ambusher; Bigboy's
Chew Toy; Blackguard's Sword; Blade of Opressed Souls; Blightbringer;
Blood-Bound Blade; Blooded Greataxe; Bow of the Banshee; Cacophony; Caitiff
Staff; Charge-Bound Warhammer; Cold Snap; Corrosive Flail; Crossbow of Arcane
Force; Cruel Sting; Darkfire Shortbow; Defender Flail; Despair of Athkalta;
Dolor Amarus; Dread Iron Dagger; Duke Ravengard's Longsword; Flail of Ages;
Fleshrender; Gleamdance Dagger; Gold Wyrmling Staff; Harmonic Dueller; Harmonium
Halberd; Harold; Hellbeard Halberd; Hellrider Longbow; Hollow's Staff;
Jorgoral's Greatsword; Kurwin's Cauterizer; Larethian's Wrath; Light of
Creation; Monster Slayer Glaive; Ne'er Misser; Phalar Aluve; Returning Pike;
Slicing Shortsword; Sorrow; Soulbreaker Greatsword; Staff of the Emperor;
Sussur Dagger; Sussur Greatsword; Sussur Sickle; Svartlebee's Woundseeker;
Sword of Clutching Umbra; Sword of Justice; Sylvan Scimitar; The Baneful; The
Joltshooter; The Skinburster; The Sparky Points; The Spellsparkler; Thermodynamo
Axe; Titanstring Bow; Twist of Fortune; Unseen Danger; Vicious Battleaxe;
Vicious Shortbow; Vicious Shortsword; Witchbreaker.

### Three JWL tiers (21 weapons / 63 results)

Assassin's Touch; Bow of Awareness; Deep Delver; Doom Hammer; Dragon's Grasp;
Everburn Blade; Exterminator's Axe; Faithbreaker; Firestoker; Hamarhraft;
Hunter's Dagger; Intransigent Warhammer; Loviatar's Scourge; Melf's First Staff;
Render of Mind and Body; Shortsword of First Blood; Speedy Reply; Spellthief;
Sword of Screams; The Watcher's Guide; Vision of the Absolute.

Total: 26 + 132 + 63 = 221 distinct compatibility results.

## Implementation audit

The source audit, all 113 base conversions, all tier overlays, tests, metadata,
and staging validation are complete for the audited bundled JWL version.
Building the PAK awaits a Divine executable, and the manual in-game checks
remain acceptance work; neither is implied by the automated resource validation.

### Phase 1: lock the manifest and audit

1. Add the 113-family manifest with all 221 exact tier stat IDs.
2. Parse the example JWL weapon stats, templates, and recipes in a source-audit
   test.
3. Assert the expected 113/221 counts.
4. Assert that each manifest tier has one effective stat and one root template.
5. Detect duplicate declarations and malformed recipe links, with the eight
   known recipe/stat defects explicitly allowlisted, plus the Wavemother root
   mismatch.
6. Fail on unmanifested new tiers so a future JWL update cannot silently ship
   unsupported weapons.

Exit criterion: every JWL tier is classified as either “existing base
conversion” or “base conversion prerequisite,” with no inferred cross-family
mapping.

### Phase 2: implement the 20 missing base conversions

Implement by firearm family so shared passives and shot actions can be reused:

1. Flintlocks: Adamantine Scimitar, Belm, Blightbringer, Hellfire Hand
   Crossbow, Knife of the Undermountain King, Kurwin's Cauterizer, Least
   Expected, Pelorsun Blade, Render of Mind and Body, Stillmaker, The Dancing
   Breeze, Vicious Shortbow, and Vicious Shortsword.
2. Muskets: Cruel Sting, Duke Ravengard's Longsword, Thermodynamo Axe, and
   Vision of the Absolute.
3. Blunderbusses: Loviatar's Scourge and Returning Pike.
4. Confirm the intended family for Blood-Bound Blade from its source
   properties; the expected choice is Flintlock if its Light/Finesse status
   matches the repository's documented priority.

Exit criterion: each source weapon has a normal main-module firearm,
round-tripping recipe, adapted behavior, and focused test.

### Phase 3: implement standard tier overlays

Generate tiers whose JWL delta consists only of rarity,
`WeaponEnchantment(n)`, `WeaponProperty(Magical)`, or unchanged effects already
adapted by the parent firearm.

For each result, verify:

- the JWL source tier and firearm parent are the manifest values;
- rarity and enchantment match the source tier;
- base firearm damage, range, ammo capacity, reload, repair, and misfire remain
  unchanged;
- no melee weapon action or source chassis field leaks into the firearm.

Exit criterion: all standard tiers assemble, disassemble, and pass structural
and semantic comparison tests.

### Phase 4: implement behavioral tier overlays

Audit every tier where JWL changes a passive, spell, numeric effect, or damage
expression. Add adapted `GSL_*` definitions in the main module when an effect
must be firearm-aware. Expected examples include:

- Bow of Awareness's initiative scaling;
- Ambusher's initiative scaling;
- Blooded Greataxe's Legendary low-HP damage passive;
- Caitiff Staff's doubled restoration action;
- Harmonic Dueller's Legendary performance action;
- Melf's First Staff's Legendary spellcasting bonus;
- tier-dependent Strength or ability changes on Harmonium Halberd and
  Handmaiden's Mace;
- damage-type-specific resistance bypass, bonus damage, and conditional damage;
- any upgraded action whose source definition performs a melee weapon attack.

Keep shared behavioral definitions in the main Gunslinger module so the
optional PAK contains only weapon records, templates, and recipes. The optional
module may depend on main-module stats but must not redefine them.

Exit criterion: every nontrivial tier has an explicit manifest policy and a
focused assertion for the intended delta.

### Phase 5: documentation, metadata, and packaging

1. Update the JWL add-on description in
   `GunslingerClass/Mods/GunslingerClass_JWL_WeaponCopiesCompat/meta.lsx` to
   remove “Faithbreaker UP1 only” and state the audited JWL version/count
   (`1.0.0.7`, 113 families, 221 tiers).
2. Update the optional compatibility table in `README.md` to report all 113
   weapon families and 221 tiers.
3. Document that the add-on must load after both required mods and remain
   enabled while any compatibility firearm exists in a save.
4. Keep `stage_packages.py --weapon-compat` as the packaging entry point.
5. Build the optional PAK with Divine so `_merged.lsx` is converted to LSF.

Exit criterion: the staged PAK contains the generated stats, recipes, compiled
templates, and updated metadata, and package listing verification reports no
missing files.

## Automated validation

Extend `tests/test_weapon_copy_compat.py` and add a focused manifest/source
audit test.

Required assertions:

1. Exactly 113 manifest families and 221 unique tier IDs exist.
2. All 221 source tier IDs resolve despite the two duplicate declarations.
3. Every tier has exactly one compatibility stat and root template.
4. Every compatibility stat has a unique stat name and UUID.
5. The existing Faithbreaker UP1 stat and UUID are unchanged.
6. Every stat inherits from its declared adapted firearm parent.
7. Every result has exactly one assembly and one disassembly path.
8. Assembly consumes the exact JWL tier; disassembly returns that same tier.
9. Recipe count is `len(stats) * 4`.
10. The firearm ingredient matches the result family.
11. All result names retain the runtime-recognized `WPN_GSL_*` prefix.
12. Effective rarity and enchantment match the JWL tier.
13. Effective firearm fields still provide ammunition, reload, repair, and
    misfire behavior.
14. No compatibility result unlocks a known melee-only source action.
15. The 20 prerequisite parent stats exist in the main module.
16. Generator output is deterministic and matches the checked-in files.
17. JWL source drift, new tiers, missing templates, or unapproved malformed
    links fail loudly.

Run the smallest relevant validation first:

```powershell
python -m unittest tests.test_weapon_copy_compat tests.test_crafting_recipes tests.test_staging_resources
python validate_xml.py
python stage_packages.py --no-pack --weapon-compat
```

Then run the full test suite before packaging.

## In-game acceptance checks

Automated tests cannot prove BG3 item-combination UI or passive timing. Test at
least one weapon from each structural and behavioral category, then perform a
full recipe smoke test.

### Representative functional matrix

- one-, two-, and three-tier families;
- one Flintlock, Musket, and Blunderbuss per tier count;
- off-hand Flintlock assembly and use;
- standard enchantment-only tier;
- tier with a changed passive;
- tier with a changed active spell;
- tier with conditional bonus damage;
- tier with resistance bypass;
- Faithbreaker UP1 loaded from a pre-expansion save;
- all six malformed-link families;
- both duplicate-declaration families.

For each representative:

1. Confirm the assembly preview names the intended firearm.
2. Craft and verify rarity, enchantment, tooltip passives, actions, and damage.
3. Fire normal, grit, and reaction shots; verify the correct ammo pool is
   charged.
4. Trigger Misfire and Repair.
5. Save, reload, unequip, re-equip, and long rest.
6. Disassemble and confirm the exact JWL tier and base firearm return.
7. Reassemble the returned items.

### Full smoke test

Use a test save or scripted inventory setup containing all 221 source tiers.
Confirm that every tier produces a valid assembly preview, creates one item,
and round-trips to its exact inputs. Record failures by manifest key so no
family can be skipped accidentally.

## Definition of done

Compatibility is complete when:

- all 113 named JWL weapon families and 221 distinct tiers are represented;
- all 20 prerequisite base conversions are implemented and tested;
- all generated stats, templates, and round-trip recipes pass validation;
- Faithbreaker UP1 remains save-compatible;
- tier-specific behavior is preserved through firearm-safe adaptations;
- the optional PAK builds and lists all expected resources;
- representative in-game behavior and the 221-tier recipe smoke test pass;
- README and module metadata no longer describe the add-on as
  Faithbreaker-only.
