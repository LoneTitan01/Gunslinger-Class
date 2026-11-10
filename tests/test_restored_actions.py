"""Firearm conversions keep their source weapon's special action and rarity."""

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from test_crafting_recipes import read_entry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass' / 'Stats' / 'Generated' / 'Data'
LOCALIZATION = ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'

ACTIONS = {
    'WPN_GSL_Blunderbuss_Sethan': ('Target_MAG_SpiritualStand_Greataxe', 'Target_MAG_SpiritualStand_Reduce'),
    'WPN_GSL_Blunderbuss_Gandrel': ('Shout_GSL_SacredMunitions_Blunderbuss',),
    'WPN_GSL_Blunderbuss_SacredStar': ('Zone_GSL_DawnburstScattershot_Blunderbuss',),
    'WPN_GSL_Blunderbuss_MoonlightGlaive': ('Projectile_GSL_MoonlightButterflies_Blunderbuss',),
    'WPN_GSL_Blunderbuss_Soulbreaker': ('Projectile_GSL_SoulbreakerShot_Blunderbuss',),
    'WPN_GSL_Blunderbuss_TwistOfFortune': ('Projectile_GSL_BloodMoney_Blunderbuss',),
    'WPN_GSL_Blunderbuss_UndeadBane': ('Projectile_GSL_ProfaneScourge_Blunderbuss',),
}

# Expected effect for each new spell.
EFFECTS = {
    'Shout_GSL_SacredMunitions_Blunderbuss': ('SpellProperties', 'MAG_WEAPON_ACTION_UNDEAD_TURNING_BOLT'),
    'Zone_GSL_DawnburstScattershot_Blunderbuss': ('SpellSuccess', 'ApplyStatus(BLINDED,100,3)'),
    'Projectile_GSL_MoonlightButterflies_Blunderbuss': ('SpellSuccess', 'MAG_MOONLIGHT_BUTTERFLY_AURA'),
    'Projectile_GSL_SoulbreakerShot_Blunderbuss': ('SpellSuccess', 'ApplyStatus(STUNNED,100,2)'),
    'Projectile_GSL_BloodMoney_Blunderbuss': ('SpellSuccess', 'Magical,,300,,true,false,true'),
    'Projectile_GSL_ProfaneScourge_Blunderbuss': ('SpellSuccess', 'ApplyStatus(BANE,100,3)'),
}


class RestoredActionTests(unittest.TestCase):
    def test_blunderbusses_unlock_their_source_weapon_action(self) -> None:
        for weapon, spells in ACTIONS.items():
            boosts = read_entry(DATA / 'Weapon.txt', 'entry', weapon)['BoostsOnEquipMainHand']
            for spell in spells:
                with self.subTest(weapon=weapon, spell=spell):
                    self.assertIn(f'UnlockSpell({spell})', boosts)

    def test_new_actions_are_blunderbuss_only_and_localized(self) -> None:
        localized = {node.get('contentuid') for node in ET.parse(LOCALIZATION).findall('.//content')}
        for spell, (field, effect) in EFFECTS.items():
            with self.subTest(spell=spell):
                entry = read_entry(DATA / 'GunslingerSpells.txt', 'entry', spell)
                self.assertIn(effect, entry[field])
                self.assertIn("HasPassive('GSL_Blunderbuss_MainHand',context.Source)", entry['RequirementConditions'])
                self.assertIn(entry['DisplayName'].split(';')[0], localized)
                self.assertIn(entry['Description'].split(';')[0], localized)
                if not spell.startswith('Shout_'):
                    self.assertEqual(entry['UseCosts'], 'ActionPoint:1;GunslingerBlunderbussAmmo:1')
                    self.assertEqual(entry['Cooldown'], 'OncePerShortRestPerItem')

    def test_ranged_rewrites_of_melee_only_passives(self) -> None:
        passives = DATA / 'GunslingerBaseConversionPassives.txt'
        blight = read_entry(passives, 'entry', 'GSL_Base_Blightbringer')
        self.assertIn("Tagged('DUERGAR', context.Target)", blight['Boosts'])
        self.assertIn('RollBonus(RangedWeaponAttack,1d4)', blight['Boosts'])
        self.assertIn('DamageBonus(1d4,Piercing,false)', blight['Boosts'])
        cruel = read_entry(passives, 'entry', 'GSL_Base_CruelSting')
        self.assertIn("IsRangedWeaponAttack() and HasStatus('SG_Restrained', context.Target)", cruel['Boosts'])

    def test_rarity_matches_source_weapon(self) -> None:
        expected = {
            'WPN_GSL_Flintlock_Blightbringer': 'VeryRare',
            'WPN_GSL_Flintlock_KurwinsCauterizer': 'Uncommon',
            'WPN_GSL_Blunderbuss_LoviatarsScourge': 'Uncommon',
            'WPN_GSL_Blunderbuss_ReturningPike': 'Uncommon',
            'WPN_GSL_Musket_VisionOfTheAbsolute': 'Uncommon',
            'WPN_GSL_Flintlock_LeastExpected': 'Rare',
            'WPN_GSL_Musket_ThermodynamoAxe': 'Rare',
            'WPN_GSL_Flintlock_ViciousShortbow': 'Rare',
            'WPN_GSL_Flintlock_ViciousShortsword': 'Rare',
        }
        for weapon, rarity in expected.items():
            with self.subTest(weapon=weapon):
                self.assertEqual(read_entry(DATA / 'Weapon.txt', 'entry', weapon)['Rarity'], rarity)


class ReturningRoundTests(unittest.TestCase):
    """Guns fused with a throw-and-return weapon hold one extra base round."""

    GUNS = {
        DATA / 'Weapon.txt': ('WPN_GSL_Blunderbuss_ReturningPike', 'WPN_GSL_Musket_DwarvenThrower'),
        ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass_ATE_WeaponCopiesCompat' / 'Stats' / 'Generated'
        / 'Data' / 'Weapon.txt': (
            'WPN_GSL_Flintlock_TricksterDagger_ATE',
            'WPN_GSL_Musket_TheBreacher_ATE',
            'WPN_GSL_Flintlock_AxeOfStorms_ATE',
        ),
    }

    def test_returning_guns_carry_the_extra_round_passive(self) -> None:
        for path, guns in self.GUNS.items():
            for gun in guns:
                with self.subTest(gun=gun):
                    passives = read_entry(path, 'entry', gun)['PassivesOnEquip'].split(';')
                    self.assertIn('GSL_Firearm_ReturningRound_Passive', passives)

    def test_extra_round_is_part_of_the_base_tinkerer_multiplies(self) -> None:
        lua = ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua'
        rules = (lua / 'GritRules.lua').read_text()
        server = (lua / 'BootstrapServer.lua').read_text()
        self.assertIn('Rules.ExtraRoundPassive = "GSL_Firearm_ReturningRound_Passive"', rules)
        self.assertIn('return firearm.capacity + (state.extraRounds or 0)', rules)
        self.assertIn('return Rules.BaseCapacity(state) * (1 + Rules.ModCount(state, "Capacity"))', rules)
        self.assertIn('state.extraRounds = extraRounds(item)', server)
        self.assertIn('Rules.Capacity(state) - Rules.Firearms[kind].capacity', server)


if __name__ == '__main__':
    unittest.main()
