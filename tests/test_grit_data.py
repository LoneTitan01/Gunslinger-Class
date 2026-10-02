from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from validate_stats import read_stats, resolve_spell, validation_errors


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
AMMO = {'Flintlock': 'GunslingerFlintlockAmmo', 'Blunderbuss': 'GunslingerBlunderbussAmmo',
        'Musket': 'GunslingerMusketAmmo'}


class GritDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = read_stats(sorted((PUBLIC / 'Stats' / 'Generated' / 'Data').glob('*.txt')))

    def fields(self, name: str) -> dict[str, str]:
        return resolve_spell(name, self.entries, {})[0]

    def test_variable_bite_the_bullet_choices(self) -> None:
        parent = self.fields('Shout_GSL_BiteTheBullet')
        self.assertEqual(parent['UseCosts'], '')
        self.assertEqual(len(parent['ContainerSpells'].split(';')), 3)
        for grit in range(1, 4):
            fields = self.fields(f'Shout_GSL_BiteTheBullet_{grit}')
            self.assertEqual(fields['UseCosts'], f'BonusActionPoint:1;GunslingerGrit:{grit}')
            status = 'GSL_BITE_THE_BULLET' if grit == 2 else f'GSL_BITE_THE_BULLET_{grit}'
            boost = self.fields(status)['Boosts']
            self.assertEqual(boost, f'TemporaryHP({"" if grit == 1 else str(grit) + "*"}ProficiencyBonus)')
            self.assertEqual(self.fields(status)['StackId'], 'TEMPORARY_HP')

    def test_merciless_is_an_attack_not_an_action_spent_on_a_buff(self) -> None:
        for weapon, resource in AMMO.items():
            for grit in range(1, 4):
                fields = self.fields(f'Projectile_GSL_MercilessShot_{weapon}_{grit}')
                self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{grit};{resource}:1')
                self.assertEqual(fields['SpellSuccess'],
                                 f'DealDamage(MainRangedWeapon*{(1 + grit / 2):g},MainRangedWeaponDamageType);ExecuteWeaponFunctors(MainHand)')
                self.assertNotIn('ApplyStatus', fields['SpellProperties'])
                self.assertIn(f"GSL_{weapon}_MainHand", fields['RequirementConditions'])

    def test_rapid_shot_fires_and_pays_bonus_action_grit_and_ammo_once(self) -> None:
        for weapon, resource in AMMO.items():
            fields = self.fields(f'Projectile_GSL_RapidShot_{weapon}')
            self.assertEqual(fields['UseCosts'], f'BonusActionPoint:1;GunslingerGrit:1;{resource}:1')
            self.assertIn('DealDamage(', fields['SpellSuccess'])
            self.assertNotIn('PiercingShot', str(fields))

    def test_line_em_up_uses_half_weapon_damage_and_quarter_on_save(self) -> None:
        fields = self.fields('Zone_GSL_LineEmUp')
        self.assertEqual(fields['Range'], '6')
        self.assertEqual(fields['SpellSuccess'], 'DealDamage(MainRangedWeapon/2,MainRangedWeaponDamageType)')
        self.assertEqual(fields['SpellFail'], 'DealDamage(MainRangedWeapon/4,MainRangedWeaponDamageType)')
        self.assertIn('Enemy()', fields['TargetConditions'])
        self.assertIn('context.Source.ProficiencyBonus', fields['SpellRoll'])

    def test_fanning_shot_count_ammo_and_penalty(self) -> None:
        for weapon, resource in AMMO.items():
            for grit in range(1, 4):
                fields = self.fields(f'Projectile_GSL_FanningFire_{weapon}_{grit}')
                self.assertEqual(fields['AmountOfTargets'], str(1 + grit))
                self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{grit};{resource}:{1 + grit}')
                self.assertIn(f'GSL_FANNING_FIRE_{grit}', fields['SpellProperties'])
                self.assertIn(f'RollBonus(Attack,-{grit})', self.fields(f'GSL_FANNING_FIRE_{grit}')['Boosts'])
                self.assertNotIn('ActionResource(ActionPoint', self.fields(f'GSL_FANNING_FIRE_{grit}')['Boosts'])

    def test_double_load_two_bullets_and_multiplier(self) -> None:
        for weapon, resource in AMMO.items():
            fields = self.fields(f'Projectile_GSL_DoubleLoad_{weapon}')
            self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:1;{resource}:2')
            self.assertIn('MainRangedWeapon*1.5', fields['SpellSuccess'])
            self.assertIn('GSL_DOUBLE_LOAD', fields['SpellProperties'])

    def test_repair_choices_have_rarity_dc_and_hand_specific_success(self) -> None:
        parent = self.fields('Shout_GSL_RapidRepair')
        self.assertEqual(parent['UseCosts'], '')
        self.assertEqual(len(parent['ContainerSpells'].split(';')), 10)
        for hand in ('Main', 'Off'):
            for dc in range(12, 17):
                fields = self.fields(f'Shout_GSL_RapidRepair_{hand}{dc}')
                self.assertEqual(fields['UseCosts'], 'BonusActionPoint:1;GunslingerGrit:1')
                self.assertEqual(fields['SpellRoll'], f'SkillCheck(Skill.SleightOfHand,{dc})')
                self.assertIn(f'GSL_REPAIR_{hand.upper()}_{dc}', fields['RequirementConditions'])
                self.assertIn(f'GSL_REPAIR_{hand.upper()}_DONE', fields['SpellSuccess'])

    def test_tinkerer_is_a_six_choice_per_hand_menu(self) -> None:
        parent = self.fields('Shout_GSL_Tinkerer')
        self.assertEqual(parent['UseCosts'], '')
        self.assertEqual(len(parent['ContainerSpells'].split(';')), 6)
        for hand in ('Main', 'Off'):
            for mode in ('Capacity', 'Damage', 'Range'):
                fields = self.fields(f'Shout_GSL_Tinkerer_{hand}{mode}')
                self.assertEqual(fields['UseCosts'], 'BonusActionPoint:1;GunslingerGrit:1')
                self.assertIn(f'GSL_FIREARM_{hand.upper()}_DISABLED', fields['RequirementConditions'])
                self.assertEqual(fields['SpellProperties'], '')
        extended = self.fields('GSL_OffHand_Flintlock_attack_Range')
        self.assertEqual(extended['TargetRadius'], '19.5')
        self.assertEqual(extended['UseCosts'], 'BonusActionPoint:1;GunslingerOffhandFlintlockAmmo:1')

    def test_reaction_shot_has_no_action_cost_but_consumes_the_equipped_ammo(self) -> None:
        fields = self.fields('Projectile_GSL_ReactionShot')
        self.assertEqual(fields['UseCosts'], '')
        for resource in AMMO.values():
            self.assertIn(f'UseActionResource(SELF,{resource},1,0)', fields['SpellProperties'])
            self.assertIn(f"HasActionResource('{resource}',1,0)", fields['RequirementConditions'])
        self.assertIn('GSL_FIREARM_MAIN_DISABLED', fields['RequirementConditions'])

    def test_all_explicit_stat_localization_references_exist(self) -> None:
        localization = ET.parse(ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml')
        handles = {content.get('contentuid') for content in localization.findall('content')}
        for entry in self.entries.values():
            for key in ('DisplayName', 'Description'):
                value = entry.fields.get(key, '')
                if value.startswith('h'):
                    with self.subTest(entry=entry.name, field=key):
                        self.assertIn(value.split(';')[0], handles)

    def test_missing_interrupt_unlock_is_detected(self) -> None:
        self.entries['GSL_Desperado_CloseCallUnlock'].fields['Boosts'] = 'UnlockInterrupt(Interrupt_GSL_Missing)'
        self.assertTrue(any('missing local stat reference Interrupt_GSL_Missing' in error
                            for error in validation_errors(self.entries, {})))

    def test_desperado_reactions_are_native_interrupts_not_free_passive_bonuses(self) -> None:
        for passive, interrupt in (
            ('GSL_Desperado_DesperadosLuckUnlock', 'Interrupt_GSL_DesperadosLuck'),
            ('GSL_Desperado_CloseCallUnlock', 'Interrupt_GSL_CloseCall'),
            ('GSL_Desperado_LastWordUnlock', 'Interrupt_GSL_LastWord'),
        ):
            self.assertEqual(self.entries[passive].fields['Boosts'], f'UnlockInterrupt({interrupt})')
            self.assertEqual(self.entries[interrupt].kind, 'InterruptData')
        luck = self.entries['Interrupt_GSL_DesperadosLuck'].fields
        self.assertEqual(luck['Cost'], 'GunslingerGrit:1')
        self.assertIn('AdjustRoll(1d4)', luck['Properties'])
        self.assertIn('GSL_DESPERADOS_LUCK_USED', luck['Conditions'])
        close = self.entries['Interrupt_GSL_CloseCall'].fields
        self.assertEqual(close['Cost'], 'ReactionActionPoint:1;GunslingerGrit:1')
        self.assertIn('AdjustRoll(-2)', close['Properties'])
        last = self.entries['Interrupt_GSL_LastWord'].fields
        self.assertEqual(last['Cost'], 'GunslingerGrit:3')
        self.assertIn('IsKillingBlow()', last['Conditions'])
        self.assertIn('DEATH_WARD', last['Properties'])

    def test_progression_grit_and_selection_schedules_match_readme(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        for subclass in ('Marksman', 'ArcaneGunsman', 'Desperado'):
            relevant = [row for row in rows if row['Name'] in ('Gunslinger', subclass)]
            picks = sorted(int(row['Level']) for row in relevant if 'GritAbility' in row.get('Selectors', ''))
            increases = sorted(int(row['Level']) for row in relevant if 'ActionResource(GunslingerGrit' in row.get('Boosts', ''))
            self.assertEqual(picks, [3, 5, 8, 11, 14, 17, 20] if subclass == 'Desperado' else [3, 5, 9, 13, 17])
            self.assertEqual(increases, [3, 6, 9, 12, 15, 18] if subclass == 'Desperado' else [3, 7, 11, 15, 19])
            for row in relevant:
                if 'GritAbility' in row.get('Selectors', ''):
                    self.assertIn(f',{2 if row["Level"] == "3" else 1},GritAbility)', row['Selectors'])


if __name__ == '__main__':
    unittest.main()
