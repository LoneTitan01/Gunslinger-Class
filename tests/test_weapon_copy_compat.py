from pathlib import Path
import re
import unittest
from uuid import UUID
import xml.etree.ElementTree as ET

from validate_stats import read_stats
from generate_jwl_compat import load_tiers
from generate_mod_weapon_compat import MODS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'GunslingerClass'
MAIN = SOURCE / 'Public' / 'GunslingerClass'


def combinations(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding='utf-8-sig')
    entries = {}
    for match in re.finditer(r'^new ItemCombination(?:Result)? "([^"]+)"\n(.*?)(?=^new |\Z)',
                             text, re.MULTILINE | re.DOTALL):
        if match[1] in entries:
            raise AssertionError(f'Duplicate combination {match[1]}')
        entries[match[1]] = dict(re.findall(r'^data "([^"]+)" "(.*)"$', match[2], re.MULTILINE))
    return entries


class WeaponCopyCompatibilityTests(unittest.TestCase):
    def test_exact_audited_copy_mappings(self) -> None:
        expected = {
            'GunslingerClass_EO_WeaponCopiesCompat': {
                'EO_SickleOfBOOOAL': 'WPN_GSL_Flintlock_SickleOfBoooal',
                'EO_StrongString_Longbow': 'WPN_GSL_Musket_Titanstring',
                'EO_Bonded_Shocking_Warhammer': 'WPN_GSL_Musket_ChargeBound',
                'EO_Shadow_Shortsword': 'WPN_GSL_Flintlock_ClutchingUmbra',
                'EO_Revitalizing_Warpick': 'WPN_GSL_Blunderbuss_Hoppy',
                'EO_Slicing_Shortsword': 'WPN_GSL_Flintlock_SlicingShortsword',
                'EO_Infernal_Hellbeard_Halberd': 'WPN_GSL_Blunderbuss_Hellbeard',
                'EO_Harpers_Harmonizing_Rapier': 'WPN_GSL_Flintlock_HarmonicDueller',
                'EO_Ambusher_Shortsword': 'WPN_GSL_Flintlock_Ambusher',
                'EO_BlightBringer_Shortbow': 'WPN_GSL_Flintlock_Blightbringer',
                'EO_Blindside_Shortsword': 'WPN_GSL_Flintlock_RenderOfMindAndBody',
                'EO_Fire_HeatOnWeaponDamage_Battleaxe': 'WPN_GSL_Musket_ThermodynamoAxe',
                'EO_ThornBlade_Scimitar': 'WPN_GSL_Flintlock_ThornBlade',
            },
            'GunslingerClass_CL_WeaponCopiesCompat': {
                'CL_WPN_MAG_HillGiant_Club': 'WPN_GSL_Flintlock_HillGiantStrength',
            },
            'GunslingerClass_JWL_WeaponCopiesCompat': {
                tier.source: tier.parent for tier in load_tiers()
            },
        }
        for mod in MODS:
            expected.setdefault(mod.folder, {}).update({
                item.conversion.source: f'WPN_GSL_{item.conversion.kind}' for item in mod.weapons
            })
        actual = {}
        for module in sorted((SOURCE / 'Mods').glob('*_WeaponCopiesCompat')):
            public = SOURCE / 'Public' / module.name
            recipes = combinations(public / 'Stats' / 'Generated' / 'ItemCombos.txt')
            stats = read_stats([public / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
            actual[module.name] = {
                fields['Object 2']: stats[recipes[f'{name}_1']['Result 1']].parent
                for name, fields in recipes.items()
                if fields.get('Object 1') == 'OBJ_GSL_AssemblyKit'
            }
        self.assertEqual(actual, expected)

    def test_optional_recipes_preserve_source_and_existing_firearm_behavior(self) -> None:
        modules = sorted((SOURCE / 'Mods').glob('*_WeaponCopiesCompat'))
        self.assertTrue(modules, 'Expected optional weapon-copy compatibility modules')
        original = combinations(MAIN / 'Stats' / 'Generated' / 'ItemCombos.txt')
        main_stats = read_stats([MAIN / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
        main_nodes = ET.parse(MAIN / 'RootTemplates' / '_merged.lsx').findall(".//node[@id='GameObjects']")
        original_templates = {node.find("attribute[@id='MapKey']").get('value') for node in main_nodes}
        main_template_parents = {
            node.find("attribute[@id='Name']").get('value'): node.find("attribute[@id='ParentTemplateId']").get('value')
            for node in main_nodes
            if node.find("attribute[@id='Name']") is not None
            and node.find("attribute[@id='ParentTemplateId']") is not None
        }
        all_ids = set(main_stats)
        all_templates = set(original_templates)
        all_recipes = set(original)
        for module in modules:
            with self.subTest(module=module.name):
                public = SOURCE / 'Public' / module.name
                recipes = combinations(public / 'Stats' / 'Generated' / 'ItemCombos.txt')
                stats = read_stats([public / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
                self.assertTrue(stats)
                self.assertFalse(all_ids.intersection(stats), 'Do not override existing firearm stats')
                all_ids.update(stats)
                self.assertFalse(all_recipes.intersection(recipes), 'Do not override existing recipes')
                all_recipes.update(recipes)
                templates = ET.parse(public / 'RootTemplates' / '_merged.lsx').findall(
                    ".//node[@id='GameObjects']"
                )
                self.assertEqual(len(templates), len(stats))
                by_stat = {
                    node.find("attribute[@id='Stats']").get('value'): {
                        attr.get('id'): attr.get('value') for attr in node.findall('attribute')
                    }
                    for node in templates
                }
                self.assertEqual(set(by_stat), set(stats))
                self.assertEqual(len(recipes), len(stats) * 4)
                for name, weapon in stats.items():
                    with self.subTest(weapon=name):
                        kind = re.fullmatch(r'WPN_GSL_(Flintlock|Musket|Blunderbuss)_.+', name)
                        self.assertIsNotNone(kind, 'Runtime firearm registration requires the standard prefix')
                        base = f'WPN_GSL_{kind[1]}'
                        self.assertIn(weapon.parent, main_stats)
                        self.assertEqual(weapon.kind, 'Weapon')
                        # Mod-original firearms are built on the base firearm, like main conversions.
                        built = weapon.parent == base
                        if built:
                            self.assertTrue({'Rarity', 'DefaultBoosts', 'DisplayName', 'Description'} <= set(weapon.fields))
                            self.assertNotEqual(weapon.fields['Rarity'], 'Legendary')
                        elif module.name != 'GunslingerClass_JWL_WeaponCopiesCompat':
                            self.assertEqual(set(weapon.fields), {'RootTemplate'})
                        else:
                            self.assertIn('Rarity', weapon.fields)
                            self.assertIn('DefaultBoosts', weapon.fields)
                        root = weapon.fields['RootTemplate']
                        UUID(root)
                        self.assertNotIn(root, all_templates)
                        all_templates.add(root)
                        self.assertEqual(by_stat[name]['MapKey'], root)
                        self.assertEqual(by_stat[name]['Name'], name)
                        self.assertEqual(by_stat[name]['Type'], 'item')
                        self.assertEqual(
                            by_stat[name]['ParentTemplateId'],
                            main_template_parents[base] if built else main_stats[weapon.parent].fields['RootTemplate'],
                        )
                        assembly_results = [
                            (key, value) for key, value in recipes.items()
                            if value.get('Result 1') == name
                        ]
                        self.assertEqual(len(assembly_results), 1)
                        result_name, result = assembly_results[0]
                        assembly = recipes[result_name.removesuffix('_1')]
                        self.assertEqual(assembly['Object 1'], 'OBJ_GSL_AssemblyKit')
                        self.assertEqual(assembly['Object 3'], base)
                        self.assertEqual(
                            [assembly[f'Transform {slot}'] for slot in (1, 2, 3)],
                            ['Consume', 'Consume', 'Transform'],
                        )
                        self.assertEqual(
                            [assembly[f'Type {slot}'] for slot in (1, 2, 3)], ['Object'] * 3
                        )
                        self.assertEqual(result['ResultAmount 1'], '1')
                        self.assertEqual(result['PreviewStatsID'], name)
                        if not built:
                            original_result = next(
                                key for key, value in original.items()
                                if value.get('Result 1') == weapon.parent
                            )
                            original_assembly = original[original_result.removesuffix('_1')]
                            self.assertEqual(original_assembly['Object 3'], base)
                            self.assertNotEqual(assembly['Object 2'], original_assembly['Object 2'])
                        disassemblies = [
                            (key, value) for key, value in recipes.items()
                            if value.get('Object 1') == name
                        ]
                        self.assertEqual(len(disassemblies), 1)
                        disassembly_name, disassembly = disassemblies[0]
                        self.assertEqual(disassembly['Object 2'], 'OBJ_GSL_DisassemblyKit')
                        self.assertEqual(disassembly['Transform 1'], 'Transform')
                        self.assertEqual(disassembly['Transform 2'], 'Consume')
                        returned = recipes[f'{disassembly_name}_1']
                        self.assertEqual(returned['Result 1'], base)
                        self.assertEqual(returned['Result 2'], assembly['Object 2'])
                        self.assertEqual(returned['ResultAmount 1'], '1')
                        self.assertEqual(returned['ResultAmount 2'], '1')
                        self.assertEqual(returned['PreviewStatsID'], base)

    def test_optional_modules_declare_dependencies_and_unique_identity(self) -> None:
        identities = set()
        for meta in sorted((SOURCE / 'Mods').glob('*/meta.lsx')):
            root = ET.parse(meta)
            info = root.find(".//node[@id='ModuleInfo']")
            uuid = info.find("attribute[@id='UUID']").get('value')
            UUID(uuid)
            self.assertNotIn(uuid, identities)
            identities.add(uuid)
            if not meta.parent.name.endswith('_WeaponCopiesCompat'):
                continue
            self.assertEqual(info.find("attribute[@id='Folder']").get('value'), meta.parent.name)
            deps = root.findall(".//node[@id='Dependencies']/children/node[@id='ModuleShortDesc']")
            self.assertGreaterEqual(len(deps), 2)
            self.assertEqual(len({dep.find("attribute[@id='UUID']").get('value') for dep in deps}), len(deps))
            self.assertIn('27bc37d3-66c2-436d-8d69-f7407a1e676e', {
                dep.find("attribute[@id='UUID']").get('value') for dep in deps
            })
            for node_id in ('PublishVersion', 'TargetModes'):
                self.assertIsNotNone(info.find(f"children/node[@id='{node_id}']"))

    def test_optional_module_info_matches_known_good_addon_schema(self) -> None:
        def schema(meta: Path) -> list[tuple[str, str]]:
            info = ET.parse(meta).find(".//node[@id='ModuleInfo']")
            return [(attr.get('id'), attr.get('type')) for attr in info.findall('attribute')]

        expected = schema(SOURCE / 'Mods' / 'GunslingerClass_5eSpellsCompat' / 'meta.lsx')
        metas = sorted((SOURCE / 'Mods').glob('*_WeaponCopiesCompat/meta.lsx'))
        self.assertEqual(len(metas), 4)
        for meta in metas:
            with self.subTest(meta=meta.parent.name):
                self.assertEqual(schema(meta), expected)


if __name__ == '__main__':
    unittest.main()
