import unittest

import gun_values as gv


class GunValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stats = gv.load_stats()

    def test_magic_firearms_cost_original_plus_half_base(self) -> None:
        cases = {
            # firearm: (original, base)
            'WPN_GSL_Flintlock_ArtificialLeech': ('MAG_Surgeon_Leech', 'WPN_GSL_Flintlock'),
            'WPN_GSL_Blunderbuss_LoviatarsScourge': ('GOB_PainPriest_Scourge', 'WPN_GSL_Blunderbuss'),
            'WPN_GSL_Musket_Bonesaw': ('MAG_Surgeon_Bonesaw', 'WPN_GSL_Musket'),
            'WPN_GSL_Flintlock_AdamantineScimitar': (
                'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar', 'WPN_GSL_Flintlock'),
        }
        for firearm, (original, base) in cases.items():
            with self.subTest(firearm=firearm):
                expected = gv.item_value(original, self.stats) + round(gv.item_value(base, self.stats) / 2)
                self.assertEqual(gv.item_value(firearm, self.stats), expected)

    def test_vanilla_gold_table_values(self) -> None:
        self.assertEqual(gv.item_value('WPN_HandCrossbow', self.stats), 50)
        self.assertEqual(gv.item_value('GOB_PainPriest_Scourge', self.stats), 370)

    def test_upgrade_chain_firearms_cost_one_and_a_half_times_the_previous_firearm(self) -> None:
        chains = (
            ('WPN_GSL_Flintlock', 'WPN_GSL_Flintlock_Quickshot', 'WPN_GSL_Flintlock_RunAndGun',
             'WPN_GSL_Flintlock_Diamond', 'WPN_GSL_Flintlock_BlackDiamond'),
            ('WPN_GSL_Flintlock_Diamond', 'WPN_GSL_Flintlock_InfernalDiamond'),
            ('WPN_GSL_Blunderbuss', 'WPN_GSL_Blunderbuss_InfernalIron', 'WPN_GSL_Blunderbuss_InfernalAlloy',
             'WPN_GSL_Blunderbuss_SoulCoin', 'WPN_GSL_Blunderbuss_EnrichedInfernalIron'),
            ('WPN_GSL_Musket', 'WPN_GSL_Musket_Silver', 'WPN_GSL_Musket_Advanced',
             'WPN_GSL_Musket_Paralyzing', 'WPN_GSL_Musket_Mithral'),
        )
        for chain in chains:
            for previous, firearm in zip(chain, chain[1:]):
                with self.subTest(firearm=firearm):
                    self.assertEqual(
                        gv.item_value(firearm, self.stats),
                        gv.half_up(gv.item_value(previous, self.stats) * 1.5),
                    )
        self.assertEqual(gv.item_value('WPN_GSL_Flintlock_BlackDiamond', self.stats), 255)

    def test_checked_in_values_are_current(self) -> None:
        for module in gv.MODULES:
            generated = gv.SOURCE_PUBLIC / module / 'Stats' / 'Generated'
            weapons = (generated / 'Data' / 'Weapon.txt').read_text(encoding='utf-8-sig')
            combos = (generated / 'ItemCombos.txt').read_text(encoding='utf-8-sig')
            with self.subTest(module=module):
                self.assertEqual(gv.apply_values(weapons, combos, self.stats), weapons)


if __name__ == '__main__':
    unittest.main()
