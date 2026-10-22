from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from uuid import UUID

from generate_base_conversions import CONVERSIONS, PUBLIC, render
from validate_stats import read_stats


def read_combinations(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding='utf-8-sig')
    return {
        match[1]: dict(re.findall(r'^data "([^"]+)" "(.*)"$', match[2], re.M))
        for match in re.finditer(
            r'^new ItemCombination(?:Result)? "([^"]+)"\n(.*?)(?=^new |\Z)',
            text,
            re.M | re.S,
        )
    }


class PrerequisiteBaseConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.weapon_path = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        cls.combo_path = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        cls.root_path = PUBLIC / 'RootTemplates' / '_merged.lsx'
        cls.passive_path = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerBaseConversionPassives.txt'
        cls.weapons = read_stats([cls.weapon_path])
        cls.combinations = read_combinations(cls.combo_path)
        cls.templates = {
            node.find("attribute[@id='Stats']").get('value'): {
                attribute.get('id'): attribute.get('value')
                for attribute in node.findall('attribute')
            }
            for node in ET.parse(cls.root_path).findall(".//node[@id='GameObjects']")
            if node.find("attribute[@id='Stats']") is not None
        }
        cls.passives = read_stats([cls.passive_path])

    def test_generator_output_is_current(self) -> None:
        for path, content in render().items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding='utf-8-sig'), content)

    def test_all_prerequisite_conversions_have_unique_ids_and_firearm_parents(self) -> None:
        self.assertEqual(len(CONVERSIONS), 21)
        self.assertEqual(len({conversion.source for conversion in CONVERSIONS}), 21)
        self.assertEqual(len({conversion.name for conversion in CONVERSIONS}), 21)
        for conversion in CONVERSIONS:
            with self.subTest(conversion=conversion.label):
                stat = self.weapons[conversion.name]
                parent = f'WPN_GSL_{conversion.kind}'
                self.assertEqual(stat.parent, parent)
                self.assertEqual(stat.kind, 'Weapon')
                self.assertEqual(stat.fields['RootTemplate'], conversion.root)
                self.assertIn('WeaponProperty(Magical)', stat.fields['DefaultBoosts'])
                UUID(stat.fields['RootTemplate'])
                self.assertIn('UnlockSpell(Shout_GSL_Repair_Main)', self.effective(parent, 'BoostsOnEquipMainHand'))
                self.assertIn('GSL_Firearm_Misfire_Passive', self.effective(conversion.name, 'PassivesOnEquip'))
                self.assertIn(conversion.name, self.templates)
                template = self.templates[conversion.name]
                self.assertEqual(template['MapKey'], conversion.root)
                self.assertEqual(template['Name'], conversion.name)
                self.assertEqual(
                    template['ParentTemplateId'],
                    self.templates[parent]['ParentTemplateId'],
                )
                self.assertEqual(template['Type'], 'item')

    def test_all_recipes_round_trip_the_exact_source_item(self) -> None:
        for conversion in CONVERSIONS:
            with self.subTest(conversion=conversion.label):
                suffix = conversion.name.removeprefix('WPN_GSL_')
                parent = f'WPN_GSL_{conversion.kind}'
                assembly_name = f'GSL_Assembly_{suffix}'
                assembly = self.combinations[assembly_name]
                assembled = self.combinations[assembly_name + '_1']
                self.assertEqual(assembly['Object 1'], 'OBJ_GSL_AssemblyKit')
                self.assertEqual(assembly['Object 2'], conversion.source)
                self.assertEqual(assembly['Object 3'], parent)
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in (1, 2, 3)],
                    ['Consume', 'Consume', 'Transform'],
                )
                self.assertEqual(assembled['Result 1'], conversion.name)

                disassembly_name = f'GSL_Disassembly_{suffix}'
                disassembly = self.combinations[disassembly_name]
                returned = self.combinations[disassembly_name + '_1']
                self.assertEqual(disassembly['Object 1'], conversion.name)
                self.assertEqual(disassembly['Object 2'], 'OBJ_GSL_DisassemblyKit')
                self.assertEqual(returned['Result 1'], parent)
                self.assertEqual(returned['Result 2'], conversion.source)

    def test_base_adaptations_include_the_requested_behavior_overlays(self) -> None:
        expected = {
            'WPN_GSL_Flintlock_AdamantineScimitarMagical': 'GSL_Flintlock_AdamantineScimitar_Passive',
            'WPN_GSL_Flintlock_Belm': 'Target_MAG_PHB_ScimitarOfSpeed_BonusAttack',
            'WPN_GSL_Flintlock_Blightbringer': 'MAG_BG_SlowedOnCrit_Passive',
            'WPN_GSL_Musket_BloodBoundBlade': 'MAG_BoundToBeBonded_Passive',
            'WPN_GSL_Musket_CruelSting': 'MAG_Drowelf_PoisonAgainstEnsnared_Passive',
            "WPN_GSL_Musket_DukeRavengardsLongsword": 'MAG_WYRM_Commander_Longsword_Passive',
            'WPN_GSL_Flintlock_HellfireHandCrossbow': 'MAG_Orthon_Hellfire_Crossbow_Passive',
            'WPN_GSL_Flintlock_KnifeOfTheUndermountainKing': 'GSL_Base_KnifeUndermountain',
            'WPN_GSL_Flintlock_KurwinsCauterizer': 'MAG_LC_BurnOnDamage_Scimitar_Passive',
            'WPN_GSL_Flintlock_LeastExpected': 'MAG_Shadow_Blinding_Bow_Passive',
            'WPN_GSL_Blunderbuss_LoviatarsScourge': 'GSL_Base_LoviatarScourge',
            'WPN_GSL_Flintlock_PelorsunBlade': 'GSL_Base_Pelorsun',
            'WPN_GSL_Flintlock_RenderOfMindAndBody': 'GSL_Base_RenderMindAndBody',
            'WPN_GSL_Blunderbuss_ReturningPike': 'GSL_Firearm_Misfire_Passive',
            'WPN_GSL_Flintlock_Stillmaker': 'Target_MAG_Bhaalist_Hold_Person',
            'WPN_GSL_Flintlock_TheDancingBreeze': 'Zone_GSL_WhirlwindShot_Flintlock',
            'WPN_GSL_Flintlock_ThornBlade': 'Projectile_GSL_EnsnaringShot_Flintlock',
            'WPN_GSL_Musket_ThermodynamoAxe': 'MAG_Fire_HeatOnWeaponDamage_Passive',
            'WPN_GSL_Flintlock_ViciousShortbow': 'GSL_Base_ViciousCritical',
            'WPN_GSL_Flintlock_ViciousShortsword': 'GSL_Base_ViciousCritical',
            'WPN_GSL_Musket_VisionOfTheAbsolute': 'FOR_TrueSoul_SpearPassive',
        }
        self.assertEqual(set(expected), {conversion.name for conversion in CONVERSIONS})
        for stat_name, behavior in expected.items():
            with self.subTest(weapon=stat_name, behavior=behavior):
                stat = self.weapons[stat_name]
                inherited = self.effective(stat_name, 'BoostsOnEquipMainHand')
                passives = self.effective(stat_name, 'PassivesOnEquip')
                self.assertTrue(
                    behavior in inherited or behavior in passives or behavior in stat.fields.get('DefaultBoosts', ''),
                    f'{stat_name} is missing expected behavior {behavior}',
                )
        returning_pike = self.weapons['WPN_GSL_Blunderbuss_ReturningPike']
        self.assertNotIn('MAG_HomingWeapon_Passive', returning_pike.fields.get('PassivesOnEquip', ''))

    def effective(self, name: str, field: str) -> str:
        visited: set[str] = set()
        while name:
            self.assertNotIn(name, visited, f'Inheritance cycle at {name}')
            visited.add(name)
            stat = self.weapons[name]
            if field in stat.fields:
                return stat.fields[field]
            name = stat.parent
        return ''


if __name__ == '__main__':
    unittest.main()
