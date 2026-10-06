from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from validate_stats import read_stats, resolve_spell, validation_errors


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
AMMO = {'Flintlock': 'GunslingerFlintlockAmmo', 'Blunderbuss': 'GunslingerBlunderbussAmmo',
        'Musket': 'GunslingerMusketAmmo'}


def firearm_dice_damage(dice: int) -> str:
    flintlock = "HasPassive('GSL_Flintlock_MainHand',context.Source)"
    return (f'IF({flintlock}):DealDamage(MainRangedWeapon+{dice}d4,MainRangedWeaponDamageType);'
            f'IF(not {flintlock}):DealDamage(MainRangedWeapon+{dice}d6,MainRangedWeaponDamageType)')


class GritDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = read_stats(sorted((PUBLIC / 'Stats' / 'Generated' / 'Data').glob('*.txt')))

    def fields(self, name: str) -> dict[str, str]:
        return resolve_spell(name, self.entries, {})[0]

    def test_class_hit_points_match_d8_progression(self) -> None:
        # The engine adds the Constitution modifier to BaseHp and to each level's HpPerLevel.
        descriptions = ET.parse(PUBLIC / 'ClassDescriptions' / 'ClassDescriptions.lsx')
        base_class = next(
            node for node in descriptions.findall('.//node[@id="ClassDescription"]')
            if node.find('attribute[@id="ParentGuid"]') is None
        )
        attributes = {attribute.get('id'): attribute.get('value') for attribute in base_class.findall('attribute')}
        self.assertEqual(attributes['BaseHp'], '8')
        self.assertEqual(attributes['HpPerLevel'], '5')

    def test_kills_and_crits_restore_grit_to_the_gunslinger(self) -> None:
        fields = self.entries['GSL_GritRecovery'].fields
        self.assertEqual(fields['StatsFunctorContext'], 'OnDamage')
        self.assertIn('IsKillingBlow()', fields['Conditions'])
        self.assertTrue(
            fields['StatsFunctors'].startswith('RestoreResource(SELF,GunslingerGrit,1,0)'),
            'OnDamage functors default to the damaged creature, so grit must target SELF',
        )

    def test_grit_recovery_triggers_on_any_kill_once_per_attack(self) -> None:
        fields = self.entries['GSL_GritRecovery'].fields
        conditions = fields['Conditions']
        self.assertTrue(conditions.startswith("not HasStatus('GSL_GRIT_RECOVERY_SPENT',context.Source) and "))
        kill, crit = conditions.split(' and ', 1)[1][1:-1].split(' or ', 1)
        self.assertEqual(kill, '(IsKillingBlow() and not Item())', 'any kill counts, not only firearm kills')
        self.assertIn('IsCritical()', crit)
        self.assertNotIn('IsKillingBlow', crit)
        self.assertEqual(
            fields['StatsFunctors'],
            'RestoreResource(SELF,GunslingerGrit,1,0);ApplyStatus(SELF,GSL_GRIT_RECOVERY_SPENT,100,1)',
            'a critical kill or several kills from one attack restore only one grit',
        )
        self.assertIn('GSL_GRIT_RECOVERY_SPENT', self.entries)
        lua = (ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua' / 'BootstrapServer.lua').read_text()
        using = lua.split('Ext.Osiris.RegisterListener("UsingSpell"', 1)[1]
        self.assertLess(using.index('GSL_GRIT_RECOVERY_SPENT'), using.index('if not spell:find("GSL_"'),
                        'every new attack, including non-Gunslinger spells, re-arms Grit Recovery')

    def test_level_up_grit_choices_share_unlocked_ability_descriptors(self) -> None:
        choices = set()
        for node in ET.parse(PUBLIC / 'Lists' / 'PassiveLists.lsx').findall('.//node[@id="PassiveList"]'):
            attributes = {attribute.get('id'): attribute.get('value') for attribute in node.findall('attribute')}
            if 'Grit Abilities' in attributes.get('Name', ''):
                choices.update(attributes['Passives'].split(','))
        self.assertTrue(choices)
        checked = set()
        for name in sorted(choices):
            passive = self.fields(name)
            targets = re.findall(r'Unlock(?:Spell|Interrupt)\(([^,)]+)', passive.get('Boosts', ''))
            if not targets:
                # Rapid Repair is a marker: the server adds it to a misfired gun's Repair menu.
                self.assertIn(name, {'GSL_Desperado_CheatDeathsOdds', 'GSL_RapidRepairUnlock'})
                self.assertTrue(passive.get('Description'))
                continue
            for target in targets:
                ability = self.fields(target)
                with self.subTest(choice=name, ability=target):
                    for key in ('DisplayName', 'Description', 'Icon'):
                        self.assertTrue(ability.get(key), key)
                        self.assertEqual(passive.get(key), ability[key], key)
                    self.assertEqual(passive.get('DescriptionParams', ''), ability.get('DescriptionParams', ''))
                checked.add(name)
        self.assertEqual(checked, choices - {'GSL_Desperado_CheatDeathsOdds', 'GSL_RapidRepairUnlock'})

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
        options = [f'Projectile_GSL_MercilessShot_{grit}' for grit in range(1, 4)]
        parent = self.fields('Shout_GSL_MercilessShot')
        self.assertIn('IsLinkedSpellContainer', parent['SpellFlags'])
        self.assertEqual(parent['ContainerSpells'].split(';'), options)
        for grit, name in enumerate(options, 1):
            fields = self.fields(name)
            self.assertEqual(fields['SpellContainerID'], 'Shout_GSL_MercilessShot')
            self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{grit}')
            self.assertEqual(fields['DisplayName'], f'h10000002g0000g4000g8000g00000000000{grit};1')
            self.assertEqual(fields['SpellSuccess'], firearm_dice_damage(grit) + ';ExecuteWeaponFunctors(MainHand)')
            self.assertNotIn('MainRangedWeapon*', fields['TooltipDamageList'])
            self.assertNotIn('ApplyStatus', fields['SpellProperties'])
            self.assertIn('GSL_FIREARM_MAIN_DISABLED', fields['RequirementConditions'])
            for weapon, resource in AMMO.items():
                self.assertIn(f"(HasPassive('GSL_{weapon}_MainHand',context.Source) and "
                              f"HasActionResource('{resource}',1,0))", fields['RequirementConditions'])
                self.assertIn(f"IF(HasPassive('GSL_{weapon}_MainHand',context.Source)):"
                              f"UseActionResource(SELF,{resource},1,0)", fields['SpellProperties'])

    def test_single_grit_shots_are_one_any_gun_spell_without_a_group(self) -> None:
        shots = {
            'RapidShot': ('GSL_RapidShotUnlock', 'BonusActionPoint:1;GunslingerGrit:1', 1),
            'DoubleLoad': ('GSL_Desperado_DoubleLoadUnlock', 'ActionPoint:1;GunslingerGrit:1', 2),
            'DazingShot': ('GSL_DazingShotUnlock', 'ActionPoint:1;GunslingerGrit:2', 1),
            'FinalJudgement': ('GSL_FinalJudgementUnlock', 'ActionPoint:1;GunslingerGrit:4', 1),
        }
        for shot, (unlock, costs, ammo) in shots.items():
            name = f'Projectile_GSL_{shot}'
            with self.subTest(shot=shot):
                self.assertNotIn(f'Shout_GSL_{shot}', self.entries)
                for weapon in AMMO:
                    self.assertNotIn(f'{name}_{weapon}', self.entries)
                self.assertEqual(self.fields(unlock)['Boosts'], f'UnlockSpell({name})')
                fields = self.fields(name)
                self.assertNotIn('SpellContainerID', fields)
                self.assertEqual(fields['UseCosts'], costs)
                self.assertEqual(fields['TooltipUseCosts'], costs)
                self.assertIn('DealDamage(', fields['SpellSuccess'])
                self.assertIn('ExecuteWeaponFunctors(MainHand)', fields['SpellSuccess'])
                self.assertIn('GSL_FIREARM_MAIN_DISABLED', fields['RequirementConditions'])
                for weapon, resource in AMMO.items():
                    self.assertIn(f"(HasPassive('GSL_{weapon}_MainHand',context.Source) and "
                                  f"HasActionResource('{resource}',{ammo},0))", fields['RequirementConditions'])
                    self.assertIn(f"IF(HasPassive('GSL_{weapon}_MainHand',context.Source)):"
                                  f"UseActionResource(SELF,{resource},{ammo},0)", fields['SpellProperties'])

    def test_trick_shot_is_one_class_action_group_with_four_options(self) -> None:
        options = (
            'Projectile_GSL_DisarmingShot',
            'Projectile_GSL_WingingShot',
            'Projectile_GSL_ForcefulShot',
            'Projectile_GSL_BullyingShot',
        )
        group = self.fields('Shout_GSL_TrickShot')
        self.assertEqual(group['ContainerSpells'].split(';'), list(options))
        self.assertIn('IsLinkedSpellContainer', group['SpellFlags'].split(';'))
        self.assertEqual(self.fields('GSL_TrickShotUnlock')['Boosts'], 'UnlockSpell(Shout_GSL_TrickShot)')
        for obsolete in ('GSL_DisarmingShotUnlock', 'GSL_WingingShotUnlock',
                         'GSL_ForcefulShotUnlock', 'GSL_BullyingShotUnlock'):
            self.assertNotIn(obsolete, self.entries)
        for spell_name in options:
            with self.subTest(spell=spell_name):
                spell = self.fields(spell_name)
                self.assertEqual(spell['SpellContainerID'], 'Shout_GSL_TrickShot')
                self.assertEqual(spell['UseCosts'], 'ActionPoint:1;GunslingerGrit:1')
                self.assertEqual(spell['TooltipUseCosts'], 'ActionPoint:1;GunslingerGrit:1')
                self.assertIn('DealDamage(', spell['SpellSuccess'])
                self.assertIn('ExecuteWeaponFunctors(MainHand)', spell['SpellSuccess'])
                self.assertIn('GSL_FIREARM_MAIN_DISABLED', spell['RequirementConditions'])
                for resource in AMMO.values():
                    self.assertIn(resource, spell['RequirementConditions'])
                    self.assertIn(f'UseActionResource(SELF,{resource},1,0)', spell['SpellProperties'])
        self.assertNotIn('PiercingShot', str(self.fields('Projectile_GSL_RapidShot')))

    def test_double_or_nothing_interrupt_on_firearm_hit_has_no_reaction_cost(self) -> None:
        self.assertEqual(self.fields('GSL_Desperado_DoubleOrNothingUnlock')['Boosts'],
                         'UnlockInterrupt(Interrupt_GSL_DoubleOrNothing)')
        self.assertNotIn('Shout_GSL_DoubleOrNothing', self.entries)
        interrupt = self.fields('Interrupt_GSL_DoubleOrNothing')
        self.assertEqual(interrupt['InterruptContext'], 'OnCastHit')
        self.assertEqual(interrupt['Cost'], 'GunslingerGrit:2')
        self.assertNotIn('IsAbleToReact(context.Observer)', interrupt['Conditions'])
        for condition in ('Self(context.Source,context.Observer)',
                          'IsWeaponAttack()', 'HasDamageEffectFlag(DamageFlags.Hit)',
                          "not SpellId('Projectile_GSL_DoubleOrNothing')",
                          "not SpellId('Projectile_GSL_DoubleOrNothingAttack')",
                          "not HasStatus('GSL_FIREARM_MAIN_DISABLED',context.Observer)"):
            self.assertIn(condition, interrupt['Conditions'])
        self.assertIn('UseSpell(Projectile_GSL_DoubleOrNothing,true,true,true)', interrupt['Properties'])
        shot = self.fields('Projectile_GSL_DoubleOrNothing')
        self.assertEqual(shot['SpellRoll'], '')
        self.assertEqual(shot['UseCosts'], '')
        self.assertEqual(shot['SpellProperties'], '')
        self.assertEqual(shot['SpellSuccess'], '')
        followup = self.fields('Projectile_GSL_DoubleOrNothingAttack')
        self.assertEqual(self.entries['Projectile_GSL_DoubleOrNothingAttack'].parent, 'Projectile_GSL_ReactionShot')
        self.assertIn("HasActionResource('GunslingerFlintlockAmmo',1,0)", followup['RequirementConditions'])
        sound = self.fields('GSL_Firearm_ShotSound_MainHand')['Conditions']
        self.assertIn("SpellId('Projectile_GSL_DoubleOrNothingAttack')", sound)
        self.assertIn("SpellId('Projectile_GSL_DoubleOrNothingAttack')",
                      self.fields('GSL_Firearm_BlunderbussSound_MainHand')['Conditions'])

    def test_smart_shooting_adds_intelligence_to_firearm_attack_and_damage(self) -> None:
        boosts = self.fields('GSL_ArcaneGunsman_SmartShooting')['Boosts'].split(';')
        firearm = "IF(IsRangedWeaponAttack() and IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())):"
        self.assertEqual(boosts, [firearm + 'RollBonus(Attack,IntelligenceModifier)',
                                  firearm + 'DamageBonus(max(0,IntelligenceModifier))'])

    def test_base_firearm_attacks_are_granted_once_by_attack_override(self) -> None:
        for name, entry in self.entries.items():
            for key in ('BoostsOnEquipMainHand', 'BoostsOnEquipOffHand', 'Boosts', 'DefaultBoosts'):
                with self.subTest(entry=name, field=key):
                    self.assertIsNone(re.search(r'UnlockSpell\(GSL_(?:MainHand|OffHand)_\w+_attack\)',
                                                entry.fields.get(key, '')))
        overrides = {'GSL_Flintlock_MainHand': 'GSL_MainHand_Flintlock_attack,Projectile_MainHandAttack',
                     'GSL_Flintlock_OffHand': 'GSL_OffHand_Flintlock_attack,Projectile_OffhandAttack',
                     'GSL_Blunderbuss_MainHand': 'GSL_MainHand_Blunderbuss_attack,Projectile_MainHandAttack',
                     'GSL_Musket_MainHand': 'GSL_MainHand_Musket_attack,Projectile_MainHandAttack'}
        for passive, override in overrides.items():
            self.assertIn(f'AttackSpellOverride({override})', self.fields(passive)['Boosts'])

    def test_line_em_up_uses_half_weapon_damage_and_quarter_on_save(self) -> None:
        fields = self.fields('Zone_GSL_LineEmUp')
        self.assertEqual(fields['Range'], '6')
        self.assertEqual(fields['SpellSuccess'], 'DealDamage(MainRangedWeapon/2,MainRangedWeaponDamageType)')
        self.assertEqual(fields['SpellFail'], 'DealDamage(MainRangedWeapon/4,MainRangedWeaponDamageType)')
        self.assertIn('not Ally()', fields['TargetConditions'])
        self.assertNotIn('Enemy()', fields['TargetConditions'], 'neutral creatures must be hit too')
        self.assertIn('context.Source.ProficiencyBonus', fields['SpellRoll'])

    def test_piercing_round_hits_every_non_ally(self) -> None:
        conditions = self.fields('Zone_GSL_PiercingRound')['TargetConditions']
        self.assertIn('not Ally()', conditions)
        self.assertNotIn('Enemy()', conditions, 'neutral creatures must be hit too')

    def test_fanning_shot_count_ammo_and_penalty(self) -> None:
        options = [f'Projectile_GSL_FanningFire_{grit}' for grit in range(1, 4)]
        self.assertEqual(self.fields('Shout_GSL_FanningFire')['ContainerSpells'].split(';'), options)
        for grit, name in enumerate(options, 1):
            fields = self.fields(name)
            self.assertEqual(fields['AmountOfTargets'], str(1 + grit))
            self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{grit}')
            self.assertIn('GSL_FIREARM_MAIN_DISABLED', fields['RequirementConditions'])
            for weapon, resource in AMMO.items():
                self.assertIn(f"(HasPassive('GSL_{weapon}_MainHand',context.Source) and "
                              f"HasActionResource('{resource}',{1 + grit},0))", fields['RequirementConditions'])
            # Inherit the firearm attack's functors instead of replacing them.
            self.assertNotIn('SpellProperties', self.entries[name].fields)
            # Evaluated during the roll itself, so the hit chance shows the penalty.
            self.assertIn(f"IF(SpellId('{name}')):RollBonus(RangedWeaponAttack,-{grit + 1})",
                          self.fields('GSL_FanningFireUnlock')['Boosts'].split(';'))
        self.assertNotIn('GSL_FANNING_FIRE_1', self.entries)

    def test_all_in_spends_exactly_all_grit_with_any_firearm(self) -> None:
        options = [f'Projectile_GSL_AllIn_{grit}' for grit in range(3, 11)]
        self.assertEqual(self.fields('Shout_GSL_AllIn')['ContainerSpells'].split(';'), options)
        self.assertEqual(self.entries['GSL_ALL_IN'].fields['Boosts'], 'RollBonus(RangedWeaponAttack,-2)')
        for grit, name in zip(range(3, 11), options):
            fields = self.fields(name)
            self.assertEqual(fields['AmountOfTargets'], str(grit))
            self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{grit}')
            upper = f"not HasActionResource('GunslingerGrit',{grit + 1},0,false,false,context.Source)"
            if grit < 10:
                self.assertIn(upper, fields['RequirementConditions'])
            else:
                self.assertNotIn('GunslingerGrit', fields['RequirementConditions'])
            for weapon, resource in AMMO.items():
                self.assertIn(f"HasActionResource('{resource}',1,0)", fields['RequirementConditions'])

    def test_double_load_two_bullets_and_bonus_dice(self) -> None:
        fields = self.fields('Projectile_GSL_DoubleLoad')
        self.assertIn(firearm_dice_damage(1), fields['SpellSuccess'])
        self.assertNotIn('MainRangedWeapon*', fields['SpellSuccess'])
        self.assertIn('ApplyStatus(SELF,GSL_DOUBLE_LOAD,100,1)', fields['SpellProperties'])

    def test_repair_is_a_per_hand_class_menu_with_fixed_dcs(self) -> None:
        self.assertNotIn('UnlockSpell', self.fields('GSL_FIREARM_MAIN_MISFIRED')['Boosts'])
        self.assertNotIn('UnlockSpell', self.fields('GSL_FIREARM_OFF_MISFIRED')['Boosts'])
        self.assertNotIn('Boosts', self.fields('GSL_RapidRepairUnlock'))
        for hand in ('Main', 'Off'):
            up = hand.upper()
            plain = self.fields(f'Shout_GSL_Repair_{hand}')
            rapid = self.fields(f'Shout_GSL_Repair_{hand}_Rapid')
            for menu in (plain, rapid):
                self.assertEqual(menu['SpellFlags'], 'IsLinkedSpellContainer')
                self.assertEqual(menu['UseCosts'], '')
            self.assertEqual(plain['ContainerSpells'], f'Shout_GSL_FieldRepair_{hand}')
            self.assertEqual(rapid['ContainerSpells'],
                             f'Shout_GSL_FieldRepair_{hand}_R;Shout_GSL_RapidRepair_{hand}')
            self.assertEqual(self.fields(f'GSL_REPAIR_MENU_{up}')['Boosts'], f'UnlockSpell(Shout_GSL_Repair_{hand})')
            self.assertEqual(self.fields(f'GSL_REPAIR_MENU_{up}_RAPID')['Boosts'],
                             f'UnlockSpell(Shout_GSL_Repair_{hand}_Rapid)')
            for name, container in ((f'Shout_GSL_FieldRepair_{hand}', f'Shout_GSL_Repair_{hand}'),
                                    (f'Shout_GSL_FieldRepair_{hand}_R', f'Shout_GSL_Repair_{hand}_Rapid')):
                fields = self.fields(name)
                self.assertEqual(fields['SpellContainerID'], container)
                self.assertEqual(fields['UseCosts'], 'ActionPoint:1')
                self.assertEqual(fields['SpellRoll'], 'SkillCheck(Skill.SleightOfHand,15)')
                self.assertEqual(fields['SpellSuccess'], f'ApplyStatus(SELF,GSL_FIELD_REPAIR_{up}_DONE,100,1)')
            fields = self.fields(f'Shout_GSL_RapidRepair_{hand}')
            self.assertEqual(fields['SpellContainerID'], f'Shout_GSL_Repair_{hand}_Rapid')
            self.assertEqual(fields['UseCosts'], 'BonusActionPoint:1;GunslingerGrit:1')
            self.assertEqual(fields['SpellRoll'], 'SkillCheck(Skill.SleightOfHand,18)')
            self.assertEqual(fields['SpellSuccess'], f'ApplyStatus(SELF,GSL_REPAIR_{up}_DONE,100,1)')

    def test_tinkerer_is_a_six_choice_per_hand_menu(self) -> None:
        parent = self.fields('Shout_GSL_Tinkerer')
        self.assertEqual(parent['UseCosts'], '')
        self.assertEqual(len(parent['ContainerSpells'].split(';')), 6)
        for hand in ('Main', 'Off'):
            for mode in ('Capacity', 'Damage', 'Range'):
                fields = self.fields(f'Shout_GSL_Tinkerer_{hand}{mode}')
                self.assertEqual(fields['UseCosts'], 'ActionPoint:1')
                self.assertNotIn('GunslingerGrit', fields['TooltipUseCosts'])
                self.assertIn(f'GSL_FIREARM_{hand.upper()}_DISABLED', fields['RequirementConditions'])
                slot = 'RangedMainHand' if hand == 'Main' else 'RangedOffHand'
                kinds = ('FLINTLOCK', 'BLUNDERBUSS', 'MUSKET') if hand == 'Main' else ('FLINTLOCK',)
                statuses = ['GSL_TINKERER_CAPACITY'] if mode == 'Capacity' else [
                    f'GSL_TINKERER_{mode.upper()}_{kind}' for kind in kinds]
                for status in statuses:
                    # Applied to the gun by the engine, like Magic Weapon, so the tooltip shows it without Lua.
                    self.assertIn(f'ApplyEquipmentStatus({slot},{status},100,-1)', fields['SpellProperties'])
        extended = self.fields('GSL_OffHand_Flintlock_attack_Range')
        self.assertEqual(extended['TargetRadius'], '19.5')
        self.assertEqual(extended['UseCosts'], 'BonusActionPoint:1;GunslingerOffhandFlintlockAmmo:1')
        extended_master = self.fields('GSL_OffHand_Flintlock_attack_RangeMaster')
        self.assertEqual(extended_master['TargetRadius'], '25.5')
        self.assertIn("HasStatus('GSL_TINKERER_OFF_RANGE_MASTER',context.Source)",
                      extended_master['RequirementConditions'])

    def test_tinkerer_modifications_are_visible_statuses_on_the_weapon(self) -> None:
        dice = {'Flintlock': '3d4', 'Blunderbuss': '1d12+1d4', 'Musket': '2d6+1d4'}
        master_dice = {'Flintlock': '4d4', 'Blunderbuss': '1d12+2d4', 'Musket': '2d6+2d4'}
        range_bonus = {'Flintlock': '6', 'Blunderbuss': '3', 'Musket': '12'}
        weapon_statuses = ['GSL_TINKERER_CAPACITY'] + [
            f'GSL_TINKERER_{mode}_{kind.upper()}' for mode in ('DAMAGE', 'RANGE') for kind in dice
        ] + ['GSL_TINKERER_MASTER_AMMO'] + [
            f'GSL_TINKERER_MASTER_{mode}_{kind.upper()}'
            for mode in ('DAMAGE', 'RANGE') for kind in dice
        ]
        for name in weapon_statuses:
            fields = self.fields(name)
            self.assertEqual(fields['StatusType'], 'BOOST')
            self.assertEqual(fields['Icon'], 'GSL_Tinkerer')
            self.assertIn('DisplayName', fields)
            self.assertIn('Description', fields)
            self.assertNotIn('DisablePortraitIndicator', fields.get('StatusPropertyFlags', ''))
            self.assertIn('RemoveOnLongRest', fields.get('StatusPropertyFlags', ''))
        stacks = {self.fields(name)['StackId'] for name in weapon_statuses}
        self.assertEqual(stacks, {'GSL_TINKERER_CAPACITY', 'GSL_TINKERER_DAMAGE', 'GSL_TINKERER_RANGE'},
                         'Each upgrade tier must replace only its corresponding gun status')
        self.assertEqual(self.fields('GSL_TINKERER_MASTER_AMMO')['StackId'], 'GSL_TINKERER_CAPACITY')
        for kind, die in dice.items():
            self.assertEqual(self.fields(f'GSL_TINKERER_DAMAGE_{kind.upper()}')['Boosts'],
                             f'WeaponDamageDieOverride({die})')
            self.assertEqual(self.fields(f'GSL_TINKERER_MASTER_DAMAGE_{kind.upper()}')['Boosts'],
                             f'WeaponDamageDieOverride({master_dice[kind]})')
            self.assertEqual(self.fields(f'GSL_TINKERER_MASTER_RANGE_{kind.upper()}')['StackId'],
                             'GSL_TINKERER_RANGE')
            boosts = self.fields(f'GSL_TINKERER_MAIN_RANGE_{kind.upper()}')['Boosts']
            self.assertIn(f'ModifyTargetRadius(AdditiveFinal,{range_bonus[kind]})', boosts)
            self.assertIn("HasStringInSpellRoll('AttackType.RangedWeaponAttack')", boosts)
            master_boosts = self.fields(f'GSL_TINKERER_MAIN_RANGE_MASTER_{kind.upper()}')['Boosts']
            self.assertIn(f'ModifyTargetRadius(AdditiveFinal,{int(range_bonus[kind]) * 2})', master_boosts)
        self.assertIn('AttackSpellOverride(GSL_OffHand_Flintlock_attack_Range',
                      self.fields('GSL_TINKERER_OFF_RANGE')['Boosts'])
        self.assertIn('AttackSpellOverride(GSL_OffHand_Flintlock_attack_RangeMaster',
                      self.fields('GSL_TINKERER_OFF_RANGE_MASTER')['Boosts'])
        self.assertNotIn('GSL_TINKERED', self.entries)

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
        ):
            self.assertEqual(self.entries[passive].fields['Boosts'], f'UnlockInterrupt({interrupt})')
            self.assertEqual(self.entries[interrupt].kind, 'InterruptData')
        luck = self.entries['Interrupt_GSL_DesperadosLuck'].fields
        self.assertEqual(luck['Cost'], 'GunslingerGrit:1')
        self.assertIn('AdjustRoll(1d4)', luck['Properties'])
        self.assertIn('GSL_DESPERADOS_LUCK_USED', luck['Conditions'])
        close = self.entries['Interrupt_GSL_CloseCall'].fields
        self.assertEqual(close['Cost'], 'ReactionActionPoint:1;GunslingerGrit:2')
        self.assertNotIn('IsFlatValueInterruptInteresting', close['Conditions'])
        self.assertIn('AdjustRoll(-2)', close['Properties'])
        self.assertIn('ApplyStatus(OBSERVER_OBSERVER,GSL_CLOSE_CALL_COUNTER,100,1)', close['Properties'])
        self.assertNotIn('UseSpell', close['Properties'])
        self.assertEqual(self.fields('GSL_CLOSE_CALL_COUNTER')['Passives'], 'GSL_CloseCall_Counter;GSL_CloseCall_Clear')
        counter = self.fields('GSL_CloseCall_Counter')
        self.assertEqual(counter['StatsFunctorContext'], 'OnAttacked')
        self.assertTrue(counter['Conditions'].startswith('(IsMiss() or IsCriticalMiss())'))
        self.assertIn('UseSpell(SWAP,Projectile_GSL_ReactionShot,true,true,true)', counter['StatsFunctors'])
        self.assertIn("HasActionResource('GunslingerMusketAmmo',1,0,false,false,context.Target)", counter['StatsFunctors'])
        self.assertIn('RemoveStatus(GSL_CLOSE_CALL_COUNTER)', counter['StatsFunctors'])
        clear = self.fields('GSL_CloseCall_Clear')
        self.assertTrue(clear['Conditions'].startswith('not (IsMiss() or IsCriticalMiss())'))
        self.assertEqual(clear['StatsFunctors'], 'RemoveStatus(GSL_CLOSE_CALL_COUNTER)')
        self.assertNotIn('Interrupt_GSL_CloseCallCounter', self.entries)
        self.assertEqual(self.fields('Target_GSL_CloseCall')['UseCosts'], 'ReactionActionPoint:1;GunslingerGrit:2')
        duck = self.entries['Interrupt_GSL_DuckAndWeave'].fields
        self.assertIn('ApplyStatus(OBSERVER_OBSERVER,GSL_DUCK_AND_WEAVE,100,2)', duck['Properties'])
        weave = self.fields('GSL_DUCK_AND_WEAVE')
        self.assertEqual(weave['Boosts'], 'ActionResource(Movement,3,0)')
        self.assertNotIn('OnTurn', weave.get('RemoveEvents', ''))
        self.assertNotIn('Interrupt_GSL_LastWord', self.entries)
        self.assertEqual(self.entries['GSL_Desperado_LastWordUnlock'].fields['Boosts'], 'UnlockSpell(Shout_GSL_LastWord)')
        last = self.entries['Shout_GSL_LastWord'].fields
        self.assertEqual(last['UseCosts'], 'BonusActionPoint:1;GunslingerGrit:3')
        self.assertEqual(last['Cooldown'], 'OncePerRest')
        self.assertEqual(last['SpellProperties'], 'ApplyStatus(SELF,GSL_LAST_WORD_ARMED,100,-1)')
        armed = self.entries['GSL_LAST_WORD_ARMED'].fields
        self.assertEqual(armed['Boosts'], 'DownedStatus(GSL_LAST_WORD_DOWNED,5)')
        self.assertEqual(armed['RemoveEvents'], 'OnLongRest')
        downed = self.entries['GSL_LAST_WORD_DOWNED'].fields
        self.assertEqual(downed['StatusType'], 'DOWNED')
        for functor in ('RemoveStatus(GSL_LAST_WORD_ARMED)', 'RegainHitPoints(1,Guaranteed)',
                        'ApplyStatus(GSL_LASTWORD_PENDING,100,1)'):
            self.assertIn(functor, downed['OnApplyFunctors'])

    def test_new_grit_reactions_are_native_interrupts(self) -> None:
        for passive, interrupt, cost in (
            ('GSL_HairTriggerUnlock', 'Interrupt_GSL_HairTrigger', 'ReactionActionPoint:1;GunslingerGrit:1'),
            ('GSL_GritAndSteelUnlock', 'Interrupt_GSL_GritAndSteel', 'GunslingerGrit:2'),
            ('GSL_Desperado_DuckAndWeaveUnlock', 'Interrupt_GSL_DuckAndWeave', 'ReactionActionPoint:1;GunslingerGrit:1'),
            ('GSL_Desperado_QuickOnTheDrawUnlock', 'Interrupt_GSL_QuickOnTheDraw', 'ReactionActionPoint:1;GunslingerGrit:2'),
            ('GSL_Desperado_DesperadosFortuneUnlock', 'Interrupt_GSL_DesperadosFortune', 'GunslingerGrit:1'),
        ):
            with self.subTest(interrupt=interrupt):
                self.assertIn(f'UnlockInterrupt({interrupt})', self.entries[passive].fields['Boosts'])
                fields = self.entries[interrupt].fields
                self.assertEqual(self.entries[interrupt].kind, 'InterruptData')
                self.assertEqual(fields['Cost'], cost)
        for interrupt in ('Interrupt_GSL_HairTrigger', 'Interrupt_GSL_QuickOnTheDraw'):
            fields = self.entries[interrupt].fields
            self.assertIn('Projectile_GSL_ReactionShot', fields['Properties'])
            self.assertIn('GSL_FIREARM_MAIN_DISABLED', fields['Conditions'])
        draw = self.entries['Interrupt_GSL_QuickOnTheDraw'].fields['Properties']
        # UseSpell resolves after the interrupted action, so the attack is cancelled first and refunded.
        self.assertTrue(draw.startswith('Counterspell();'))
        for refund in ('ApplyStatus(OBSERVER_SOURCE,EXTRA_ATTACK_Q,100,1)', 'ApplyStatus(OBSERVER_SOURCE,EXTRA_ATTACK,100,1)',
                       'ApplyStatus(OBSERVER_SOURCE,GSL_QUICK_ON_THE_DRAW_REFUND,100,0)'):
            self.assertIn(refund, draw)
        self.assertLess(draw.index('Counterspell()'), draw.index('Projectile_GSL_ReactionShot'))
        self.assertIn('RestoreResource(SELF,ActionPoint,1,0)', self.entries['GSL_QUICK_ON_THE_DRAW_REFUND'].fields['OnApplyFunctors'])
        self.assertIn('AdjustRoll(1d8)', self.entries['Interrupt_GSL_DesperadosFortune'].fields['Properties'])
        self.assertNotIn('Interrupt_GSL_HighNoonLuck', self.entries)
        self.assertEqual(self.entries['GSL_Desperado_HighNoonUnlock'].fields['Boosts'], 'UnlockSpell(Target_GSL_HighNoon)')
        noon = self.entries['GSL_HIGH_NOON'].fields['Boosts']
        self.assertIn('CharacterWeaponDamage(1d8)', noon)
        self.assertNotIn('RollBonus(Attack,1d8)', noon)
        self.assertNotIn('RollBonus(SavingThrow,1d8)', noon)
        self.assertIn("HasStatus('GSL_HIGH_NOON_MARK',context.Target,context.Source)", noon)
        self.assertIn("IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())", noon)
        luck = self.entries['Interrupt_GSL_DesperadosLuck'].fields['Conditions']
        self.assertIn("not HasPassive('GSL_Desperado_DesperadosFortuneUnlock',context.Observer)", luck)
        # Killing-blow flags aren't set before damage, so death saves use vanilla DownedStatus replacements.
        for name, entry in self.entries.items():
            pre = entry.fields.get('InterruptContext') == 'OnPreDamage'
            self.assertFalse(pre and 'IsKillingBlow()' in entry.fields.get('Conditions', ''), name)
        self.assertFalse({'Shout_GSL_LastStand', 'GSL_Desperado_LastStandUnlock', 'GSL_LAST_STAND',
                          'GSL_LAST_STAND_WARD', 'GSL_LAST_STAND_DOWNED'} & self.entries.keys())

    def test_progression_grit_and_selection_schedules_match_readme(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        for subclass in ('Marksman', 'ArcaneGunsman', 'Desperado'):
            relevant = [row for row in rows if row['Name'] in ('Gunslinger', subclass)]
            picks = sorted(int(row['Level']) for row in relevant if re.search(r'SelectPassives\([^)]*,GritAbility\)', row.get('Selectors', '')))
            increases = sorted(int(row['Level']) for row in relevant if 'ActionResource(GunslingerGrit' in row.get('Boosts', ''))
            self.assertEqual(picks, [3, 5, 7, 9, 11, 13, 15, 17, 18] if subclass == 'Desperado' else [3, 5, 9, 13, 17])
            self.assertEqual(increases, [3, 6, 9, 12, 15, 18] if subclass == 'Desperado' else [3, 7, 11, 15, 18])
            for row in relevant:
                if re.search(r'SelectPassives\([^)]*,GritAbility\)', row.get('Selectors', '')):
                    self.assertIn(f',{2 if row["Level"] == "3" else 1},GritAbility)', row['Selectors'])

    def test_level_three_grit_pick_follows_subclass_and_desperado_pools(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        lists = {}
        for node in ET.parse(PUBLIC / 'Lists' / 'PassiveLists.lsx').findall('.//node[@id="PassiveList"]'):
            attrs = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            lists[attrs['UUID']] = attrs['Passives'].split(',')
        base = next(r for r in rows if r['Name'] == 'Gunslinger' and r['Level'] == '3')
        self.assertNotIn('GritAbility', base.get('Selectors', ''))
        for subclass in ('Marksman', 'ArcaneGunsman', 'Desperado'):
            third = next(r for r in rows if r['Name'] == subclass and r['Level'] == '3')
            self.assertIn(',2,GritAbility)', third.get('Selectors', ''))
        # Level 5/9/13/17 picks live on subclass rows so the Desperado can use its merged pools.
        base_picks = sorted(int(r['Level']) for r in rows if r['Name'] == 'Gunslinger' and re.search(r'SelectPassives\([^)]*,GritAbility\)', r.get('Selectors', '')))
        self.assertEqual(base_picks, [])
        for subclass, levels in (
            ('Marksman', [3, 5, 9, 13, 17]),
            ('ArcaneGunsman', [3, 5, 9, 13, 17]),
            ('Desperado', [3, 5, 7, 9, 11, 13, 15, 17, 18]),
        ):
            own = sorted(int(r['Level']) for r in rows if r['Name'] == subclass and re.search(r'SelectPassives\([^)]*,GritAbility\)', r.get('Selectors', '')))
            self.assertEqual(own, levels, subclass)
        general = {
            'GSL_TrickShotUnlock': 3, 'GSL_QuickloadUnlock': 3, 'GSL_FlashPowderUnlock': 3,
            'GSL_ViolentShotUnlock': 9, 'GSL_DazingShotUnlock': 9, 'GSL_PiercingRoundUnlock': 9,
            'GSL_HairTriggerUnlock': 9, 'GSL_GritAndSteelUnlock': 13,
            'GSL_BulletTimeUnlock': 17, 'GSL_HailOfLeadUnlock': 17, 'GSL_FinalJudgementUnlock': 17,
        }
        desperado = {
            'GSL_Desperado_DesperadosLuckUnlock': 3, 'GSL_Desperado_AnteUpUnlock': 3,
            'GSL_Desperado_LuckyDrawUnlock': 3, 'GSL_Desperado_TwoGunTangoUnlock': 3,
            'GSL_Desperado_DoubleLoadUnlock': 7, 'GSL_Desperado_RollTheBonesUnlock': 7,
            'GSL_Desperado_DuckAndWeaveUnlock': 7, 'GSL_Desperado_CloseCallUnlock': 7,
            'GSL_Desperado_CheatDeathsOdds': 7, 'GSL_Desperado_HotHandUnlock': 7,
            'GSL_Desperado_LastWordUnlock': 11, 'GSL_Desperado_DoubleOrNothingUnlock': 11,
            'GSL_Desperado_QuickOnTheDrawUnlock': 11, 'GSL_Desperado_RicochetShotUnlock': 11,
            'GSL_Desperado_DeadMansHandUnlock': 15,
            'GSL_Desperado_AllInUnlock': 18,
            'GSL_Desperado_HighNoonUnlock': 18,
        }
        for passive in (*general, *desperado):
            self.assertEqual(self.entries[passive].kind, 'PassiveData', passive)
        seen = set()
        for row in rows:
            self.assertFalse(set(row.get('PassivesAdded', '').split(';')) & set(desperado))
            for list_id in re.findall(r'SelectPassives\(([0-9a-f-]+),\d+,GritAbility\)', row.get('Selectors', '')):
                pool = lists[list_id]
                seen.update(pool)
                self.assertIn('GSL_MercilessShotUnlock', pool)
                self.assertEqual(len(pool), len(set(pool)), f'duplicate grit pick at level {row["Level"]}')
                level = int(row['Level'])
                self.assertEqual({p for p in pool if p in general}, {p for p, lvl in general.items() if lvl <= level})
                expected = {p for p, lvl in desperado.items() if lvl <= level} if row['Name'] == 'Desperado' else set()
                self.assertEqual({p for p in pool if p in desperado}, expected)
        self.assertLessEqual(set(general) | set(desperado), seen)
        self.assertNotIn('GSL_Desperado_DesperadosFortuneUnlock', seen)

    def test_desperados_luck_evolves_into_fortune_at_level_15(self) -> None:
        rows = [
            {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]')
        ]
        level_15 = next(r for r in rows if r['Name'] == 'Desperado' and r['Level'] == '15')
        self.assertIn('GSL_Desperado_DesperadosFortuneUnlock', level_15['PassivesAdded'].split(';'))
        self.assertIn('GSL_Desperado_DesperadosLuckUnlock', level_15['PassivesRemoved'].split(';'))
        fortune = self.entries['GSL_Desperado_DesperadosFortuneUnlock']
        self.assertIn(
            "IF(HasPassive('GSL_Desperado_DesperadosLuckUnlock',context.Source)):UnlockInterrupt(Interrupt_GSL_DesperadosFortune)",
            fortune.fields['Boosts'],
        )

    def test_optional_grit_ability_replacement_is_removed(self) -> None:
        progressions = ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx')
        selectors = [
            attribute.get('value', '')
            for attribute in progressions.findall('.//node[@id="Progression"]/attribute[@id="Selectors"]')
        ]
        self.assertFalse(any('ReplacePassives' in value or 'GritAbilityReplace' in value for value in selectors))

        passive_lists = ET.parse(PUBLIC / 'Lists' / 'PassiveLists.lsx')
        names = [
            node.find('./attribute[@id="Name"]').get('value', '')
            for node in passive_lists.findall('.//node[@id="PassiveList"]')
        ]
        self.assertFalse(any('Grit Swap Abilities' in name for name in names))

    def test_grit_abilities_are_class_actions(self) -> None:
        spells = set()
        for name, entry in self.entries.items():
            if entry.kind == 'PassiveData' and name.endswith('Unlock') and name != 'GSL_LineEmUpUnlock':
                spells.update(re.findall(r'UnlockSpell\(([^,)]+)', entry.fields.get('Boosts', '')))
        spells -= {'Shout_GSL_InfusedRounds', 'Shout_GSL_Tinkerer'}
        spells |= {'Projectile_GSL_ReactionShot', 'Projectile_GSL_DoubleOrNothing', 'Target_GSL_CloseCall'}
        spells |= {f'Shout_GSL_Repair_{hand}{rapid}' for hand in ('Main', 'Off') for rapid in ('', '_Rapid')}
        pending = list(spells)
        while pending:
            children = self.fields(pending.pop()).get('ContainerSpells', '')
            for child in filter(None, children.split(';')):
                if child not in spells:
                    spells.add(child)
                    pending.append(child)
        self.assertGreater(len(spells), 60)
        not_class = sorted(name for name in spells if self.fields(name).get('SpellStyleGroup') != 'Class')
        self.assertEqual(not_class, [], 'grit abilities should show under Class Actions on the hotbar')

    def test_feat_dexterity_passives_only_describe_the_dexterity_increase(self) -> None:
        text = {
            node.get('contentuid'): node.text
            for node in ET.parse(ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml').iter('content')
        }
        for feat in ('Gunner', 'CloseQuartersGunner', 'LongarmSpecialist', 'CalledShot', 'QuickReload'):
            with self.subTest(feat=feat):
                fields = self.entries[f'GSL_Feat_{feat}_Dexterity'].fields
                self.assertEqual(fields['Boosts'], 'Ability(Dexterity,1,20)')
                description = text[fields['Description'].split(';')[0]]
                self.assertTrue(description.startswith('Increase your Dexterity score by 1, to a maximum of 20.'))
                if feat != 'QuickReload':
                    self.assertNotIn('Reload', description, 'a copied description describes another feat')

    def test_longarm_specialist_adds_musket_range_without_advantage(self) -> None:
        fields = self.entries['GSL_Feat_LongarmSpecialist_Range'].fields
        self.assertNotIn('Boosts', fields)
        self.assertEqual(fields['DescriptionParams'], 'Distance(6)')
        status = self.entries['GSL_LONGARM_SPECIALIST_RANGE']
        self.assertEqual(status.parent, 'GSL_TINKERER_MAIN_RANGE_FLINTLOCK')
        self.assertEqual(status.fields['StackId'], 'GSL_LONGARM_SPECIALIST_RANGE')
        self.assertIn('ModifyTargetRadius(AdditiveFinal,6)', self.entries[status.parent].fields['Boosts'])
        lua = (ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua' / 'BootstrapServer.lua').read_text()
        self.assertIn('"GSL_LONGARM_SPECIALIST_RANGE", state and state.kind == "Musket"', lua)

    def test_feat_and_late_subclass_levels(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        feats = sorted(int(r['Level']) for r in rows if r['Name'] == 'Gunslinger' and r.get('AllowImprovement') == 'true')
        self.assertEqual(feats, [4, 8, 12, 16, 19])
        levels = {p: r['Level'] for r in rows for p in r.get('PassivesAdded', '').split(';') if p}
        self.assertEqual(levels['GSL_Marksman_Headshot'], '18')
        self.assertEqual(levels['GSL_ArcaneGunsman_SpellstrikeShooter'], '18')
        fifth = [r['Level'] for r in rows if r['Name'] == 'ArcaneGunsman' and 'ActionResource(SpellSlot,1,5)' in r.get('Boosts', '')]
        self.assertEqual(fifth, ['19'])

    def test_gunslingers_draw_and_deadeye(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        levels = {p: (r['Name'], r['Level']) for r in rows for p in r.get('PassivesAdded', '').split(';') if p}
        self.assertEqual(levels['GSL_GunslingersDraw'], ('Gunslinger', '1'))
        self.assertEqual(levels['GSL_Deadeye'], ('Gunslinger', '20'))
        self.assertEqual(self.fields('GSL_GunslingersDraw')['Boosts'], 'Initiative(3)')
        deadeye = self.fields('GSL_Deadeye')
        self.assertEqual(deadeye['StatsFunctorContext'], 'OnDamage')
        self.assertIn("IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())", deadeye['Conditions'])
        self.assertIn('IsCritical()', deadeye['Conditions'])
        self.assertEqual(deadeye['StatsFunctors'], 'DealDamage(5d10,Piercing)')

    def test_second_attack_is_class_wide_and_long_shot_is_once_per_turn(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        grants = [(r['Name'], r['Level']) for r in rows if 'GSL_SecondAttack' in r.get('PassivesAdded', '').split(';')]
        self.assertEqual(grants, [('Gunslinger', '6')])
        second = self.fields('GSL_SecondAttack')
        self.assertIn('ExtraAttackSpellCheck()', second['Conditions'])
        self.assertIn('ApplyStatus(EXTRA_ATTACK, 100, 1)', second['StatsFunctors'])
        self.assertNotIn('Boosts', second)
        self.assertNotIn('GSL_Desperado_SecondAttack', self.entries)
        spellstrike = self.fields('GSL_ArcaneGunsman_SpellstrikeShooter')
        self.assertEqual(spellstrike['StatsFunctorContext'], 'OnCast')
        self.assertIn("HasUseCosts('ActionPoint',true)", spellstrike['Conditions'])
        self.assertIn("HasUseCosts('SpellSlot')", spellstrike['Conditions'])
        self.assertIn('ApplyStatus(SELF,EXTRA_ATTACK_Q,100,1)', spellstrike['StatsFunctors'])
        self.assertNotIn('BonusAttack', spellstrike.get('Boosts', ''))
        self.assertIn('OncePerTurn', self.fields('GSL_Marksman_LongShot')['Properties'].split(';'))

    def test_lock_on_is_a_concentration_mark_that_reapplies_on_kill(self) -> None:
        self.assertEqual(self.fields('GSL_Marksman_LockOn')['Boosts'], 'UnlockSpell(Target_GSL_LockOn)')
        spell = self.fields('Target_GSL_LockOn')
        self.assertEqual(spell['UseCosts'], 'BonusActionPoint:1')
        self.assertEqual(spell['Cooldown'], 'OncePerShortRest')
        self.assertIn('IsConcentration', spell['SpellFlags'].split(';'))
        self.assertEqual(spell['ConcentrationSpellID'], 'Target_GSL_LockOn_Reapply')
        self.assertIn('ApplyStatus(GSL_LOCK_ON,100,-1)', spell['SpellProperties'])
        self.assertIn('ApplyStatus(SELF,GSL_LOCK_ON_OWNER,100,-1)', spell['SpellProperties'])
        mark = self.fields('GSL_LOCK_ON')
        self.assertIn('IF(RemoveCause(StatusRemoveCause.Death)):ApplyStatus(SELF,GSL_LOCK_ON_REAPPLY', mark['OnRemoveFunctors'])
        self.assertEqual(self.fields('GSL_LOCK_ON_REAPPLY')['Boosts'], 'UnlockSpell(Target_GSL_LockOn_Reapply)')
        reapply = self.fields('Target_GSL_LockOn_Reapply')
        self.assertEqual(reapply['UseCosts'], 'BonusActionPoint:1')
        self.assertEqual(reapply['Cooldown'], '')
        self.assertEqual(reapply['ConcentrationSpellID'], '')
        self.assertEqual(reapply['FollowUpOriginalSpell'], 'Target_GSL_LockOn')
        self.assertNotIn('IsConcentration', reapply['SpellFlags'].split(';'))
        self.assertIn('RemoveStatus(SELF,GSL_LOCK_ON_REAPPLY)', reapply['SpellProperties'])
        self.assertEqual(self.fields('GSL_LOCK_ON_OWNER')['Passives'], 'GSL_LockOn_Damage')
        damage = self.fields('GSL_LockOn_Damage')
        self.assertIn("HasStatus('GSL_LOCK_ON',context.Target,context.Source)", damage['Conditions'])
        self.assertEqual(damage['StatsFunctors'], 'DealDamage(ProficiencyBonus,Piercing)')

    def test_tinkerer_is_a_level_four_class_feature_with_a_second_mod_at_ten(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        levels = {p: (r['Name'], r['Level']) for r in rows for p in r.get('PassivesAdded', '').split(';') if p}
        self.assertEqual(levels['GSL_TinkererUnlock'], ('Gunslinger', '4'))
        self.assertEqual(levels['GSL_MasterTinkerer'], ('Gunslinger', '10'))
        self.assertNotIn('IsHidden', self.fields('GSL_TinkererUnlock').get('Properties', ''))
        self.assertEqual(self.fields('GSL_TinkererUnlock')['Boosts'], 'UnlockSpell(Shout_GSL_Tinkerer)')
        lists = ET.parse(PUBLIC / 'Lists' / 'PassiveLists.lsx').findall('.//attribute[@id="Passives"]')
        self.assertFalse(any('GSL_TinkererUnlock' in a.get('value', '') for a in lists))

    def test_misfire_is_a_to_hit_penalty_not_a_firing_lock(self) -> None:
        self.assertIn('RollBonus(RangedWeaponAttack,-2)', self.fields('GSL_FIREARM_MAIN_MISFIRED')['Boosts'])
        self.assertIn('RollBonus(RangedOffHandWeaponAttack,-2)', self.fields('GSL_FIREARM_OFF_MISFIRED')['Boosts'])
        self.assertNotIn('Disadvantage', self.fields('GSL_MISFIRE')['Boosts'])
        self.assertNotIn('-99', self.fields('GSL_MISFIRE')['Boosts'])
        for hand in ('MAIN', 'OFF'):
            self.assertEqual(self.fields(f'GSL_FIREARM_{hand}_DISABLED')['Boosts'], '')
            self.assertIn('DisablePortraitIndicator', self.fields(f'GSL_FIREARM_{hand}_DISABLED')['StatusPropertyFlags'])
        # The penalty is a character BOOST status (like vanilla Archery's per-hand RollBonus), so the hit-chance
        # breakdown and combat log name it; each hand only penalises its own attack roll type.
        for hand, roll, other in (('MAIN', 'RangedWeaponAttack', 'RangedOffHandWeaponAttack'),
                                  ('OFF', 'RangedOffHandWeaponAttack', 'RangedWeaponAttack')):
            fields = self.fields(f'GSL_FIREARM_{hand}_MISFIRED')
            self.assertEqual(fields['StatusType'], 'BOOST')
            self.assertTrue(fields['DisplayName'] and fields['Description'] and fields['Icon'])
            self.assertNotIn(f'RollBonus({other},', fields['Boosts'])
            for hidden in ('DisableCombatlog', 'DisablePortraitIndicator'):
                self.assertNotIn(hidden, fields.get('StatusPropertyFlags', ''))
        self.assertEqual(self.fields('GSL_FIREARM_ITEM_MISFIRED').get('Boosts', ''), '')
        # Basic shots keep the vanilla main-hand/off-hand attack rolls the boosts target.
        self.assertEqual(self.fields('Projectile_GSL_FirearmAttack')['SpellRoll'], 'Attack(AttackType.RangedWeaponAttack)')
        self.assertIn('using "Projectile_OffhandAttack"', (PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerSpells.txt').read_text(encoding='utf-8').split('new entry "GSL_OffHand_Flintlock_attack"')[1][:200])

    def test_improved_critical_at_level_fourteen(self) -> None:
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        grants = [(r['Name'], r['Level']) for r in rows if 'GSL_ImprovedCritical' in r.get('PassivesAdded', '').split(';')]
        self.assertEqual(grants, [('Gunslinger', '14')])
        self.assertEqual(self.fields('GSL_ImprovedCritical')['Boosts'], 'ReduceCriticalAttackThreshold(1)')

    def test_skill_choices_and_defaults(self) -> None:
        expected = {'SleightOfHand', 'Acrobatics', 'Athletics', 'Deception', 'Insight', 'Intimidation',
                    'Perception', 'Persuasion', 'Stealth'}
        skill_list = ET.parse(PUBLIC / 'Lists' / 'SkillLists.lsx').find('.//node[@id="SkillList"]')
        values = {a.get('id'): a.get('value') for a in skill_list.findall('attribute')}
        self.assertEqual({s.strip() for s in values['Skills'].split(',')}, expected)
        progression = (PUBLIC / 'Progressions' / 'Progressions.lsx').read_text(encoding='utf-8')
        self.assertIn(f"SelectSkills({values['UUID']},2)", progression)
        default = ET.parse(PUBLIC / 'DefaultValues' / 'Skills.lsx').find('.//attribute[@id="Add"]').get('value').split(';')
        self.assertEqual(default[:2], ['SleightOfHand', 'Perception'])
        self.assertEqual(set(default), expected)
        rows = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            rows.append({a.get('id'): a.get('value', '') for a in node.findall('attribute')})
        expertise = [(r['Name'], r['Level'], s) for r in rows for s in r.get('Selectors', '').split(';')
                     if s.startswith('SelectSkillsExpertise(')]
        self.assertEqual(expertise, [('Gunslinger', '6', 'SelectSkillsExpertise(f974ebd6-3725-4b90-bb5c-2b647d41615d,1)')])

    def test_saving_throw_proficiencies_are_dexterity_and_constitution(self) -> None:
        saves = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            row = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            saves += [(row['Name'], row['Level'], ability) for ability in re.findall(r'ProficiencyBonus\(SavingThrow,(\w+)\)', row.get('Boosts', ''))]
        self.assertEqual(sorted(saves), [('Gunslinger', '1', 'Constitution'), ('Gunslinger', '1', 'Dexterity')])

    def test_armor_and_weapon_proficiencies(self) -> None:
        granted = set()
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            row = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            granted |= set(re.findall(r'(?<!Bonus)Proficiency\((\w+)\)', row.get('Boosts', '')))
        self.assertEqual(granted, {
            'LightArmor', 'Shields', 'Slings',
            'Shortbows', 'Longbows', 'HandCrossbows', 'LightCrossbows', 'HeavyCrossbows',
            'Clubs', 'Daggers', 'Handaxes', 'LightHammers', 'Sickles', 'Scimitars', 'Shortswords',
        })

    def test_starting_equipment_kit(self) -> None:
        text = (PUBLIC / 'Stats' / 'Generated' / 'Equipment.txt').read_text(encoding='utf-8')
        self.assertIn('add initialweaponset "Ranged"', text)
        entries = re.findall(r'add equipment entry "(\w+)"', text)
        for item in ('ARM_Leather_Body', 'WPN_Dagger', 'ARM_Boots_Leather', 'WPN_LightCrossbow'):
            self.assertEqual(entries.count(item), 1, item)
        self.assertEqual([e for e in entries if e.startswith('WPN_')], ['WPN_LightCrossbow', 'WPN_Dagger'])
        self.assertEqual([e for e in entries if e.startswith('ARM_') and not e.startswith('ARM_Camp')], ['ARM_Boots_Leather', 'ARM_Leather_Body'])

    def test_level_one_fighting_style_choice(self) -> None:
        list_id = 'f6882a6c-8cab-49d9-8681-acda9106f6f6'
        lists = {}
        for node in ET.parse(PUBLIC / 'Lists' / 'PassiveLists.lsx').findall('.//node[@id="PassiveList"]'):
            row = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            lists[row['UUID']] = row['Passives'].split(',')
        self.assertEqual(lists[list_id], [
            'FightingStyle_Archery', 'FightingStyle_TwoWeaponFighting', 'FightingStyle_Dueling',
            'GSL_FightingStyle_CloseQuarters', 'FightingStyle_Defense',
        ])
        selectors = []
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            row = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            selectors += [(row['Name'], row['Level'], s) for s in re.findall(r'SelectPassives\(([^)]*FightingStyle)\)', row.get('Selectors', ''))]
        self.assertEqual(selectors, [('Gunslinger', '1', f'{list_id},1,FightingStyle')])
        passive = self.fields('GSL_FightingStyle_CloseQuarters')
        self.assertEqual(passive['Boosts'], 'RollBonus(RangedWeaponAttack,1);RollBonus(RangedOffHandWeaponAttack,1);IgnorePointBlankDisadvantage(Ammunition)')
        self.assertEqual(passive['Icon'], 'GSL_FightingStyle_CloseQuarters')

    def test_close_quarters_gunner_removes_point_blank_disadvantage(self) -> None:
        feats = {}
        for node in ET.parse(PUBLIC / 'Feats' / 'Feats.lsx').findall('.//node[@id="Feat"]'):
            row = {a.get('id'): a.get('value', '') for a in node.findall('attribute')}
            feats[row['Name']] = row['PassivesAdded'].split(';')
        self.assertEqual(feats['GSL_Feat_CloseQuartersGunner'], [
            'GSL_Feat_CloseQuartersGunner_PointBlank', 'GSL_Feat_CloseQuartersGunner_Dexterity',
        ])
        passive = self.fields('GSL_Feat_CloseQuartersGunner_PointBlank')
        self.assertEqual(passive['Boosts'], 'IgnorePointBlankDisadvantage(Ammunition)')
        self.assertNotIn('StatsFunctors', passive)
        self.assertNotIn('GSL_Feat_CloseQuartersGunner_Push', self.entries)

    def test_next_firearm_attack_buffs_last_until_end_of_next_turn(self) -> None:
        appliers = {
            'Shout_GSL_StableShot': ['GSL_STABLE_SHOT'],
            'Shout_GSL_Headshot': ['GSL_HEADSHOT'],
            'Shout_GSL_AnteUp': ['GSL_ANTE_UP', 'GSL_ANTE_UP_STAKE'],
            'Interrupt_GSL_HotHand': ['GSL_HOT_HAND'],
            'Shout_GSL_DeadMansHand': ['GSL_DEAD_MANS_HAND'],
            'GSL_Feat_SpellshotAdept_Rider': ['GSL_SPELLSHOT_CHARGED'],
        }
        for source, statuses in appliers.items():
            fields = self.fields(source)
            interrupt = source.startswith('Interrupt_')
            functors = fields['Properties'] if interrupt else fields.get('SpellProperties') or fields['StatsFunctors']
            target = 'OBSERVER_OBSERVER' if interrupt else 'SELF'
            for status in statuses:
                with self.subTest(status=status):
                    self.assertIn(f'ApplyStatus({target},{status},100,2)', functors)
                    self.assertNotIn('OnTurn', self.fields(status).get('RemoveEvents', ''))
        for status in ('GSL_STABLE_SHOT', 'GSL_HEADSHOT', 'GSL_ANTE_UP', 'GSL_HOT_HAND', 'GSL_DEAD_MANS_HAND', 'GSL_SPELLSHOT_CHARGED'):
            self.assertEqual(self.fields(status)['RemoveEvents'], 'OnAttack')

    def test_hot_hand_interrupt_on_firearm_hit_has_no_reaction_cost(self) -> None:
        self.assertEqual(self.fields('GSL_Desperado_HotHandUnlock')['Boosts'], 'UnlockInterrupt(Interrupt_GSL_HotHand)')
        interrupt = self.fields('Interrupt_GSL_HotHand')
        self.assertEqual(interrupt['InterruptContext'], 'OnCastHit')
        self.assertEqual(interrupt['Cost'], 'GunslingerGrit:2')
        self.assertNotIn('IsAbleToReact(context.Observer)', interrupt['Conditions'])
        for condition in ('Self(context.Source,context.Observer)',
                          "IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())", 'HasDamageEffectFlag(DamageFlags.Hit)'):
            self.assertIn(condition, interrupt['Conditions'])
        self.assertIn('GSL_CHEAT_DEATHS_ODDS_REFUND', interrupt['Properties'])
        for removed in ('Shout_GSL_HotHand', 'GSL_HOT_HAND_READY'):
            self.assertNotIn(removed, self.entries)


if __name__ == '__main__':
    unittest.main()
