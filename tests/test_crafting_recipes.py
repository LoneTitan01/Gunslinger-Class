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
    fields = dict(re.findall(r'^data "([^"]+)" "(.*)"$', match[1], re.MULTILINE))
    using = re.search(r'^using "([^"]+)"$', match[1], re.MULTILINE)
    if using is not None:
        fields['using'] = using.group(1)
    return fields


class CraftingRecipeTests(unittest.TestCase):
    def test_combination_firearm_display_names_are_unique(self) -> None:
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        localization = ET.parse(
            ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
        )
        localized_names = {
            content.get('contentuid'): content.text
            for content in localization.findall('.//content')
        }
        entries = read_stats([weapon_stats])

        def inherited_display_handle(name: str) -> str:
            weapon_name = name
            visited: set[str] = set()
            while name:
                self.assertNotIn(name, visited, f'Weapon inheritance cycle at {name}')
                visited.add(name)
                entry = entries.get(name)
                self.assertIsNotNone(entry, f'Missing weapon stat {name}')
                display = entry.fields.get('DisplayName')
                if display is not None:
                    return display.split(';', 1)[0]
                name = entry.parent
            self.fail(f'No inherited DisplayName for combination weapon {weapon_name}')

        display_names: dict[str, list[str]] = {}
        for name in entries:
            if not re.match(r'WPN_GSL_(?:Flintlock|Musket|Blunderbuss)_', name):
                continue
            handle = inherited_display_handle(name)
            self.assertIn(handle, localized_names, name)
            label = localized_names[handle]
            display_names.setdefault(label, []).append(name)
        duplicates = {
            label: weapons
            for label, weapons in display_names.items()
            if len(weapons) > 1
        }
        self.assertFalse(duplicates, f'Combination weapons need unique display names: {duplicates}')

    def test_blunderbuss_combinations_are_reversible_and_mapped(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        localization = ET.parse(
            ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
        )
        localized_uid_values = [
            content.get('contentuid')
            for content in localization.findall('.//content')
        ]
        localized_ids = set(localized_uid_values)
        self.assertEqual(len(localized_uid_values), len(localized_ids))
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('Hoppy', 'MAG_Revitalizing_Warpick'),
            ('InfernalMaceUncommon', 'MAG_Infernal_Mace'),
            ('DoomHammer', 'UNI_DoomHammer'),
            ('EverburnBlade', 'MAG_Fire_AlwaysDippedInFire_Greatsword'),
            ('VeryHeavyGreataxe', 'UNI_SuperheavyWeapon'),
            ('SwordOfJustice', 'PLA_WPN_SwordOfJustice'),
            ('Skinburster', 'MAG_ZOC_ForceConduit_Halberd'),
            ('UndeadBane', 'MAG_WYRM_UndeadBane_GreatAxe'),
            ('Gandrel', 'MAG_Gandrel_UndeadSlayer_HeavyCrossbow'),
            ('ArgumentSolver', 'MAG_Poison_Greatclub'),
            ('Hamarhraft', 'MAG_Mobility_ExplosionOnJump_Maul'),
            ('BloodedGreataxe', 'MAG_LowHP_IncreaseDamage_Greataxe'),
            ('CorrosiveFlail', 'MAG_Corrosive_Flail'),
            ('DefenderFlail', 'MAG_BG_OfEasthaven_Defender_Flail'),
            ('FlailOfAges', 'MAG_BG_OfAges_Flail'),
            ('InfernalMace', 'MAG_Infernal_Mace_2'),
            ('DefenderGreataxe', 'MAG_PHB_Defender_Greataxe'),
            ('Drakethroat', 'MAG_BG_DragonsBreath_Glaive'),
            ('Harmonium', 'MAG_BG_Harmonium_Halberd'),
            ('Hellbeard', 'MAG_Infernal_Hellbeard_Halberd'),
            ('MonsterSlayer', 'MAG_MonsterSlayer_Glaive'),
            ('MoonlightGlaive', 'MAG_Moonlight_Glaive'),
            ('Sorrow', 'DEN_HalsinBlade'),
            ('SussurGreatsword', 'FOR_IncompleteMasterwork_SussurGreatsword'),
            ('Harold', 'MAG_BG_Harold_HeavyCrossbow'),
            ('PunchDrunkBastard', 'MAG_TWN_Brewery_Greatclub'),
            ('SwordOfChaos', 'MAG_BG_Sarevok_OfChaos_Greatsword'),
            ('UnseenMenace', 'MAG_Invisible_Pike'),
            ('DeepDelver', 'UND_KC_Elder_Warpick'),
            ('Xyanyde', 'GOB_DrowCommander_Mace'),
            ('ExterminatorsAxe', 'UND_DuergarRaft_PestKillerAxe'),
            ('PsionicGreatsword', 'MAG_LowHP_IncreaseDamagePsychic_GithGreatsword'),
            ('LightOfCreation', 'WPN_Tower_AutomatonHalberd'),
            ('Woundseeker', 'MAG_TheWoundSeeker_Greatsword'),
            ('ArcaneForce', 'MAG_Githborn_TelekineticBolt_HeavyCrossbow'),
            ('AdamantineMace', 'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Mace'),
            ('ShatteredFlail', 'PLA_ConflictedFlind_Flail_Broken'),
            ('TwistOfFortune', 'MAG_TWN_Taxblade_Morningstar'),
            ('BreachingPikestaff', 'MAG_Force_Pike'),
            ('Corpsegrinder', 'MAG_SWA_Roaring_Maul'),
            ('JorgoralsGreatsword', 'MAG_Colossal_Greatsword'),
            ('RatBat', 'TWN_RatCatcher'),
            ('Soulbreaker', 'MAG_Githborn_Mindcrusher_Greatsword'),
            ('Giantbreaker', 'MAG_MeleeDebuff_AttackDebuff2_OnDamage_HeavyCrossbow'),
            ('HandmaidensMace', 'MAG_Viconia_Mace'),
            ('SacredStar', 'MAG_RadiantLight_Morningstar'),
            ('Foebreaker', 'MAG_TheDestroyer_Maul'),
            ('HalberdOfVigilance', 'MAG_PoR_OfVigilance_Halberd'),
            ('HellfireGreataxe', 'MAG_WATCHER_Human_Greataxe'),
            ('Sethan', 'MAG_SpiritualStand_Greataxe'),
            ('FabricatedArbalest', 'MAG_Gortash_HeavyCrossbow'),
            ('HellfireEngineCrossbow', 'MAG_WATCHER_Human_Crossbow'),
            ('RavengardsScourger', 'MAG_LC_OfTheFist_MorningStar'),
            ('LongArmOfTheGur', 'MAG_LC_UndeadSlayer_Crossbow'),
        )
        expected_names = {name for name, _ in recipes}
        combination_text = combinations.read_text(encoding='utf-8-sig')
        weapon_text = weapon_stats.read_text(encoding='utf-8-sig')
        self.assertEqual(
            set(re.findall(r'^new ItemCombination "GSL_Assembly_Blunderbuss_(.+)"$', combination_text, re.MULTILINE)),
            expected_names,
        )
        self.assertEqual(
            set(re.findall(r'^new entry "WPN_GSL_Blunderbuss_(.+)"$', weapon_text, re.MULTILINE)),
            expected_names,
        )
        maps: set[str] = set()

        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Blunderbuss_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Blunderbuss_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Blunderbuss'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Blunderbuss_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Blunderbuss_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Blunderbuss_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Blunderbuss')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                map_key = template.find("attribute[@id='MapKey']").get('value')
                maps.add(map_key)
                self.assertEqual(fused['RootTemplate'], map_key)
                self.assertEqual(
                    template.find("attribute[@id='Stats']").get('value'),
                    crafted_weapon,
                )
                for ability in (
                    'UnlockSpell(Shout_GSL_Reload_Blunderbuss)',
                    'UnlockSpell(Zone_GSL_Scattershot)',
                ):
                    self.assertIn(ability, fused['BoostsOnEquipMainHand'])
                self.assertIn(
                    fused['DisplayName'].split(';')[0],
                    localized_ids,
                )
                self.assertIn(
                    fused['Description'].split(';')[0],
                    localized_ids,
                )

        self.assertEqual(len(maps), len(recipes))

    def test_new_blunderbuss_sources_have_verified_templates_and_adapted_effects(self) -> None:
        reference_weapons = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        passives = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'
        references = (
            ('MAG_LC_OfTheFist_MorningStar', '83715b12-8d39-48b7-a981-fe50a4ec2d4e'),
            ('MAG_LC_UndeadSlayer_Crossbow', '85f60e49-d868-4897-afc5-b22e965a0471'),
        )
        for source_name, template_id in references:
            with self.subTest(source=source_name):
                source = read_entry(reference_weapons, 'entry', source_name)
                self.assertEqual(source['RootTemplate'], template_id)

        scourger = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Blunderbuss_RavengardsScourger',
        )
        self.assertIn('UnlockSpell(Target_MAG_CommanderStrike)', scourger['Boosts'])
        gur = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Blunderbuss_LongArmOfTheGur',
        )
        self.assertIn('GSL_Blunderbuss_UndeadSlayer_Passive', gur['PassivesOnEquip'])
        undead_slayer = read_entry(
            passives,
            'entry',
            'GSL_Blunderbuss_UndeadSlayer_Passive',
        )
        self.assertIn("Tagged('UNDEAD',context.Target)", undead_slayer['Boosts'])
        self.assertIn('RollBonus(RangedWeaponAttack,1d4)', undead_slayer['Boosts'])
        self.assertIn('CharacterWeaponDamage(1d4,MainRangedWeaponDamageType)', undead_slayer['Boosts'])

    def test_remaining_blunderbuss_passives_are_firearm_adapted(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        passives = data_dir / 'GunslingerPassives.txt'
        weapon_stats = data_dir / 'Weapon.txt'
        localization = ET.parse(
            ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
        )
        localized_ids = {
            content.get('contentuid')
            for content in localization.findall('.//content')
        }

        psionic = read_entry(passives, 'entry', 'GSL_Blunderbuss_Psionic_Passive')
        self.assertIn("Tagged('GITHYANKI',context.Source)", psionic['BoostConditions'])
        self.assertIn('IsRangedWeaponAttack()', psionic['Boosts'])
        woundseeker = read_entry(
            passives,
            'entry',
            'GSL_Blunderbuss_Woundseeker_Passive',
        )
        self.assertIn('RollBonus(RangedWeaponAttack,1d4)', woundseeker['Boosts'])
        taxblade = read_entry(passives, 'entry', 'GSL_Blunderbuss_Taxblade_Passive')
        self.assertIn('IsRangedWeaponAttack()', taxblade['Boosts'])
        soulbreaker = read_entry(
            passives,
            'entry',
            'GSL_Blunderbuss_Soulbreaker_Passive',
        )
        self.assertIn('IsRangedWeaponAttack()', soulbreaker['Boosts'])
        for name, passive_name, passive in (
            ('PsionicGreatsword', 'GSL_Blunderbuss_Psionic_Passive', psionic),
            ('Woundseeker', 'GSL_Blunderbuss_Woundseeker_Passive', woundseeker),
            ('TwistOfFortune', 'GSL_Blunderbuss_Taxblade_Passive', taxblade),
            ('Soulbreaker', 'GSL_Blunderbuss_Soulbreaker_Passive', soulbreaker),
        ):
            with self.subTest(name=name):
                fused = read_entry(
                    weapon_stats,
                    'entry',
                    f'WPN_GSL_Blunderbuss_{name}',
                )
                self.assertIn(
                    passive['DisplayName'].split(';')[0],
                    localized_ids,
                )
                self.assertIn(passive['Description'].split(';')[0], localized_ids)
                self.assertIn(passive_name, fused.get('PassivesOnEquip', ''))

    def test_blunderbuss_adapted_abilities_are_defined_and_ammo_costed(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        localization = ET.parse(
            ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
        )
        localized_ids = {
            content.get('contentuid')
            for content in localization.findall('.//content')
        }
        weapon = read_entry(
            data_dir / 'Weapon.txt',
            'entry',
            'WPN_GSL_Blunderbuss_VeryHeavyGreataxe',
        )
        self.assertIn(
            'UnlockSpell(Zone_GSL_GargantuanScattershot_Blunderbuss)',
            weapon['BoostsOnEquipMainHand'],
        )

        spells = data_dir / 'GunslingerSpells.txt'
        expected_spells = {
            'Projectile_GSL_RevitalizingShot_Blunderbuss': (
                'ActionPoint:1;GunslingerBlunderbussAmmo:1',
                'RegainHitPoints(SELF,1d6)',
            ),
            'Projectile_GSL_CorrosiveShot_Blunderbuss': (
                'ActionPoint:1;GunslingerBlunderbussAmmo:1',
                'CreateSurface(1.5,3,Acid)',
            ),
            'Projectile_GSL_SorrowfulLash_Blunderbuss': (
                'BonusActionPoint:1;GunslingerBlunderbussAmmo:1',
                'Force(-3',
            ),
            'Zone_GSL_PoisonMist_Blunderbuss': (
                'ActionPoint:1;GunslingerBlunderbussAmmo:1',
                'CreateSurface(1.5,3,PoisonCloud)',
            ),
            'Zone_GSL_GargantuanScattershot_Blunderbuss': (
                'ActionPoint:1;GunslingerBlunderbussAmmo:1',
                'DealDamage(1d6/2,Bludgeoning)',
            ),
            'Zone_GSL_PunchDrunkScattershot_Blunderbuss': (
                'ActionPoint:1;GunslingerBlunderbussAmmo:1',
                "HasStatus('DRUNK',context.Source)",
            ),
        }
        for spell_name, (cost, effect) in expected_spells.items():
            with self.subTest(spell=spell_name):
                spell = read_entry(spells, 'entry', spell_name)
                self.assertEqual(spell['UseCosts'], cost)
                self.assertIn(effect, spell['SpellSuccess'])
                self.assertIn(spell['DisplayName'].split(';')[0], localized_ids)
                self.assertIn(spell['Description'].split(';')[0], localized_ids)

        passives = data_dir / 'GunslingerPassives.txt'
        undead_bane = read_entry(passives, 'entry', 'GSL_Blunderbuss_UndeadBane_Passive')
        blooded = read_entry(passives, 'entry', 'GSL_Blunderbuss_Blooded_Passive')
        self.assertIn("Tagged('UNDEAD') or Tagged('FIEND')", undead_bane['Boosts'])
        self.assertIn('DamageBonus(1d6,Bludgeoning,false)', undead_bane['Boosts'])
        self.assertIn('HasHPPercentageWithoutTemporaryHPEqualOrLessThan(50,context.Target)', blooded['Boosts'])
        self.assertIn('DamageBonus(1d4,Bludgeoning,false)', blooded['Boosts'])

        drunk = read_entry(passives, 'entry', 'GSL_Blunderbuss_PunchDrunk_Passive')
        unseen = read_entry(passives, 'entry', 'GSL_Blunderbuss_UnseenMenace_Passive')
        defender = read_entry(passives, 'entry', 'GSL_Blunderbuss_DefenderFlail_Passive')
        self.assertIn("HasStatus('DRUNK',context.Source)", drunk['Boosts'])
        self.assertIn('Advantage(AttackRoll)', drunk['Boosts'])
        self.assertIn('ApplyEquipmentStatus(SELF, RangedMainHand', unseen['StatsFunctors'])
        unseen_weapon = read_entry(data_dir / 'Weapon.txt', 'entry', 'WPN_GSL_Blunderbuss_UnseenMenace')
        self.assertIn('CriticalHit(1)', unseen_weapon['DefaultBoosts'])
        self.assertEqual(defender['Boosts'], 'DamageReduction(Bludgeoning, Flat, 1)')
        for passive in (undead_bane, blooded, drunk, unseen, defender):
            self.assertIn(passive['DisplayName'].split(';')[0], localized_ids)
            self.assertIn(passive['Description'].split(';')[0], localized_ids)

    def test_musket_action_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        recipes = (
            ('Bonesaw', 'MAG_Surgeon_Bonesaw', 'WPN_GSL_Musket_Bonesaw'),
            ('Faithbreaker', 'GOB_GoblinKing_Warhammer', 'WPN_GSL_Musket_Faithbreaker'),
            ('Witchbreaker', 'MAG_Spellbreaker_Battleaxe', 'WPN_GSL_Musket_Witchbreaker'),
            ('Titanstring', 'MAG_StrongString_Longbow', 'WPN_GSL_Musket_Titanstring'),
            ('WatchersGuide', 'CHA_CompassSpear', 'WPN_GSL_Musket_WatchersGuide'),
            ('CorellonsGrace', 'UNI_RepeatStaff', 'WPN_GSL_Musket_CorellonsGrace'),
            ('Intransigent', 'UND_DuergarRaft_GruesomeHammer', 'WPN_GSL_Musket_Intransigent'),
            ('JaggedSpear', 'GOB_Torturer_Spear', 'WPN_GSL_Musket_JaggedSpear'),
            ('MelfsFirstStaff', 'MAG_BasicEnchanted_Quarterstaff', 'WPN_GSL_Musket_MelfsFirstStaff'),
            ('NaturesSnare', 'DEN_TunnelStaff', 'WPN_GSL_Musket_NaturesSnare'),
            ('RainDancer', 'UNI_StaffOfRain', 'WPN_GSL_Musket_RainDancer'),
            ('MumblingWizard', 'WYR_Circus_MumblingStaff', 'WPN_GSL_Musket_MumblingWizard'),
            ('ArcaneBlessing', 'UND_Tower_StaffBlessMystra', 'WPN_GSL_Musket_ArcaneBlessing'),
            ('Crones', 'Quest_HAG_HagLair_Staff', 'WPN_GSL_Musket_Crones'),
            ('Hellrider', 'MAG_WYR_Hellrider_Longbow', 'WPN_GSL_Musket_Hellrider'),
            ('Spellthief', 'UNI_Bow_SpellslotRecharge', 'WPN_GSL_Musket_Spellthief'),
            ('DespairAthkatla', 'MAG_LC_Lorroakan_Quarterstaff', 'WPN_GSL_Musket_DespairAthkatla'),
            (
                'AdamantineLongsword',
                'MAG_MeleeDebuff_AttackDebuff12versatile_OnDamage_Longsword',
                'WPN_GSL_Musket_AdamantineLongsword',
            ),
            ('BigboyChewToy', 'MAG_Combat_Quarterstaff', 'WPN_GSL_Musket_BigboyChewToy'),
            ('BlackguardSword', 'MAG_OB_Paladin_DeathKnight_Longsword', 'WPN_GSL_Musket_BlackguardSword'),
            ('BladeOppressedSouls', 'MAG_Illithid_MindOverload_Weapon_Longsword', 'WPN_GSL_Musket_BladeOppressedSouls'),
            ('Cacophony', 'MAG_Thunder_ThunderClap_Quarterstaff', 'WPN_GSL_Musket_Cacophony'),
            ('Caitiff', 'MAG_PHB_PactKeeper_Quarterstaff', 'WPN_GSL_Musket_Caitiff'),
            ('ChargeBound', 'MAG_Bonded_Shocking_Warhammer', 'WPN_GSL_Musket_ChargeBound'),
            ('ClownHammer', 'UNI_WYR_Circus_ClownHammer', 'WPN_GSL_Musket_ClownHammer'),
            ('CreationsEcho', 'MAG_Creation_Echo_Quarterstaff', 'WPN_GSL_Musket_CreationsEcho'),
            ('GoldWyrmling', 'MAG_Fire_FireDamage_Quarterstaff', 'WPN_GSL_Musket_GoldWyrmling'),
            ('HammerOfTheJust', 'MAG_Tyrrant_Warhammer', 'WPN_GSL_Musket_HammerOfTheJust'),
            ('HarperSacredstriker', 'MAG_Harpers_OfWeapons_Quarterstaff', 'WPN_GSL_Musket_HarperSacredstriker'),
            ('HollowsStaff', 'MAG_HigherNecromancy_Staff', 'WPN_GSL_Musket_HollowsStaff'),
            ('KethericsWarhammer', 'MAG_Ketheric_Warhammer', 'WPN_GSL_Musket_KethericsWarhammer'),
            ('PaleOak', 'DEN_FaithwardenStaff', 'WPN_GSL_Musket_PaleOak'),
            ('SparkyPoints', 'MAG_ChargedLightning_Trident', 'WPN_GSL_Musket_SparkyPoints'),
            ('Spellsparkler', 'MAG_ChargedLightning_Quarterstaff', 'WPN_GSL_Musket_Spellsparkler'),
            ('StaffOfInterruption', 'MAG_LC_Counterspell_Quarterstaff', 'WPN_GSL_Musket_StaffOfInterruption'),
            ('StaffOfTheEmperor', 'END_Emperor_Staff', 'WPN_GSL_Musket_StaffOfTheEmperor'),
            ('SwordOfTheEmperor', 'LOW_Elfsong_EmperorSword_LongSword', 'WPN_GSL_Musket_SwordOfTheEmperor'),
            ('ViciousBattleaxe', 'MAG_Vicious_Battleaxe', 'WPN_GSL_Musket_ViciousBattleaxe'),
            ('Joltshooter', 'MAG_ChargedLightning_Longbow', 'WPN_GSL_Musket_Joltshooter'),
            ('DwarvenThrower', 'MAG_PHB_DwarvenThrower_Warhammer', 'WPN_GSL_Musket_DwarvenThrower'),
            ('IncandescentStaff', 'MAG_FlamingFist_StaffOfFire', 'WPN_GSL_Musket_IncandescentStaff'),
            ('MourningFrost', 'MAG_Cold_IncreaseColdDamageOnCast_Staff', 'WPN_GSL_Musket_MourningFrost'),
            ('CherishedNecromancy', 'MAG_GreaterNecromancy_Staff', 'WPN_GSL_Musket_CherishedNecromancy'),
            ('Spellpower', 'MAG_OfSpellPower_Quarterstaff', 'WPN_GSL_Musket_Spellpower'),
            ('StaffOfTheRam', 'MAG_LC_OfTheRam_Quarterstaff', 'WPN_GSL_Musket_StaffOfTheRam'),
            ('TridentOfTheWaves', 'MAG_LC_Wave_Trident', 'WPN_GSL_Musket_TridentOfTheWaves'),
            ('VossSilverSword', 'MAG_Primeval_Silver_Longsword', 'WPN_GSL_Musket_VossSilverSword'),
            ('Woe', 'MAG_LC_CazadorVampiric_Quarterstaff', 'WPN_GSL_Musket_Woe'),
            ('DeadShot', 'MAG_DeadShot_Longbow', 'WPN_GSL_Musket_DeadShot'),
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        for name, source_weapon, crafted_weapon in recipes:
            with self.subTest(name=name):
                assembly = read_entry(combinations, 'ItemCombination', f'GSL_Assembly_Musket_{name}')
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Musket'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Musket_{name}_1',
                )
                self.assertEqual(assembly_result['Result 1'], crafted_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Musket_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(disassembly['Transform 1'], 'Transform')
                self.assertEqual(disassembly['Transform 2'], 'Consume')
                disassembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Musket_{name}_1',
                )
                self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Musket')
                self.assertEqual(disassembly_result['Result 2'], source_weapon)

    def test_latest_musket_combos_adapt_source_weapon_features(self) -> None:
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        passive_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'
        status_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerStatuses.txt'

        clown = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_ClownHammer')
        clown_source = read_entry(source_dev / 'Weapon.txt', 'entry', 'UNI_WYR_Circus_ClownHammer')
        clown_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'UNI_WYR_Circus_ClownHammer_Passive',
        )
        self.assertIn('WeaponEnchantment(2)', clown['DefaultBoosts'])
        self.assertIn('UNI_WYR_Circus_ClownHammer_Passive', clown_source['PassivesOnEquip'])
        self.assertIn('UNI_WYR_Circus_ClownHammer_Passive', clown['PassivesOnEquip'])
        self.assertIn('IsCritical()', clown_passive['Conditions'])
        self.assertIn('SavingThrow(Ability.Wisdom,17', clown_passive['StatsFunctors'])
        self.assertIn('HIDEOUS_LAUGHTER', clown_passive['StatsFunctors'])

        echo = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_CreationsEcho')
        echo_passive = read_entry(passive_stats, 'entry', 'GSL_CreationEcho_Resistance')
        self.assertEqual(echo['DefaultBoosts'], 'WeaponProperty(Magical)')
        self.assertIn('GSL_CreationEcho_Resistance', echo['PassivesOnEquip'])
        for damage_type in ('Acid', 'Fire', 'Lightning', 'Radiant', 'Necrotic'):
            status = f'GSL_CREATION_ECHO_{damage_type.upper()}_RESISTANCE'
            self.assertIn(f'IsDamageType{damage_type}()', echo_passive['StatsFunctors'])
            self.assertIn(f'ApplyStatus(SELF,{status},100,2)', echo_passive['StatsFunctors'])
            self.assertEqual(
                read_entry(status_stats, 'entry', status)['Boosts'],
                f'Resistance({damage_type},Resistant)',
            )

        gold = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_GoldWyrmling')
        gold_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Fire_FireDamage_Quarterstaff',
        )
        fire_bolt = read_entry(
            source_dev / 'Spell_Projectile.txt',
            'entry',
            'Projectile_MAG_FireBolt_Staff',
        )
        self.assertIn('WeaponDamage(1d4,Fire)', gold['DefaultBoosts'])
        self.assertIn('WeaponEnchantment(1)', gold['DefaultBoosts'])
        self.assertIn('Projectile_MAG_FireBolt_Staff', gold_source['Boosts'])
        self.assertIn('UnlockSpell(Projectile_MAG_FireBolt_Staff)', gold['BoostsOnEquipMainHand'])
        self.assertEqual(fire_bolt['using'], 'Projectile_FireBolt')

        hammer = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_HammerOfTheJust')
        hammer_source = read_entry(source_dev / 'Weapon.txt', 'entry', 'MAG_Tyrrant_Warhammer')
        hammer_passive = read_entry(passive_stats, 'entry', 'GSL_HammerOfTheJust_Passive')
        detect_thoughts = read_entry(source_dev / 'Spell_Shout.txt', 'entry', 'Shout_MAG_DetectThoughts')
        self.assertIn('WeaponEnchantment(2)', hammer['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Radiant)', hammer['DefaultBoosts'])
        self.assertIn('UnlockSpell(Shout_MAG_DetectThoughts)', hammer_source['Boosts'])
        self.assertIn('UnlockSpell(Shout_MAG_DetectThoughts)', hammer['BoostsOnEquipMainHand'])
        self.assertIn("Tagged('UNDEAD'", hammer_passive['Conditions'])
        self.assertIn("Tagged('FIEND'", hammer_passive['Conditions'])
        self.assertIn('DealDamage(1d6,Piercing)', hammer_passive['StatsFunctors'])
        self.assertEqual(detect_thoughts['Cooldown'], 'OncePerRestPerItem')

    def test_following_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        passives = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'

        harper = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_HarperSacredstriker')
        harper_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Harpers_OfWeapons_Quarterstaff',
        )
        spiritual_weapon = read_entry(
            source_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_SpiritualWeapon',
        )
        self.assertIn('WeaponEnchantment(1)', harper['DefaultBoosts'])
        self.assertIn('Target_MAG_SpiritualWeapon', harper_source['Boosts'])
        self.assertIn('UnlockSpell(Target_MAG_SpiritualWeapon)', harper['BoostsOnEquipMainHand'])
        self.assertEqual(spiritual_weapon['Level'], '6')
        self.assertEqual(spiritual_weapon['Cooldown'], 'OncePerRestPerItem')

        hollow = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_HollowsStaff')
        hollow_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_HigherNecromancy_Staff',
        )
        heightened_necromancy = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_Heightened_Necromancy_Passive',
        )
        arms_of_hadar = read_entry(
            source_dev / 'Spell_Shout.txt',
            'entry',
            'Shout_MAG_ArmsOfHadar_3',
        )
        self.assertIn('WeaponEnchantment(1)', hollow['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Necrotic)', hollow['DefaultBoosts'])
        self.assertIn('MAG_Heightened_Necromancy_Passive', hollow_source['PassivesOnEquip'])
        self.assertIn('MAG_Heightened_Necromancy_Passive', hollow['PassivesOnEquip'])
        self.assertIn('ModifySavingThrowDisadvantage()', heightened_necromancy['Boosts'])
        self.assertIn('Shout_MAG_ArmsOfHadar_3', hollow_source['Boosts'])
        self.assertIn('UnlockSpell(Shout_MAG_ArmsOfHadar_3)', hollow['BoostsOnEquipMainHand'])
        self.assertEqual(arms_of_hadar['Cooldown'], 'OncePerRestPerItem')

        ketheric = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_KethericsWarhammer')
        ketheric_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Ketheric_Warhammer',
        )
        self.assertEqual(ketheric_source['using'], 'WPN_Warhammer_1')
        self.assertIn('WeaponEnchantment(1)', ketheric['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Psychic)', ketheric['DefaultBoosts'])

        pale_oak = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_PaleOak')
        pale_source = read_entry(source / 'Weapon.txt', 'entry', 'DEN_FaithwardenStaff')
        faithwarden_passive = read_entry(
            source / 'Passive.txt',
            'entry',
            'DEN_FaithwardenStaff_Passive',
        )
        entangle_staff = read_entry(
            source / 'Spell_Target.txt',
            'entry',
            'Target_DEN_Entangle_Staff',
        )
        self.assertIn('DEN_FaithwardenStaff_Passive', pale_source['PassivesOnEquip'])
        self.assertIn('DEN_FaithwardenStaff_Passive', pale_oak['PassivesOnEquip'])
        self.assertIn('StatusImmunity(ENSNARED_VINES)', faithwarden_passive['Boosts'])
        self.assertIn('UnlockSpell(Target_DEN_Entangle_Staff', pale_source['Boosts'])
        self.assertIn('UnlockSpell(Target_DEN_Entangle_Staff', pale_oak['BoostsOnEquipMainHand'])
        self.assertEqual(entangle_staff['Cooldown'], 'OncePerRestPerItem')

    def test_next_four_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'

        sparky = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_SparkyPoints')
        sparky_source = read_entry(source / 'Weapon.txt', 'entry', 'MAG_ChargedLightning_Trident')
        weapon_charge = read_entry(
            source / 'Passive.txt',
            'entry',
            'MAG_ChargedLightning_Charge_OnDamage_Passive',
        )
        self.assertEqual(sparky['DefaultBoosts'], 'WeaponProperty(Magical)')
        self.assertIn('MAG_ChargedLightning_Charge_OnDamage_Passive', sparky_source['PassivesOnEquip'])
        self.assertIn('MAG_ChargedLightning_Charge_OnDamage_Passive', sparky['PassivesOnEquip'])
        self.assertEqual(weapon_charge['Properties'], 'OncePerAttack')
        self.assertIn('AttackedWithPassiveSourceWeapon()', weapon_charge['Conditions'])
        self.assertIn("ApplyStatus(SELF, MAG_CHARGED_LIGHTNING,100, 2)", weapon_charge['StatsFunctors'])

        sparkler = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Spellsparkler')
        sparkler_source = read_entry(
            source / 'Weapon.txt',
            'entry',
            'MAG_ChargedLightning_Quarterstaff',
        )
        spell_charge = read_entry(
            source / 'Passive.txt',
            'entry',
            'MAG_ChargedLightning_Charge_OnSpellDamage_Passive',
        )
        self.assertEqual(sparkler['DefaultBoosts'], 'WeaponProperty(Magical)')
        self.assertIn('MAG_ChargedLightning_Charge_OnSpellDamage_Passive', sparkler_source['PassivesOnEquip'])
        self.assertIn('MAG_ChargedLightning_Charge_OnSpellDamage_Passive', sparkler['PassivesOnEquip'])
        self.assertEqual(spell_charge['Conditions'], 'IsSpell()')
        self.assertIn("ApplyStatus(SELF, MAG_CHARGED_LIGHTNING,100, 2)", spell_charge['StatsFunctors'])

        interruption = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_StaffOfInterruption')
        interruption_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_LC_Counterspell_Quarterstaff',
        )
        counterspell = read_entry(
            source_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_CounterSpell',
        )
        self.assertIn('WeaponEnchantment(2)', interruption['DefaultBoosts'])
        self.assertIn('UnlockSpell(Target_MAG_CounterSpell)', interruption_source['Boosts'])
        self.assertIn('UnlockSpell(Target_MAG_CounterSpell)', interruption['BoostsOnEquipMainHand'])
        self.assertIn(
            'MAG_LC_Counterspell_Quarterstaff_Resource_Passive',
            interruption_source['PassivesOnEquip'],
        )
        self.assertIn(
            'MAG_LC_Counterspell_Quarterstaff_Resource_Passive',
            interruption['PassivesOnEquip'],
        )
        self.assertEqual(counterspell['Level'], '5')
        self.assertEqual(counterspell['Cooldown'], 'OncePerRestPerItem')

        emperor = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_StaffOfTheEmperor')
        emperor_source = read_entry(source_dev / 'Weapon.txt', 'entry', 'END_Emperor_Staff')
        arcane_enchantment = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_ArcaneEnchantment_Lesser_Passive',
        )
        retaliation = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_END_PsychicRetaliation_Passive',
        )
        self.assertIn('WeaponEnchantment(2)', emperor['DefaultBoosts'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', emperor_source['PassivesOnEquip'])
        self.assertIn('MAG_END_PsychicRetaliation_Passive', emperor_source['PassivesOnEquip'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', emperor['PassivesOnEquip'])
        self.assertIn('MAG_END_PsychicRetaliation_Passive', emperor['PassivesOnEquip'])
        self.assertIn('SpellSaveDC(1)', arcane_enchantment['Boosts'])
        self.assertIn('RollBonus(RangedSpellAttack,1)', arcane_enchantment['Boosts'])
        self.assertIn('IsLastConditionRollSuccess(ConditionRollType.ConditionSavingThrow)', retaliation['Conditions'])
        self.assertIn('ApplyStatus(SWAP, STUNNED, 100, 1', retaliation['StatsFunctors'])

    def test_following_four_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        local_passives = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'

        emperor_sword = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_SwordOfTheEmperor')
        emperor_sword_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'LOW_Elfsong_EmperorSword_LongSword',
        )
        shapesifter = read_entry(source_dev / 'Passive.txt', 'entry', 'MAG_ShapesifterSlayer_Passive')
        durability = read_entry(source_dev / 'Passive.txt', 'entry', 'MAG_MagicalDurability_Passive')
        self.assertIn('WeaponEnchantment(2)', emperor_sword['DefaultBoosts'])
        self.assertEqual(
            emperor_sword_source['PassivesOnEquip'],
            'MAG_ShapesifterSlayer_Passive;MAG_MagicalDurability_Passive',
        )
        self.assertIn('MAG_ShapesifterSlayer_Passive', emperor_sword['PassivesOnEquip'])
        self.assertIn('MAG_MagicalDurability_Passive', emperor_sword['PassivesOnEquip'])
        self.assertIn("HasStatus('SG_Polymorph', context.Target)", shapesifter['Boosts'])
        self.assertIn('RollBonus(SavingThrow,2)', durability['Boosts'])

        vicious = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_ViciousBattleaxe')
        vicious_source = read_entry(source_dev / 'Weapon.txt', 'entry', 'MAG_Vicious_Battleaxe')
        vicious_passive = read_entry(source_dev / 'Passive.txt', 'entry', 'MAG_Vicious_Weapon_Passive')
        self.assertIn('WeaponEnchantment(2)', vicious['DefaultBoosts'])
        self.assertIn('MAG_Vicious_Weapon_Passive', vicious_source['PassivesOnEquip'])
        self.assertIn('MAG_Vicious_Weapon_Passive', vicious['PassivesOnEquip'])
        self.assertIn('IsWeaponAttack() and IsCritical()', vicious_passive['Boosts'])
        self.assertIn('DamageBonus(7,,false)', vicious_passive['Boosts'])

        joltshooter = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Joltshooter')
        joltshooter_source = read_entry(source / 'Weapon.txt', 'entry', 'MAG_ChargedLightning_Longbow')
        charge_passive = read_entry(
            source / 'Passive.txt',
            'entry',
            'MAG_ChargedLightning_Charge_OnDamage_Passive',
        )
        self.assertIn('MAG_ChargedLightning_Charge_OnDamage_Passive', joltshooter_source['PassivesOnEquip'])
        self.assertIn('MAG_ChargedLightning_Charge_OnDamage_Passive', joltshooter['PassivesOnEquip'])
        self.assertIn('ApplyStatus(SELF, MAG_CHARGED_LIGHTNING,100, 2)', charge_passive['StatsFunctors'])

        dwarven = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_DwarvenThrower')
        dwarven_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_PHB_DwarvenThrower_Warhammer',
        )
        dwarven_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_PHB_DwarvenThrower_Passive',
        )
        adapted_dwarven_passive = read_entry(
            local_passives,
            'entry',
            'GSL_Musket_DwarvenThrower_Passive',
        )
        self.assertIn('WeaponEnchantment(2)', dwarven['DefaultBoosts'])
        self.assertIn('MAG_PHB_DwarvenThrower_Passive', dwarven_source['PassivesOnEquip'])
        self.assertIn('GSL_Musket_DwarvenThrower_Passive', dwarven['PassivesOnEquip'])
        self.assertNotIn('MAG_HomingWeapon_Passive', dwarven['PassivesOnEquip'])
        self.assertIn('DealDamage(1d8, Bludgeoning)', dwarven_passive['DescriptionParams'])
        self.assertIn("Tagged('DWARF',context.Source)", adapted_dwarven_passive['Conditions'])
        self.assertIn('SizeEqualOrGreater(Size.Large)', adapted_dwarven_passive['StatsFunctors'])
        self.assertIn('DealDamage(2d8,Bludgeoning)', adapted_dwarven_passive['StatsFunctors'])
        self.assertIn('DealDamage(1d8,Bludgeoning)', adapted_dwarven_passive['StatsFunctors'])

    def test_next_four_very_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'

        incandescent = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_IncandescentStaff')
        incandescent_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_FlamingFist_StaffOfFire',
        )
        fireball = read_entry(
            source_dev / 'Spell_Projectile.txt',
            'entry',
            'Projectile_MAG_FlamingFist_StaffOfFire_Fireball',
        )
        self.assertEqual(
            incandescent['DefaultBoosts'],
            'WeaponProperty(Magical);RollBonus(RangedSpellAttack,1);Resistance(Fire,Resistant)',
        )
        self.assertIn('RollBonus(RangedSpellAttack,1)', incandescent_source['Boosts'])
        self.assertIn('Resistance(Fire, Resistant)', incandescent_source['Boosts'])
        self.assertIn('Projectile_MAG_FireBolt_Staff', incandescent['BoostsOnEquipMainHand'])
        self.assertIn(
            'Projectile_MAG_FlamingFist_StaffOfFire_Fireball',
            incandescent['BoostsOnEquipMainHand'],
        )
        self.assertEqual(fireball['Cooldown'], 'OncePerRestPerItem')

        mourning = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_MourningFrost')
        mourning_source = read_entry(source / 'Weapon.txt', 'entry', 'MAG_Cold_IncreaseColdDamageOnCast_Staff')
        cold_bonus = read_entry(
            source / 'Passive.txt',
            'entry',
            'MAG_Cold_IncreaseColdDamageOnCast_Passive',
        )
        chill = read_entry(
            source / 'Passive.txt',
            'entry',
            'MAG_Cold_ChilledOnSpellDamage_Passive',
        )
        self.assertIn('WeaponEnchantment(1)', mourning['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Cold)', mourning['DefaultBoosts'])
        self.assertIn('UnlockSpell(Projectile_MAG_RayOfFrost_Staff)', mourning_source['Boosts'])
        self.assertIn('Projectile_MAG_RayOfFrost_Staff', mourning['BoostsOnEquipMainHand'])
        self.assertIn('MAG_Cold_IncreaseColdDamageOnCast_Passive', mourning['PassivesOnEquip'])
        self.assertIn('MAG_Cold_ChilledOnSpellDamage_Passive', mourning['PassivesOnEquip'])
        self.assertIn('DamageBonus(1, Cold)', cold_bonus['Boosts'])
        self.assertIn('IsSpell() and HasDamageDoneForType(DamageType.Cold)', chill['Conditions'])
        self.assertIn('ApplyStatus(CHILLED, 100, 2)', chill['StatsFunctors'])

        cherished = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_CherishedNecromancy')
        cherished_source = read_entry(source_dev / 'Weapon.txt', 'entry', 'MAG_GreaterNecromancy_Staff')
        heightened = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_Heightened_Necromancy_Passive',
        )
        essence = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_GreaterNecromancyStaff_LifeEssenceHarvest_Passive',
        )
        self.assertIn('WeaponEnchantment(2)', cherished['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Necrotic)', cherished['DefaultBoosts'])
        self.assertEqual(
            cherished_source['PassivesOnEquip'],
            'MAG_Heightened_Necromancy_Passive;MAG_GreaterNecromancyStaff_LifeEssenceHarvest_Passive',
        )
        self.assertIn('MAG_Heightened_Necromancy_Passive', cherished['PassivesOnEquip'])
        self.assertIn('MAG_GreaterNecromancyStaff_LifeEssenceHarvest_Passive', cherished['PassivesOnEquip'])
        self.assertIn('UnlockSpellVariant(HeightenedNecromancySpellCheck()', heightened['Boosts'])
        self.assertIn('not Item() and Enemy() and IsKillingBlow() and IsSpell()', essence['Conditions'])
        self.assertIn('MAG_GREATER_NECROMANCY_LIFE_ESSENCE', essence['StatsFunctors'])

        spellpower = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Spellpower')
        spellpower_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_OfSpellPower_Quarterstaff',
        )
        arcane = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_ArcaneEnchantment_Lesser_Passive',
        )
        powered_cast = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_MagicItemPoweredCast_Passive',
        )
        self.assertIn('WeaponEnchantment(2)', spellpower['DefaultBoosts'])
        self.assertEqual(
            spellpower_source['PassivesOnEquip'],
            'MAG_ArcaneEnchantment_Lesser_Passive;MAG_MagicItemPoweredCast_Passive',
        )
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', spellpower['PassivesOnEquip'])
        self.assertIn('MAG_MagicItemPoweredCast_Passive', spellpower['PassivesOnEquip'])
        self.assertEqual(spellpower['StatusOnEquip'], 'MAG_SPELL_POWER_STAFF_TECHNICAL')
        self.assertIn('SpellSaveDC(1)', arcane['Boosts'])
        self.assertIn('RollBonus(RangedSpellAttack,1)', arcane['Boosts'])
        self.assertIn('OncePerLongRest', powered_cast['Properties'])
        self.assertIn('RemoveStatus(MAG_MAGIC_ITEM_POWERED_CAST)', powered_cast['StatsFunctors'])

    def test_following_four_very_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        local_passives = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'
        local_spells = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerSpells.txt'
        source_weapons = source_dev / 'Weapon.txt'
        source_passives = source_dev / 'Passive.txt'
        source_spells = source_dev / 'Spell_Target.txt'

        ram = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_StaffOfTheRam')
        ram_source = read_entry(source_weapons, 'entry', 'MAG_LC_OfTheRam_Quarterstaff')
        ram_passive = read_entry(source_passives, 'entry', 'MAG_StaffOFRam_KnockStun_Passive')
        self.assertIn('MAG_StaffOFRam_KnockStun_Passive', ram_source['PassivesOnEquip'])
        self.assertIn('MAG_StaffOFRam_KnockStun_Passive', ram['PassivesOnEquip'])
        self.assertEqual(ram_passive['Properties'], 'OncePerTurn')
        self.assertIn('TargetSizeEqualOrSmaller(Size.Large)', ram_passive['Conditions'])
        self.assertIn("not Tagged('DRAGON')", ram_passive['Conditions'])
        self.assertIn('SavingThrow(Ability.Constitution, 8', ram_passive['Conditions'])
        self.assertIn('ApplyStatus(STUNNED, 100, 1)', ram_passive['StatsFunctors'])

        waves = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_TridentOfTheWaves')
        waves_source = read_entry(source_weapons, 'entry', 'MAG_LC_Wave_Trident')
        waves_passive = read_entry(source_passives, 'entry', 'MAG_LC_Wave_Trident_Passive')
        self.assertIn('MAG_LC_Wave_Trident_Passive', waves_source['PassivesOnEquip'])
        self.assertIn('MAG_LC_Wave_Trident_Passive', waves['PassivesOnEquip'])
        self.assertEqual(waves_passive['Conditions'], 'AttackedWithPassiveSourceWeapon()')
        self.assertIn('ApplyStatus(WET,100, 3)', waves_passive['StatsFunctors'])
        self.assertIn('CreateSurface(2, 0, Water)', waves_passive['StatsFunctors'])

        voss = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_VossSilverSword')
        voss_source = read_entry(source_weapons, 'entry', 'MAG_Primeval_Silver_Longsword')
        voss_passive = read_entry(local_passives, 'entry', 'GSL_Musket_VossSilverSword_Passive')
        smite = read_entry(local_spells, 'entry', 'Projectile_GSL_WrathfulSmite_Musket')
        self.assertIn('UnlockSpell(Target_MAG_Smite_Wrathful)', voss_source['Boosts'])
        self.assertIn('MAG_PlaneShifterSlayer_Passive', voss_source['PassivesOnEquip'])
        self.assertIn('GSL_Musket_VossSilverSword_Passive', voss['PassivesOnEquip'])
        self.assertIn("Tagged('GITHYANKI',context.Target)", voss_passive['Boosts'])
        self.assertIn("Tagged('ELEMENTAL',context.Target)", voss_passive['Boosts'])
        self.assertIn("Tagged('ABERRATION',context.Target)", voss_passive['Boosts'])
        self.assertIn("Tagged('FIEND',context.Target)", voss_passive['Boosts'])
        self.assertIn('RollBonus(RangedWeaponAttack,1d4)', voss_passive['Boosts'])
        self.assertIn('CharacterWeaponDamage(1d4,MainRangedWeaponDamageType)', voss_passive['Boosts'])
        self.assertEqual(smite['Cooldown'], 'OncePerShortRest')
        self.assertIn('DealDamage(1d6,Psychic,Magical)', smite['SpellSuccess'])
        self.assertIn('SavingThrow(Ability.Wisdom', smite['SpellSuccess'])
        self.assertIn('ApplyStatus(FRIGHTENED,100,2)', smite['SpellSuccess'])

        woe = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Woe')
        woe_source = read_entry(source_weapons, 'entry', 'MAG_LC_CazadorVampiric_Quarterstaff')
        vampiric = read_entry(
            source_passives,
            'entry',
            'MAG_LC_CazadorVampiric_Quarterstaff_Passive',
        )
        arcane = read_entry(source_passives, 'entry', 'MAG_ArcaneEnchantment_Lesser_Passive')
        blight = read_entry(source_spells, 'entry', 'Target_MAG_Blight')
        self.assertIn('Target_MAG_Blight', woe_source['Boosts'])
        self.assertIn('Target_MAG_Blight', woe['BoostsOnEquipMainHand'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', woe['PassivesOnEquip'])
        self.assertIn('MAG_LC_CazadorVampiric_Quarterstaff_Passive', woe['PassivesOnEquip'])
        self.assertIn('IsSavingThrow()', vampiric['Conditions'])
        self.assertIn('RegainHitPoints(1d4)', vampiric['DescriptionParams'])
        self.assertIn('SpellSaveDC(1)', arcane['Boosts'])
        self.assertEqual(blight['Cooldown'], 'OncePerRestPerItem')

    def test_dead_shot_musket_adapts_critical_and_ranged_attack_bonuses(self) -> None:
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        dead_shot = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_DeadShot')
        source_weapon = read_entry(source_dev / 'Weapon.txt', 'entry', 'MAG_DeadShot_Longbow')
        passives = source_dev / 'Passive.txt'
        improved_critical = read_entry(
            passives,
            'entry',
            'MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive',
        )
        double_proficiency = read_entry(
            passives,
            'entry',
            'MAG_DoubleProficiencyBonusToRangedAttack_Passive',
        )

        self.assertEqual(dead_shot['DefaultBoosts'], 'WeaponEnchantment(2);WeaponProperty(Magical)')
        self.assertEqual(
            source_weapon['PassivesOnEquip'],
            'MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive;MAG_DoubleProficiencyBonusToRangedAttack_Passive',
        )
        self.assertIn('MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive', dead_shot['PassivesOnEquip'])
        self.assertIn('MAG_DoubleProficiencyBonusToRangedAttack_Passive', dead_shot['PassivesOnEquip'])
        self.assertEqual(improved_critical['Boosts'], 'ReduceCriticalAttackThreshold(1)')
        self.assertIn('IF(not HasDisadvantage())', double_proficiency['Boosts'])
        self.assertIn('RollBonus(RangedWeaponAttack, ProficiencyBonus)', double_proficiency['Boosts'])

    def test_next_musket_combos_adapt_source_passives(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        passives = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerPassives.txt'

        watchers_guide = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_WatchersGuide')
        watcher_passive = read_entry(source / 'Passive.txt', 'entry', 'CHA_CompassSpear_Passive')
        self.assertIn('CHA_CompassSpear_Passive', watchers_guide['PassivesOnEquip'])
        self.assertIn('IsMiss()', watcher_passive['Conditions'])
        self.assertIn('ApplyStatus(TRUE_STRIKE,100,2)', watcher_passive['StatsFunctors'])
        self.assertIn('ApplyStatus(SELF,TRUE_STRIKE_OWNER,100,2)', watcher_passive['StatsFunctors'])

        corellon = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_CorellonsGrace')
        source_repeat_staff = read_entry(source / 'Weapon.txt', 'entry', 'UNI_RepeatStaff')
        resistance_passive = read_entry(source / 'Passive.txt', 'entry', 'UNI_RepeatStaff_Passive')
        attack_damage_passive = read_entry(
            passives,
            'entry',
            'GSL_CorellonsGrace_Musket_Passive',
        )
        self.assertIn('MAG_UnarmedEnchantment_1_Passive', source_repeat_staff['PassivesOnEquip'])
        self.assertIn('UNI_RepeatStaff_Passive', source_repeat_staff['PassivesOnEquip'])
        self.assertIn('UNI_RepeatStaff_Passive', corellon['PassivesOnEquip'])
        self.assertIn('not WearingArmor(context.Source)', resistance_passive['BoostConditions'])
        self.assertIn('RollBonus(SavingThrow, 2)', resistance_passive['Boosts'])
        self.assertEqual(
            attack_damage_passive['BoostConditions'],
            'not WearingArmor(context.Source)',
        )
        self.assertEqual(
            attack_damage_passive['Boosts'],
            "IF(IsRangedWeaponAttack() and IsWeaponOfProficiencyGroup('Slings',GetActiveWeapon())):WeaponEnchantment(1)",
        )

        intransigent = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Intransigent')
        source_hammer = read_entry(
            source / 'Weapon.txt',
            'entry',
            'UND_DuergarRaft_GruesomeHammer',
        )
        hammer_passive = read_entry(
            source / 'Passive.txt',
            'entry',
            'UND_DuergarRaft_Hammer_Passive',
        )
        hammer_explosion = read_entry(
            source / 'Spell_Projectile.txt',
            'entry',
            'Projectile_UND_DuergarRaft_Hammer_Explosion',
        )
        self.assertIn('UND_DuergarRaft_Hammer_Passive', source_hammer['PassivesOnEquip'])
        self.assertIn('UND_DuergarRaft_Hammer_Passive', intransigent['PassivesOnEquip'])
        self.assertIn('IsCritical()', hammer_passive['Conditions'])
        self.assertIn('IsKillingBlow()', hammer_passive['Conditions'])
        self.assertIn('CreateExplosion(Projectile_UND_DuergarRaft_Hammer_Explosion)', hammer_passive['StatsFunctors'])
        self.assertEqual(hammer_explosion['AreaRadius'], '3')
        self.assertIn('ApplyStatus(PRONE, 100, 2)', hammer_explosion['SpellSuccess'])

        jagged = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_JaggedSpear')
        jagged_passive = read_entry(source / 'Passive.txt', 'entry', 'GOB_Torturer_Spear_Passive')
        tortured = read_entry(source / 'Status_BOOST.txt', 'entry', 'GOB_TORTURED')
        self.assertIn('GOB_Torturer_Spear_Passive', jagged['PassivesOnEquip'])
        self.assertIn('not SavingThrow(Ability.Charisma,10)', jagged_passive['StatsFunctors'])
        self.assertIn('ApplyStatus(GOB_TORTURED,100,2', jagged_passive['StatsFunctors'])
        self.assertIn('Disadvantage(SavingThrow, Constitution)', tortured['Boosts'])

    def test_following_musket_combos_adapt_source_weapon_features(self) -> None:
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'

        melf_source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        melf_staff = read_entry(
            melf_source / 'Weapon.txt',
            'entry',
            'MAG_BasicEnchanted_Quarterstaff',
        )
        melf_arrow = read_entry(
            melf_source / 'Spell_Projectile.txt',
            'entry',
            'Projectile_MAG_MelfsMagicArrow',
        )
        melf_passive = read_entry(
            melf_source / 'Passive.txt',
            'entry',
            'MAG_ArcaneEnchantment_Lesser_Passive',
        )
        fused_melf = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_MelfsFirstStaff')
        self.assertIn('UnlockSpell(Projectile_MAG_MelfsMagicArrow)', melf_staff['Boosts'])
        self.assertIn('UnlockSpell(Projectile_MAG_MelfsMagicArrow)', fused_melf['BoostsOnEquipMainHand'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', fused_melf['PassivesOnEquip'])
        self.assertEqual(melf_arrow['Cooldown'], 'OncePerRestPerItem')
        self.assertEqual(melf_arrow['UseCosts'], 'ActionPoint:1')
        self.assertEqual(melf_arrow['using'], 'Projectile_AcidArrow')
        self.assertIn('SpellSaveDC(1)', melf_passive['Boosts'])
        self.assertIn('RollBonus(RangedSpellAttack,1)', melf_passive['Boosts'])

        nature_source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        nature_staff = read_entry(nature_source / 'Weapon.txt', 'entry', 'DEN_TunnelStaff')
        nature_passive = read_entry(nature_source / 'Passive.txt', 'entry', 'DEN_TunnelStaff_Passive')
        fused_nature = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_NaturesSnare')
        self.assertIn('DEN_TunnelStaff_Passive', nature_staff['PassivesOnEquip'])
        self.assertIn('DEN_TunnelStaff_Passive', fused_nature['PassivesOnEquip'])
        self.assertIn("not Tagged('BEAST')", nature_passive['Conditions'])
        self.assertIn("not Tagged('PLANT')", nature_passive['Conditions'])
        self.assertIn('not SavingThrow(Ability.Strength, 12)', nature_passive['StatsFunctors'])
        self.assertIn('ApplyStatus(ENSNARING_STRIKE,100, 2)', nature_passive['StatsFunctors'])

        rain_source = (
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
            / 'Stats' / 'Generated' / 'Data'
        )
        rain_staff = read_entry(rain_source / 'Weapon.txt', 'entry', 'UNI_StaffOfRain')
        create_water = read_entry(
            rain_source / 'Spell_Target.txt',
            'entry',
            'Target_CreateWater_StaffOfRain',
        )
        fused_rain = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_RainDancer')
        self.assertIn('UnlockSpell(Target_CreateWater_StaffOfRain)', rain_staff['Boosts'])
        self.assertIn(
            'UnlockSpell(Target_CreateWater_StaffOfRain)',
            fused_rain['BoostsOnEquipMainHand'],
        )
        self.assertEqual(create_water['Cooldown'], 'OncePerShortRest')
        self.assertEqual(create_water['UseCosts'], 'ActionPoint:1')
        self.assertEqual(create_water['using'], 'Target_CreateWater')

        mumbling_source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        mumbling_staff = read_entry(
            mumbling_source / 'Weapon.txt',
            'entry',
            'WYR_Circus_MumblingStaff',
        )
        fire_bolt = read_entry(
            mumbling_source / 'Spell_Projectile.txt',
            'entry',
            'Projectile_WYR_Circus_MumblingStaff_FireBolt',
        )
        fused_mumbling = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Musket_MumblingWizard',
        )
        self.assertIn(
            'UnlockSpell(Projectile_WYR_Circus_MumblingStaff_FireBolt)',
            mumbling_staff['BoostsOnEquipMainHand'],
        )
        self.assertIn(
            'UnlockSpell(Projectile_WYR_Circus_MumblingStaff_FireBolt)',
            fused_mumbling['BoostsOnEquipMainHand'],
        )
        self.assertIn('RollDieAgainstDC(DiceType.d20,20)', fire_bolt['SpellProperties'])
        self.assertIn('CreateExplosion(Projectile_Fireball)', fire_bolt['SpellProperties'])
        self.assertEqual(fire_bolt['SpellSuccess'], 'DealDamage(1d10,Fire,Magical)')

        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        arcane_blessing = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Musket_ArcaneBlessing',
        )
        blessing_weapon = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'UND_Tower_StaffBlessMystra',
        )
        blessing_spell = read_entry(
            source_gustav / 'Spell_Target.txt',
            'entry',
            'Target_UND_Bless_StaffBlessMystra',
        )
        blessing_passive = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'UND_Tower_StaffBlessMystra_Passive',
        )
        self.assertIn('Target_UND_Bless_StaffBlessMystra', blessing_weapon['Boosts'])
        self.assertIn(
            'Target_UND_Bless_StaffBlessMystra',
            arcane_blessing['BoostsOnEquipMainHand'],
        )
        self.assertIn(
            'UND_Tower_StaffBlessMystra_Passive',
            arcane_blessing['PassivesOnEquip'],
        )
        self.assertEqual(blessing_spell['Cooldown'], 'OncePerRestPerItem')
        self.assertIn('ApplyStatus(UND_BLESS_STAFF_MYSTRA,100,10)', blessing_passive['StatsFunctors'])

        crones = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Crones')
        source_crones = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'Quest_HAG_HagLair_Staff',
        )
        ray_of_sickness = read_entry(
            source_gustav / 'Spell_Projectile.txt',
            'entry',
            'Projectile_HAG_RayOfSickness_Staff',
        )
        self.assertIn(
            'Projectile_HAG_RayOfSickness_Staff',
            source_crones['Boosts'],
        )
        self.assertIn(
            'UnlockSpell(Projectile_HAG_RayOfSickness_Staff)',
            crones['BoostsOnEquipMainHand'],
        )
        self.assertEqual(ray_of_sickness['Cooldown'], 'OncePerShortRestPerItem')

        hellrider = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Hellrider')
        sentinel_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_PHB_Sentinel_Shield_Passive',
        )
        faerie_fire_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_WYR_Hellrider_Longbow_Passive',
        )
        self.assertEqual(hellrider['DefaultBoosts'], 'WeaponEnchantment(1)')
        self.assertIn('MAG_PHB_Sentinel_Shield_Passive', hellrider['PassivesOnEquip'])
        self.assertIn('MAG_WYR_Hellrider_Longbow_Passive', hellrider['PassivesOnEquip'])
        self.assertEqual(sentinel_passive['Boosts'], 'Initiative(3);Advantage(Skill, Perception)')
        self.assertEqual(faerie_fire_passive['Properties'], 'OncePerTurn')
        self.assertIn('ApplyStatus(FAERIE_FIRE, 100, 1)', faerie_fire_passive['StatsFunctors'])

        spellthief = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Spellthief')
        spellthief_passive = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'UNI_Bow_SpellslotRecharge_Passive',
        )
        self.assertIn(
            'UNI_Bow_SpellslotRecharge_Passive',
            spellthief['PassivesOnEquip'],
        )
        self.assertEqual(spellthief_passive['Properties'], 'OncePerShortRest')
        self.assertIn(
            'DamageFlags.Critical',
            spellthief_passive['Conditions'],
        )
        self.assertEqual(
            spellthief_passive['StatsFunctors'],
            'RestoreResource(SELF,SpellSlot,1,1)',
        )

    def test_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'

        despair = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_DespairAthkatla')
        despair_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_LC_Lorroakan_Quarterstaff',
        )
        arcane_enchantment = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_ArcaneEnchantment_Lesser_Passive',
        )
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', despair_source['PassivesOnEquip'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', despair['PassivesOnEquip'])
        self.assertIn('SpellSaveDC(1)', arcane_enchantment['Boosts'])
        self.assertIn('WeaponEnchantment(2)', despair['DefaultBoosts'])

        adamantine = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Musket_AdamantineLongsword',
        )
        adamantine_source = read_entry(
            source / 'Weapon.txt',
            'entry',
            'MAG_MeleeDebuff_AttackDebuff12versatile_OnDamage_Longsword',
        )
        adamantine_critical = read_entry(
            source / 'Passive.txt',
            'entry',
            'UNI_Adamantine_CriticalVsItems_Passive',
        )
        slashing_resistance = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_IgnoreSlashingResistance_Passive',
        )
        piercing_resistance = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_IgnorePiercingResistance_Passive',
        )
        self.assertIn('UNI_Adamantine_CriticalVsItems_Passive', adamantine_source['PassivesOnEquip'])
        self.assertIn('UNI_Adamantine_CriticalVsItems_Passive', adamantine['PassivesOnEquip'])
        self.assertIn('MAG_IgnorePiercingResistance_Passive', adamantine['PassivesOnEquip'])
        self.assertIn('Item(context.Target)', adamantine_critical['Boosts'])
        self.assertIn('CriticalHit(AttackRoll,Success, ForcedAlways)', adamantine_critical['Boosts'])
        self.assertIn('IgnoreResistance(Slashing, Resistant)', slashing_resistance['Boosts'])
        self.assertIn('IgnoreResistance(Piercing, Resistant)', piercing_resistance['Boosts'])
        self.assertEqual(adamantine['StatusOnEquip'], 'MAG_DIAMONDSBANE_TECHNICAL')

        bigboy = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_BigboyChewToy')
        bigboy_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Combat_Quarterstaff',
        )
        enlarge = read_entry(
            source_dev / 'Spell_Shout.txt',
            'entry',
            'Shout_MAG_CombatStaff_Enlarge',
        )
        self.assertIn('Shout_MAG_CombatStaff_Enlarge', bigboy_source['Boosts'])
        self.assertIn('UnlockSpell(Shout_MAG_CombatStaff_Enlarge)', bigboy['BoostsOnEquipMainHand'])
        self.assertEqual(bigboy['StatusOnEquip'], bigboy_source['StatusOnEquip'])
        self.assertEqual(enlarge['Cooldown'], 'OncePerRestPerItem')

        blackguard = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Musket_BlackguardSword',
        )
        blackguard_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_OB_Paladin_DeathKnight_Longsword',
        )
        dazing_smite = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_DazingSmite_Passive',
        )
        self.assertIn('MAG_DazingSmite_Passive', blackguard_source['PassivesOnEquip'])
        self.assertIn('MAG_DazingSmite_Passive', blackguard['PassivesOnEquip'])
        self.assertIn('IsSmiteSpells()', dazing_smite['StatsFunctors'])
        self.assertIn('SavingThrow(Ability.Constitution,13)', dazing_smite['StatsFunctors'])
        self.assertIn('WeaponEnchantment(2)', blackguard['DefaultBoosts'])

    def test_next_rare_musket_combos_adapt_source_weapon_features(self) -> None:
        source_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        source = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        spells = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerSpells.txt'

        blade = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Musket_BladeOppressedSouls',
        )
        blade_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Illithid_MindOverload_Weapon_Longsword',
        )
        crowning_source = read_entry(
            source_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_Mindoverload',
        )
        crowning = read_entry(spells, 'entry', 'Projectile_GSL_CrowningShot_Musket')
        self.assertEqual(blade['DefaultBoosts'], 'WeaponEnchantment(1);WeaponProperty(Magical);WeaponDamage(1d4,Psychic)')
        self.assertIn('Target_MAG_WeaponAction_Mindoverload', blade_source['BoostsOnEquipMainHand'])
        self.assertIn(
            'UnlockSpell(Projectile_GSL_CrowningShot_Musket)',
            blade['BoostsOnEquipMainHand'],
        )
        self.assertIn('DealDamage(ProficiencyBonus, Psychic)', crowning_source['SpellSuccess'])
        self.assertIn("Tagged('HUMANOID') and not Tagged('UNDEAD')", crowning['TargetConditions'])
        self.assertIn('DealDamage(ProficiencyBonus,Psychic)', crowning['SpellSuccess'])
        self.assertIn('ApplyStatus(CROWN_OF_MADNESS,100,3)', crowning['SpellSuccess'])

        cacophony = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Cacophony')
        cacophony_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Thunder_ThunderClap_Quarterstaff',
        )
        thunderous_source = read_entry(
            source_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_ThunderousSmite',
        )
        thunderous = read_entry(spells, 'entry', 'Projectile_GSL_ThunderousSmite_Musket')
        self.assertIn('Target_MAG_ThunderousSmite', cacophony_source['Boosts'])
        self.assertIn('UnlockSpell(Projectile_GSL_ThunderousSmite_Musket)', cacophony['BoostsOnEquipMainHand'])
        self.assertIn('WeaponEnchantment(1)', cacophony['DefaultBoosts'])
        self.assertEqual(thunderous_source['Cooldown'], 'OncePerShortRestPerItem')
        self.assertEqual(thunderous['Cooldown'], 'OncePerShortRest')
        self.assertIn('DealDamage(2d6,Thunder,Magical)', thunderous['SpellSuccess'])
        self.assertIn('PRONE_THUNDEROUS_SMITE', thunderous['SpellSuccess'])

        caitiff = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_Caitiff')
        caitiff_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_PHB_PactKeeper_Quarterstaff',
        )
        warlock_restore = read_entry(
            source_dev / 'Spell_Shout.txt',
            'entry',
            'Shout_MAG_WarlockSpellRestoration',
        )
        arcane_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_ArcaneEnchantment_Lesser_Passive',
        )
        self.assertIn('Shout_MAG_WarlockSpellRestoration', caitiff_source['Boosts'])
        self.assertIn('UnlockSpell(Shout_MAG_WarlockSpellRestoration)', caitiff['BoostsOnEquipMainHand'])
        self.assertIn('MAG_ArcaneEnchantment_Lesser_Passive', caitiff['PassivesOnEquip'])
        self.assertIn('WeaponEnchantment(2)', caitiff['DefaultBoosts'])
        self.assertEqual(warlock_restore['Cooldown'], 'OncePerRestPerItem')
        self.assertIn('RestoreResource(WarlockSpellSlot,1,5)', warlock_restore['SpellProperties'])
        self.assertIn('SpellSaveDC(1)', arcane_passive['Boosts'])

        charge_bound = read_entry(weapon_stats, 'entry', 'WPN_GSL_Musket_ChargeBound')
        charge_source = read_entry(
            source_dev / 'Weapon.txt',
            'entry',
            'MAG_Bonded_Shocking_Warhammer',
        )
        shocking_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_ShockingBound_Passive',
        )
        bound_bonus_status = read_entry(
            source_dev / 'Status_BOOST.txt',
            'entry',
            'MAG_ATTACK_ROLL_BONUS_BONDED_TECHNICAL',
        )
        bound_bonus_passive = read_entry(
            source_dev / 'Passive.txt',
            'entry',
            'MAG_BoundToBeBonded_Technical_Passive',
        )
        bound_bonus = read_entry(
            source_dev / 'Status_BOOST.txt',
            'entry',
            'MAG_WEAPON_ATTACK_ROLL_BONUS',
        )
        self.assertIn('MAG_BoundToBeBonded_Passive', charge_source['PassivesOnEquip'])
        self.assertIn('MAG_ShockingBound_Passive', charge_source['PassivesOnEquip'])
        self.assertIn('MAG_BoundToBeBonded_Passive', charge_bound['PassivesOnEquip'])
        self.assertIn('MAG_ShockingBound_Passive', charge_bound['PassivesOnEquip'])
        self.assertIn('DealDamage(1d6, Lightning)', shocking_passive['DescriptionParams'])
        self.assertIn('MAG_BoundToBeBonded_Technical_Passive', bound_bonus_status['Passives'])
        self.assertIn(
            'ApplyStatus(MAG_WEAPON_ATTACK_ROLL_BONUS, 100, -1)',
            bound_bonus_passive['StatsFunctors'],
        )
        self.assertEqual(bound_bonus['Boosts'], 'WeaponEnchantment(1)')
        self.assertIn('WeaponEnchantment(1)', charge_bound['DefaultBoosts'])

    def test_musket_action_shots_adapt_gustav_weapon_mechanics(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        entries = read_stats(sorted(data_dir.glob('*.txt')))
        projectile = (
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
            / 'Stats' / 'Generated' / 'Data' / 'Spell_Projectile.txt'
        )
        external = read_stats([projectile]) if projectile.is_file() else {}
        bonesaw = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        incise, _ = resolve_spell('Projectile_GSL_InciseLigaments_Musket', entries, external)
        source_incise = read_entry(
            bonesaw / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_Bonesaw',
        )
        self.assertIn('ApplyStatus(SLOW,100,2)', source_incise['SpellSuccess'])
        self.assertEqual(incise['UseCosts'], 'ActionPoint:1;GunslingerMusketAmmo:1')
        self.assertEqual(incise['Cooldown'], 'OncePerShortRest')
        self.assertEqual(incise['SpellRoll'], 'Attack(AttackType.RangedWeaponAttack)')
        self.assertIn('SavingThrow(Ability.Dexterity,ManeuverSaveDC()+2)', incise['SpellSuccess'])
        self.assertIn('DealDamage(1d6,MainRangedWeaponDamageType)', incise['SpellSuccess'])
        self.assertNotIn('DealDamage(1d6,Necrotic)', incise['SpellSuccess'])

        absolute, _ = resolve_spell('Projectile_GSL_AbsolutePower_Musket', entries, external)
        source_absolute = read_entry(
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data' / 'Spell_Target.txt',
            'entry',
            'Target_GOB_GoblinKing_ForceAttack',
        )
        self.assertIn('DealDamage(1d6, Force)', source_absolute['SpellSuccess'])
        self.assertIn('SavingThrow(Ability.Strength, SourceSpellDC())', source_absolute['SpellSuccess'])
        self.assertEqual(absolute['Cooldown'], 'OncePerTurn')
        self.assertEqual(absolute['UseCosts'], 'ActionPoint:1;GunslingerMusketAmmo:1')
        self.assertIn('DealDamage(1d6,Force)', absolute['SpellSuccess'])
        self.assertIn('SavingThrow(Ability.Strength,SourceSpellDC())', absolute['SpellSuccess'])
        self.assertIn('Force(5)', absolute['SpellSuccess'])
        source_faithbreaker = read_entry(
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt',
            'entry',
            'GOB_GoblinKing_Warhammer',
        )
        self.assertEqual(
            source_faithbreaker['DefaultBoosts'],
            'WeaponEnchantment(1);WeaponProperty(Magical)',
        )

        hush, _ = resolve_spell('Projectile_GSL_HushYou_Musket', entries, external)
        source_weapon = read_entry(
            bonesaw / 'Weapon.txt',
            'entry',
            'MAG_Spellbreaker_Battleaxe',
        )
        self.assertIn('Target_MAG_WeaponAction_SilencingBlade', source_weapon['BoostsOnEquipMainHand'])
        source_hush = read_entry(
            bonesaw / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_SilencingBlade',
        )
        self.assertIn('ApplyStatus(SILENCED,100,2)', source_hush['SpellSuccess'])
        self.assertEqual(hush['UseCosts'], 'ActionPoint:1;GunslingerMusketAmmo:1')
        self.assertEqual(hush['Cooldown'], 'OncePerShortRest')
        self.assertIn('SavingThrow(Ability.Constitution,ManeuverSaveDC()+2)', hush['SpellSuccess'])
        self.assertIn('ApplyStatus(SILENCED,100,2)', hush['SpellSuccess'])

        push, _ = resolve_spell('Projectile_GSL_PushingShot_Musket', entries, external)
        source_push = read_entry(
            bonesaw / 'Spell_Projectile.txt',
            'entry',
            'Projectile_MAG_PushingAttack',
        )
        self.assertEqual(source_push['Cooldown'], 'OncePerShortRest')
        self.assertIn('Force(5)', source_push['SpellSuccess'])
        self.assertEqual(push['UseCosts'], 'ActionPoint:1;GunslingerMusketAmmo:1')
        self.assertEqual(push['Cooldown'], source_push['Cooldown'])
        self.assertEqual(push['SpellRoll'], 'Attack(AttackType.RangedWeaponAttack)')
        self.assertIn('SavingThrow(Ability.Strength,ManeuverSaveDC())', push['SpellSuccess'])
        self.assertIn('Force(5)', push['SpellSuccess'])

        source_titanstring = read_entry(
            bonesaw / 'Weapon.txt',
            'entry',
            'MAG_StrongString_Longbow',
        )
        self.assertIn('MAG_StrengthBonusToWeaponDamage_Passive', source_titanstring['PassivesOnEquip'])
        strength_passive = read_entry(
            bonesaw / 'Passive.txt',
            'entry',
            'MAG_StrengthBonusToWeaponDamage_Passive',
        )
        self.assertEqual(
            strength_passive['Boosts'],
            'IF(IsRangedWeaponAttack()):DamageBonus(max(1,StrengthModifier))',
        )

        expected_weapons = {
            'Bonesaw': ('Uncommon', 'WeaponEnchantment(1)'),
            'Faithbreaker': ('Uncommon', 'WeaponEnchantment(1);WeaponProperty(Magical)'),
            'Witchbreaker': ('Uncommon', 'WeaponEnchantment(1)'),
            'Titanstring': ('Rare', 'WeaponEnchantment(1)'),
        }
        for name, (rarity, boosts) in expected_weapons.items():
            fused = read_entry(data_dir / 'Weapon.txt', 'entry', f'WPN_GSL_Musket_{name}')
            self.assertEqual(fused['DefaultBoosts'], boosts)
            self.assertEqual(fused['Rarity'], rarity)
            self.assertNotIn('UnlockSpell(GSL_MainHand_Musket_attack)', fused['BoostsOnEquipMainHand'])
            self.assertIn('UnlockSpell(Shout_GSL_Reload_Musket)', fused['BoostsOnEquipMainHand'])
        witchbreaker = read_entry(data_dir / 'Weapon.txt', 'entry', 'WPN_GSL_Musket_Witchbreaker')
        self.assertIn('MAG_Spellbreaker_Battleaxe_Passive', witchbreaker['PassivesOnEquip'])

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

    def test_first_four_flintlock_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('AssassinShortsword', 'TWN_ShortswordOfStealth'),
            ('AssassinTouch', 'DEN_CapturedGoblin_MurderDagger'),
            ('HillGiantStrength', 'UND_StrengthChair_Leg'),
        )
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembly_result['Result 1'], crafted_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertNotIn('BoostsOnEquipMainHand', fused)
                base_flintlock = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock')
                self.assertNotIn('UnlockSpell(GSL_MainHand_Flintlock_attack)', base_flintlock['BoostsOnEquipMainHand'])
                self.assertIn('UnlockSpell(Shout_GSL_Reload_Flintlock)', base_flintlock['BoostsOnEquipMainHand'])

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(disassembly['Transform 1'], 'Transform')
                self.assertEqual(disassembly['Transform 2'], 'Consume')
                disassembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(disassembly_result['Result 2'], source_weapon)

    def test_first_four_flintlock_combinations_adapt_source_abilities(self) -> None:
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        stealth = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_AssassinShortsword',
        )
        self.assertEqual(stealth['DefaultBoosts'], 'WeaponEnchantment(1)')
        self.assertEqual(stealth['Boosts'], 'Advantage(Skill,Stealth)')

        assassin_touch = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_AssassinTouch',
        )
        self.assertEqual(assassin_touch['Rarity'], 'Uncommon')
        self.assertIn('WeaponEnchantment(1)', assassin_touch['DefaultBoosts'])
        self.assertIn("HasStatus('SLEEPING',context.Target)", assassin_touch['DefaultBoosts'])
        self.assertIn("HasStatus('KNOCKED_OUT',context.Target)", assassin_touch['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Necrotic)', assassin_touch['DefaultBoosts'])

        strength = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_HillGiantStrength',
        )
        self.assertEqual(
            strength['PassivesOnEquip'],
            'GSL_Firearm_Misfire_Passive;UND_StrengthChair_Leg_Passive',
        )

    def test_next_four_flintlock_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('DragonsGrasp', 'MAG_Fire_IncreaseSlashingDamageToBurning_Handaxe'),
            ('Firestoker', 'MAG_Fire_IncreasePiercingDamageToBurning_HandCrossbow'),
            ('HuntersDagger', 'MAG_TheHunters_Dagger'),
            ('MurderousCut', 'MAG_Murderous_Dagger'),
        )
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembly_result['Result 1'], crafted_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                disassembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(disassembly_result['Result 2'], source_weapon)

    def test_next_four_flintlock_combinations_adapt_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_dir = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        honour_weapon_stats = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Honour'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )

        dragons_grasp = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_DragonsGrasp')
        source_dragons_grasp = read_entry(
            honour_weapon_stats,
            'entry',
            'MAG_Fire_IncreaseSlashingDamageToBurning_Handaxe',
        )
        self.assertIn("HasStatus('BURNING',context.Target)", source_dragons_grasp['DefaultBoosts'])
        self.assertIn(
            "IF(HasStatus('BURNING',context.Target)):WeaponDamage(1d4,Piercing)",
            dragons_grasp['DefaultBoosts'],
        )

        firestoker = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Firestoker')
        source_firestoker = read_entry(
            honour_weapon_stats,
            'entry',
            'MAG_Fire_IncreasePiercingDamageToBurning_HandCrossbow',
        )
        self.assertIn("HasStatus('BURNING',context.Target)", source_firestoker['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Piercing)', firestoker['DefaultBoosts'])

        hunters_dagger = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_HuntersDagger')
        hunters_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_HuntersDagger_Passive',
        )
        source_hunters_passive = read_entry(
            source_dir / 'Passive.txt',
            'entry',
            'MAG_TheHunters_Dagger_Passive',
        )
        self.assertIn('GSL_Firearm_Misfire_Passive', hunters_dagger['PassivesOnEquip'])
        self.assertIn('AttackedWithPassiveSourceWeapon()', source_hunters_passive['Conditions'])
        self.assertEqual(hunters_passive['Conditions'], source_hunters_passive['Conditions'])
        self.assertIn('ApplyStatus(BARBED_ARROW,100,3)', hunters_passive['StatsFunctors'])

        murderous_cut = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_MurderousCut',
        )
        source_murderous_cut = read_entry(
            source_dir / 'Weapon.txt',
            'entry',
            'MAG_Murderous_Dagger',
        )
        self.assertIn('WeaponEnchantment(1)', source_murderous_cut['DefaultBoosts'])
        self.assertIn(
            'HasHPPercentageEqualOrLessThan(50, context.Target)',
            source_murderous_cut['DefaultBoosts'],
        )
        self.assertIn('WeaponEnchantment(1)', murderous_cut['DefaultBoosts'])
        self.assertIn('HasHPPercentageEqualOrLessThan(50,context.Target)', murderous_cut['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Piercing)', murderous_cut['DefaultBoosts'])

    def test_following_four_flintlock_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('RitualAxe', 'GOB_PainPriest_Handaxe'),
            ('RitualDagger', 'GOB_PainPriest_Dagger'),
            ('RitualDaggerShar', 'TWN_SharDagger'),
            ('ShiningStaver', 'MAG_Radiant_Radiating_Hammer'),
        )
        base_flintlock = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock')
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembly_result['Result 1'], crafted_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertNotIn(
                    'UnlockSpell(GSL_MainHand_Flintlock_attack)',
                    base_flintlock['BoostsOnEquipMainHand'],
                )

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                disassembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(disassembly_result['Result 2'], source_weapon)

    def test_following_four_flintlock_combinations_adapt_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        ritual_axe = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_RitualAxe')
        source_axe_passive = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'GOB_PainPriest_Axe_Passive',
        )
        axe_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_RitualAxe_Passive',
        )
        self.assertIn('ApplyStatus(BANE,100,2)', source_axe_passive['StatsFunctors'])
        self.assertIn('ApplyStatus(BANE,100,2)', axe_passive['StatsFunctors'])
        self.assertIn(
            'HasHPPercentageWithoutTemporaryHPEqualOrMoreThan(50,context.Source)',
            axe_passive['StatsFunctors'],
        )
        self.assertIn('DealDamage(SELF,1d6,Piercing,Magical)', axe_passive['StatsFunctors'])
        self.assertIn('GSL_Firearm_Misfire_Passive', ritual_axe['PassivesOnEquip'])

        ritual_dagger = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_RitualDagger',
        )
        source_dagger_passive = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'GOB_PainPriest_Dagger_Passive',
        )
        dagger_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_RitualDagger_Passive',
        )
        self.assertEqual(dagger_passive['StatsFunctors'], source_dagger_passive['StatsFunctors'])
        self.assertIn('UnlockSpell(Shout_GSL_BloodSacrifice_Flintlock)', ritual_dagger['Boosts'])
        source_blood_sacrifice = read_entry(
            source_gustav / 'Spell_Shout.txt',
            'entry',
            'Shout_GOB_PainPriest_DaggerSpell',
        )
        blood_sacrifice = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Shout_GSL_BloodSacrifice_Flintlock',
        )
        self.assertEqual(source_blood_sacrifice['UseCosts'], 'BonusActionPoint:1')
        self.assertEqual(blood_sacrifice['UseCosts'], source_blood_sacrifice['UseCosts'])
        self.assertIn('DealDamage(SELF,1d4,Piercing)', blood_sacrifice['SpellProperties'])
        self.assertIn('GOB_PAIN_PRIEST_DAGGER_BLESS', blood_sacrifice['SpellProperties'])

        shar_dagger = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_RitualDaggerShar',
        )
        source_shar_dagger = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'TWN_SharDagger',
        )
        self.assertEqual(
            source_shar_dagger['RootTemplate'],
            '7773610f-f246-4837-a75f-2d260f815718',
        )
        self.assertIn('WeaponEnchantment(1)', shar_dagger['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Necrotic)', shar_dagger['DefaultBoosts'])

        staver = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_ShiningStaver')
        source_staver = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Radiant_Radiating_Hammer',
        )
        self.assertEqual(
            source_staver['RootTemplate'],
            'b76baf78-5aaf-4c15-9468-6333a0eb4b92',
        )
        self.assertIn('WeaponEnchantment(1)', staver['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Radiant)', staver['DefaultBoosts'])
        self.assertIn('ActiveCharacterLight(233033a1-b43a-4ad9-976a-8a062b345e21)', staver['Boosts'])

    def test_next_four_flintlock_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('FirstBlood', 'UND_Duergar_ShortswordOfFirstBlood'),
            ('Skybreaker', 'UND_DuergarBlacksmithHammer'),
            ('SpeedyReply', 'MAG_Mobility_MomentumOnAttack_Scimitar'),
            ('SwordOfScreams', 'UND_Nere_Sword'),
        )
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembly_result['Result 1'], crafted_weapon)
                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertNotIn('BoostsOnEquipMainHand', fused)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                disassembly_result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(disassembly_result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(disassembly_result['Result 2'], source_weapon)

    def test_next_four_flintlock_combinations_adapt_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        first_blood = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_FirstBlood')
        first_blood_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_FirstBlood_Passive',
        )
        source_first_blood = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'UND_Duergar_ShortswordOfFirstBlood_Passive',
        )
        self.assertIn('HasMaxHP()', source_first_blood['Conditions'])
        self.assertIn('IsAttack()', first_blood_passive['Conditions'])
        self.assertIn('not IsMiss()', first_blood_passive['Conditions'])
        self.assertIn('DealDamage(1d8,MainRangedWeaponDamageType,Magical)', first_blood_passive['StatsFunctors'])
        self.assertIn('GSL_Firearm_Misfire_Passive', first_blood['PassivesOnEquip'])

        skybreaker = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Skybreaker')
        self.assertEqual(skybreaker['DefaultBoosts'], 'WeaponEnchantment(1)')
        self.assertIn('UnlockSpell(Projectile_GSL_SearingSmite_Flintlock)', skybreaker['Boosts'])
        source_skybreaker = read_entry(
            source_gustav / 'Spell_Target.txt',
            'entry',
            'Target_UND_Smite_Searing_DuergarBlacksmithHammer',
        )
        self.assertEqual(source_skybreaker['Cooldown'], 'OncePerRestPerItem')
        source_searing = read_entry(
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
            / 'Stats' / 'Generated' / 'Data' / 'Spell_Target.txt',
            'entry',
            'Target_Smite_Searing',
        )
        searing_shot = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Projectile_GSL_SearingSmite_Flintlock',
        )
        self.assertIn('DealDamage(1d6, Fire,Magical)', source_searing['SpellSuccess'])
        self.assertIn('ApplyStatus(SEARING_SMITE, 100, 10)', source_searing['SpellSuccess'])
        self.assertEqual(searing_shot['Cooldown'], 'OncePerLongRest')
        self.assertIn('DealDamage(1d6,Fire,Magical)', searing_shot['SpellSuccess'])
        self.assertIn('ApplyStatus(SEARING_SMITE,100,10)', searing_shot['SpellSuccess'])
        self.assertIn('GunslingerFlintlockAmmo:1', searing_shot['UseCosts'])

        speedy_reply = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SpeedyReply')
        speedy_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_SpeedyReply_Passive',
        )
        source_speedy = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'MAG_Mobility_MomentumOnDamage_Passive',
        )
        self.assertEqual(speedy_passive['Conditions'], source_speedy['Conditions'])
        self.assertEqual(speedy_passive['StatsFunctors'], source_speedy['StatsFunctors'])
        self.assertIn('GSL_Firearm_Misfire_Passive', speedy_reply['PassivesOnEquip'])

        sword_of_screams = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_SwordOfScreams',
        )
        source_sword = read_entry(source_gustav / 'Weapon.txt', 'entry', 'UND_Nere_Sword')
        self.assertIn('WeaponDamage(1d4, Psychic)', source_sword['DefaultBoosts'])
        self.assertIn('WeaponDamage(1d4,Psychic)', sword_of_screams['DefaultBoosts'])

    def test_following_four_flintlock_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('SylvanScimitar', 'MAG_HAV_Sylvan_Scimitar'),
            ('Syringe', 'MAG_Surgeon_Syringe'),
            ('Trepan', 'MAG_Surgeon_Trepan'),
            ('Worgfang', 'GOB_Pens_Dagger'),
        )
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)
                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(result['Result 2'], source_weapon)

    def test_following_four_flintlock_combinations_adapt_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_shared_dev = (
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'SharedDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        sylvan = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SylvanScimitar')
        source_sylvan = read_entry(
            source_shared_dev / 'Weapon.txt',
            'entry',
            'MAG_HAV_Sylvan_Scimitar',
        )
        source_sylvan_status = read_entry(
            source_shared_dev / 'Status_BOOST.txt',
            'entry',
            'MAG_MELEE_CASTER_BOON',
        )
        self.assertEqual(source_sylvan['RootTemplate'], 'b9656931-da39-4024-92a2-f45264593b14')
        self.assertIn('MAG_MeleeCaster_Passive', source_sylvan['PassivesOnEquip'])
        self.assertIn(
            'WeaponAttackRollAbilityOverride(SpellCastingAbility)',
            source_sylvan_status['Boosts'],
        )
        self.assertEqual(sylvan['DefaultBoosts'], 'WeaponEnchantment(1);WeaponProperty(Magical)')
        self.assertEqual(
            sylvan['Boosts'],
            'WeaponAttackRollAbilityOverride(SpellCastingAbility)',
        )

        source_syringe = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Surgeon_Syringe',
        )
        source_syringe_action = read_entry(
            source_gustav_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_Syringe',
        )
        syringe = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Syringe')
        nostrum = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Projectile_GSL_Nostrum_Flintlock',
        )
        self.assertEqual(source_syringe['RootTemplate'], '95c3af3c-83b9-4cc0-b633-1493b7daca4d')
        self.assertIn('ApplyStatus(POISONED,100,2)', source_syringe_action['SpellSuccess'])
        self.assertIn('DealDamage(1d6, Necrotic)', source_syringe_action['SpellSuccess'])
        self.assertEqual(nostrum['Cooldown'], 'OncePerShortRest')
        self.assertIn('GunslingerFlintlockAmmo:1', nostrum['UseCosts'])
        self.assertIn('ApplyStatus(POISONED,100,2)', nostrum['SpellSuccess'])
        self.assertIn('DealDamage(1d6,Necrotic)', nostrum['SpellSuccess'])
        self.assertIn('ManeuverSaveDC()+2', nostrum['SpellSuccess'])
        self.assertIn('UnlockSpell(Projectile_GSL_Nostrum_Flintlock)', syringe['Boosts'])

        source_trepan = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Surgeon_Trepan',
        )
        source_trepan_action = read_entry(
            source_gustav_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_Trepan',
        )
        trepan = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Trepan')
        trephination = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Projectile_GSL_Trephination_Flintlock',
        )
        self.assertEqual(source_trepan['RootTemplate'], '8fee8eb3-f16b-4b9a-85a0-d46a9cd4937e')
        self.assertIn('ApplyStatus(PRONE,100,2)', source_trepan_action['SpellSuccess'])
        self.assertIn('DealDamage(1d6, Necrotic)', source_trepan_action['SpellSuccess'])
        self.assertIn('WeaponEnchantment(1)', trepan['DefaultBoosts'])
        self.assertIn('UnlockSpell(Projectile_GSL_Trephination_Flintlock)', trepan['Boosts'])
        self.assertIn('ApplyStatus(PRONE,100,2)', trephination['SpellSuccess'])
        self.assertIn('DealDamage(1d6,Necrotic)', trephination['SpellSuccess'])
        self.assertIn('ManeuverSaveDC()+2', trephination['SpellSuccess'])
        self.assertEqual(trephination['Cooldown'], 'OncePerShortRest')
        self.assertIn('GunslingerFlintlockAmmo:1', trephination['UseCosts'])

        source_worgfang = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'GOB_Pens_Dagger',
        )
        source_worgfang_passive = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'GOB_Pens_Dagger_Passive',
        )
        worgfang_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_Worgfang_Passive',
        )
        worgfang = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Worgfang')
        self.assertEqual(source_worgfang['RootTemplate'], '529fe100-de0b-4a34-a669-4861ee4538a2')
        self.assertIn('GOB_Pens_Dagger_Passive', source_worgfang['PassivesOnEquip'])
        self.assertEqual(worgfang_passive['Boosts'], source_worgfang_passive['Boosts'])
        self.assertIn('GSL_Firearm_Misfire_Passive', worgfang['PassivesOnEquip'])

    def test_wulbren_awareness_hunting_adamantine_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('WulbrensHammer', 'MOO_WulbrenHammer'),
            ('BowOfAwareness', 'MAG_OfAwareness_Bow'),
            ('HuntingShortbow', 'MAG_Hunting_Shortbow'),
            ('AdamantineScimitar', 'WPN_HUM_Scimitar_Adamantine_A'),
        )
        for name, source_weapon in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)
                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(result['Result 2'], source_weapon)

    def test_wulbren_awareness_hunting_adamantine_effects(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_shared = (
            ROOT / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
            / 'Stats' / 'Generated' / 'Data'
        )

        wulbren = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_WulbrensHammer',
        )
        source_wulbren = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MOO_WulbrenHammer',
        )
        self.assertIn('IF(Item()):DealDamage(2d4,Force)', source_wulbren['WeaponFunctors'])
        self.assertEqual(wulbren['WeaponFunctors'], source_wulbren['WeaponFunctors'])

        awareness = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_BowOfAwareness',
        )
        source_awareness = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_OfAwareness_Bow',
        )
        initiative_passive = read_entry(
            source_gustav_dev / 'Passive.txt',
            'entry',
            'MAG_InitiativeBonus_1_Passive',
        )
        self.assertEqual(
            source_awareness['RootTemplate'],
            'c57ba806-b340-4307-9c37-170792052b8d',
        )
        self.assertIn('MAG_InitiativeBonus_1_Passive', awareness['PassivesOnEquip'])
        self.assertEqual(initiative_passive['Boosts'], 'Initiative(1)')

        hunting = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_HuntingShortbow',
        )
        source_hunting = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Hunting_Shortbow',
        )
        monster_hunter = read_entry(
            source_gustav_dev / 'Passive.txt',
            'entry',
            'MAG_LC_MonsterHunter_Passive',
        )
        source_hunters_mark = read_entry(
            source_gustav_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_HuntersMark',
        )
        base_hunters_mark = read_entry(
            source_shared / 'Spell_Target.txt',
            'entry',
            'Target_HuntersMark',
        )
        hunters_mark = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Target_GSL_HuntersMark_Flintlock',
        )
        self.assertEqual(
            source_hunting['RootTemplate'],
            'a1d1634c-02e6-4428-a822-7603e9163264',
        )
        self.assertIn("Tagged('MONSTROSITY', context.Target)", monster_hunter['Boosts'])
        self.assertIn('MAG_LC_MonsterHunter_Passive', hunting['PassivesOnEquip'])
        self.assertEqual(source_hunters_mark['using'], 'Target_HuntersMark')
        self.assertNotIn('using', hunters_mark)
        self.assertEqual(hunters_mark['SpellProperties'], base_hunters_mark['SpellProperties'])
        self.assertEqual(hunters_mark['TargetConditions'], base_hunters_mark['TargetConditions'])
        self.assertEqual(hunters_mark['SpellFlags'], base_hunters_mark['SpellFlags'])
        self.assertEqual(hunters_mark['Cooldown'], 'OncePerLongRest')
        self.assertEqual(hunters_mark['UseCosts'], 'BonusActionPoint:1')
        self.assertIn('GSL_FIREARM_MAIN_DISABLED', hunters_mark['RequirementConditions'])

        adamantine = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_AdamantineScimitar',
        )
        source_adamantine = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar',
        )
        adamantine_passive = read_entry(
            data_dir / 'GunslingerPassives.txt',
            'entry',
            'GSL_Flintlock_AdamantineScimitar_Passive',
        )
        self.assertEqual(
            source_adamantine['RootTemplate'],
            '503b4f8d-da61-4fc1-a4b7-cad124a10c69',
        )
        self.assertIn('UNI_Adamantine_CriticalVsItems_Passive', source_adamantine['PassivesOnEquip'])
        self.assertIn('IgnoreResistance(Piercing,Resistant)', adamantine_passive['Boosts'])
        self.assertIn('Item(context.Target)', adamantine_passive['Boosts'])
        self.assertIn('CriticalHit(AttackRoll,Success,ForcedAlways)', adamantine_passive['Boosts'])
        self.assertIn('GSL_Firearm_Misfire_Passive', adamantine['PassivesOnEquip'])

    def test_fused_firearm_has_plus_one_enchantment_and_framework_action(self) -> None:
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        fused = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_ArtificialLeech')
        self.assertEqual(fused['DefaultBoosts'], 'WeaponEnchantment(1)')
        self.assertEqual(fused['Rarity'], 'Uncommon')
        self.assertEqual(
            fused['BoostsOnEquipMainHand'],
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

    def test_ambusher_cold_snap_dolor_dread_combinations_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        source_weapons = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('Ambusher', 'MAG_Ambusher_Shortsword', '7a96f6cc-c6bb-4caf-a1ab-a86af3fa21a5'),
            ('ColdSnap', 'MAG_Frost_Offhand_Dagger', 'a8661143-d94d-4f49-a92f-cbd0a9a500a1'),
            ('DolorAmarus', 'MAG_Vicious_Dagger', 'd3e121fb-09c0-4478-84f1-f4f3e28cd50f'),
            ('DreadIronDagger', 'MAG_Zhentarim_SleeperDagger', '9829ba14-b236-4e50-ad54-426ff618074b'),
        )
        for name, source_weapon, source_root in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                source = read_entry(source_weapons, 'entry', source_weapon)
                self.assertEqual(source['RootTemplate'], source_root)

                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembled = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembled['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertEqual(
                    template.find("attribute[@id='Stats']").get('value'),
                    crafted_weapon,
                )

    def test_ambusher_cold_snap_dolor_dread_keep_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_weapons = source_gustav_dev / 'Weapon.txt'
        source_passives = source_gustav_dev / 'Passive.txt'
        source_statuses = source_gustav_dev / 'Status_BOOST.txt'

        ambusher = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Ambusher')
        source_ambusher = read_entry(source_weapons, 'entry', 'MAG_Ambusher_Shortsword')
        initiative = read_entry(source_passives, 'entry', 'MAG_InitiativeWeapon_Passive')
        ambushing = read_entry(source_passives, 'entry', 'MAG_Ambushing_Attack_Passive')
        self.assertIn('MAG_InitiativeWeapon_Passive', source_ambusher['PassivesOnEquip'])
        self.assertIn('MAG_Ambushing_Attack_Passive', source_ambusher['PassivesOnEquip'])
        self.assertEqual(initiative['Boosts'], 'Initiative(1);Advantage(Skill, Perception)')
        self.assertIn('not HadTurnInCombat()', ambushing['Boosts'])
        self.assertIn('CharacterWeaponDamage(1d6, Necrotic)', ambushing['Boosts'])
        self.assertIn('MAG_InitiativeWeapon_Passive', ambusher['PassivesOnEquip'])
        self.assertIn('MAG_Ambushing_Attack_Passive', ambusher['PassivesOnEquip'])
        self.assertIn('GSL_Firearm_Misfire_Passive', ambusher['PassivesOnEquip'])

        cold_snap = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_ColdSnap')
        source_cold_snap = read_entry(source_weapons, 'entry', 'MAG_Frost_Offhand_Dagger')
        chilling_counter = read_entry(
            source_passives,
            'entry',
            'MAG_FrostTalon_ChillingCounter_Passive',
        )
        self.assertIn('MAG_FrostTalon_ChillingCounter_Passive', source_cold_snap['PassivesOffHand'])
        self.assertEqual(chilling_counter['StatsFunctorContext'], 'OnAttacked')
        self.assertEqual(chilling_counter['Conditions'], 'IsMiss() or IsCriticalMiss()')
        self.assertIn('ApplyStatus(SWAP, CHILLED, 100, 2)', chilling_counter['StatsFunctors'])
        self.assertIn('WeaponDamage(1d4,Cold)', cold_snap['DefaultBoosts'])
        self.assertEqual(
            cold_snap['BoostsOnEquipOffHand'],
            'UnlockSpell(Shout_GSL_Reload_OffhandFlintlock);'
            'UnlockSpell(Shout_GSL_Reload_DualFlintlock);AC(1)',
        )
        self.assertIn('GSL_Flintlock_OffHand', cold_snap['PassivesOffHand'])
        self.assertIn('MAG_FrostTalon_ChillingCounter_Passive', cold_snap['PassivesOffHand'])

        dolor = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_DolorAmarus')
        source_dolor = read_entry(source_weapons, 'entry', 'MAG_Vicious_Dagger')
        vicious = read_entry(source_passives, 'entry', 'MAG_Vicious_Weapon_Passive')
        self.assertIn('MAG_Vicious_Weapon_Passive', source_dolor['PassivesOnEquip'])
        self.assertEqual(vicious['Boosts'], 'IF(IsWeaponAttack() and IsCritical()):DamageBonus(7,,false)')
        self.assertEqual(dolor['DefaultBoosts'], 'WeaponEnchantment(2);WeaponProperty(Magical)')
        self.assertIn('MAG_Vicious_Weapon_Passive', dolor['PassivesOnEquip'])
        self.assertIn('GSL_Firearm_Misfire_Passive', dolor['PassivesOnEquip'])

        dread = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_DreadIronDagger')
        source_dread = read_entry(source_weapons, 'entry', 'MAG_Zhentarim_SleeperDagger')
        hidden_passive = read_entry(
            source_passives,
            'entry',
            'MAG_Zhentarim_SleeperDagger_Passive',
        )
        hidden_bonus = read_entry(
            source_statuses,
            'entry',
            'MAG_HIDING_NECROTIC_DAMAGE_BONUS',
        )
        self.assertIn('MAG_Zhentarim_SleeperDagger_Passive', source_dread['PassivesOnEquip'])
        self.assertIn("StatusId('SNEAKING_CLEAR')", hidden_passive['Conditions'])
        self.assertIn('ApplyStatus(MAG_HIDING_NECROTIC_DAMAGE_BONUS, 100, -1)', hidden_passive['StatsFunctors'])
        self.assertIn('CharacterWeaponDamage(1d6, Necrotic)', hidden_bonus['Boosts'])
        self.assertIn('MAG_Zhentarim_SleeperDagger_Passive', dread['PassivesOnEquip'])
        self.assertIn('GSL_Firearm_Misfire_Passive', dread['PassivesOnEquip'])

    def test_fleshrender_gleamdance_harmonic_neer_misser_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        source_weapons = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            ('Fleshrender', 'MAG_LC_Fleshrend_Shortsword', '3db6b7be-1e36-405e-94fd-cf5a9f0e4b68'),
            ('GleamdanceDagger', 'MAG_WYRM_Farlin_Dagger', '3d449afb-b99a-492c-b636-85ced6b39e69'),
            ('HarmonicDueller', 'MAG_Harpers_Harmonizing_Rapier', '530a5c21-0f52-428f-bf41-ef33fd6c447b'),
            ('NeerMisser', 'MAG_MagicMissile_HandCrossbow', 'c9dcf78e-a46c-4959-aade-707d9dd2c51a'),
        )
        for name, source_weapon, source_root in recipes:
            crafted_weapon = f'WPN_GSL_Flintlock_{name}'
            with self.subTest(name=name):
                source = read_entry(source_weapons, 'entry', source_weapon)
                self.assertEqual(source['RootTemplate'], source_root)

                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                assembled = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(assembled['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                self.assertEqual(
                    [disassembly[f'Transform {slot}'] for slot in range(1, 3)],
                    ['Transform', 'Consume'],
                )
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertEqual(
                    template.find("attribute[@id='Stats']").get('value'),
                    crafted_weapon,
                )

    def test_fleshrender_gleamdance_harmonic_neer_misser_keep_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        passives = data_dir / 'GunslingerPassives.txt'
        spells = data_dir / 'GunslingerSpells.txt'
        source_data = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_weapons = source_data / 'Weapon.txt'
        source_passives = source_data / 'Passive.txt'
        source_statuses = source_data / 'Status_BOOST.txt'

        fleshrender_source = read_entry(source_weapons, 'entry', 'MAG_LC_Fleshrend_Shortsword')
        fleshrend_action = read_entry(
            source_data / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_Fleshrend',
        )
        fleshrend_status = read_entry(source_statuses, 'entry', 'MAG_FLESHREND')
        fleshrender = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Fleshrender')
        fleshrend_shot = read_entry(
            spells,
            'entry',
            'Projectile_GSL_PartTheFlesh_Flintlock',
        )
        self.assertIn('UnlockSpell(Target_MAG_WeaponAction_Fleshrend)', fleshrender_source['BoostsOnEquipMainHand'])
        self.assertIn('ApplyStatus(MAG_FLESHREND,100,3)', fleshrend_action['SpellSuccess'])
        self.assertIn('BlockRegainHP()', fleshrend_status['Boosts'])
        self.assertIn('UnlockSpell(Projectile_GSL_PartTheFlesh_Flintlock)', fleshrender['Boosts'])
        self.assertEqual(fleshrend_shot['Cooldown'], 'OncePerShortRest')
        self.assertEqual(
            fleshrend_shot['UseCosts'],
            'ActionPoint:1;GunslingerFlintlockAmmo:1',
        )
        self.assertIn('ManeuverSaveDC()+2', fleshrend_shot['SpellSuccess'])
        self.assertIn('ApplyStatus(MAG_FLESHREND,100,3)', fleshrend_shot['SpellSuccess'])
        self.assertIn('DealDamage(ProficiencyBonus,Necrotic)', fleshrend_shot['SpellSuccess'])
        self.assertNotIn('MainMeleeWeapon', fleshrend_shot['SpellSuccess'])

        gleam_source = read_entry(source_weapons, 'entry', 'MAG_WYRM_Farlin_Dagger')
        light_passive_source = read_entry(source_passives, 'entry', 'MAG_Light_FarlinDagger_Passive')
        offhand_source = read_entry(source_passives, 'entry', 'MAG_WYRM_Farlin_Dagger_Passive')
        gleam = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_GleamdanceDagger')
        adapted_light = read_entry(passives, 'entry', 'GSL_Flintlock_Gleamdance_Light_Passive')
        self.assertIn('MAG_Light_FarlinDagger_Passive', gleam_source['PassivesOnEquip'])
        self.assertIn('MAG_WYRM_Farlin_Dagger_Passive', gleam_source['PassivesOffHand'])
        self.assertIn('MAG_FARLIN_DAGGER_LIGHT_TECHNICAL', light_passive_source['ToggleOnFunctors'])
        self.assertEqual(offhand_source['Boosts'], 'AC(1)')
        self.assertEqual(gleam['StatusOnEquip'], 'MAG_FARLIN_DAGGER_LIGHT_TECHNICAL')
        self.assertIn('GSL_Flintlock_Gleamdance_Light_Passive', gleam['PassivesOnEquip'])
        self.assertIn('EquipmentSlot.RangedMainHand', adapted_light['ToggleOnFunctors'])
        self.assertIn('EquipmentSlot.RangedOffHand', adapted_light['ToggleOnFunctors'])
        self.assertIn('RangedMainHand, MAG_LIGHT_DIVINE', adapted_light['ToggleOnFunctors'])
        self.assertIn('RangedOffHand, MAG_LIGHT_DIVINE', adapted_light['ToggleOnFunctors'])
        self.assertIn('MAG_WYRM_Farlin_Dagger_Passive', gleam['PassivesOffHand'])
        self.assertIn('GSL_Flintlock_OffHand', gleam['PassivesOffHand'])

        harmonic_source = read_entry(
            source_weapons,
            'entry',
            'MAG_Harpers_Harmonizing_Rapier',
        )
        harmony_source = read_entry(
            source_statuses,
            'entry',
            'MAG_HARPERS_HARMONIZING_RAPIER_HARMONY',
        )
        harmony_shout_source = read_entry(
            source_data / 'Spell_Shout.txt',
            'entry',
            'Shout_MAG_Harpers_HarmonizingRapier_Perfrom',
        )
        harmonic = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_HarmonicDueller')
        harmony_status = read_entry(
            passives,
            'entry',
            'GSL_FLINTLOCK_HARMONIC_HARMONY',
        )
        harmony_technical = read_entry(
            passives,
            'entry',
            'GSL_FLINTLOCK_HARMONIC_HARMONY_TECHNICAL',
        )
        harmony_shout = read_entry(
            spells,
            'entry',
            'Shout_GSL_MellowHarmony_Flintlock',
        )
        self.assertEqual(
            harmonic_source['StatusOnEquip'],
            'MAG_HARPERS_HARMONIZING_RAPIER_TECHNICAL',
        )
        self.assertIn('IF(IsMeleeWeaponAttack())', harmony_source['Boosts'])
        self.assertIn('DamageBonus(max(1, CharismaModifier))', harmony_source['Boosts'])
        self.assertIn('SkillCheck(Skill.Performance, 15)', harmony_shout_source['SpellRoll'])
        self.assertEqual(harmony_status['StackId'], 'GSL_FLINTLOCK_HARMONIC_HARMONY')
        self.assertIn('IsRangedWeaponAttack()', harmony_status['Boosts'])
        self.assertIn('DamageBonus(max(1, CharismaModifier))', harmony_status['Boosts'])
        self.assertIn(
            'RemoveStatus(GSL_FLINTLOCK_HARMONIC_HARMONY)',
            harmony_technical['OnRemoveFunctors'],
        )
        self.assertEqual(harmony_shout['SpellRoll'], harmony_shout_source['SpellRoll'])
        self.assertEqual(
            harmony_shout['SpellSuccess'],
            'ApplyStatus(GSL_FLINTLOCK_HARMONIC_HARMONY,100,10)',
        )
        self.assertEqual(harmony_shout['Cooldown'], 'OncePerShortRest')

        missile_source = read_entry(source_weapons, 'entry', 'MAG_MagicMissile_HandCrossbow')
        missile_source_spell = read_entry(
            source_data / 'Spell_Projectile.txt',
            'entry',
            'Projectile_MAG_MagicMissile_Shot',
        )
        neermisser = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_NeerMisser')
        magic_missile = read_entry(
            spells,
            'entry',
            'Projectile_GSL_MagicMissile_Flintlock',
        )
        self.assertEqual(missile_source['Damage Type'], 'Force')
        self.assertEqual(neermisser['Damage Type'], missile_source['Damage Type'])
        self.assertIn('UnlockSpell(Projectile_MAG_MagicMissile_Shot)', missile_source['Boosts'])
        self.assertIn('Projectile_MagicMissile_3', missile_source_spell['using'])
        self.assertEqual(missile_source_spell['Level'], '3')
        self.assertEqual(missile_source_spell['Cooldown'], 'OncePerShortRestPerItem')
        self.assertEqual(magic_missile['using'], 'Projectile_MagicMissile_3')
        self.assertEqual(magic_missile['Level'], missile_source_spell['Level'])
        self.assertEqual(magic_missile['Cooldown'], 'OncePerShortRest')
        self.assertEqual(magic_missile['UseCosts'], 'ActionPoint:1')
        self.assertNotIn('FlintlockAmmo', magic_missile['UseCosts'])
        self.assertIn('GSL_Flintlock_MainHand', magic_missile['RequirementConditions'])

    def test_salty_sickle_slicing_sussur_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        )
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        recipes = (
            (
                'SaltyScimitar',
                'MAG_LC_PirateCommander_Scimitar',
                'WPN_GSL_Flintlock_SaltyScimitar',
                'f9100179-19f6-49f9-8ad5-bda4d21220bc',
                source_gustav_dev,
            ),
            (
                'SickleOfBoooal',
                'UNI_SickleOfBOOOAL',
                'WPN_GSL_Flintlock_SickleOfBoooal',
                'a07f2e91-e084-4fe5-9dbb-ef7de76a3c0a',
                source_gustav,
            ),
            (
                'SlicingShortsword',
                'MAG_Slicing_Shortsword',
                'WPN_GSL_Flintlock_SlicingShortsword',
                'de0e16f6-6dbb-4edd-8ba5-106486b05552',
                source_gustav_dev,
            ),
            (
                'SussurDagger',
                'FOR_IncompleteMasterwork_SussurDagger',
                'WPN_GSL_Flintlock_SussurDagger',
                '8733edb7-f04e-4b6d-ad48-7d49fb782bef',
                source_gustav,
            ),
        )
        for name, source_weapon, crafted_weapon, template_id, source_file in recipes:
            with self.subTest(name=name):
                source = read_entry(source_file, 'entry', source_weapon)
                self.assertEqual(source['RootTemplate'], template_id)

                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [disassembly[f'Object {slot}'] for slot in range(1, 3)],
                    [crafted_weapon, 'OBJ_GSL_DisassemblyKit'],
                )
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertEqual(template.find("attribute[@id='Stats']").get('value'), crafted_weapon)

    def test_salty_sickle_slicing_sussur_keep_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        passives = data_dir / 'GunslingerPassives.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        salty_source = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_LC_PirateCommander_Scimitar',
        )
        salty = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SaltyScimitar')
        command = read_entry(
            source_gustav_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_Command_Container',
        )
        self.assertIn('UnlockSpell(Target_MAG_Command_Container)', salty_source['Boosts'])
        self.assertEqual(salty['Boosts'], salty_source['Boosts'])
        self.assertEqual(salty['DefaultBoosts'], 'WeaponEnchantment(2);WeaponProperty(Magical)')
        self.assertEqual(command['Cooldown'], 'OncePerRestPerItem')
        self.assertEqual(command['UseCosts'], 'ActionPoint:1')
        self.assertEqual(command['using'], 'Target_Command_Container')
        self.assertIn('Target_MAG_Command_Flee', command['ContainerSpells'])

        sickle_source = read_entry(source_gustav / 'Weapon.txt', 'entry', 'UNI_SickleOfBOOOAL')
        blessing = read_entry(
            source_gustav / 'Passive.txt',
            'entry',
            'UND_BlessingOfBOOOAL',
        )
        sickle = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SickleOfBoooal')
        self.assertEqual(sickle_source['Damage'], '2d4')
        self.assertEqual(sickle['Damage'], sickle_source['Damage'])
        self.assertEqual(sickle['DefaultBoosts'], 'WeaponProperty(Magical)')
        self.assertIn("HasStatus('BLEEDING',context.Target)", blessing['Boosts'])

        slicing_source = read_entry(
            source_gustav_dev / 'Passive.txt',
            'entry',
            'MAG_Slicing_Shortsword_Passive',
        )
        slicing = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SlicingShortsword')
        slicing_passive = read_entry(
            passives,
            'entry',
            'GSL_Flintlock_SlicingShortsword_Passive',
        )
        self.assertEqual(slicing_source['StatsFunctorContext'], 'OnDamage')
        self.assertIn('HasAdvantage() and not HasDisadvantage()', slicing_source['Conditions'])
        self.assertEqual(slicing_source['StatsFunctors'], slicing_passive['StatsFunctors'])
        self.assertIn('GSL_Flintlock_SlicingShortsword_Passive', slicing['PassivesOnEquip'])
        self.assertIn('IsRangedWeaponAttack()', slicing_passive['Conditions'])
        self.assertIn('HasAdvantage() and not HasDisadvantage()', slicing_passive['Conditions'])
        self.assertEqual(slicing_passive['StatsFunctors'], slicing_source['StatsFunctors'])

        sussur_source = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'FOR_IncompleteMasterwork_SussurDagger',
        )
        sussur = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SussurDagger')
        firearm_attack = read_entry(
            data_dir / 'GunslingerSpells.txt',
            'entry',
            'Projectile_GSL_FirearmAttack',
        )
        self.assertEqual(sussur_source['WeaponFunctors'], sussur['WeaponFunctors'])
        self.assertIn('SavingThrow(Ability.Constitution, 12)', sussur['WeaponFunctors'])
        self.assertIn('ApplyStatus(SILENCED,100, 2)', sussur['WeaponFunctors'])
        self.assertIn('ExecuteWeaponFunctors(MainHand)', firearm_attack['SpellSuccess'])


    def test_sussur_umbra_baneful_wavemothers_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        sources = {
            'SussurSickle': (
                'FOR_IncompleteMasterwork_SussurSickle',
                'WPN_GSL_Flintlock_SussurSickle',
                '6b95bb45-41c3-4954-ac2f-ef1aa169b0b6',
            ),
            'ClutchingUmbra': (
                'MAG_Shadow_Shortsword',
                'WPN_GSL_Flintlock_ClutchingUmbra',
                '82afffba-16cb-47ff-8520-bac8b9c46ad3',
            ),
            'Baneful': (
                'MAG_Bonded_Baneful_Shortsword',
                'WPN_GSL_Flintlock_Baneful',
                '3b578a43-222e-480b-8a22-2c424471099f',
            ),
            'WavemothersSickle': (
                'MAG_LC_Umberlee_Cold_Sickle',
                'WPN_GSL_Flintlock_WavemothersSickle',
                '5b4b10cd-089f-4675-8392-5bfa6749d79c',
            ),
        }
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        for name, (source_weapon, crafted_weapon, source_template) in sources.items():
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(disassembly['Object 1'], crafted_weapon)
                self.assertEqual(disassembly['Object 2'], 'OBJ_GSL_DisassemblyKit')
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertNotEqual(fused['RootTemplate'], source_template)

    def test_sussur_umbra_baneful_wavemothers_keep_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        spells = data_dir / 'GunslingerSpells.txt'
        source_gustav = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'Gustav'
            / 'Stats' / 'Generated' / 'Data'
        )
        source_gustav_dev = (
            ROOT / 'examples' / 'BG3 Gustav Reference' / 'Public' / 'GustavDev'
            / 'Stats' / 'Generated' / 'Data'
        )

        sussur_source = read_entry(
            source_gustav / 'Weapon.txt',
            'entry',
            'FOR_IncompleteMasterwork_SussurSickle',
        )
        sussur = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_SussurSickle')
        self.assertEqual(sussur['WeaponFunctors'], sussur_source['WeaponFunctors'])
        self.assertIn('SavingThrow(Ability.Constitution, 12)', sussur['WeaponFunctors'])
        self.assertIn('ApplyStatus(SILENCED,100, 2)', sussur['WeaponFunctors'])

        umbra_source = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Shadow_Shortsword',
        )
        shadow_source = read_entry(
            source_gustav_dev / 'Spell_Target.txt',
            'entry',
            'Target_MAG_WeaponAction_ShadowBlade',
        )
        umbra = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_ClutchingUmbra')
        shadow_shot = read_entry(
            spells,
            'entry',
            'Projectile_GSL_ShadowsoakedShot_Flintlock',
        )
        self.assertIn('Target_MAG_WeaponAction_ShadowBlade', umbra_source['BoostsOnEquipMainHand'])
        self.assertIn('DealDamage(MainMeleeWeapon+ProficiencyBonus, MainMeleeWeaponDamageType)', shadow_source['SpellSuccess'])
        self.assertIn('DealDamage(1d6, Psychic)', shadow_source['SpellSuccess'])
        self.assertIn('Stealth', shadow_source['SpellFlags'])
        self.assertIn('UnlockSpell(Projectile_GSL_ShadowsoakedShot_Flintlock)', umbra['Boosts'])
        self.assertEqual(
            shadow_shot['UseCosts'],
            'ActionPoint:1;GunslingerFlintlockAmmo:1',
        )
        self.assertIn('DealDamage(MainRangedWeapon+ProficiencyBonus,MainRangedWeaponDamageType)', shadow_shot['SpellSuccess'])
        self.assertIn('DealDamage(1d6,Psychic)', shadow_shot['SpellSuccess'])
        self.assertIn('Stealth', shadow_shot['SpellFlags'])

        baneful_source = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_Bonded_Baneful_Shortsword',
        )
        baneful = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_Baneful')
        self.assertEqual(baneful['WeaponFunctors'], baneful_source['WeaponFunctors'])
        self.assertEqual(baneful['PassivesOnEquip'], 'GSL_Firearm_Misfire_Passive;' + baneful_source['PassivesOnEquip'])
        self.assertIn('WEAPON_BOND', baneful['WeaponFunctors'])
        self.assertIn('PACT_BLADE', baneful['WeaponFunctors'])
        self.assertIn('ApplyStatus(BANE', baneful['WeaponFunctors'])

        wave_source = read_entry(
            source_gustav_dev / 'Weapon.txt',
            'entry',
            'MAG_LC_Umberlee_Cold_Sickle',
        )
        wave_passive = read_entry(
            source_gustav_dev / 'Passive.txt',
            'entry',
            'MAG_LC_Umberlee_Cold_Sickle_Passive',
        )
        wave = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_WavemothersSickle')
        self.assertEqual(
            wave['DefaultBoosts'],
            'WeaponEnchantment(2);WeaponProperty(Magical);WeaponDamage(1d4,Cold)',
        )
        self.assertIn('MAG_LC_Umberlee_Cold_Sickle_Passive', wave['PassivesOnEquip'])
        self.assertIn("HasStatus('WET', context.Target)", wave_passive['Boosts'])

    def test_larethian_phalar_banshee_darkfire_recipes_are_reversible(self) -> None:
        combinations = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
        weapon_stats = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        sources = {
            'LarethiansWrath': (
                'MAG_Finesse_Longsword',
                'WPN_GSL_Flintlock_LarethiansWrath',
                'ceb904bd-1242-4cd6-8d44-dc45afe4eff3',
            ),
            'PhalarAluve': (
                'UND_SwordInStone',
                'WPN_GSL_Flintlock_PhalarAluve',
                '128e257b-5289-4348-91aa-41c7de56c062',
            ),
            'BowOfTheBanshee': (
                'MAG_BG_OfTheBanshee_Bow',
                'WPN_GSL_Flintlock_BowOfTheBanshee',
                '714e3114-99fb-40a0-9ba1-bc316a0c6781',
            ),
            'DarkfireShortbow': (
                'MAG_BG_Darkfire_Shortbow',
                'WPN_GSL_Flintlock_DarkfireShortbow',
                '6918c720-e952-4689-95c9-c190b7fb7510',
            ),
        }
        templates = ET.parse(PUBLIC / 'RootTemplates' / '_merged.lsx').findall(
            ".//node[@id='GameObjects']"
        )
        for name, (source_weapon, crafted_weapon, expected_template) in sources.items():
            with self.subTest(name=name):
                assembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Assembly_Flintlock_{name}',
                )
                self.assertEqual(
                    [assembly[f'Object {slot}'] for slot in range(1, 4)],
                    ['OBJ_GSL_AssemblyKit', source_weapon, 'WPN_GSL_Flintlock'],
                )
                self.assertEqual(
                    [assembly[f'Transform {slot}'] for slot in range(1, 4)],
                    ['Consume', 'Consume', 'Transform'],
                )
                result = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Assembly_Flintlock_{name}_1',
                )
                self.assertEqual(result['Result 1'], crafted_weapon)

                disassembly = read_entry(
                    combinations,
                    'ItemCombination',
                    f'GSL_Disassembly_Flintlock_{name}',
                )
                self.assertEqual(disassembly['Object 1'], crafted_weapon)
                self.assertEqual(disassembly['Object 2'], 'OBJ_GSL_DisassemblyKit')
                returned = read_entry(
                    combinations,
                    'ItemCombinationResult',
                    f'GSL_Disassembly_Flintlock_{name}_1',
                )
                self.assertEqual(returned['Result 1'], 'WPN_GSL_Flintlock')
                self.assertEqual(returned['Result 2'], source_weapon)

                fused = read_entry(weapon_stats, 'entry', crafted_weapon)
                template = next(
                    node for node in templates
                    if node.find("attribute[@id='Name']").get('value') == crafted_weapon
                )
                self.assertEqual(
                    fused['RootTemplate'],
                    template.find("attribute[@id='MapKey']").get('value'),
                )
                self.assertEqual(fused['RootTemplate'], expected_template)

    def test_larethian_phalar_banshee_darkfire_adapt_source_abilities(self) -> None:
        data_dir = PUBLIC / 'Stats' / 'Generated' / 'Data'
        weapon_stats = data_dir / 'Weapon.txt'
        spells = data_dir / 'GunslingerSpells.txt'
        passives = data_dir / 'GunslingerPassives.txt'

        larethian = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_LarethiansWrath',
        )
        razor_gale = read_entry(
            spells,
            'entry',
            'Zone_GSL_RazorGale_Flintlock',
        )
        razor_gale_base = read_entry(spells, 'entry', 'Zone_GSL_LineEmUp')
        self.assertIn('WeaponEnchantment(1)', larethian['DefaultBoosts'])
        self.assertIn('UnlockSpell(Zone_GSL_RazorGale_Flintlock)', larethian['Boosts'])
        self.assertEqual(
            razor_gale['UseCosts'],
            'ActionPoint:1;GunslingerFlintlockAmmo:1',
        )
        self.assertIn('Shape', razor_gale)
        self.assertIn('SavingThrow(Ability.Dexterity', razor_gale_base['SpellRoll'])
        self.assertIn('ProficiencyBonus', razor_gale['SpellSuccess'])
        self.assertIn('ProficiencyBonus', razor_gale['SpellFail'])

        phalar = read_entry(weapon_stats, 'entry', 'WPN_GSL_Flintlock_PhalarAluve')
        melody = read_entry(spells, 'entry', 'Shout_GSL_PhalarMelody_Flintlock')
        sing = read_entry(spells, 'entry', 'Shout_GSL_PhalarSing_Flintlock')
        shriek = read_entry(spells, 'entry', 'Shout_GSL_PhalarShriek_Flintlock')
        self.assertIn('Skill(Performance, 1)', phalar['Boosts'])
        self.assertEqual(phalar['StatusOnEquip'], 'MAG_SWORD_IN_STONE_TECHNICAL')
        self.assertEqual(melody['Cooldown'], 'OncePerShortRest')
        self.assertEqual(
            melody['ContainerSpells'],
            'Shout_GSL_PhalarSing_Flintlock;Shout_GSL_PhalarShriek_Flintlock',
        )
        self.assertIn(
            'MAG_HARPERS_SINGING_SWORD_SINGING_AURA',
            sing['SpellProperties'],
        )
        self.assertIn(
            'MAG_HARPERS_SINGING_SWORD_SHRIEKING_AURA',
            shriek['SpellProperties'],
        )
        self.assertIn('HasPassive(', sing['RequirementConditions'])
        self.assertIn('HasPassive(', shriek['RequirementConditions'])

        banshee = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_BowOfTheBanshee',
        )
        banshee_passive = read_entry(
            passives,
            'entry',
            'GSL_Flintlock_BansheeBless_Passive',
        )
        self.assertIn('WeaponEnchantment(1)', banshee['DefaultBoosts'])
        self.assertIn('FRIGHTENED', banshee['WeaponFunctors'])
        self.assertIn('SavingThrow(Ability.Wisdom, 12)', banshee['WeaponFunctors'])
        self.assertIn('SG_Frightened', banshee_passive['Boosts'])
        self.assertIn('CharacterWeaponDamage(1d4)', banshee_passive['Boosts'])
        self.assertIn('RollBonus(Attack,1d4)', banshee_passive['Boosts'])

        darkfire = read_entry(
            weapon_stats,
            'entry',
            'WPN_GSL_Flintlock_DarkfireShortbow',
        )
        self.assertIn('WeaponEnchantment(2)', darkfire['DefaultBoosts'])
        self.assertIn('Resistance(Fire, Resistant)', darkfire['Boosts'])
        self.assertIn('Resistance(Cold, Resistant)', darkfire['Boosts'])
        self.assertIn('UnlockSpell(Target_MAG_Haste)', darkfire['Boosts'])


if __name__ == '__main__':
    unittest.main()
