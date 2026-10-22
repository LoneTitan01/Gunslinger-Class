from dataclasses import replace
from pathlib import Path
import re
import unittest

from generate_mod_weapon_compat import (
    ATE, EFFECTS_FILE, EO, MODS, audit, firearm_kind, parse_weapons, render, sound_passive, stat_name,
    VANILLA_WEAPONS,
)
from validate_stats import read_stats

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
EXAMPLES = ROOT / 'examples'
SOURCE_DATA = {
    ATE.tag: EXAMPLES / 'Act Two Expansion' / 'Public' / 'ActTwoExpansion_41ec643a-e2ad-e69d-52c2-920a6f4a98ad',
    EO.tag: EXAMPLES / 'Encounters Overhaul' / 'Public' / 'EncountersOverhaul',
}


def entry_names(paths) -> set[str]:
    names: set[str] = set()
    for path in paths:
        names.update(re.findall(r'^new entry "([^"]+)"', path.read_text(encoding='utf-8-sig', errors='replace'), re.M))
    return names


class ModWeaponCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vanilla_names = entry_names(
            path for folder in ('BG3 Reference', 'BG3 Gustav Reference')
            for path in sorted((EXAMPLES / folder).rglob('Stats/Generated/Data/*.txt'))
        )
        cls.main_names = entry_names(sorted((MAIN / 'Stats' / 'Generated' / 'Data').glob('*.txt')))

    def test_generator_output_is_current(self) -> None:
        for path, content in render().items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding='utf-8-sig').replace('\r\n', '\n'), content)

    def test_every_source_weapon_is_mapped_copied_or_excluded_with_a_reason(self) -> None:
        self.assertEqual(len(ATE.weapons), 25)
        self.assertEqual(len(EO.weapons), 3)
        for mod in MODS:
            with self.subTest(mod=mod.tag):
                audit(mod)
                self.assertTrue(all(reason.strip() for reason in mod.excluded.values()))

    def test_legendary_and_unclassified_sources_are_rejected(self) -> None:
        legendary = ATE.weapons[0].conversion
        legendary = replace(legendary, source='CHI_MAG_WPN_Longsword_Sun', label='Dawnblade', kind='Musket',
                            rarity='Legendary', enchantment=3)
        excluded = {key: value for key, value in ATE.excluded.items() if key != 'CHI_MAG_WPN_Longsword_Sun'}
        with self.assertRaisesRegex(ValueError, 'Legendary'):
            audit(replace(ATE, weapons=ATE.weapons + (replace(ATE.weapons[0], conversion=legendary),),
                          excluded=excluded))
        with self.assertRaisesRegex(ValueError, 'unclassified'):
            audit(replace(ATE, excluded=excluded))

    def test_firearm_kind_follows_the_readme_priority(self) -> None:
        self.assertEqual(firearm_kind({'Weapon Properties': 'Finesse;Thrown', 'Proficiency Group': ''}), 'Flintlock')
        self.assertEqual(firearm_kind({'Weapon Properties': 'Versatile', 'Proficiency Group': ''}), 'Musket')
        self.assertEqual(firearm_kind({'Weapon Properties': '', 'Proficiency Group': 'LightCrossbows'}), 'Musket')
        self.assertEqual(firearm_kind({'Weapon Properties': 'Heavy;Twohanded', 'Proficiency Group': ''}), 'Blunderbuss')
        entries = parse_weapons(VANILLA_WEAPONS)
        for mod in MODS:
            source = parse_weapons(VANILLA_WEAPONS + (mod.weapon_file,))
            for item in mod.weapons:
                with self.subTest(source=item.conversion.source):
                    self.assertNotIn(item.conversion.source, entries)
                    self.assertIn(item.conversion.source, source)

    def test_every_referenced_effect_exists(self) -> None:
        for mod in MODS:
            data = mod.public / 'Stats' / 'Generated' / 'Data'
            local = entry_names(sorted(data.glob('*.txt')))
            available = (
                self.vanilla_names | self.main_names | local
                | entry_names(sorted(SOURCE_DATA[mod.tag].rglob('Stats/Generated/Data/*.txt')))
            )
            stats = read_stats([data / 'Weapon.txt'])
            references: set[str] = set()
            for item in mod.weapons:
                weapon = stats[stat_name(mod, item.conversion)]
                references.update(filter(None, weapon.fields.get('PassivesOnEquip', '').split(';')))
                for field in ('Boosts', 'BoostsOnEquipMainHand'):
                    references.update(re.findall(r'Unlock(?:Spell|Interrupt)\(([^)]+)\)', weapon.fields.get(field, '')))
                references.update(re.findall(r'ApplyStatus\((\w+)', weapon.fields.get('WeaponFunctors', '')))
                if item.status_on_equip:
                    references.add(item.status_on_equip)
            for kind, name, parent, fields in mod.effects:
                references.add(parent)
                for _, value in fields:
                    references.update(re.findall(r'Unlock(?:Spell|Interrupt)\(([^)]+)\)', value))
                    references.update(re.findall(r'UseSpell\(\w+,(\w+)', value))
            # UCL_DECOMPOSE comes from UtutsCoreLibrary, a declared Encounters Overhaul dependency.
            references.discard('UCL_DECOMPOSE')
            with self.subTest(mod=mod.tag):
                self.assertEqual(sorted(references - available), [])

    def test_custom_shots_use_firearm_ammo_and_play_firearm_sounds(self) -> None:
        for mod in MODS:
            shots = {shot.name: shot for shot in mod.shots}
            if not shots:
                continue
            path = mod.public / 'Stats' / 'Generated' / 'Data' / EFFECTS_FILE
            effects = read_stats([path])
            sound = effects[sound_passive(mod)].fields
            self.assertEqual(set(re.findall(r"SpellId\('([^']+)'\)", sound['Conditions'])), set(shots))
            stats = read_stats([mod.public / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
            for item in mod.weapons:
                if item.conversion.action not in shots:
                    continue
                with self.subTest(weapon=item.conversion.label):
                    shot = shots[item.conversion.action]
                    spell = effects[shot.name]
                    self.assertEqual(spell.parent, f'GSL_MainHand_{shot.kind}_attack')
                    self.assertIn(f'Gunslinger{shot.kind}Ammo:1', spell.fields['UseCosts'])
                    self.assertIn(f"HasPassive('GSL_{shot.kind}_MainHand'", spell.fields['RequirementConditions'])
                    self.assertTrue(spell.fields['SpellSuccess'].startswith('DealDamage('))
                    weapon = stats[stat_name(mod, item.conversion)]
                    self.assertIn(sound_passive(mod), weapon.fields['PassivesOnEquip'].split(';'))
                    self.assertIn(f'UnlockSpell({shot.name})', weapon.fields['BoostsOnEquipMainHand'])

    def test_melee_only_conditions_are_replaced_with_firearm_conditions(self) -> None:
        for mod in MODS:
            for kind, name, parent, fields in mod.effects:
                text = ' '.join(value for _, value in fields)
                with self.subTest(effect=name):
                    self.assertNotIn('IsMeleeWeaponAttack()', text)
                    if 'Conditions' in dict(fields) and kind == 'PassiveData':
                        self.assertIn('IsRangedWeaponAttack()', text)


if __name__ == '__main__':
    unittest.main()
