"""Generate audited firearm conversions for magical weapons original to optional mods."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import re
from uuid import UUID, uuid5

from generate_base_conversions import Conversion, conversion_fields, replace_marked, template_for
from validate_stats import read_stats

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / 'examples'
SOURCE = ROOT / 'GunslingerClass'
MAIN = SOURCE / 'Public' / 'GunslingerClass'
LOCALIZATION = SOURCE / 'Localization' / 'English' / 'GunslingerClass.xml'
NAMESPACE = UUID('98ea52d4-f6c1-4a76-9b51-951b4b180449')
BEGIN = '# BEGIN GENERATED MOD WEAPON CONVERSIONS'
END = '# END GENERATED MOD WEAPON CONVERSIONS'
XML_BEGIN = '                <!-- BEGIN GENERATED MOD WEAPON CONVERSIONS -->'
XML_END = '                <!-- END GENERATED MOD WEAPON CONVERSIONS -->'
LOC_BEGIN = '        <!-- BEGIN GENERATED MOD WEAPON CONVERSIONS -->'
LOC_END = '        <!-- END GENERATED MOD WEAPON CONVERSIONS -->'
JWL_LOC_BEGIN = '        <!-- BEGIN GENERATED JWL DESCRIPTIONS -->'
EFFECTS_FILE = 'GunslingerCompatEffects.txt'
EMPTY_TEMPLATES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n<save>\n'
    '    <version major="4" minor="0" revision="9" build="331"/>\n'
    '    <region id="Templates">\n        <node id="Templates">\n            <children>\n'
    '            </children>\n        </node>\n    </region>\n</save>\n'
)
TEMPLATES_CLOSE = '            </children>\n        </node>\n    </region>\n</save>'
VANILLA_WEAPONS = tuple(EXAMPLES / path for path in (
    'BG3 Reference/Public/Shared/Stats/Generated/Data/Weapon.txt',
    'BG3 Reference/Public/SharedDev/Stats/Generated/Data/Weapon.txt',
    'BG3 Gustav Reference/Public/Gustav/Stats/Generated/Data/Weapon.txt',
    'BG3 Gustav Reference/Public/GustavDev/Stats/Generated/Data/Weapon.txt',
    'BG3 Gustav Reference/Public/Honour/Stats/Generated/Data/Weapon.txt',
))
FIREARM_DC = '8 + context.Source.ProficiencyBonus + GetModifier(context.Source.Dexterity)'
SHOT_DAMAGE = 'DealDamage(max(1,MainRangedWeapon),MainRangedWeaponDamageType)'
SHOT_TOOLTIP = 'DealDamage(MainRangedWeapon,MainRangedWeaponDamageType)'


@dataclass(frozen=True)
class ModWeapon:
    conversion: Conversion
    status_on_equip: str = ''


@dataclass(frozen=True)
class Shot:
    name: str
    kind: str
    label: str
    description: str
    success: str
    tooltip_damage: str = SHOT_TOOLTIP
    damage: str = SHOT_DAMAGE
    save: str = ''
    status: str = ''


@dataclass(frozen=True)
class SourceMod:
    tag: str
    folder: str
    weapon_file: Path
    weapon_hash: str
    weapons: tuple[ModWeapon, ...]
    excluded: dict[str, str]
    shots: tuple[Shot, ...] = ()
    effects: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] = ()

    @property
    def public(self) -> Path:
        return SOURCE / 'Public' / self.folder


def weapon(label: str, source: str, kind: str, rarity: str, enchantment: int, behavior: str,
           status_on_equip: str = '', **fields: str) -> ModWeapon:
    return ModWeapon(Conversion(label, source, kind, rarity, enchantment, behavior, **fields), status_on_equip)


def effect(kind: str, name: str, parent: str = '', **fields: str) -> tuple[str, str, str, tuple[tuple[str, str], ...]]:
    return kind, name, parent, tuple(fields.items())


ATE = SourceMod(
    tag='ATE',
    folder='GunslingerClass_ATE_WeaponCopiesCompat',
    weapon_file=EXAMPLES / 'Act Two Expansion' / 'Public' / 'ActTwoExpansion_41ec643a-e2ad-e69d-52c2-920a6f4a98ad'
    / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt',
    weapon_hash='4a6f0109d431b3d54c39a4536086647a87cae6d820ad91f7f4fb40d7211b4046',
    weapons=(
        weapon('Trickster Dagger', 'CHI_MAG_WPN_HUM_Dagger_Return', 'Flintlock', 'Rare', 2,
               'Once per short rest, when a melee attack damages you, gain Mirror Image for 3 turns.',
               passives='CHI_MAG_WPN_HUM_Dagger_Return_MirrorImagePassive'),
        weapon('Scimitar of Flowing Waters', 'CHI_MAG_WPN_Scimitar_Water_Myrmidon_B', 'Flintlock', 'VeryRare', 2,
               'Grants +1 to Dexterity saving throws and Initiative, and a firearm Razor Gale.',
               spell_boosts='RollBonus(SavingThrow, 1, Dexterity)',
               passives='CHI_MAG_WPN_Scimitar_Water_Myrmidon_B_Elf_Passive;MAG_InitiativeWeapon_Passive',
               action='Zone_GSL_RazorGale_Flintlock'),
        weapon('Gnomish Tinkerer Crossbow', 'CHI_WPN_Crossbow_Gnomish', 'Musket', 'VeryRare', 2,
               'Once per short rest, Ricochet Shot bounces off its target like an Arrow of Ricochet.',
               action='Projectile_GSL_ATE_RicochetShot_Musket'),
        weapon('Dexterous Flail', 'CHI_WPN_Flail_Agility', 'Blunderbuss', 'Rare', 2,
               'Your Dexterity score becomes at least 18.',
               spell_boosts='AbilityOverrideMinimum(Dexterity, 18)'),
        weapon('Silver Sword of the Comet', 'CHI_WPN_Greatsword_Spellcaster', 'Blunderbuss', 'VeryRare', 2,
               'Shots deal +1d4 Psychic damage. Once per short rest, a critical hit restores a level 2 spell slot. '
               'Once per short rest, Mindcrush Shot adds Psychic damage equal to your Proficiency Bonus and can Stun.',
               passives='CHI_WPN_Greatsword_Spellcaster_Passive;GSL_ATE_Mindcrusher_Passive',
               action='Projectile_GSL_ATE_MindcrushShot_Blunderbuss'),
        weapon('Kara-Turan Katana', 'CHI_WPN_HUM_Katana_B', 'Musket', 'Rare', 2,
               'Shots ignore Piercing resistance. Hits made with Advantage inflict Bleeding for 2 turns.',
               spell_boosts='IgnoreResistance(Piercing,Resistant)',
               passives='GSL_Flintlock_SlicingShortsword_Passive'),
        weapon('Lance Pike', 'CHI_WPN_HUM_Lancespear_A', 'Blunderbuss', 'VeryRare', 2,
               'Grants Zephyr Flash and Zephyr Break.',
               spell_boosts='UnlockSpell(Rush_MAG_ZephyrFlash);UnlockSpell(Zone_MAG_ZephyrBreak)'),
        weapon('Ironvine Shortbow', 'CHI_WPN_HUM_Shortbow_Druid_A', 'Flintlock', 'Rare', 2,
               'Reduces the critical-hit threshold by 1, and damaging hits can Poison (DC 15 Dexterity). '
               'Once per short rest, Hail of Thorns Shot deals an extra 1d10 Piercing damage on a failed Dexterity save.',
               passives='MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive;MAG_Druid_Longbow_Passive',
               action='Projectile_GSL_ATE_HailOfThornsShot_Flintlock'),
        weapon('The Breacher', 'CHI_WPN_Javelin', 'Musket', 'Rare', 2,
               'Grants Heroic Throw once per short rest.',
               spell_boosts='UnlockSpell(Throw_CHI_HeroicThrow)'),
        weapon('Axe of Storms', 'CHI_WPN_MAG_Axe_Lightning', 'Flintlock', 'VeryRare', 2,
               'Grants Lightning Whirlwind: once per short rest, nearby creatures make a Strength save '
               'or take 2d6 Lightning damage and are Shocked.',
               spell_boosts='UnlockSpell(Shout_CHI_Whirlwind_Lightning)'),
        weapon('Firbolg Greataxe', 'CHI_WPN_MAG_Battleaxe_Firbolg', 'Blunderbuss', 'VeryRare', 2,
               'Once per combat, a damaging shot can outline the target in Faerie Fire (DC 13 Dexterity). '
               'Grants Missile Snaring.',
               passives='CHI_WPN_MAG_Axe_Firbolg_Faerie_Passive;MAG_OfMissileSnaring_Gloves_Passive'),
        weapon('Phasmid Longbow', 'CHI_WPN_MAG_Longbow_PhantasmalKiller', 'Musket', 'Rare', 2,
               'Damaging shots can inflict Phantasmal Force (DC 14 Wisdom). Once per short rest, '
               'Menacing Shot deals an extra 1d8 damage and can Frighten.',
               passives='CHI_WPN_MAG_Longbow_PhantasmalKiller_Passive',
               action='Projectile_GSL_ATE_MenacingShot_Musket'),
        weapon('Bow of the Thunder Lord', 'CHI_WPN_MAG_Longbow_Thunder', 'Musket', 'Rare', 2,
               'Grants Gushing Air once per short rest.',
               spell_boosts='UnlockSpell(Projectile_CHI_GushingAir)'),
        weapon("Death Knight's Longsword", 'CHI_WPN_MAG_Longsword_Necromancy', 'Musket', 'VeryRare', 2,
               'Killing an enemy with a shot grants Life Essence.',
               passives='GSL_ATE_DeathKnight_Passive'),
        weapon('Enfeebling Rapier', 'CHI_WPN_MAG_Rapier_Enfeeble', 'Flintlock', 'VeryRare', 2,
               'Damaging shots can inflict Ray of Enfeeblement for 2 turns (DC 12 Constitution).',
               passives='CHI_WPN_MAG_Rapier_Enfeeble_Passive'),
        weapon('Gish Shortsword', 'CHI_WPN_MAG_Shortsword_GithAssassin', 'Flintlock', 'VeryRare', 2,
               "Shots deal +1d4 Psychic damage. Once per short rest, when an enemy misses you with a melee attack, "
               "Assassin's Riposte fires a reaction shot.",
               passives='CHI_AssassinsRiposte_Resource_Passive;GSL_ATE_AssassinsRiposte_Passive;GSL_ATE_Mindcrusher_Passive'),
        weapon('Hoarfrost Blade', 'CHI_WPN_MAG_Shortsword_Ice', 'Flintlock', 'VeryRare', 2,
               'Critical hits deal 10 Cold damage and grant Advantage on your next attack. Ice cannot knock you Prone.',
               status_on_equip='MAG_FROST_ICE_PRONE_IMMUNITY_BOOTS',
               passives='CHI_WPN_MAG_Shortsword_Ice_Passive;MAG_Frost_IceSurfaceProneImmunity_Boots_Passive'),
        weapon('Firefly Keeper Staff', 'CHI_WPN_MAG_Staff_Fireflies', 'Musket', 'VeryRare', 2,
               'Grants +1 to ranged spell attack rolls, Protective Lights, and Faerie Fire.',
               spell_boosts='RollBonus(RangedSpellAttack,1);UnlockSpell(Shout_CHI_MAG_FIREFLIES_PROTECTIVE_LIGHTS);'
               'UnlockSpell(Target_CHI_Axe_FaerieFire_UNI)'),
        weapon('Still Wind Staff', 'CHI_WPN_MAG_Staff_Icicle', 'Musket', 'VeryRare', 2,
               'Grants Cold resistance, +1 to ranged spell attack rolls, +2 spell save DC, Explosive Icicle, and Ray of Frost.',
               spell_boosts='Resistance(Cold, Resistant);RollBonus(RangedSpellAttack,1);'
               'UnlockSpell(Projectile_CHI_ExplosiveIcicle);UnlockSpell(Projectile_MAG_RayOfFrost_Staff)',
               passives='MAG_SpellSaveDC_Enchantment_Passive'),
        weapon('Sun Crystal Staff', 'CHI_WPN_MAG_Staff_Sun', 'Musket', 'Rare', 2,
               'Grants Sunbeam.',
               spell_boosts='UnlockSpell(Zone_MAG_BloodOfLathander_Sunbeam)'),
        weapon('Trident of Healing Waters', 'CHI_WPN_MAG_Trident_Water', 'Musket', 'Rare', 2,
               'Grants Mass Healing Word and Create Water.',
               spell_boosts='UnlockSpell(Shout_CHI_Trident_HealingWord_Mass_UNI);UnlockSpell(Target_CreateWater_StaffOfRain)'),
        weapon('Gnomish War Pick', 'CHI_WPN_MAG_WarPick', 'Blunderbuss', 'Rare', 2,
               'Critical hits and killing blows against enemies create a shockwave that can knock nearby enemies Prone '
               '(DC 14 Dexterity).',
               passives='CHI_WPN_MAG_WarPick_Passive'),
        weapon('Ancient Warhammer', 'CHI_WPN_MAG_Warhammer_Smite', 'Musket', 'Rare', 2,
               'Smites can Daze (DC 13 Constitution). Once per short rest, Scorching Shot deals an extra 1d10 Fire '
               'damage and can set the target Burning (DC 13 Constitution).',
               passives='MAG_DazingSmite_Passive',
               action='Projectile_GSL_ATE_ScorchingShot_Musket'),
        weapon('Sickle of Slicing', 'CHI_WPN_SickleOfSlicing', 'Flintlock', 'Rare', 2,
               'Shots deal an additional 1d4 Piercing damage to Bleeding targets.',
               passives='GSL_ATE_SickleOfSlicing_Passive'),
        weapon('Shadar-Kai Spear', 'CHI_WPN_Spear_Shadow', 'Musket', 'Rare', 2,
               'Grants +1 to Stealth checks. Entering stealth makes your weapon attacks deal +1d12 Necrotic damage.',
               passives='ARM_Stealthy_1_Passive;CHI_ShadowSpear_Passive'),
    ),
    excluded={
        'CHI_MAG_WPN_Longsword_Sun': 'Legendary weapons are out of scope.',
        'CHI_WPN_Minotaur_Greatclub_1': 'Non-magical NPC weapon.',
    },
    shots=(
        Shot('Projectile_GSL_ATE_RicochetShot_Musket', 'Musket', 'Ricochet Shot',
             'Fire a shot that ricochets off the target to strike nearby creatures, as an Arrow of Ricochet does. '
             'Once per short rest.',
             'SpawnExtraProjectiles(Projectile_ArrowOfRicochet_Ricochet)'),
        Shot('Projectile_GSL_ATE_MindcrushShot_Blunderbuss', 'Blunderbuss', 'Mindcrush Shot',
             'Fire a shot that deals additional Psychic damage equal to your Proficiency Bonus. The target makes a '
             'Constitution saving throw or is Stunned for 2 turns. Once per short rest.',
             f'DealDamage(ProficiencyBonus,Psychic,Magical);IF(not SavingThrow(Ability.Constitution,{FIREARM_DC})):'
             'ApplyStatus(STUNNED,100,2)',
             tooltip_damage=f'{SHOT_TOOLTIP};DealDamage(ProficiencyBonus,Psychic)',
             save='Constitution', status='ApplyStatus(STUNNED,100,2)'),
        Shot('Projectile_GSL_ATE_HailOfThornsShot_Flintlock', 'Flintlock', 'Hail of Thorns Shot',
             'Fire a thorn-wrapped shot. On a hit, the target makes a Dexterity saving throw or takes an additional '
             '1d10 Piercing damage. Once per short rest.',
             f'IF(not SavingThrow(Ability.Dexterity,{FIREARM_DC})):DealDamage(1d10,Piercing,Magical)',
             tooltip_damage=f'{SHOT_TOOLTIP};DealDamage(1d10,Piercing)', save='Dexterity'),
        Shot('Projectile_GSL_ATE_MenacingShot_Musket', 'Musket', 'Menacing Shot',
             'Fire a shot that deals an additional 1d8 damage. The target makes a Wisdom saving throw or is '
             'Frightened for 2 turns. Once per short rest.',
             f'IF(not SavingThrow(Ability.Wisdom,{FIREARM_DC},AdvantageOnFrightened(),DisadvantageOnFrightened())):'
             'ApplyStatus(FRIGHTENED,100,2)',
             tooltip_damage='DealDamage(MainRangedWeapon+1d8,MainRangedWeaponDamageType)',
             damage='DealDamage(max(1,MainRangedWeapon+1d8),MainRangedWeaponDamageType)',
             save='Wisdom', status='ApplyStatus(FRIGHTENED,100,2)'),
        Shot('Projectile_GSL_ATE_ScorchingShot_Musket', 'Musket', 'Scorching Shot',
             'Fire a searing shot that deals an additional 1d10 Fire damage. The target makes a DC 13 Constitution '
             'saving throw or is set Burning for 2 turns. Once per short rest.',
             'DealDamage(1d10,Fire,Magical);IF(not SavingThrow(Ability.Constitution,13)):ApplyStatus(BURNING,100,2)',
             tooltip_damage=f'{SHOT_TOOLTIP};DealDamage(1d10,Fire)',
             save='Constitution', status='ApplyStatus(BURNING,100,2)'),
    ),
    effects=(
        effect('PassiveData', 'GSL_ATE_Mindcrusher_Passive', 'MAG_Githborn_Mindcrusher_Greatsword_Passive',
               Boosts='IF(IsRangedWeaponAttack()):CharacterWeaponDamage(1d4, Psychic)'),
        effect('PassiveData', 'GSL_ATE_DeathKnight_Passive', 'CHI_WPN_MAG_Longsword_Necromancy_Passive',
               Conditions='not Item() and Enemy() and IsKillingBlow() and IsRangedWeaponAttack() '
               'and AttackedWithPassiveSourceWeapon()'),
        effect('PassiveData', 'GSL_ATE_SickleOfSlicing_Passive', 'CHI_WPN_SickleOfSlicing_Passive',
               DescriptionParams='DealDamage(1d4,Piercing)',
               Conditions="AttackedWithPassiveSourceWeapon() and IsRangedWeaponAttack() and not IsRedirectedDamage() "
               "and HasStatus('BLEEDING')",
               StatsFunctors='DealDamage(1d4,Piercing)'),
        effect('PassiveData', 'GSL_ATE_AssassinsRiposte_Passive', 'CHI_AssassinsRiposte_Passive',
               Boosts="IF(not HasStatus('SG_Polymorph_BeastShape')):UnlockInterrupt(Interrupt_GSL_ATE_AssassinsRiposte)"),
        effect('InterruptData', 'Interrupt_GSL_ATE_AssassinsRiposte', 'CHI_AssassinsRiposte',
               Conditions="IsAbleToReact(context.Observer) and Enemy(context.Source,context.Observer) and IsMeleeAttack() "
               "and IsMiss() and not HasStatus('INVISIBILITY') and not AnyEntityIsItem() and "
               "not DistanceToEntityGreaterThan(2, context.ObserverPosition, context.Source) and HasLastAttackTriggered() "
               "and not HasStatus('GSL_FIREARM_MAIN_DISABLED',context.Observer) and "
               "HasPassive('GSL_Flintlock_MainHand',context.Observer) and "
               "HasActionResource('GunslingerFlintlockAmmo',1,0,false,false,context.Observer)",
               Properties='UseSpell(OBSERVER_SOURCE,Projectile_GSL_ReactionShot,true,true,true);'
               'ApplyStatus(OBSERVER_OBSERVER,INTERRUPT_RIPOSTE,100,0);RemoveStatus(CHI_AssassinsRiposte_Resource)'),
    ),
)

EO = SourceMod(
    tag='EO',
    folder='GunslingerClass_EO_WeaponCopiesCompat',
    weapon_file=EXAMPLES / 'Encounters Overhaul' / 'Public' / 'EncountersOverhaul' / 'Stats' / 'Generated' / 'Data'
    / 'Weapon.txt',
    weapon_hash='7c278897688c73c197f0ae81c14a4917e0a7f8c67f993c9875547fd8bbef75e7',
    weapons=(
        weapon("Nightwalker's Claw", 'EO_Sickle_NightwalkersClaw', 'Flintlock', 'VeryRare', 2,
               'Hits can drain life, reducing the target\'s maximum hit points by 2d8 (DC 10 Constitution).',
               weapon_functors='IF(not SavingThrow(Ability.Constitution, 10)):ApplyStatus(LIFE_DRAIN,100, -1)'),
        weapon('Ebonbone Scepter', 'EO_Staff_Ebonbone', 'Musket', 'VeryRare', 1,
               'Grants Cone of Cold once per long rest, and Elemental Affinity for Cold spells.',
               spell_boosts='UnlockSpell(Zone_EO_Ebonbone_ConeOfCold)',
               passives='EO_ElementalAffinity_White_Ebonbone_Scepter_Passive'),
        weapon('Woe (Skull Lord variant)', 'EO_MAG_SkullLords_Quarterstaff', 'Musket', 'VeryRare', 2,
               'Shots deal +1d10 Necrotic damage and inflict Decompose for 4 turns.',
               boosts='WeaponDamage(1d10, Necrotic)',
               weapon_functors='ApplyStatus(UCL_DECOMPOSE, 100, 4)'),
    ),
    excluded={
        'EO_WPN_Light_Greataxe_1': 'Only a +1 enchantment.',
        'EO_WPN_Light_Shortbow_1': 'Only a +1 enchantment.',
        'EO_WPN_Light_Warhammer_2': 'Only a +2 enchantment.',
        'EO_WPN_Scimitar_2': 'Only a +2 enchantment.',
        'EO_WPN_Artificer_Crossbow': 'Only a +2 enchantment and the standard Piercing Shot.',
        'AE_MAG_SkullLords_Quarterstaff': 'Unreferenced legacy duplicate of EO_MAG_SkullLords_Quarterstaff.',
        'AE_WPN_Artificer_Crossbow': 'Unreferenced legacy duplicate.',
        'AE_WPN_Greataxe_1': 'Unreferenced legacy duplicate.',
        'AE_WPN_Scimitar_2': 'Unreferenced legacy duplicate.',
        'AE_WPN_Shortbow_1': 'Unreferenced legacy duplicate.',
        'AE_WPN_Warhammer_2': 'Unreferenced legacy duplicate.',
        'AE_WPN_Trident_Allip': 'Unreferenced legacy duplicate of a non-magical NPC weapon.',
    },
)

MODS = (ATE, EO)


def stat_name(mod: SourceMod, conversion: Conversion) -> str:
    return f'{conversion.name}_{mod.tag}'


def stat_root(name: str) -> str:
    return str(uuid5(NAMESPACE, name))


def localized_handle(name: str, purpose: str) -> str:
    return 'h' + str(uuid5(NAMESPACE, name + ':' + purpose)).replace('-', 'g')


def sound_passive(mod: SourceMod) -> str:
    return f'GSL_{mod.tag}_ShotSound'


def parse_weapons(paths: tuple[Path, ...]) -> dict[str, tuple[str, dict[str, str]]]:
    entries: dict[str, tuple[str, dict[str, str]]] = {}
    for path in paths:
        text = path.read_text(encoding='utf-8-sig')
        for match in re.finditer(r'^new entry "([^"]+)"\s*\n(.*?)(?=^new entry |\Z)', text, re.M | re.S):
            name, body = match.groups()
            if not re.search(r'^\s*type "Weapon"', body, re.M):
                continue
            parent = re.search(r'^\s*using "([^"]+)"', body, re.M)
            fields = dict(re.findall(r'^\s*data "([^"]+)" "(.*)"', body, re.M))
            if parent and parent[1] == name and name in entries:
                # Later modules patch an entry in place by inheriting from themselves.
                entries[name] = (entries[name][0], {**entries[name][1], **fields})
            else:
                entries[name] = (parent[1] if parent else '', fields)
    return entries


def resolve(name: str, entries: dict[str, tuple[str, dict[str, str]]]) -> dict[str, str]:
    chain: list[dict[str, str]] = []
    seen: set[str] = set()
    while name in entries and name not in seen:
        seen.add(name)
        parent, fields = entries[name]
        chain.append(fields)
        name = parent
    resolved: dict[str, str] = {}
    for fields in reversed(chain):
        resolved.update(fields)
    return resolved


def firearm_kind(fields: dict[str, str]) -> str:
    properties = set(fields.get('Weapon Properties', '').split(';'))
    proficiency = set(fields.get('Proficiency Group', '').split(';'))
    if properties & {'Light', 'Finesse'} or proficiency & {'Shortbows', 'HandCrossbows'}:
        return 'Flintlock'
    if properties & {'Versatile', 'Thrown'} or proficiency & {'Longbows', 'LightCrossbows'}:
        return 'Musket'
    return 'Blunderbuss'


def copied_sources(mod: SourceMod) -> set[str]:
    path = mod.public / 'Stats' / 'Generated' / 'ItemCombos.txt'
    if not path.exists():
        return set()
    text = re.sub(rf'{re.escape(BEGIN)}.*?{re.escape(END)}', '', path.read_text(encoding='utf-8-sig'), flags=re.S)
    return set(re.findall(r'data "Object 1" "OBJ_GSL_AssemblyKit"\n(?:.*\n)*?data "Object 2" "([^"]+)"', text))


def audit(mod: SourceMod) -> dict[str, dict[str, str]]:
    text = mod.weapon_file.read_text(encoding='utf-8-sig')
    canonical = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
    if hashlib.sha256(canonical.encode()).hexdigest() != mod.weapon_hash:
        raise ValueError(f'{mod.weapon_file}: source changed; re-audit {mod.tag} weapons before generation.')
    entries = parse_weapons(VANILLA_WEAPONS + (mod.weapon_file,))
    own = set(parse_weapons((mod.weapon_file,)))
    mapped = {item.conversion.source for item in mod.weapons}
    copies = copied_sources(mod)
    excluded = set(mod.excluded)
    if len(mapped) != len(mod.weapons):
        raise ValueError(f'{mod.tag}: duplicate source weapons in manifest.')
    for first, second in ((mapped, copies), (mapped, excluded), (copies, excluded)):
        if first & second:
            raise ValueError(f'{mod.tag}: weapons classified twice: {sorted(first & second)}')
    unclassified = own - mapped - copies - excluded
    unknown = (mapped | copies | excluded) - own
    if unclassified or unknown:
        raise ValueError(f'{mod.tag}: unclassified {sorted(unclassified)}; unknown {sorted(unknown)}')
    resolved = {}
    for item in mod.weapons:
        conversion = item.conversion
        fields = resolve(conversion.source, entries)
        rarity = fields.get('Rarity', 'Common')
        enchantment = re.search(r'WeaponEnchantment\((\d+)\)', fields.get('DefaultBoosts', ''))
        if rarity == 'Legendary':
            raise ValueError(f'{conversion.source}: Legendary weapons are out of scope.')
        if rarity != conversion.rarity:
            raise ValueError(f'{conversion.source}: rarity {rarity} != {conversion.rarity}')
        if enchantment is None or int(enchantment[1]) != conversion.enchantment:
            raise ValueError(f'{conversion.source}: enchantment does not match the source.')
        if firearm_kind(fields) != conversion.kind:
            raise ValueError(f'{conversion.source}: expected {firearm_kind(fields)}, not {conversion.kind}')
        resolved[conversion.source] = fields
    return resolved


def effect_text(kind: str, name: str, parent: str, fields: tuple[tuple[str, str], ...]) -> str:
    lines = [f'new entry "{name}"', f'type "{kind}"']
    if parent:
        lines.append(f'using "{parent}"')
    lines.extend(f'data "{key}" "{value}"' for key, value in fields)
    return '\n'.join(lines) + '\n'


def shot_fields(shot: Shot) -> tuple[tuple[str, str], ...]:
    ammo = f'Gunslinger{shot.kind}Ammo'
    fields = [
        ('DisplayName', f'{localized_handle(shot.name, "name")};1'),
        ('Description', f'{localized_handle(shot.name, "description")};1'),
        ('Icon', f'GSL_Shoot{shot.kind}'),
        ('Cooldown', 'OncePerShortRestPerItem'),
        ('UseCosts', f'ActionPoint:1;{ammo}:1'),
        ('TooltipUseCosts', f'ActionPoint:1;{ammo}:1'),
        ('RequirementConditions',
         f"HasPassive('GSL_{shot.kind}_MainHand',context.Source) and "
         f"not HasStatus('GSL_FIREARM_MAIN_DISABLED',context.Source) and HasActionResource('{ammo}',1,0)"),
        ('SpellSuccess', f'{shot.damage};ExecuteWeaponFunctors(MainHand);{shot.success}'),
        ('TooltipDamageList', shot.tooltip_damage),
    ]
    if shot.save:
        fields.append(('TooltipAttackSave', shot.save))
    if shot.status:
        fields.append(('TooltipStatusApply', shot.status))
    return tuple(fields)


def sound_fields(mod: SourceMod) -> tuple[tuple[str, str], ...]:
    functors = []
    for status, kinds in (('GSL_FIREARM_SHOT_SOUND', {'Flintlock', 'Musket'}),
                          ('GSL_BLUNDERBUSS_SHOT_SOUND', {'Blunderbuss'})):
        spells = [shot.name for shot in mod.shots if shot.kind in kinds]
        if spells:
            condition = ' or '.join(f"SpellId('{spell}')" for spell in spells)
            functors.append(f'IF({condition}):ApplyStatus(SELF,{status},100,0)')
    return (
        ('Icon', 'GSL_ShootFlintlock'),
        ('Properties', 'IsHidden'),
        ('StatsFunctorContext', 'OnCast'),
        ('Conditions', ' or '.join(f"SpellId('{shot.name}')" for shot in mod.shots)),
        ('StatsFunctors', ';'.join(functors)),
    )


def recipe_text(name: str, source: str, parent: str) -> str:
    suffix = name.removeprefix('WPN_GSL_')
    assembly = f'GSL_Assembly_{suffix}'
    disassembly = f'GSL_Disassembly_{suffix}'
    return (
        f'new ItemCombination "{assembly}"\n'
        'data "Type 1" "Object"\ndata "Object 1" "OBJ_GSL_AssemblyKit"\ndata "Transform 1" "Consume"\n'
        f'data "Type 2" "Object"\ndata "Object 2" "{source}"\ndata "Transform 2" "Consume"\n'
        f'data "Type 3" "Object"\ndata "Object 3" "{parent}"\ndata "Transform 3" "Transform"\n\n'
        f'new ItemCombinationResult "{assembly}_1"\ndata "ResultAmount 1" "1"\n'
        f'data "Result 1" "{name}"\ndata "PreviewStatsID" "{name}"\n\n'
        f'new ItemCombination "{disassembly}"\n'
        f'data "Type 1" "Object"\ndata "Object 1" "{name}"\ndata "Transform 1" "Transform"\n'
        'data "Type 2" "Object"\ndata "Object 2" "OBJ_GSL_DisassemblyKit"\ndata "Transform 2" "Consume"\n\n'
        f'new ItemCombinationResult "{disassembly}_1"\ndata "ResultAmount 1" "1"\n'
        f'data "Result 1" "{parent}"\ndata "ResultAmount 2" "1"\n'
        f'data "Result 2" "{source}"\ndata "PreviewStatsID" "{parent}"\n'
    )


def marked(content: str, body: str) -> str:
    return replace_marked(content.rstrip(), BEGIN, END, body).strip('\n')


def render() -> dict[Path, str]:
    main_stats = read_stats([MAIN / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'])
    main_templates = (MAIN / 'RootTemplates' / '_merged.lsx').read_text(encoding='utf-8-sig')
    outputs: dict[Path, str] = {}
    localized: list[str] = []
    for mod in MODS:
        audit(mod)
        shots = {shot.name: shot for shot in mod.shots}
        weapons, recipes, nodes = [], [], []
        for item in mod.weapons:
            conversion = item.conversion
            parent = f'WPN_GSL_{conversion.kind}'
            if conversion.action in shots:
                if shots[conversion.action].kind != conversion.kind:
                    raise ValueError(f'{conversion.source}: {conversion.action} does not match {conversion.kind}')
                conversion = replace(conversion, passives=';'.join(
                    part for part in (conversion.passives, sound_passive(mod)) if part
                ))
            name = stat_name(mod, conversion)
            root = stat_root(name)
            display = localized_handle(name, 'name')
            description = localized_handle(name, 'description')
            fields = conversion_fields(
                conversion, root, main_stats[parent].fields['BoostsOnEquipMainHand'], display, description,
            )
            if item.status_on_equip:
                fields.insert(3, ('StatusOnEquip', item.status_on_equip))
            weapons.append(
                f'new entry "{name}"\ntype "Weapon"\nusing "{parent}"\n'
                + ''.join(f'data "{key}" "{value}"\n' for key, value in fields)
            )
            recipes.append(recipe_text(name, conversion.source, parent))
            nodes.append(template_for(main_templates, parent, conversion, display, description, name, root))
            localized.extend((
                f'        <content contentuid="{display}" version="1">{conversion.label} {conversion.kind}</content>',
                f'        <content contentuid="{description}" version="1">{conversion.behavior}</content>',
            ))
        for shot in mod.shots:
            localized.extend((
                f'        <content contentuid="{localized_handle(shot.name, "name")}" version="1">{shot.label}</content>',
                f'        <content contentuid="{localized_handle(shot.name, "description")}" version="1">'
                f'{shot.description}</content>',
            ))

        data = mod.public / 'Stats' / 'Generated' / 'Data'
        weapon_path = data / 'Weapon.txt'
        combo_path = mod.public / 'Stats' / 'Generated' / 'ItemCombos.txt'
        root_path = mod.public / 'RootTemplates' / '_merged.lsx'
        read = lambda path, default='': path.read_text(encoding='utf-8-sig') if path.exists() else default
        outputs[weapon_path] = marked(read(weapon_path), '\n'.join(weapons)) + '\n'
        outputs[combo_path] = marked(read(combo_path), '\n'.join(recipes)) + '\n'

        templates = read(root_path, EMPTY_TEMPLATES).replace('\r\n', '\n')
        templates = re.sub(
            r'\n' + re.escape(XML_BEGIN) + r'.*?' + re.escape(XML_END), '', templates, flags=re.S,
        )
        block = XML_BEGIN + '\n' + '\n'.join(
            '                ' + line for node in nodes for line in node.splitlines()
        ) + '\n' + XML_END
        if templates.count(TEMPLATES_CLOSE) != 1:
            raise ValueError(f'{root_path}: cannot locate root-template insertion point.')
        outputs[root_path] = templates.replace(TEMPLATES_CLOSE, block + '\n' + TEMPLATES_CLOSE)

        effects = [effect_text(*entry) for entry in mod.effects]
        effects.extend(effect_text('SpellData', shot.name, f'GSL_MainHand_{shot.kind}_attack', shot_fields(shot))
                       for shot in mod.shots)
        if mod.shots:
            effects.append(effect_text('PassiveData', sound_passive(mod), '', sound_fields(mod)))
        if effects:
            outputs[data / EFFECTS_FILE] = '\n'.join(effects)

    # generate_jwl_compat.py always moves its block to the end, so stay just before it.
    localization = re.sub(
        re.escape(LOC_BEGIN) + r'.*?' + re.escape(LOC_END) + r'\n', '',
        LOCALIZATION.read_text(encoding='utf-8'), flags=re.S,
    )
    anchor = JWL_LOC_BEGIN if JWL_LOC_BEGIN in localization else '</contentList>'
    if localization.count(anchor) != 1:
        raise ValueError('Cannot locate localization insertion point.')
    outputs[LOCALIZATION] = localization.replace(
        anchor, LOC_BEGIN + '\n' + '\n'.join(localized) + '\n' + LOC_END + '\n' + anchor,
    )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated files are stale.')
    args = parser.parse_args()
    for path, content in render().items():
        if args.check:
            current = path.read_text(encoding='utf-8-sig').replace('\r\n', '\n') if path.exists() else None
            if current != content:
                raise SystemExit(f'Stale mod weapon conversion resource: {path}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    total = sum(len(mod.weapons) for mod in MODS)
    print(f'Mod weapon conversions: {total}; ' + ('verified.' if args.check else 'generated.'))


if __name__ == '__main__':
    main()
