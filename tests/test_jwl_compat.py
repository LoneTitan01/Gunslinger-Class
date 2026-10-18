from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from generate_jwl_compat import (
    DUPLICATES, LEGACY_NAME, LEGACY_ROOT, LEGACY_SOURCE, PREREQUISITE_BASES,
    MODULE, SOURCE_TEMPLATE_ALIASES, effective, load_tiers, read_jwl, records, render,
)
from validate_stats import read_stats

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / MODULE
JWL = ROOT / 'examples' / 'JWL Soul Smithing' / 'Public' / 'JWL_SoulSmithing'


class JwlCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tiers = load_tiers()
        cls.stats = read_stats([PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
        cls.source = read_jwl(JWL / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt')
        cls.entries = {}
        for folder in ('BG3 Reference', 'BG3 Gustav Reference'):
            for path in sorted((ROOT / 'examples' / folder).rglob('Weapon.txt')):
                if 'Honour' not in path.parts:
                    cls.entries.update(read_stats([path]))
        cls.entries.update(read_stats([MAIN / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt']))
        cls.entries.update(cls.source)
        cls.entries.update(cls.stats)

    def test_complete_scoped_coverage(self) -> None:
        self.assertEqual(len(self.stats), 221)
        self.assertEqual(len({t.parent for t in self.tiers}), 113)
        sources = {
            n for n in self.source
            if n.startswith('JWL_')
        }
        self.assertEqual({t.source for t in self.tiers}, sources)
        self.assertEqual(len(PREREQUISITE_BASES), 20)
        self.assertEqual(len({n for n in self.source if n.startswith('JWL_')}), 221)
        self.assertEqual(set(self.stats), {t.name for t in self.tiers})
        tier_bases = {tier.source[4:].rsplit('_UP', 1)[0] for tier in self.tiers}
        self.assertTrue(PREREQUISITE_BASES.issubset(tier_bases))
        self.assertEqual(
            sum(tier.source[4:].rsplit('_UP', 1)[0] in PREREQUISITE_BASES for tier in self.tiers),
            36,
        )

    def test_generated_resources_are_current_and_deterministic(self) -> None:
        first = render()
        self.assertEqual(first, render())
        for path, content in first.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_text(encoding='utf-8'), content)

    def test_source_enchantment_and_rarity_with_firearm_chassis(self) -> None:
        for tier in self.tiers:
            with self.subTest(source=tier.source):
                source = effective(tier.source, self.entries)
                weapon = effective(tier.name, self.entries)
                parent = effective(tier.parent, self.entries)
                self.assertEqual(weapon['Rarity'], source['Rarity'])
                enchantment = lambda fields: re.findall(
                    r'WeaponEnchantment\((\d+)\)', fields.get('DefaultBoosts', ''),
                )
                self.assertEqual(enchantment(weapon), enchantment(source))
                self.assertIn('WeaponProperty(Magical)', weapon['DefaultBoosts'])
                for field in (
                    'Damage', 'Damage Type', 'WeaponRange', 'Slot', 'Projectile',
                    'Weapon Properties', 'Proficiency Group', 'PassivesMainHand', 'PassivesOffHand',
                ):
                    self.assertEqual(weapon.get(field), parent.get(field), field)
                self.assertIn('GSL_Firearm_Misfire_Passive', weapon['PassivesOnEquip'])
                for field in ('BoostsOnEquipMainHand', 'BoostsOnEquipOffHand'):
                    for spell in re.findall(r'UnlockSpell\(([^)]+)\)', parent.get(field, '')):
                        if spell == 'Shout_MAG_WarlockSpellRestoration':
                            continue
                        self.assertIn(f'UnlockSpell({spell})', weapon.get(field, ''))

    def test_round_trip_every_exact_tier(self) -> None:
        recipes = records(PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt', 'ItemCombination')
        results = records(PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt', 'ItemCombinationResult')
        self.assertEqual(len(recipes), 442)
        self.assertEqual(len(results), 442)
        for tier in self.tiers:
            suffix = tier.name.removeprefix('WPN_GSL_')
            assembly = recipes['GSL_Assembly_' + suffix]
            disassembly = results['GSL_Disassembly_' + suffix + '_1']
            self.assertEqual(assembly['Object 2'], tier.source)
            self.assertEqual(disassembly['Result 2'], tier.source)
            self.assertEqual(disassembly['Result 1'], assembly['Object 3'])

    def test_legacy_identity_and_conflicting_source_definitions(self) -> None:
        legacy = next(t for t in self.tiers if t.source == LEGACY_SOURCE)
        self.assertEqual(legacy.name, LEGACY_NAME)
        self.assertEqual(legacy.root, LEGACY_ROOT)
        for source in DUPLICATES:
            self.assertEqual(self.source[source].fields['Rarity'], 'Legendary')
        # JWL omits Cold Snap's rarity; the Dagger_2 parent supplies Rare for both tiers.
        for number in (1, 2):
            source = f'JWL_MAG_Frost_Offhand_Dagger_UP{number}'
            tier = next(t for t in self.tiers if t.source == source)
            self.assertEqual(self.stats[tier.name].fields['Rarity'], 'Rare')

    def test_missing_source_root_has_a_disassembly_safe_alias(self) -> None:
        nodes = ET.parse(PUBLIC / 'RootTemplates' / 'JwlSourceTemplates.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        self.assertEqual(len(nodes), len(SOURCE_TEMPLATE_ALIASES))
        for node in nodes:
            fields = {a.get('id'): a.get('value') for a in node.findall('attribute')}
            source = fields['Stats']
            missing, actual = SOURCE_TEMPLATE_ALIASES[source]
            self.assertEqual(fields['MapKey'], missing)
            self.assertEqual(fields['ParentTemplateId'], actual)
            self.assertEqual(self.source[source].fields['RootTemplate'], missing)

    def test_tier_behavior_changes(self) -> None:
        def fields(base: str, number: int) -> dict[str, str]:
            tier = next(t for t in self.tiers if t.source == f'JWL_{base}_UP{number}')
            return effective(tier.name, self.entries)

        self.assertIn('Skill(Performance, 3)', fields('UND_SwordInStone', 2)['Boosts'])
        self.assertIn('MAG_InitiativeWeapon_Passive_2', fields('MAG_Ambusher_Shortsword', 1)['PassivesOnEquip'])
        self.assertIn('MAG_InitiativeWeapon_Passive_3', fields('MAG_Ambusher_Shortsword', 2)['PassivesOnEquip'])
        self.assertIn('MAG_InitiativeBonus_3_Passive', fields('MAG_OfAwareness_Bow', 3)['PassivesOnEquip'])
        self.assertIn('GSL_JWL_Blooded_Passive', fields('MAG_LowHP_IncreaseDamage_Greataxe', 2)['PassivesOnEquip'])
        self.assertIn('GSL_JWL_Obscured_Passive', fields('MAG_LC_Fleshrend_Shortsword', 1)['PassivesOnEquip'])
        self.assertIn('MAG_Fire_IncreasePiercingDamageToBurning_Passive', fields('MAG_WYRM_Farlin_Dagger', 2)['PassivesOnEquip'])
        self.assertIn('Shout_MAG_WarlockSpellRestoration_Double', fields('MAG_PHB_PactKeeper_Quarterstaff', 2)['BoostsOnEquipMainHand'])
        self.assertIn('MAG_ArcaneEnchantment_Passive_LG', fields('MAG_BasicEnchanted_Quarterstaff', 3)['PassivesOnEquip'])
        self.assertIn('MAG_ArcaneEnchantment_Passive', fields('MAG_BasicEnchanted_Quarterstaff', 1)['PassivesOnEquip'])
        self.assertIn('MAG_GreaterNecromancyStaff_LifeEssenceHarvest_Passive', fields('MAG_HigherNecromancy_Staff', 2)['PassivesOnEquip'])
        self.assertIn('AC(2)', fields('MAG_Frost_Offhand_Dagger', 2)['BoostsOnEquipOffHand'])
        self.assertEqual(fields('MAG_BG_OfEasthaven_Defender_Flail', 2)['Boosts'], 'AC(2)')
        self.assertIn('AbilityOverrideMinimum(Strength,20)', fields('MAG_Viconia_Mace', 1)['DefaultBoosts'])
        self.assertNotIn('Strength,18', fields('MAG_Viconia_Mace', 1)['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d6,Radiant)', fields('MAG_Moonlight_Glaive', 1)['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d6,Lightning)', fields('MAG_Bonded_Baneful_Shortsword', 2)['DefaultBoosts'])
        self.assertIn('Ability(Strength, 3, 24)', fields('MAG_BG_Harmonium_Halberd', 2)['Boosts'])
        self.assertIn('UnlockSpell(Shout_SteadyRanged)', fields('MAG_BG_Darkfire_Shortbow', 1)['Boosts'])
        self.assertIn('UnlockSpell(Target_MAG_HuntersMark)', fields('MAG_TheHunters_Dagger', 3)['Boosts'])
        for base in ('MAG_Vicious_Battleaxe', 'MAG_Vicious_Dagger'):
            self.assertIn('MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive', fields(base, 2)['PassivesOnEquip'])
        for base in ('MAG_Vicious_Shortbow', 'MAG_Vicious_Shortsword'):
            for number in (1, 2):
                passives = fields(base, number)['PassivesOnEquip']
                self.assertIn('GSL_Base_ViciousCritical', passives)
                self.assertIn('MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive', passives)
        for number, dc in ((1, 11), (2, 12), (3, 14)):
            self.assertEqual(
                fields('FOR_TrueSoul_Spear', number)['WeaponFunctors'],
                f'IF(not SavingThrow(Ability.Dexterity, {dc})):ApplyStatus(BLINDED, 100, 2)',
            )
        for number in (1, 2, 3):
            render = fields('MAG_Blindside_Shortsword', number)
            self.assertIn('GSL_Base_RenderMindAndBody', render['PassivesOnEquip'])
            self.assertNotIn('WeaponDamage(1d4', render['DefaultBoosts'])
        self.assertIn('MAG_AdvantageOnReactionAttack_Passive', fields('MAG_Infernal_Hellbeard_Halberd', 2)['PassivesOnEquip'])
        for base in ('FOR_IncompleteMasterwork_SussurDagger', 'FOR_IncompleteMasterwork_SussurGreatsword', 'FOR_IncompleteMasterwork_SussurSickle'):
            self.assertIn('15', fields(base, 2)['WeaponFunctors'])
        self.assertIn('14', fields('MAG_BG_OfTheBanshee_Bow', 2)['WeaponFunctors'])
        self.assertIn('15', fields('MAG_Bonded_Baneful_Shortsword', 2)['WeaponFunctors'])

    def test_adapted_effects_and_localization(self) -> None:
        effects = read_stats([MAIN / 'Stats' / 'Generated' / 'Data' / 'JwlCompatEffects.txt'])
        blooded = effects['GSL_JWL_Blooded_Passive'].fields
        self.assertIn('70,context.Source', blooded['Conditions'])
        self.assertIn('AttackedWithPassiveSourceWeapon()', blooded['Conditions'])
        self.assertEqual(blooded['StatsFunctors'], 'DealDamage(1d4,Bludgeoning,Magical)')
        shadow = effects['GSL_JWL_Obscured_Passive'].fields
        self.assertIn('IsRangedWeaponAttack()', shadow['Boosts'])
        self.assertNotIn('IsMeleeAttack()', shadow['Boosts'])
        harmony = effects['Shout_GSL_MellowHarmony_Flintlock_JWL'].fields
        self.assertEqual(harmony['SpellRoll'], 'SkillCheck(Skill.Performance,12)')
        self.assertEqual(harmony['Cooldown'], 'OncePerShortRestPerItem')
        handles = {
            node.get('contentuid')
            for node in ET.parse(ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml').findall('.//content')
        }
        for effect in effects.values():
            self.assertIn(effect.fields['Description'].split(';')[0], handles)
        texts = {
            node.get('contentuid'): node.text
            for node in ET.parse(ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml').findall('.//content')
        }
        for tier in self.tiers:
            self.assertIn(self.stats[tier.name].fields['Description'].split(';')[0], texts)
        for base, number, expected, stale in (
            ('MAG_Ambusher_Shortsword', 2, '+3 Initiative', '+1 Initiative'),
            ('MAG_Frost_Offhand_Dagger', 2, '+2 AC', '+1 AC'),
            ('MAG_Viconia_Mace', 1, 'at least 20', 'at least 18'),
            ('MAG_BasicEnchanted_Quarterstaff', 3, '+3 to spell attack', '+1 to spell attack'),
            ('MAG_Harpers_Harmonizing_Rapier', 2, 'DC 12', 'DC 15'),
        ):
            tier = next(t for t in self.tiers if t.source == f'JWL_{base}_UP{number}')
            text = texts[self.stats[tier.name].fields['Description'].split(';')[0]]
            self.assertIn(expected, text)
            self.assertNotIn(stale, text)


if __name__ == '__main__':
    unittest.main()
