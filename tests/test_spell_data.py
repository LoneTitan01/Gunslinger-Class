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

    def test_stat_parents_load_before_children(self) -> None:
        # The engine loads stats files in name order and silently drops inheritance from later entries.
        defined = set()
        for path in sorted(DATA.glob('*.txt'), key=lambda p: p.name.lower()):
            text = path.read_text(encoding='utf-8-sig')
            for block in re.split(r'^(?=new entry ")', text, flags=re.M):
                name = re.match(r'new entry "([^"]+)"', block)
                if not name:
                    continue
                name = name.group(1)
                parent = re.search(r'^using "([^"]+)"', block, re.M)
                parent = parent.group(1) if parent else None
                if parent in self.entries:
                    with self.subTest(entry=name):
                        self.assertIn(parent, defined, f'{name} inherits {parent} before it is loaded')
                defined.add(name)

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
            'Shout_GSL_RapidRepair_Off': 'Target_Mending',
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
            'Projectile_GSL_FanningFire_3': 'Target_Volley',
            'Projectile_GSL_DisarmingShot': 'Projectile_DisarmingAttack',
            'Projectile_GSL_WingingShot': 'Projectile_TripAttack',
            'Projectile_GSL_ForcefulShot': 'Projectile_PushingAttack',
            'Projectile_GSL_BullyingShot': 'Projectile_MenacingAttack',
            'Projectile_GSL_DazingShot': 'Projectile_DistractingStrike',
            'Projectile_GSL_ViolentShot_3': 'Projectile_PinDown',
            'Target_GSL_FlashPowder': 'Target_FaerieFire',
            'Shout_GSL_BulletTime': 'Shout_ActionSurge',
            'Shout_GSL_HailOfLead': 'Target_Volley',
            'Projectile_GSL_FinalJudgement': 'Projectile_SneakAttack',
            'Shout_GSL_AnteUp': 'Target_Bless',
            'Projectile_GSL_DoubleOrNothing': 'Projectile_SneakAttack',
            'Shout_GSL_DeadMansHand': 'Target_Bane',
            'Projectile_GSL_AllIn_8': 'Target_Volley',
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
        def fires_weapon(name: str) -> bool:
            while name in self.entries:
                if name in {'Projectile_GSL_FirearmAttack', 'GSL_MainHand_Flintlock_attack', 'GSL_OffHand_Flintlock_attack'}:
                    return True
                name = self.entries[name].parent
            return False

        projectiles = [name for name in self.entries if name.startswith('Projectile_GSL_') and fires_weapon(name)]
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

        upgrade_shots = {
            'Projectile_GSL_DashAndGun_Flintlock',
            'Projectile_GSL_ParalyzingShot_Musket',
        }
        sound_passives = {
            'GSL_Firearm_ShotSound_MainHand': (main_hand - upgrade_shots, 'GSL_FIREARM_SHOT_SOUND'),
            'GSL_Firearm_BlunderbussSound_MainHand': (main_hand - upgrade_shots, 'GSL_BLUNDERBUSS_SHOT_SOUND'),
            'GSL_Firearm_ShotSound_OffHand': (off_hand, 'GSL_FIREARM_SHOT_SOUND'),
            'GSL_Firearm_UpgradeShotSound': (upgrade_shots, 'GSL_FIREARM_SHOT_SOUND'),
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

    def test_misfire_is_visible_and_tracks_every_firearm_template(self) -> None:
        self.assertNotIn('IsHidden', self.entries['GSL_Firearm_Misfire_Passive'].fields.get('Properties', ''))
        for name, icon in (('GSL_FIREARM_ITEM_MISFIRED', 'GSL_Misfire'), ('GSL_FIREARM_ITEM_DESTROYED', 'GSL_BrokenFirearm')):
            fields = self.entries[name].fields
            self.assertEqual(fields['Icon'], icon)
            self.assertNotIn('Boosts', fields)
        self.assertIn('RemoveOnLongRest', self.entries['GSL_FIREARM_ITEM_MISFIRED'].fields['StatusPropertyFlags'])
        # Like Tinkerer, the engine marks the gun itself; the script only reconciles repair/break/long rest.
        functors = self.entries['GSL_Firearm_Misfire_Passive'].fields['StatsFunctors']
        self.assertTrue(functors.startswith('ApplyStatus(SELF,GSL_MISFIRE,100,-1);'))
        for slot, hand in (('RangedMainHand', 'not IsOffHandAttack()'), ('RangedOffHand', 'IsOffHandAttack()')):
            item = f'GetItemInEquipmentSlot(EquipmentSlot.{slot},context.Source)'
            self.assertIn(f"IF({hand} and not HasStatus('GSL_FIREARM_ITEM_MISFIRED',{item}) and "
                          f"not HasStatus('GSL_FIREARM_ITEM_DESTROYED',{item})):"
                          f"ApplyEquipmentStatus({slot},GSL_FIREARM_ITEM_MISFIRED,100,-1)", functors)
        lua = (ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua' / 'BootstrapServer.lua').read_text()
        self.assertIn('Ext.Stats.GetStats("Weapon")', lua)
        self.assertIn('templates[root:lower()] = kind', lua)
        self.assertIn('status(item, "GSL_FIREARM_ITEM_MISFIRED"', lua)
        localization = {
            node.get('contentuid'): node.text
            for node in ET.parse(
                ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
            ).findall('content')
        }
        for name in ('GSL_FIREARM_MAIN_DESTROYED', 'GSL_FIREARM_OFF_DESTROYED', 'GSL_FIREARM_ITEM_DESTROYED'):
            entry, display = name, None
            while display is None:
                display = self.entries[entry].fields.get('DisplayName')
                entry = self.entries[entry].parent
            self.assertEqual(localization[display.split(';')[0]], 'Broken')

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
                self.assertEqual(fields['SpellProperties'], f'RestoreResource({resource},100%,0)')
                self.assertEqual(fields['UseCosts'], 'BonusActionPoint:1', 'the hotbar shows the real cost')
                self.assertNotIn('TooltipUseCosts', fields, 'a static tooltip cost would hide the action fallback')
                self.assertEqual(fields['RequirementConditions'], f"HasPassive('{passive}',context.Source)")
                self.assertFalse(fields.get('SpellRoll'))
                self.assertIn('IsDefaultWeaponAction', fields['SpellFlags'].split(';'))
                self.assertIn(f'UnlockSpell(Shout_GSL_Reload_{weapon})', self.equip_boosts(weapon))
                self.assertNotIn('UnlockSpell(', self.entries[passive].fields['Boosts'])
        dual = self.spell('Shout_GSL_Reload_DualFlintlock')
        self.assertEqual(dual['UseCosts'], 'ActionPoint:1')
        self.assertNotIn('TooltipUseCosts', dual)
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

    def test_reloads_fall_back_to_an_action_without_a_bonus_action(self) -> None:
        single = ' or '.join(
            f"SpellId('Shout_GSL_Reload_{weapon}')" for weapon in ('Flintlock', 'OffhandFlintlock', 'Blunderbuss', 'Musket')
        )
        status = self.entries['GSL_RELOAD_NO_BONUS_ACTION'].fields
        self.assertEqual(
            status['Boosts'], f'UnlockSpellVariant({single},ModifyUseCosts(Replace,ActionPoint,1,0,BonusActionPoint))'
        )
        self.assertIn('DisablePortraitIndicator', status['StatusPropertyFlags'])
        lua = (ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua' / 'BootstrapServer.lua').read_text()
        self.assertIn('"GSL_RELOAD_NO_BONUS_ACTION", not bonus', lua)

    def test_quick_reload_makes_full_reload_a_bonus_action(self) -> None:
        self.assertEqual(self.spell('Shout_GSL_Reload_DualFlintlock')['UseCosts'], 'ActionPoint:1')
        self.assertNotIn(
            'Boosts', self.entries['GSL_Feat_QuickReload_Marker'].fields,
            'an unconditional variant would keep Full Reload a bonus action after the bonus action is spent',
        )
        status = self.entries['GSL_QUICK_FULL_RELOAD'].fields
        self.assertEqual(
            status['Boosts'],
            "UnlockSpellVariant(SpellId('Shout_GSL_Reload_DualFlintlock'),"
            'ModifyUseCosts(Replace,BonusActionPoint,1,0,ActionPoint))',
        )
        lua = (ROOT / 'GunslingerClass' / 'Mods' / 'GunslingerClass' / 'ScriptExtender' / 'Lua' / 'BootstrapServer.lua').read_text()
        self.assertIn('"GSL_QUICK_FULL_RELOAD", bonus and Osi.HasPassive(character, "GSL_Feat_QuickReload_Marker") == 1', lua)
        feat = ET.parse(PUBLIC / 'Feats' / 'Feats.lsx').find('.//attribute[@value="GSL_Feat_QuickReload"]/..')
        self.assertIn('GSL_Feat_QuickReload_Marker', feat.find('attribute[@id="PassivesAdded"]').get('value'))

    def test_spell_lists_use_semicolon_separators(self) -> None:
        for path in (PUBLIC / 'Lists' / 'SpellLists.lsx', PUBLIC.with_name('GunslingerClass_5eSpellsCompat') / 'Lists' / 'SpellLists.lsx'):
            for spells in ET.parse(path).iterfind('.//attribute[@id="Spells"]'):
                value = spells.get('value')
                self.assertNotIn(',', value, f'{path.name}: BG3 spell lists are ";"-separated')
                self.assertTrue(all(re.fullmatch(r'\w+', name) for name in value.split(';')), value)

    def test_5e_compat_merges_into_the_base_arcane_gunsman_lists(self) -> None:
        def lists(path: Path) -> dict[str, list[str]]:
            return {
                node.find('attribute[@id="UUID"]').get('value'): node.find('attribute[@id="Spells"]').get('value').split(';')
                for node in ET.parse(path).iterfind('.//node[@id="SpellList"]')
            }

        compat_root = PUBLIC.with_name('GunslingerClass_5eSpellsCompat')
        base = lists(PUBLIC / 'Lists' / 'SpellLists.lsx')
        compat = lists(compat_root / 'Lists' / 'SpellLists.lsx')
        self.assertTrue(compat)
        for uuid, spells in compat.items():
            with self.subTest(list=uuid):
                self.assertIn(uuid, base, 'compat lists must override a base list, not add a separate pick')
                self.assertLessEqual(set(base[uuid]), set(spells))
                self.assertEqual(len(spells), len(set(spells)))
        self.assertFalse((compat_root / 'Progressions').exists(), 'separate 5e selectors split the spell choice')

    def test_arcane_gunsman_spellcasting_progression(self) -> None:
        rows = {}
        for node in ET.parse(PUBLIC / 'Progressions' / 'Progressions.lsx').iterfind('.//node[@id="Progression"]'):
            attributes = {attribute.get('id'): attribute.get('value') for attribute in node.findall('attribute')}
            if attributes['Name'] == 'ArcaneGunsman':
                rows[int(attributes['Level'])] = attributes
        self.assertIn('SelectSpells(ceb7dba3-aeb9-47f7-bebb-41a0c0833c97,2,0,', rows[3]['Selectors'])
        self.assertIn('SelectSpells(93f4be1c-e2b3-4f34-9850-f16b9291d14a,3,0,', rows[3]['Selectors'])
        first_slot = {}
        for level, attributes in sorted(rows.items()):
            for slot_level in re.findall(r'ActionResource\(SpellSlot,\d+,(\d)\)', attributes.get('Boosts', '')):
                first_slot.setdefault(int(slot_level), level)
        self.assertEqual(first_slot, {1: 3, 2: 5, 3: 9, 4: 13, 5: 19})
        for slot_level, level in first_slot.items():
            with self.subTest(slot_level=slot_level):
                self.assertIn(f'UnlockedSpellSlotLevel{slot_level}', rows[level].get('PassivesAdded', '').split(';'))

        cantrips = 'ceb7dba3-aeb9-47f7-bebb-41a0c0833c97'
        slot_lists = {
            1: '93f4be1c-e2b3-4f34-9850-f16b9291d14a',
            2: '241f47a5-5bb2-4a11-87cf-a25d87a40fab',
            3: '8d085377-16f2-44fd-ac85-013e5d0053d7',
            4: '5bb50772-adba-4021-b1c8-fecb2ed421a0',
            5: 'a6a675d9-ce50-409e-9271-094559fffa43',
        }
        for level, attributes in sorted(rows.items()):
            highest = max((slot for slot, first in first_slot.items() if first <= level), default=0)
            selected = [uuid for uuid in re.findall(r'SelectSpells\(([\w-]+),', attributes.get('Selectors', '')) if uuid != cantrips]
            with self.subTest(level=level):
                self.assertLessEqual(len(selected), 1, 'each level-up offers one merged spell pick')
                if selected:
                    self.assertEqual(selected, [slot_lists[highest]], 'pick from every castable level, nothing higher')

        for path in (PUBLIC / 'Lists' / 'SpellLists.lsx', PUBLIC.with_name('GunslingerClass_5eSpellsCompat') / 'Lists' / 'SpellLists.lsx'):
            lists = {
                node.find('attribute[@id="UUID"]').get('value'): node.find('attribute[@id="Spells"]').get('value').split(';')
                for node in ET.parse(path).iterfind('.//node[@id="SpellList"]')
            }
            self.assertNotIn('Mephit', ';'.join(sum(lists.values(), [])))
            self.assertNotIn('Zone_GustOfWind_3', ';'.join(sum(lists.values(), [])))
            for slot in range(2, 6):
                with self.subTest(path=path.parent.parent.name, slot=slot):
                    self.assertLessEqual(set(lists[slot_lists[slot - 1]]), set(lists[slot_lists[slot]]), 'spell lists are cumulative')
                    self.assertEqual(len(lists[slot_lists[slot]]), len(set(lists[slot_lists[slot]])))

        descriptions = [
            {attribute.get('id'): attribute.get('value') for attribute in node.findall('attribute')}
            for node in ET.parse(PUBLIC / 'Progressions' / 'ProgressionDescriptions.lsx').iterfind('.//node[@id="ProgressionDescription"]')
        ]
        slot_matches = {d.get('ParamMatch') for d in descriptions if d.get('ProgressionTableId') == 'bc7315da-8802-4247-ad7a-c50278dd379f'}
        self.assertLessEqual({'0:SpellSlot;1:1', '0:SpellSlot'}, slot_matches, 'level-up screen lists the spell slots gained')

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

    def test_flash_powder_can_target_the_ground(self) -> None:
        fields = self.spell('Target_GSL_FlashPowder')
        self.assertEqual(fields['SpellType'], 'Target')
        self.assertEqual(fields['AreaRadius'], '1.5')
        self.assertNotIn('Character()', fields['TargetConditions'], 'the ground is not a character, so it could not be aimed at')
        self.assertEqual(fields['TargetConditions'], 'not Item() and not Dead()')
        self.assertEqual(fields['CycleConditions'], 'Enemy() and not Dead()')
        self.assertIn('RangeIgnoreVerticalThreshold', fields['SpellFlags'].split(';'))

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

    def test_firearm_templates_use_firearm_weapon_type_tags(self) -> None:
        # The tooltip weapon-type label comes from tag DisplayNames, and child tags merge with
        # the parent's, so firearms must not inherit the vanilla crossbow bases.
        localization = {
            node.get('contentuid'): node.text
            for node in ET.parse(
                ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
            ).findall('content')
        }
        tags = {}
        for path in (PUBLIC / 'Tags').glob('*.lsx'):
            node = ET.parse(path).find('.//node[@id="Tags"]')
            attributes = {attr.get('id'): attr for attr in node.findall('attribute')}
            self.assertEqual(path.stem, attributes['UUID'].get('value'))
            tags[attributes['UUID'].get('value')] = localization[attributes['DisplayName'].get('handle')]
        crossbow_parents = {
            'a5d843ab-c3af-4e60-a925-bb2e15828938',
            '04622e3d-5b3f-4f2c-a0db-513a717d911f',
            '43b7fbf5-7f6e-4e9e-bce7-c679eea44593',
        }
        weapons = 0
        for node in ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall('.//node[@id="GameObjects"]'):
            attributes = {attr.get('id'): attr.get('value') for attr in node.findall('attribute')}
            stats = attributes.get('Stats', '')
            kind = next((k for k in ('Flintlock', 'Blunderbuss', 'Musket') if stats.startswith(f'WPN_GSL_{k}')), None)
            if kind is None:
                continue
            weapons += 1
            with self.subTest(template=attributes['Name']):
                self.assertNotIn(attributes['ParentTemplateId'], crossbow_parents)
                self.assertEqual(attributes['ParentTemplateId'], 'f44c9c6f-bc71-42ad-9cad-2dae306e750e')
                self.assertIn('PhysicsTemplate', attributes)
                labels = [tags[tag.get('value')] for tag in node.findall('.//node[@id="Tag"]/attribute[@id="Object"]')]
                self.assertEqual(labels, [kind])
                # Item names come from the root template; BASE_WEAPON's is just "Weapon".
                handles = {
                    attr.get('id'): attr.get('handle')
                    for attr in node.findall('attribute')
                    if attr.get('id') in ('DisplayName', 'Description')
                }
                self.assertEqual(set(handles), {'DisplayName', 'Description'})
                for handle in handles.values():
                    self.assertTrue(localization.get(handle), handle)
        self.assertEqual(weapons, 163)

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
        self.assertEqual(float(fields['Range']) / 0.3, 15)
        self.assertEqual(fields['UseCosts'], 'ActionPoint:1;GunslingerBlunderbussAmmo:1')
        self.assertEqual(fields['Cooldown'], 'OncePerShortRest')
        self.assertEqual(
            fields['SpellRoll'],
            'not SavingThrow(Ability.Dexterity,8 + context.Source.ProficiencyBonus + GetModifier(context.Source.Dexterity))',
        )
        self.assertTrue(
            fields['SpellSuccess'].startswith(
                'DealDamage(MainRangedWeapon/2,MainRangedWeaponDamageType);'
            )
        )
        self.assertIn(
            "IF(HasPassive('GSL_Blunderbuss_SoulCoin_Passive',context.Source)):DealDamage(1d4,Fire)",
            fields['SpellSuccess'],
        )
        self.assertIn(
            "IF(HasPassive('GSL_Blunderbuss_EnrichedInfernalIron_Passive',context.Source)):DealDamage(2d4,Fire)",
            fields['SpellSuccess'],
        )
        self.assertEqual(fields['SpellFail'], 'ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)')
        self.assertEqual(fields['TooltipOnSave'], '')
        for variant in ('PoisonMist', 'GargantuanScattershot', 'PunchDrunkScattershot'):
            with self.subTest(variant=variant):
                spell = self.spell(f'Zone_GSL_{variant}_Blunderbuss')
                self.assertEqual(spell['Cooldown'], 'OncePerShortRest')
                self.assertEqual(float(spell['Range']) / 0.3, 20)
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
            [f'Shout_GSL_InfusedRounds_{e}' for e in elements],
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
        self.assertNotIn('Shout_GSL_InfusedRounds_Unstable', self.entries)
        toggle = self.entries['GSL_ArcaneGunsman_UnstableInfusedRoundsUnlock'].fields
        self.assertIn('IsToggled', toggle['Properties'])
        self.assertEqual(toggle['ToggleOnFunctors'], 'ApplyStatus(GSL_INFUSED_ROUNDS_UNSTABLE,100,-1)')
        self.assertEqual(toggle['ToggleOffFunctors'], 'RemoveStatus(GSL_INFUSED_ROUNDS_UNSTABLE)')
        self.assertIn("HasStatus('GSL_INFUSED_ROUNDS',context.Source)",
                      self.entries['GSL_InfusedRounds_UnstableBackfire'].fields['Conditions'])
        self.assertEqual(self.entries['GSL_INFUSED_ROUNDS_UNSTABLE'].fields['Passives'], 'GSL_InfusedRounds_UnstableBackfire')
        backfire = self.entries['GSL_InfusedRounds_UnstableBackfire'].fields
        self.assertEqual(backfire['StatsFunctorContext'], 'OnAttack')
        self.assertIn('Highlighted', backfire['Properties'])
        self.assertNotIn('IsHidden', backfire['Properties'])
        self.assertEqual(
            backfire['StatsFunctors'],
            'IF(RollDieAgainstDC(DiceType.d4,4)):UseSpell(SELF,Zone_GSL_UnstableBackfire,true,true,true)',
        )
        explosion = self.spell('Zone_GSL_UnstableBackfire')
        self.assertEqual(explosion['SpellType'], 'Shout')
        self.assertEqual(explosion['AreaRadius'], '1.5')
        self.assertEqual(explosion['SpellProperties'], 'DealDamage(3d4,Force)')
        self.assertIn('ImmediateCast', explosion['SpellFlags'].split(';'))

    def test_reloading_does_not_break_stealth_or_invisibility(self) -> None:
        # Same flags as vanilla Shout_Hide/Shout_Dash: Stealth keeps sneaking, Invisible keeps invisibility.
        for name in ('Shout_GSL_Reload_Flintlock', 'Shout_GSL_Reload_OffhandFlintlock', 'Shout_GSL_Reload_DualFlintlock',
                     'Shout_GSL_Reload_Blunderbuss', 'Shout_GSL_Reload_Musket',
                     'Shout_GSL_Quickload_MainHand', 'Shout_GSL_Quickload_OffHand', 'Shout_GSL_Quickload_Both'):
            with self.subTest(spell=name):
                flags = self.spell(name).get('SpellFlags', '').split(';')
                self.assertIn('Stealth', flags)
                self.assertIn('Invisible', flags)

    def test_violent_shot_is_three_weapon_agnostic_grit_tiers(self) -> None:
        self.assertEqual(self.spell('Shout_GSL_ViolentShot')['ContainerSpells'],
                         'Projectile_GSL_ViolentShot_1;Projectile_GSL_ViolentShot_2;Projectile_GSL_ViolentShot_3')
        for tier in (1, 2, 3):
            with self.subTest(tier=tier):
                fields = self.spell(f'Projectile_GSL_ViolentShot_{tier}')
                self.assertEqual(fields['UseCosts'], f'ActionPoint:1;GunslingerGrit:{tier}')
                for gun, dice in (('Flintlock', f'{tier}d8'), ('Blunderbuss', f'{2 * tier}d6'), ('Musket', f'{3 * tier}d4')):
                    self.assertIn(f"IF(HasPassive('GSL_{gun}_MainHand',context.Source)):DealDamage(MainRangedWeapon+{dice},",
                                  fields['SpellSuccess'])
                    self.assertIn(f'UseActionResource(SELF,Gunslinger{gun}Ammo,1,0)', fields['SpellProperties'])
                    self.assertIn(f"HasActionResource('Gunslinger{gun}Ammo',1,0)", fields['RequirementConditions'])

    def test_ricochet_shot_chains_to_four_enemies_for_three_grit(self) -> None:
        base = self.spell('Projectile_GSL_RicochetShot')
        self.assertEqual(base['UseCosts'], 'ActionPoint:1;GunslingerGrit:3')
        self.assertEqual(base['TooltipUseCosts'], 'ActionPoint:1;GunslingerGrit:3')
        self.assertEqual(base['TargetConditions'], 'Character() and Enemy() and not Dead()')
        for kind in ('Flintlock', 'Blunderbuss', 'Musket'):
            self.assertIn(f'UseActionResource(SELF,Gunslinger{kind}Ammo,1,0)', base['SpellProperties'])
            self.assertIn(f"HasActionResource('Gunslinger{kind}Ammo',1,0)", base['RequirementConditions'])
        self.assertIn('DealDamage(MainRangedWeapon,MainRangedWeaponDamageType)', base['SpellSuccess'])
        self.assertIn('SpawnExtraProjectiles(Projectile_GSL_RicochetShot_Ricochet)', base['SpellSuccess'])
        self.assertEqual(base['SpellFail'], 'SpawnExtraProjectiles(Projectile_GSL_RicochetShot_Ricochet)')
        self.assertEqual(base['Icon'], 'Item_ARR_Arrow_Of_Ricochet')
        self.assertEqual(self.entries['GSL_Desperado_RicochetShotUnlock'].fields['Boosts'],
                         'UnlockSpell(Projectile_GSL_RicochetShot)')

        chain = (
            ('Projectile_GSL_RicochetShot_Ricochet', 'Projectile_GSL_RicochetShot_Ricochet_2'),
            ('Projectile_GSL_RicochetShot_Ricochet_2', 'Projectile_GSL_RicochetShot_Ricochet_3'),
            ('Projectile_GSL_RicochetShot_Ricochet_3', None),
        )
        for name, next_name in chain:
            with self.subTest(projectile=name):
                fields = self.spell(name)
                self.assertIn('DealDamage(MainRangedWeapon/2,MainRangedWeaponDamageType)', fields['SpellSuccess'])
                self.assertIn('not Self() and not Dead() and Enemy()', fields['TargetConditions'])
                self.assertNotIn('UseActionResource', self.entries[name].fields.get('SpellProperties', ''))
                self.assertEqual(self.entries[name].fields.get('UseCosts', ''), '')
                expected_next = f'SpawnExtraProjectiles({next_name})' if next_name else ''
                self.assertEqual(fields['SpellFail'], expected_next)
                if next_name:
                    self.assertTrue(fields['SpellSuccess'].endswith(expected_next))
                else:
                    self.assertEqual(fields['ExtraProjectileTargetConditions'], '')

    def test_arcane_reload_is_a_concentration_weapon_enchantment(self) -> None:
        spell = self.spell('Shout_GSL_ArcaneReload')
        self.assertEqual(spell['UseCosts'], 'BonusActionPoint:1')
        self.assertIn('IsConcentration', spell['SpellFlags'].split(';'))
        self.assertNotIn('IsSpell', spell['SpellFlags'].split(';'))
        self.assertEqual(spell['SpellProperties'], 'ApplyEquipmentStatus(RangedMainHand,GSL_ARCANE_RELOAD,100,-1)')
        self.assertNotIn('Cooldown', spell)
        self.assertEqual(self.entries['GSL_ARCANE_RELOAD'].fields['Icon'], 'GSL_ArcaneReload')

    def test_save_repair_temporary_hp_and_movement_definitions(self) -> None:
        line = self.spell('Zone_GSL_LineEmUp')
        self.assertTrue(line['SpellRoll'].startswith('not SavingThrow(Ability.Dexterity,'))
        self.assertEqual(line['Shape'], 'Square')
        self.assertEqual(line['SpellFail'], 'DealDamage(MainRangedWeapon/4,MainRangedWeaponDamageType)')
        self.assertEqual(self.spell('Shout_GSL_RapidRepair_Main')['SpellRoll'], 'SkillCheck(Skill.SleightOfHand,18)')
        self.assertEqual(self.entries['GSL_BITE_THE_BULLET'].fields['Boosts'], 'TemporaryHP(2*ProficiencyBonus)')
        self.assertEqual(self.spell('Shout_GSL_StableShot')['UseCosts'], 'Movement:6')
        self.assertNotIn('Movement(-6)', self.entries['GSL_Marksman_StableShot'].fields['Boosts'])


if __name__ == '__main__':
    unittest.main()
