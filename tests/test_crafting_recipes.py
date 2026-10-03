from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from validate_stats import read_stats, resolve_spell

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'


def read_entry(path: Path, kind: str, name: str) -> dict[str, str]:
    content = path.read_text(encoding='utf-8-sig')
    match = re.search(
        rf'^new {re.escape(kind)} "{re.escape(name)}"\n(.*?)(?=^new |\Z)',
        content,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f'Missing {kind} entry {name}')
    return dict(re.findall(r'^data "([^"]+)" "(.*)"$', match[1], re.MULTILINE))


class CraftingRecipeTests(unittest.TestCase):
    def test_artificial_leech_recipe_is_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        assembly = read_entry(combinations, 'ItemCombination', 'GSL_Assembly_Flintlock_ArtificialLeech')
        self.assertEqual(
            [assembly[f'Object {slot}'] for slot in range(1, 4)],
            ['OBJ_GSL_AssemblyKit', 'MAG_Surgeon_Leech', 'WPN_GSL_Flintlock'],
        )
        self.assertEqual(
            [assembly[f'Transform {slot}'] for slot in range(1, 4)],
            ['Consume', 'Consume', 'Transform'],
        )
        assembly_result = read_entry(
            combinations,
            'ItemCombinationResult',
            'GSL_Assembly_Flintlock_ArtificialLeech_1',
        )
        self.assertEqual(assembly_result['Result 1'], 'WPN_GSL_Flintlock_ArtificialLeech')

        disassembly = read_entry(
            combinations,
            'ItemCombination',
            'GSL_Disassembly_Flintlock_ArtificialLeech',
        )
        self.assertEqual(disassembly['Object 1'], 'WPN_GSL_Flintlock_ArtificialLeech')
        self.assertEqual(disassembly['Transform 1'], 'Transform')
        self.assertEqual(disassembly['Object 2'], 'OBJ_GSL_DisassemblyKit')
        self.assertEqual(disassembly['Transform 2'], 'Consume')
        disassembly_result = read_entry(
            combinations,
            'ItemCombinationResult',
            'GSL_Disassembly_Flintlock_ArtificialLeech_1',
        )
        self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Flintlock')
        self.assertEqual(disassembly_result['Result 2'], 'MAG_Surgeon_Leech')

    def test_fused_firearm_has_plus_one_enchantment_and_framework_action(self) -> None:
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        fused = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_ArtificialLeech')
        self.assertEqual(fused['DefaultBoosts'], 'WeaponEnchantment(1)')
        self.assertEqual(fused['Rarity'], 'Uncommon')
        self.assertEqual(
            fused['BoostsOnEquipMainHand'],
            'UnlockSpell(GSL_MainHand_Flintlock_attack);'
            'UnlockSpell(Shout_GSL_Reload_Flintlock);'
            'UnlockSpell(Projectile_GSL_Bloodletting_Flintlock)',
        )

        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx')
        nodes = templates.findall(".//node[@id='GameObjects']")
        fused_template = next(
            node for node in nodes
            if node.find("attribute[@id='Name']").get('value') == 'WPN_GSL_Flintlock_ArtificialLeech'
        )
        self.assertEqual(fused['RootTemplate'], fused_template.find("attribute[@id='MapKey']").get('value'))
        for kit_name in ('OBJ_GSL_AssemblyKit', 'OBJ_GSL_DisassemblyKit'):
            kit = next(
                node for node in nodes
                if node.find("attribute[@id='Name']").get('value') == kit_name
            )
            action = kit.find("./children/node[@id='OnUsePeaceActions']/children/node[@id='Action']")
            self.assertIsNotNone(action)
            self.assertEqual(action.find("attribute[@id='ActionType']").get('value'), '23')
            self.assertEqual(
                action.find("./children/node[@id='Attributes']/attribute[@id='CombineSlots']").get('value'),
                '3',
            )

    def test_bloodletting_is_a_normal_ammo_using_shot_with_bleed_on_hit(self) -> None:
        entries = read_stats(sorted((PUBLIC / 'Stats' / 'Generated' / 'Data').glob('*.txt')))
        vanilla = (
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
            / 'Stats' / 'Generated' / 'Data' / 'Spell_Projectile.txt'
        )
        external = read_stats([vanilla]) if vanilla.is_file() else {}
        shot, _ = resolve_spell('GSL_MainHand_Flintlock_attack', entries, external)
        bloodletting, _ = resolve_spell('Projectile_GSL_Bloodletting_Flintlock', entries, external)
        for field in (
            'UseCosts', 'TooltipUseCosts', 'Trajectories', 'TargetRadius',
            'SpellRoll', 'SpellFlags', 'SpellProperties',
        ):
            self.assertEqual(bloodletting[field], shot[field], field)
        self.assertEqual(bloodletting['UseCosts'], 'ActionPoint:1;GunslingerFlintlockAmmo:1')
        self.assertEqual(bloodletting['SpellRoll'], 'Attack(AttackType.RangedWeaponAttack)')
        self.assertEqual(
            bloodletting['SpellSuccess'],
            shot['SpellSuccess'] + ';IF(Character()):ApplyStatus(BLEEDING,100,2)',
        )
        self.assertNotIn('BLEEDING', bloodletting.get('SpellFail', ''))
        self.assertEqual(bloodletting['Cooldown'], 'OncePerShortRest')
        self.assertIn('GSL_FIREARM_MAIN_DISABLED', bloodletting['RequirementConditions'])


if __name__ == '__main__':
    unittest.main()
