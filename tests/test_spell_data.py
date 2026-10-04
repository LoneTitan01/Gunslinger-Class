from copy import deepcopy
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from validate_stats import read_stats, resolve_spell, validation_errors


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
DATA = PUBLIC / 'Stats' / 'Generated' / 'Data'
VANILLA = (
    ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
    / 'Stats' / 'Generated' / 'Data' / 'Spell_Projectile.txt'
)
STRAIGHT_BOLT = '9c0f6a51-3b7e-4d2a-8f61-2e4b7c9d1a05'
STRAIGHT_BOLT_OFFHAND = 'd4e2b8a7-6c13-4f9e-a5b0-7e1f3c2d8b96'
AMMO = {
    'Flintlock': ('GunslingerFlintlockAmmo', 3, 'GSL_Flintlock_MainHand'),
    'OffhandFlintlock': ('GunslingerOffhandFlintlockAmmo', 3, 'GSL_Flintlock_OffHand'),
    'Blunderbuss': ('GunslingerBlunderbussAmmo', 2, 'GSL_Blunderbuss_MainHand'),
    'Musket': ('GunslingerMusketAmmo', 1, 'GSL_Musket_MainHand'),
}


class SpellDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = read_stats(sorted(DATA.glob('*.txt')))
        self.external = read_stats([VANILLA]) if VANILLA.is_file() else {}

    def spell(self, name: str) -> dict[str, str]:
        return resolve_spell(name, self.entries, self.external)[0]

    def test_all_custom_stats_validate(self) -> None:
        self.assertEqual(validation_errors(self.entries, self.external), [])

    def test_every_spell_resolves_animation_and_event_against_vanilla(self) -> None:
        if not self.external:
            self.skipTest('Vanilla reference is not present in this checkout')
        for entry in self.entries.values():
            if entry.kind != 'SpellData':
                continue
            with self.subTest(spell=entry.name):
                fields = self.spell(entry.name)
                if 'ImmediateCast' not in fields.get('SpellFlags', '').split(';'):
                    self.assertTrue(fields.get('SpellAnimation'))
                    self.assertIn(fields.get('CastTextEvent'), {'Cast', 'CastOffhand'})
                if fields.get('SpellType') == 'Projectile':
                    self.assertTrue(fields.get('Trajectories'))

    def test_missing_inherited_animation_is_detected(self) -> None:
        self.entries['Shout_GSL_ClassAction'].fields['SpellAnimation'] = ''
        self.assertTrue(any(
            'Shout_GSL_MercilessShot: missing effective SpellAnimation' in error
            for error in validation_errors(self.entries, self.external)
        ))

    def test_animation_resources_are_used_by_reference_spells(self) -> None:
        reference = ROOT / 'examples' / 'BG3 Reference' / 'Public'
        if not reference.is_dir():
            self.skipTest('Vanilla reference is not present in this checkout')
        animations = set()
        for path in reference.rglob('Spell_*.txt'):
            for value in re.findall(r'data "(?:DualWielding)?SpellAnimation" "([^"]+)"', path.read_text(encoding='utf-8-sig')):
                animations.update(re.findall(r'[0-9a-f-]{36}', value))
        for entry in self.entries.values():
            animation = entry.fields.get('SpellAnimation')
            if animation:
                with self.subTest(spell=entry.name):
                    self.assertEqual(len(animation.split(';')), 9)
                    self.assertTrue(set(re.findall(r'[0-9a-f-]{36}', animation)) <= animations)

    def test_grit_abilities_use_matching_vanilla_visuals(self) -> None:
        reference = ROOT / 'examples' / 'BG3 Reference' / 'Public'
        if not reference.is_dir():
            self.skipTest('Vanilla reference is not present in this checkout')
        vanilla = {}
        for path in sorted(reference.rglob('Spell_*.txt')):
            vanilla.update(read_stats([path]))
        sources = {
            'Shout_GSL_BiteTheBullet_3': 'Shout_SecondWind',
            'Shout_GSL_ShotInTheDark': 'Target_Darkvision',
            'Shout_GSL_RapidRepair_Off16': 'Target_Mending',
            'Shout_GSL_Tinkerer_OffRange': 'Target_Mending',
            'Target_GSL_CloseCall': 'Shout_Shield_Wizard',
            'Shout_GSL_LastWord': 'Target_DeathWard',
            'Shout_GSL_StableShot': 'Shout_SteadyRangedCrossbow',
            'Shout_GSL_Headshot': 'Target_HuntersMark',
            'Target_GSL_LockOn': 'Target_HuntersMark',
            'Shout_GSL_InfusedRounds_Fire': 'Shout_DivineFavor',
            'Zone_GSL_LineEmUp': 'Projectile_PiercingShot',
            'Projectile_GSL_MercilessShot_3': 'Projectile_SneakAttack',
            'Projectile_GSL_RapidShot': 'Projectile_HordeBreaker',
            'Projectile_GSL_DoubleLoad': 'Projectile_HamstringShot',
            'Projectile_GSL_FanningFire_Blunderbuss_3': 'Target_Volley',
            'Projectile_GSL_DisarmingShot': 'Projectile_DisarmingAttack',
            'Projectile_GSL_WingingShot': 'Projectile_TripAttack',
            'Projectile_GSL_ForcefulShot': 'Projectile_PushingAttack',
            'Projectile_GSL_BullyingShot': 'Projectile_MenacingAttack',
            'Projectile_GSL_DazingShot': 'Projectile_DistractingStrike',
            'Projectile_GSL_ViolentShot_Musket_3': 'Projectile_PinDown',
            'Target_GSL_FlashPowder': 'Target_FaerieFire',
            'Shout_GSL_BulletTime': 'Shout_ActionSurge',
            'Shout_GSL_HailOfLead': 'Target_Volley',
            'Projectile_GSL_FinalJudgement': 'Projectile_SneakAttack',
            'Shout_GSL_AnteUp': 'Target_Bless',
            'Projectile_GSL_DoubleOrNothing': 'Projectile_SneakAttack',
            'Shout_GSL_DeadMansHand': 'Target_Bane',
            'Shout_GSL_LastStand': 'Shout_Blur',
            'Projectile_GSL_AllIn_Blunderbuss_8': 'Target_Volley',
            'Target_GSL_HighNoon': 'Target_HuntersMark',
        }
        for name, source in sources.items():
            with self.subTest(spell=name):
                fields = self.spell(name)
                expected = resolve_spell(source, {}, vanilla)[0]
                for key in ('SpellAnimation', 'PrepareEffect', 'CastEffect', 'CastSound'):
                    if key == 'CastSound' and name.startswith('Projectile_GSL_'):
                        continue
                    self.assertEqual(fields.get(key, ''), expected.get(key, ''), key)

    def test_grit_projectile_shots_use_the_firing_weapon_sound(self) -> None:
        grit_spells = read_stats([DATA / 'GunslingerGritSpells.txt'])
        projectiles = [name for name in grit_spells if name.startswith('Projectile_GSL_')]
        self.assertGreater(len(projectiles), 20)
        for name in projectiles:
            with self.subTest(spell=name):
                fields = self.spell(name)
                self.assertEqual(fields.get('CastSound', ''), '')
                self.assertEqual(fields.get('TargetSound', ''), '')
                if self.external:
                    self.assertEqual(fields.get('SpellSoundMagnitude'), 'None')

    def test_firearm_shots_play_immersive_firearms_sounds(self) -> None:
        def descends(name: str, base: str) -> bool:
            while name in self.entries:
                if name == base:
                    return True
                name = self.entries[name].parent
            return False

        shot_fields = ('SpellProperties', 'SpellSuccess', 'SpellFail', 'TooltipDamageList')
        main_hand, off_hand = set(), set()
        for name, entry in self.entries.items():
            if entry.kind != 'SpellData' or name == 'Projectile_GSL_FirearmAttack':
                continue
            if descends(name, 'GSL_OffHand_Flintlock_attack'):
                off_hand.add(name)
            elif 'MainRangedWeapon' in ' '.join(self.spell(name).get(field, '') for field in shot_fields):
                main_hand.add(name)
        self.assertIn('Zone_GSL_Scattershot', main_hand)
        self.assertIn('Projectile_GSL_RapidShot', main_hand)
        self.assertEqual(len(off_hand), 3)

        sound_passives = {
            'GSL_Firearm_ShotSound_MainHand': (main_hand, 'GSL_FIREARM_SHOT_SOUND'),
            'GSL_Firearm_BlunderbussSound_MainHand': (main_hand, 'GSL_BLUNDERBUSS_SHOT_SOUND'),
            'GSL_Firearm_ShotSound_OffHand': (off_hand, 'GSL_FIREARM_SHOT_SOUND'),
        }
        bank = ET.parse(PUBLIC / 'Content' / '[PAK]_GSL_Firearm_Sounds' / '_merged.lsx')
        bank_sources = {
            resource.find('attribute[@id="ID"]').get('value'):
                resource.find('attribute[@id="SourceFile"]').get('value')
            for resource in bank.iter('node') if resource.get('id') == 'Resource'
        }
        for passive, (spells, status) in sound_passives.items():
            with self.subTest(passive=passive):
                fields = self.entries[passive].fields
                self.assertIn('IsHidden', fields['Properties'])
                self.assertEqual(fields['StatsFunctorContext'], 'OnCast')
                self.assertEqual(set(re.findall(r"SpellId\('([^']+)'\)", fields['Conditions'])), spells)
                self.assertEqual(fields['StatsFunctors'], f'ApplyStatus(SELF,{status},100,0)')

                status_fields = self.entries[status].fields
                self.assertEqual(status_fields['StatusType'], 'EFFECT')
                mei = ET.parse(PUBLIC / 'MultiEffectInfos' / f"{status_fields['StatusEffect']}.lsx")
                effect = next(
                    attribute.get('value') for attribute in mei.iter('attribute')
                    if attribute.get('id') == 'EffectResourceGuid'
                )
                source = bank_sources[effect]
                self.assertTrue(source.endswith('.lsfx'))
                self.assertTrue((ROOT / 'GunslingerClass' / Path(source).with_suffix('.lsx')).is_file())

        for weapon, hand, passive in (
            ('WPN_GSL_Flintlock', 'PassivesMainHand', 'GSL_Firearm_ShotSound_MainHand'),
            ('WPN_GSL_Flintlock', 'PassivesOffHand', 'GSL_Firearm_ShotSound_OffHand'),
            ('WPN_GSL_Blunderbuss', 'PassivesMainHand', 'GSL_Firearm_BlunderbussSound_MainHand'),
            ('WPN_GSL_Musket', 'PassivesMainHand', 'GSL_Firearm_ShotSound_MainHand'),
        ):
            with self.subTest(weapon=weapon, hand=hand):
                self.assertIn(passive, self.entries[weapon].fields[hand].split(';'))
        for entry in self.entries.values():
            if 'PassivesOffHand' in entry.fields and 'GSL_Flintlock_OffHand' in entry.fields['PassivesOffHand']:
                with self.subTest(override=entry.name):
                    self.assertIn('GSL_Firearm_ShotSound_OffHand', entry.fields['PassivesOffHand'].split(';'))

    def test_projectile_without_inheritance_is_detected(self) -> None:
        self.entries['Projectile_GSL_RapidShot'].parent = ''
        self.entries['Projectile_GSL_RapidShot'].fields['SpellType'] = 'Projectile'
        errors = validation_errors(self.entries, self.external)
        self.assertTrue(any('Projectile_GSL_RapidShot: missing projectile Trajectories' in error for error in errors))

    def test_local_spell_unlocks_and_lists_exist(self) -> None:
        for entry in self.entries.values():
            for name in re.findall(r'UnlockSpell\(([^,)]+)', entry.fields.get('Boosts', '')):
                if '_GSL_' in name:
                    with self.subTest(unlock=entry.name):
                        self.assertEqual(self.entries[name].kind, 'SpellData')
        for path in (PUBLIC / 'Lists').glob('*.lsx'):
            for attribute in ET.parse(path).findall('.//attribute[@id="Spells"]'):
                for name in attribute.get('value', '').split(','):
                    if '_GSL_' in name:
                        self.assertEqual(self.entries[name.strip()].kind, 'SpellData')

    def test_craft_options_inherit_cast_and_charge_and_have_templates(self) -> None:
        templates = {
            attribute.get('value')
            for attribute in ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall('.//attribute[@id="MapKey"]')
        }
        options = self.spell('Shout_GSL_Craft')['ContainerSpells'].split(';')
        self.assertEqual(len(options), 5)
        for name in options:
            with self.subTest(option=name):
                fields = self.spell(name)
                self.assertEqual(fields['UseCosts'], 'ActionPoint:1;GunslingerCraftCharges:1')
                self.assertEqual(fields['CastTextEvent'], 'Cast')
                self.assertTrue(fields['SpellAnimation'])
                self.assertEqual(fields['ContainerSpells'], '')
                template = re.search(r'SummonInInventory\(([0-9a-f-]{36}),Permanent,', fields['SpellProperties'])
                self.assertIsNotNone(template)
                if template is not None:
                    self.assertIn(template[1], templates)

    def test_reload_effect_in_wrong_field_is_detected(self) -> None:
        entry = self.entries['Shout_GSL_Reload_Musket']
        entry.fields['SpellSuccess'] = entry.fields.pop('SpellProperties')
        errors = validation_errors(self.entries, self.external)
        self.assertTrue(any('unconditional reload effect left in SpellSuccess' in error for error in errors))

    def test_natural_one_misfires_the_attacking_firearm(self) -> None:
        conditions = self.entries['GSL_Firearm_Misfire_Passive'].fields['Conditions']
        self.assertEqual(conditions, 'IsCriticalMiss() and AttackedWithPassiveSourceWeapon()')
        double_load = self.entries['GSL_DoubleLoad_Misfire'].fields['Conditions']
        self.assertIn('IsCriticalMiss()', double_load)
        for condition in (conditions, double_load):
            self.assertNotIn('GetActiveWeapon', condition)
            self.assertNotIn('IsRangedWeaponAttack', condition)

    def test_unbundled_firearm_helper_is_detected(self) -> None:
        self.entries['GSL_Firearm_Misfire_Passive'].fields['Conditions'] = 'IsFirearmAttack()'
        self.assertTrue(any(
            'unsupported/unbundled expression IsFirearmAttack()' in error
            for error in validation_errors(self.entries, self.external)
        ))

    def test_inheritance_cycles_are_detected(self) -> None:
        self.entries['Shout_GSL_ClassAction'].parent = 'Shout_GSL_MercilessShot'
        self.assertTrue(any('inheritance cycle' in error for error in validation_errors(self.entries, self.external)))

    def test_dangling_status_reference_is_detected(self) -> None:
        self.entries['Shout_GSL_StableShot'].fields['SpellProperties'] += ';RemoveStatus(GSL_MISSING)'
        self.assertTrue(any('missing local stat reference GSL_MISSING' in error for error in validation_errors(self.entries, self.external)))

    def test_firearm_attack_costs_and_weapon_wiring(self) -> None:
        attacks = {
            'Flintlock': ('GSL_MainHand_Flintlock_attack', 'ActionPoint'),
            'OffhandFlintlock': ('GSL_OffHand_Flintlock_attack', 'BonusActionPoint'),
            'Blunderbuss': ('GSL_MainHand_Blunderbuss_attack', 'ActionPoint'),
            'Musket': ('GSL_MainHand_Musket_attack', 'ActionPoint'),
        }
        for weapon, (attack, action) in attacks.items():
            resource, capacity, passive = AMMO[weapon]
            with self.subTest(weapon=weapon):
                fields = self.spell(attack)
                self.assertEqual(fields['UseCosts'], f'{action}:1;{resource}:1')
                self.assertIn('IsAttack', fields['SpellFlags'].split(';'))
                self.assertNotIn('CanDualWield', fields['SpellFlags'].split(';'))
                self.assertNotIn('CastOffhand[', fields['SpellSuccess'])
                boosts = self.entries[passive].fields['Boosts']
                self.assertIn(f'ActionResource({resource},{capacity},0)', boosts)
                self.assertIn(f'AttackSpellOverride({attack},', boosts)
                weapon_name = 'Flintlock' if weapon == 'OffhandFlintlock' else weapon
                slot = 'PassivesOffHand' if weapon == 'OffhandFlintlock' else 'PassivesMainHand'
                self.assertIn(passive, self.entries[f'WPN_GSL_{weapon_name}'].fields[slot].split(';'))

    def test_reload_restores_correct_equipped_pool(self) -> None:
        for weapon, (resource, _, passive) in AMMO.items():
            with self.subTest(weapon=weapon):
                fields = self.spell(f'Shout_GSL_Reload_{weapon}')
                bonus = "HasActionResource('BonusActionPoint',1,0,false,false,context.Source)"
                action = "HasActionResource('ActionPoint',1,0,false,false,context.Source)"
                self.assertEqual(fields['SpellProperties'], f'RestoreResource({resource},100%,0);'
                                 f'IF(not {bonus}):UseActionResource(SELF,ActionPoint,1,0);'
                                 f'IF({bonus}):UseActionResource(SELF,BonusActionPoint,1,0)')
                self.assertEqual(fields['UseCosts'], '')
                self.assertEqual(fields['TooltipUseCosts'], 'BonusActionPoint:1')
                self.assertIn(f'({bonus} or {action})', fields['RequirementConditions'])
                self.assertIn(f"HasPassive('{passive}',context.Source)", fields['RequirementConditions'])
                self.assertFalse(fields.get('SpellRoll'))
                self.assertIn('IsDefaultWeaponAction', fields['SpellFlags'].split(';'))
                self.assertIn(f'UnlockSpell(Shout_GSL_Reload_{weapon})', self.equip_boosts(weapon))
                self.assertNotIn('UnlockSpell(', self.entries[passive].fields['Boosts'])
        dual = self.spell('Shout_GSL_Reload_DualFlintlock')
        self.assertEqual(dual['UseCosts'], 'ActionPoint:1')
        self.assertEqual(
            dual['SpellProperties'],
            'RestoreResource(GunslingerFlintlockAmmo,100%,0);RestoreResource(GunslingerOffhandFlintlockAmmo,100%,0)',
        )
        definitions = ET.parse(PUBLIC / 'ActionResourceDefinitions' / 'ActionResourceDefinitions.lsx')
        names = {
            node.get('value')
            for node in definitions.findall('.//attribute[@id="Name"]')
        }
        self.assertTrue({value[0] for value in AMMO.values()} <= names)

    def test_base_class_has_a_progression_row_for_every_level(self) -> None:
        rows = {}
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').findall('.//node[@id="Progression"]'):
            attributes = {attribute.get('id'): attribute.get('value') for attribute in node.findall('attribute')}
            if attributes['TableUUID'] == '68521742-30c0-45eb-b95d-48e50e0c0828':
                self.assertEqual(attributes['Name'], 'Gunslinger')
                self.assertEqual(attributes['ProgressionType'], '0')
                rows.setdefault(int(attributes['Level']), []).append(attributes['UUID'])
        self.assertEqual(sorted(rows), list(range(1, 21)), 'a missing base level blacks out the level-up screen')

    def test_quick_reload_makes_full_reload_a_bonus_action(self) -> None:
        self.assertEqual(self.spell('Shout_GSL_Reload_DualFlintlock')['UseCosts'], 'ActionPoint:1')
        self.assertEqual(
            self.entries['GSL_Feat_QuickReload_Marker'].fields['Boosts'],
            "UnlockSpellVariant(SpellId('Shout_GSL_Reload_DualFlintlock'),"
            'ModifyUseCosts(Replace,BonusActionPoint,1,0,ActionPoint))',
        )
        feat = ET.parse(PUBLIC / 'Feats' / 'Feats.lsx').find('.//attribute[@value="GSL_Feat_QuickReload"]/..')
        self.assertIn('GSL_Feat_QuickReload_Marker', feat.find('attribute[@id="PassivesAdded"]').get('value'))

    def test_spell_lists_use_semicolon_separators(self) -> None:
        for path in (PUBLIC / 'Lists' / 'SpellLists.lsx', PUBLIC.with_name('GunslingerClass_5eSpellsCompat') / 'Lists' / 'SpellLists.lsx'):
            for spells in ET.parse(path).iterfind('.//attribute[@id="Spells"]'):
                value = spells.get('value')
                self.assertNotIn(',', value, f'{path.name}: BG3 spell lists are ";"-separated')
                self.assertTrue(all(re.fullmatch(r'\w+', name) for name in value.split(';')), value)

    def test_reload_actions_are_equipment_grants_not_class_grants(self) -> None:
        for path in (PUBLIC / 'Lists' / 'SpellLists.lsx', PUBLIC / 'Progressions' / 'Progressions.lsx'):
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('ad9500fe-a489-4eff-9658-cbd82c1edfb8', text)
            self.assertNotIn('Shout_GSL_Reload_', text)
        self.assertIn('UnlockSpell(Shout_GSL_Reload_DualFlintlock)', self.equip_boosts('OffhandFlintlock'))
        for weapon in ('Flintlock', 'Blunderbuss', 'Musket'):
            self.assertNotIn('Reload_OffhandFlintlock', self.equip_boosts(weapon))
            self.assertNotIn('Reload_DualFlintlock', self.equip_boosts(weapon))

    def equip_boosts(self, weapon: str) -> str:
        if weapon == 'OffhandFlintlock':
            return self.entries['WPN_GSL_Flintlock'].fields['BoostsOnEquipOffHand']
        return self.entries[f'WPN_GSL_{weapon}'].fields['BoostsOnEquipMainHand']

    def test_firearm_class_actions_listed_on_weapon_tooltips(self) -> None:
        expected = {
            ('Flintlock', 'BoostsOnEquipMainHand'): ['Shout_GSL_Reload_Flintlock'],
            ('Flintlock', 'BoostsOnEquipOffHand'): [
                'Shout_GSL_Reload_OffhandFlintlock', 'Shout_GSL_Reload_DualFlintlock',
            ],
            ('Blunderbuss', 'BoostsOnEquipMainHand'): [
                'Shout_GSL_Reload_Blunderbuss', 'Zone_GSL_Scattershot',
            ],
            ('Musket', 'BoostsOnEquipMainHand'): ['Shout_GSL_Reload_Musket'],
        }
        for (weapon, field), spells in expected.items():
            with self.subTest(weapon=weapon, field=field):
                self.assertEqual(
                    self.entries[f'WPN_GSL_{weapon}'].fields[field],
                    ';'.join(f'UnlockSpell({spell})' for spell in spells),
                )
                for spell in spells:
                    self.assertIn(spell, self.entries)
        for weapon in ('Blunderbuss', 'Musket'):
            self.assertNotIn('BoostsOnEquipOffHand', self.entries[f'WPN_GSL_{weapon}'].fields)

    def test_firearm_base_ranges_and_straight_projectiles(self) -> None:
        ranges = {'Flintlock': (45, 1350), 'Blunderbuss': (25, 750), 'Musket': (80, 2400)}
        for weapon, (feet, value) in ranges.items():
            with self.subTest(weapon=weapon):
                entry = self.entries[f'WPN_GSL_{weapon}']
                self.assertEqual(int(entry.fields['WeaponRange']), value)
                self.assertEqual(value / 1800 * 60, feet)
                attack = self.spell(f'GSL_MainHand_{weapon}_attack')
                self.assertEqual(attack['TargetRadius'], 'RangedMainWeaponRange')
                self.assertEqual(attack['ProjectileCount'], '1')
                self.assertEqual(attack['Trajectories'], STRAIGHT_BOLT)
                self.assertEqual(entry.fields['Projectile'], attack['Trajectories'])
                self.assertEqual(attack['SpellRoll'], 'Attack(AttackType.RangedWeaponAttack)')
                self.assertEqual(attack['Icon'], f'GSL_Shoot{weapon}')
        offhand = self.spell('GSL_OffHand_Flintlock_attack')
        self.assertEqual(offhand['TargetRadius'], '13.5')
        self.assertEqual(offhand['Trajectories'], STRAIGHT_BOLT_OFFHAND)
        self.assertEqual(offhand['SpellRoll'], 'Attack(AttackType.RangedOffHandWeaponAttack)')

    def test_firearm_projectiles_keep_crossbow_bolt_without_arc(self) -> None:
        templates = {
            node.find('attribute[@id="MapKey"]').get('value'): {
                attribute.get('id'): attribute.get('value') for attribute in node.findall('attribute')
            }
            for node in ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall('.//node[@id="GameObjects"]')
        }
        for key in (STRAIGHT_BOLT, STRAIGHT_BOLT_OFFHAND):
            with self.subTest(template=key):
                template = templates[key]
                self.assertEqual(template['Type'], 'projectile')
                self.assertEqual(template['ParentTemplateId'], '')
                self.assertEqual(template['TrailFX'], 'VFX_Projectiles_Arrow_Normal_01')
                self.assertEqual(template['ImpactFX'], 'VFX_Projectiles_Arrow_Normal_Impact_01')
                for arc_field in ('ProjectilePath', 'OffsetMin_Bezier3', 'ShiftMin_Bezier3'):
                    self.assertNotIn(arc_field, template)
        eldritch_blast = '3eaf2c46-46a9-4b52-8e05-fae7dc4e548b'
        for path in DATA.glob('*.txt'):
            self.assertNotIn(eldritch_blast, path.read_text(encoding='utf-8'), path.name)

    def test_firearm_handedness_and_animation_equipment_types(self) -> None:
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx')
        equipment = ET.parse(PUBLIC / 'EquipmentTypes' / 'EquipmentTypes.lsx')
        reference = ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared' / 'EquipmentTypes' / 'EquipmentTypes.lsx'
        equipment_nodes = list(equipment.findall('.//node[@id="EquipmentType"]'))
        if reference.is_file():
            equipment_nodes.extend(ET.parse(reference).findall('.//node[@id="EquipmentType"]'))
        types = {}
        for node in equipment_nodes:
            attributes = {attr.get('id'): attr.get('value') for attr in node.findall('attribute')}
            types[attributes['UUID']] = attributes
        for weapon, hands in (('Flintlock', 'Crossbow1H'), ('Blunderbuss', 'Crossbow2H'), ('Musket', 'Crossbow2H')):
            with self.subTest(weapon=weapon):
                properties = self.entries[f'WPN_GSL_{weapon}'].fields['Weapon Properties'].split(';')
                self.assertEqual('Twohanded' in properties, weapon != 'Flintlock')
                self.assertNotIn('Two-Handed', properties)
                if weapon != 'Flintlock':
                    self.assertNotIn('PassivesOffHand', self.entries[f'WPN_GSL_{weapon}'].fields)
                node = next(
                    (item for item in templates.findall('.//node[@id="GameObjects"]')
                     if item.find(f'attribute[@id="Stats"][@value="WPN_GSL_{weapon}"]') is not None),
                    None,
                )
                self.assertIsNotNone(node)
                if node is not None:
                    attribute = node.find('attribute[@id="EquipmentTypeID"]')
                    self.assertIsNotNone(attribute)
                    if attribute is not None and attribute.get('value') in types:
                        self.assertEqual(types[attribute.get('value')]['WeaponType_TwoHanded'], hands)

    def test_long_guns_use_vanilla_twohanded_property(self) -> None:
        reference = ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared' / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        if not reference.is_file():
            self.skipTest('Vanilla weapon reference is not present in this checkout')
        vanilla = read_stats([reference])
        for weapon, parent in (('Blunderbuss', 'WPN_HeavyCrossbow'), ('Musket', 'WPN_LightCrossbow')):
            with self.subTest(weapon=weapon):
                inherited = vanilla[parent].fields['Weapon Properties'].split(';')
                properties = self.entries[f'WPN_GSL_{weapon}'].fields['Weapon Properties'].split(';')
                self.assertIn('Twohanded', inherited)
                self.assertIn('Twohanded', properties)

    def test_firearms_drop_inherited_crossbow_weapon_actions(self) -> None:
        reference = ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared' / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        vanilla = read_stats([reference]) if reference.is_file() else {}
        parents = {'Flintlock': 'WPN_HandCrossbow', 'Blunderbuss': 'WPN_HeavyCrossbow', 'Musket': 'WPN_LightCrossbow'}
        for weapon, parent in parents.items():
            with self.subTest(weapon=weapon):
                entry = self.entries[f'WPN_GSL_{weapon}']
                self.assertEqual(entry.parent, parent)
                self.assertNotIn('PiercingShot', entry.fields['BoostsOnEquipMainHand'])
                self.assertNotIn('MobileShooting', entry.fields['BoostsOnEquipMainHand'])
                self.assertNotIn('SteadyRanged', entry.fields['BoostsOnEquipMainHand'])
                if vanilla:
                    self.assertIn('UnlockSpell(', vanilla[parent].fields['BoostsOnEquipMainHand'])
                    for key in ('BoostsOnEquipOffHand', 'Boosts', 'DefaultBoosts'):
                        self.assertNotIn('UnlockSpell(', vanilla[parent].fields.get(key, ''))

    def test_blunderbuss_scattershot_cone_save_damage(self) -> None:
        fields = self.spell('Zone_GSL_Scattershot')
        self.assertEqual(fields['SpellType'], 'Zone')
        self.assertEqual(fields['Shape'], 'Cone')
        self.assertEqual(float(fields['Range']) / 0.3, 10)
        self.assertEqual(fields['UseCosts'], 'ActionPoint:1;GunslingerBlunderbussAmmo:1')
        self.assertEqual(
            fields['SpellRoll'],
            'not SavingThrow(Ability.Dexterity,8 + context.Source.ProficiencyBonus + GetModifier(context.Source.Dexterity))',
        )
        self.assertEqual(fields['SpellSuccess'], 'DealDamage(MainRangedWeapon/2,MainRangedWeaponDamageType)')
        self.assertEqual(fields['SpellFail'], 'ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)')
        self.assertEqual(fields['TooltipOnSave'], '')
        for variant in ('PoisonMist', 'GargantuanScattershot', 'PunchDrunkScattershot'):
            with self.subTest(variant=variant):
                spell = self.spell(f'Zone_GSL_{variant}_Blunderbuss')
                self.assertNotIn('DealDamage', spell['SpellFail'])
                for effect in spell['SpellSuccess'].split(';'):
                    if 'DealDamage(' in effect:
                        self.assertIn('/2,', effect)
        self.assertIn("HasPassive('GSL_Blunderbuss_MainHand',context.Source)", fields['RequirementConditions'])
        self.assertIn("not HasStatus('GSL_FIREARM_MAIN_DISABLED',context.Source)", fields['RequirementConditions'])
        self.assertIn('UnlockSpell(Zone_GSL_Scattershot)', self.equip_boosts('Blunderbuss'))
        for weapon in ('Flintlock', 'OffhandFlintlock', 'Musket'):
            self.assertNotIn('Scattershot', self.equip_boosts(weapon))

    def test_invalid_twohanded_spelling_is_detected(self) -> None:
        entry = self.entries['WPN_GSL_Musket']
        entry.fields['Weapon Properties'] = entry.fields['Weapon Properties'].replace('Twohanded', 'Two-Handed')
        self.assertTrue(any(
            'invalid weapon property Two-Handed' in error
            for error in validation_errors(self.entries, self.external)
        ))

    def test_shooting_and_reload_labels_are_localized(self) -> None:
        contents = ET.parse(ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml')
        labels = {node.get('contentuid'): node.text for node in contents.findall('.//content')}
        for weapon in ('Flintlock', 'Blunderbuss', 'Musket'):
            with self.subTest(weapon=weapon):
                attack = self.spell(f'GSL_MainHand_{weapon}_attack')
                self.assertEqual(labels[attack['DisplayName'].split(';')[0]], f'Shoot {weapon}')
                reload = self.spell(f'Shout_GSL_Reload_{weapon}')
                self.assertEqual(labels[reload['DisplayName'].split(';')[0]], 'Primary Reload')
        for name, label in (('OffhandFlintlock', 'Secondary Reload'), ('DualFlintlock', 'Full Reload')):
            fields = self.spell(f'Shout_GSL_Reload_{name}')
            self.assertEqual(labels[fields['DisplayName'].split(';')[0]], label)

    def test_custom_icons_are_not_treated_as_stat_references(self) -> None:
        names = {
            attribute.get('value')
            for path in (PUBLIC / 'GUI').glob('Icons_*.lsx')
            for attribute in ET.parse(path).findall('.//attribute[@id="MapKey"]')
        }
        for weapon in ('Flintlock', 'Blunderbuss', 'Musket'):
            self.assertIn(self.spell(f'GSL_MainHand_{weapon}_attack')['Icon'], names)
        self.assertFalse(any('in Icon' in error for error in validation_errors(self.entries, self.external)))

    def test_bundled_dual_shot_is_detected(self) -> None:
        self.entries = deepcopy(self.entries)
        self.entries['Projectile_GSL_FirearmAttack'].fields['SpellFlags'] += ';CanDualWield'
        self.assertTrue(any('bundled offhand shot bypasses' in error for error in validation_errors(self.entries, self.external)))

    def test_infused_rounds_is_a_tiered_element_buff_group(self) -> None:
        base = ['Fire', 'Thunder', 'Lightning', 'Acid', 'Cold', 'Poison']
        elements = base + ['Force', 'Radiant', 'Necrotic']
        container = self.spell('Shout_GSL_InfusedRounds')
        self.assertEqual(
            container['ContainerSpells'].split(';'),
            [f'Shout_GSL_InfusedRounds_{e}' for e in elements] + ['Shout_GSL_InfusedRounds_Unstable'],
        )
        self.assertIn('IsLinkedSpellContainer', container['SpellFlags'])
        self.assertEqual(
            self.entries['GSL_ArcaneGunsman_InfusedRoundsUnlock'].fields['Boosts'],
            'UnlockSpell(Shout_GSL_InfusedRounds)',
        )
        for passive in ('ImprovedInfusedRounds', 'MasteredInfusedRounds', 'UnstableInfusedRoundsUnlock'):
            self.assertNotIn('Boosts', self.entries[f'GSL_ArcaneGunsman_{passive}'].fields)
        for old in ('', '_2', '_3', '_Unstable'):
            self.assertNotIn(f'Projectile_GSL_InfusedRounds{old}', self.entries)
        unlocks = {'Force': 'Improved', 'Radiant': 'Mastered', 'Necrotic': 'Mastered'}
        for element in elements:
            with self.subTest(element=element):
                spell = self.spell(f'Shout_GSL_InfusedRounds_{element}')
                status = f'GSL_INFUSED_ROUNDS_{element.upper()}'
                self.assertEqual(spell['SpellContainerID'], 'Shout_GSL_InfusedRounds')
                self.assertEqual(spell['UseCosts'], 'BonusActionPoint:1')
                self.assertEqual(
                    spell['SpellProperties'],
                    f'ApplyStatus(SELF,GSL_INFUSED_ROUNDS,100,10);ApplyStatus(SELF,{status},100,10)',
                )
                if element in unlocks:
                    self.assertEqual(
                        spell['RequirementConditions'],
                        f"HasPassive('GSL_ArcaneGunsman_{unlocks[element]}InfusedRounds',context.Source)",
                    )
                else:
                    self.assertEqual(spell.get('RequirementConditions', ''), '')
                fields = self.entries[status].fields
                self.assertEqual(fields['StackId'], 'GSL_INFUSED_ROUNDS_ELEMENT')
                boosts = fields['Boosts'].split(';')
                self.assertEqual(
                    [re.search(r':CharacterWeaponDamage\((\w+),(\w+)\)$', b).groups() for b in boosts],
                    [(dice, element) for dice in ('1d4', '2d4', '3d4', '5d4')],
                )
                for boost in boosts:
                    self.assertIn("IsWeaponOfProficiencyGroup('Slings',GetAttackWeapon())", boost)
        unstable = self.spell('Shout_GSL_InfusedRounds_Unstable')
        self.assertIn("HasPassive('GSL_ArcaneGunsman_UnstableInfusedRoundsUnlock',context.Source)", unstable['RequirementConditions'])
        self.assertIn("HasStatus('GSL_INFUSED_ROUNDS',context.Source)", unstable['RequirementConditions'])
        self.assertEqual(unstable['SpellProperties'], 'ApplyStatus(SELF,GSL_INFUSED_ROUNDS_UNSTABLE,100,10)')
        self.assertEqual(self.entries['GSL_INFUSED_ROUNDS_UNSTABLE'].fields['Passives'], 'GSL_InfusedRounds_UnstableBackfire')
        backfire = self.entries['GSL_InfusedRounds_UnstableBackfire'].fields
        self.assertEqual(backfire['StatsFunctorContext'], 'OnAttack')
        self.assertEqual(
            backfire['StatsFunctors'],
            'IF(RollDieAgainstDC(DiceType.d4,4)):UseSpell(SELF,Zone_GSL_UnstableBackfire,true,true,true)',
        )
        explosion = self.spell('Zone_GSL_UnstableBackfire')
        self.assertEqual(explosion['SpellType'], 'Shout')
        self.assertEqual(explosion['AreaRadius'], '1.5')
        self.assertEqual(explosion['SpellProperties'], 'DealDamage(3d4,Force)')
        self.assertIn('ImmediateCast', explosion['SpellFlags'].split(';'))

    def test_save_repair_temporary_hp_and_movement_definitions(self) -> None:
        line = self.spell('Zone_GSL_LineEmUp')
        self.assertTrue(line['SpellRoll'].startswith('not SavingThrow(Ability.Dexterity,'))
        self.assertEqual(line['Shape'], 'Square')
        self.assertEqual(line['SpellFail'], 'DealDamage(MainRangedWeapon/4,MainRangedWeaponDamageType)')
        self.assertEqual(self.spell('Shout_GSL_RapidRepair_Main12')['SpellRoll'], 'SkillCheck(Skill.SleightOfHand,12)')
        self.assertEqual(self.entries['GSL_BITE_THE_BULLET'].fields['Boosts'], 'TemporaryHP(2*ProficiencyBonus)')
        self.assertEqual(self.spell('Shout_GSL_StableShot')['UseCosts'], 'ActionPoint:1;Movement:6')
        self.assertNotIn('Movement(-6)', self.entries['GSL_Marksman_StableShot'].fields['Boosts'])


if __name__ == '__main__':
    unittest.main()
