"""Generate prerequisite main-module firearm conversions from JWL source IDs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from uuid import UUID, uuid5
import xml.etree.ElementTree as ET

from validate_stats import read_stats

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'GunslingerClass' / 'Public' / 'GunslingerClass'
NAMESPACE = UUID('dd72b637-3876-4c63-a1e4-273ef6831857')
BEGIN = '# BEGIN GENERATED PREREQUISITE BASE CONVERSIONS'
END = '# END GENERATED PREREQUISITE BASE CONVERSIONS'
XML_BEGIN = '                <!-- BEGIN GENERATED PREREQUISITE BASE CONVERSIONS -->'
XML_END = '                <!-- END GENERATED PREREQUISITE BASE CONVERSIONS -->'


@dataclass(frozen=True)
class Conversion:
    label: str
    source: str
    kind: str
    rarity: str
    enchantment: int
    behavior: str
    boosts: str = ''
    passives: str = ''
    action: str = ''
    spell_boosts: str = ''
    weapon_functors: str = ''

    @property
    def name(self) -> str:
        cleaned = re.sub(r"'s\b", 's', self.label)
        slug = ''.join(part[:1].upper() + part[1:] for part in re.findall(r'[A-Za-z0-9]+', cleaned))
        if self.source == 'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar':
            slug += 'Magical'
        return f'WPN_GSL_{self.kind}_{slug}'

    @property
    def root(self) -> str:
        return str(uuid5(NAMESPACE, self.name))


CONVERSIONS = (
    Conversion(
        'Adamantine Scimitar', 'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar',
        'Flintlock', 'Rare', 1,
        'Shots ignore Piercing resistance and critically hit objects.',
        passives='GSL_Flintlock_AdamantineScimitar_Passive',
    ),
    Conversion(
        'Belm', 'MAG_PHB_OfSpeed_Scimitar', 'Flintlock', 'VeryRare', 2,
        "Grants Belm's bonus attack as a firearm action.",
        action='Target_MAG_PHB_ScimitarOfSpeed_BonusAttack',
    ),
    Conversion(
        'Blightbringer', 'MAG_BG_BlightBringer_Shortbow', 'Flintlock', 'Rare', 1,
        'Against Gnomes and Dwarves, shots gain +1d4 to attack and damage; critical hits can Slow.',
        passives='MAG_BG_BlightBringer_Passive;MAG_BG_SlowedOnCrit_Passive',
    ),
    Conversion(
        'Blood-Bound Blade', 'MAG_Bonded_Lethal_Longsword', 'Musket', 'Rare', 1,
        'Preserves the bonded weapon and proficiency-to-damage effects on firearm attacks.',
        passives='MAG_BoundToBeBonded_Passive;MAG_Bound_ProficiencyToDamage_Passive',
    ),
    Conversion(
        'Cruel Sting', 'MAG_Drowelf_SpiderSnare_Longsword', 'Musket', 'Rare', 1,
        'Preserves the Ensnaring Strike and poison-against-ensnared effects for firearm attacks.',
        passives='MAG_Drowelf_PoisonAgainstEnsnared_Passive',
        spell_boosts="IF(Tagged('PLAYABLE',context.Source)):UnlockSpell(Target_MAG_Drow_EnsnaringStrike)",
    ),
    Conversion(
        "Duke Ravengard's Longsword", 'MAG_WYRM_Commander_Longsword', 'Musket', 'Rare', 1,
        'Preserves the commander effects on firearm attacks.',
        passives='MAG_WYRM_Commander_Longsword_Passive',
        spell_boosts='UnlockSpell(Target_MAG_CommanderStrike);Ability(Charisma, 2)',
    ),
    Conversion(
        'Hellfire Hand Crossbow', 'MAG_Orthon_Hellfire_HandCrossbow', 'Flintlock', 'VeryRare', 2,
        'Preserves the hidden and invisible attack Burning trigger and grants Scorching Ray.',
        passives='MAG_Orthon_Hellfire_Crossbow_Passive',
        action='Projectile_MAG_ScorchingRay_Shot',
    ),
    Conversion(
        'Knife of the Undermountain King', 'MAG_Duergar_Sword_KingsKnife',
        'Flintlock', 'VeryRare', 2,
        'Reduces the critical-hit threshold and grants Advantage against Obscured targets.',
        passives='MAG_TheClover_Rearrangement_Passive;ShadowBlade_Passive;GSL_Base_KnifeUndermountain',
    ),
    Conversion(
        "Kurwin's Cauterizer", 'MAG_LC_BurnOnDamage_Scimitar', 'Flintlock', 'Rare', 1,
        'Preserves its Burning-on-hit behavior on firearm damage.',
        passives='MAG_LC_BurnOnDamage_Scimitar_Passive',
    ),
    Conversion(
        'Least Expected', 'MAG_Shadow_Blinding_Bow', 'Flintlock', 'VeryRare', 2,
        'While Obscured, gains +1d4 to firearm attack rolls and grants Blinding Shot.',
        passives='MAG_Shadow_Blinding_Bow_Passive',
        action='Projectile_MAG_WeaponAction_BlindingShot',
    ),
    Conversion(
        "Loviatar's Scourge", 'GOB_PainPriest_Scourge', 'Blunderbuss', 'Rare', 1,
        'Grants Necrotic resistance, deals 1d6 Necrotic splash damage, and deals 1d6 Necrotic damage to its wielder on a hit.',
        boosts='WeaponDamage(1d6,Necrotic);Resistance(Necrotic,Resistant)',
        passives='GOB_PainPriest_Scourge_Passive;GSL_Base_LoviatarScourge',
    ),
    Conversion(
        'Pelorsun Blade', 'MAG_LC_RadiantLight_Rapier', 'Flintlock', 'VeryRare', 2,
        'Shots deal +1d4 Radiant damage and gain Advantage against Undead.',
        boosts='WeaponDamage(1d4,Radiant)',
        passives='MAG_LC_RadiantLight_Rapier_Passive;GSL_Base_Pelorsun',
    ),
    Conversion(
        'Render of Mind and Body', 'MAG_Blindside_Shortsword', 'Flintlock', 'Rare', 1,
        'When attacking with Advantage, shots deal an additional 1d4 Psychic damage.',
        passives='GSL_Base_RenderMindAndBody',
    ),
    Conversion(
        'Returning Pike', 'MAG_Throwable_Pike', 'Blunderbuss', 'Rare', 1,
        'Replaces throwing behavior with firearm ammunition and reload mechanics.',
    ),
    Conversion(
        'Stillmaker', 'MAG_Bhaalist_Paralyzing_Dagger', 'Flintlock', 'VeryRare', 2,
        'Grants Hold Person as a firearm action.',
        action='Target_MAG_Bhaalist_Hold_Person',
    ),
    Conversion(
        'The Dancing Breeze', 'MAG_Finesse_Glaive', 'Flintlock', 'VeryRare', 2,
        'Replaces Whirlwind Attack with a firearm-compatible 20-foot Whirlwind Shot.',
        action='Zone_GSL_WhirlwindShot_Flintlock',
    ),
    Conversion(
        'Thermodynamo Axe', 'MAG_Fire_HeatOnWeaponDamage_Battleaxe',
        'Musket', 'VeryRare', 2,
        'Generates Heat when firearm damage is dealt.',
        passives='MAG_Fire_HeatOnWeaponDamage_Passive',
    ),
    Conversion(
        'Vicious Shortbow', 'MAG_Vicious_Shortbow', 'Flintlock', 'VeryRare', 2,
        'Critical hits deal 7 additional firearm damage.',
        passives='MAG_Vicious_Weapon_Passive;GSL_Base_ViciousCritical',
    ),
    Conversion(
        'Vicious Shortsword', 'MAG_Vicious_Shortsword', 'Flintlock', 'VeryRare', 2,
        'Critical hits deal 7 additional firearm damage.',
        passives='MAG_Vicious_Weapon_Passive;GSL_Base_ViciousCritical',
    ),
    Conversion(
        'Vision of the Absolute', 'FOR_TrueSoul_Spear', 'Musket', 'Rare', 1,
        'Preserves the multi-eyed-target effect and firearm-safe special action.',
        passives='FOR_TrueSoul_SpearPassive',
        weapon_functors='IF(not SavingThrow(Ability.Dexterity, 11)):ApplyStatus(BLINDED, 100, 2)',
    ),
)

CUSTOM_PASSIVES = {
    'GSL_Base_KnifeUndermountain': {
        'Boosts': (
            'ReduceCriticalAttackThreshold(1);'
            'IF(IsRangedWeaponAttack() and (IsInDarkness() or IsInDimLight())):Advantage(AttackRoll)'
        ),
    },
    'GSL_Base_LoviatarScourge': {
        'StatsFunctors': (
            'IF(IsRangedWeaponAttack() and HasDamageEffectFlag(DamageFlags.Hit)):'
            'DealDamage(SELF,1d6,Necrotic,Magical)'
        ),
    },
    'GSL_Base_Pelorsun': {
        'Boosts': "IF(IsRangedWeaponAttack() and Tagged('UNDEAD')):Advantage(AttackRoll)",
    },
    'GSL_Base_RenderMindAndBody': {
        'Boosts': (
            'IF(IsRangedWeaponAttack() and HasAdvantage() and not HasDisadvantage()):'
            'DamageBonus(1d4,Psychic,false)'
        ),
    },
    'GSL_Base_ViciousCritical': {
        'Boosts': 'IF(IsRangedWeaponAttack() and IsCritical()):DamageBonus(7,Piercing,false)',
    },
}


def localized_handle(name: str, purpose: str) -> str:
    return 'h' + str(uuid5(NAMESPACE, name + ':' + purpose)).replace('-', 'g')


def replace_marked(content: str, begin: str, end: str, body: str) -> str:
    start = content.find(begin)
    finish = content.find(end)
    if (start == -1) != (finish == -1):
        raise ValueError(f'Unpaired generated markers: {begin}')
    block = f'{begin}\n{body}\n{end}'
    if start == -1:
        return content.rstrip() + '\n' + block + '\n'
    if finish < start:
        raise ValueError(f'Invalid generated marker order: {begin}')
    finish += len(end)
    return content[:start] + block + content[finish:]


def remove_marked(content: str, begin: str, end: str) -> str:
    start = content.find(begin)
    finish = content.find(end)
    if (start == -1) != (finish == -1):
        raise ValueError(f'Unpaired generated markers: {begin}')
    if start == -1:
        return content
    if finish < start:
        raise ValueError(f'Invalid generated marker order: {begin}')
    finish += len(end)
    return content[:start] + content[finish:]


def remove_xml_marked(content: str) -> str:
    pattern = re.compile(
        r'\n[ \t]*' + re.escape(XML_BEGIN.strip()) + r'.*?'
        + re.escape(XML_END.strip()) + r'\n',
        re.S,
    )
    return pattern.sub('\n', content)


def template_for(
    source_text: str,
    parent: str,
    conversion: Conversion,
    display_handle: str,
    description_handle: str,
) -> str:
    tree = ET.fromstring(source_text)
    parent_node = next((
        node for node in tree.findall(".//node[@id='GameObjects']")
        if (name := node.find("attribute[@id='Name']")) is not None
        and name.get('value') == parent
    ), None)
    if parent_node is None:
        raise ValueError(f'Missing base root template for {parent}')
    copied = ET.tostring(parent_node, encoding='unicode')
    match = re.search(r'<attribute id="MapKey" type="FixedString" value="([^"]+)"', copied)
    if match is None:
        raise ValueError(f'{parent}: base template has no MapKey')
    copied = copied.replace(match[1], conversion.root, 1)
    copied = re.sub(
        r'(<attribute id="(?:Name|Stats)"[^>]+value=")' + re.escape(parent) + '"',
        rf'\g<1>{conversion.name}"',
        copied,
    )
    copied = re.sub(
        r'(<attribute id="DisplayName" type="TranslatedString" handle=")[^"]+',
        rf'\g<1>{display_handle}',
        copied,
        count=1,
    )
    copied = re.sub(
        r'(<attribute id="Description" type="TranslatedString" handle=")[^"]+',
        rf'\g<1>{description_handle}',
        copied,
        count=1,
    )
    return copied


def render() -> dict[Path, str]:
    weapon_path = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
    combo_path = PUBLIC / 'Stats' / 'Generated' / 'ItemCombos.txt'
    root_path = PUBLIC / 'RootTemplates' / '_merged.lsx'
    localization_path = ROOT / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
    original_weapon_content = weapon_path.read_text(encoding='utf-8-sig')
    original_combo_content = combo_path.read_text(encoding='utf-8-sig')
    original_template_content = root_path.read_text(encoding='utf-8-sig')
    current_stats = read_stats([weapon_path])
    generated_stats = {
        match[1] for match in re.finditer(
            r'^new entry "([^"]+)"',
            original_weapon_content.split(BEGIN, 1)[1].split(END, 1)[0]
            if BEGIN in original_weapon_content and END in original_weapon_content else '',
            re.M,
        )
    }
    existing_stats = set(current_stats) - generated_stats
    existing_combos = combo_path.read_text(encoding='utf-8-sig')
    existing_templates = remove_xml_marked(original_template_content)
    localization = localization_path.read_text(encoding='utf-8')

    names = [conversion.name for conversion in CONVERSIONS]
    sources = [conversion.source for conversion in CONVERSIONS]
    if len(names) != len(set(names)) or len(sources) != len(set(sources)):
        raise ValueError('Conversion stat names and source IDs must be unique.')
    for conversion in CONVERSIONS:
        if conversion.name in existing_stats:
            raise ValueError(f'{conversion.name}: conversion stat already exists.')
        assembly = f'GSL_Assembly_{conversion.name.removeprefix("WPN_GSL_")}'
        disassembly = f'GSL_Disassembly_{conversion.name.removeprefix("WPN_GSL_")}'
        outside_generated = remove_marked(existing_combos, BEGIN, END)
        if re.search(rf'^new ItemCombination(?:Result)? "{re.escape(assembly)}', outside_generated, re.M):
            raise ValueError(f'{assembly}: conversion recipe already exists.')
        if re.search(rf'^new ItemCombination(?:Result)? "{re.escape(disassembly)}', outside_generated, re.M):
            raise ValueError(f'{disassembly}: conversion recipe already exists.')

    weapons: list[str] = []
    recipes: list[str] = []
    nodes: list[str] = []
    localized: list[str] = []
    for conversion in CONVERSIONS:
        parent = f'WPN_GSL_{conversion.kind}'
        display_handle = localized_handle(conversion.name, 'name')
        description_handle = localized_handle(conversion.name, 'description')
        display_name = conversion.label
        if conversion.source == 'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar':
            display_name = 'Adamantine Scimitar (Magical variant)'
        boosts = [f'WeaponEnchantment({conversion.enchantment})', 'WeaponProperty(Magical)']
        if conversion.boosts:
            boosts.append(conversion.boosts)
        fields = [
            ('RootTemplate', conversion.root),
            ('Rarity', conversion.rarity),
            ('DefaultBoosts', ';'.join(boosts)),
            ('DisplayName', f'{display_handle};1'),
            ('Description', f'{description_handle};1'),
        ]
        if conversion.passives:
            fields.insert(3, (
                'PassivesOnEquip',
                ';'.join(('GSL_Firearm_Misfire_Passive', conversion.passives)),
            ))
        if conversion.spell_boosts:
            fields.insert(3, ('Boosts', conversion.spell_boosts))
        if conversion.weapon_functors:
            fields.insert(3, ('WeaponFunctors', conversion.weapon_functors))
        if conversion.action:
            base_actions = current_stats[parent].fields['BoostsOnEquipMainHand']
            fields.insert(3, (
                'BoostsOnEquipMainHand',
                base_actions.replace('UnlockSpell(Shout_GSL_Repair_Main)', '')
                .rstrip(';') + f';UnlockSpell({conversion.action});UnlockSpell(Shout_GSL_Repair_Main)',
            ))
        weapons.append(
            f'new entry "{conversion.name}"\ntype "Weapon"\nusing "{parent}"\n'
            + ''.join(f'data "{key}" "{value}"\n' for key, value in fields)
        )
        suffix = conversion.name.removeprefix('WPN_GSL_')
        assembly = f'GSL_Assembly_{suffix}'
        disassembly = f'GSL_Disassembly_{suffix}'
        recipes.append(
            f'new ItemCombination "{assembly}"\n'
            'data "Type 1" "Object"\ndata "Object 1" "OBJ_GSL_AssemblyKit"\ndata "Transform 1" "Consume"\n'
            f'data "Type 2" "Object"\ndata "Object 2" "{conversion.source}"\ndata "Transform 2" "Consume"\n'
            f'data "Type 3" "Object"\ndata "Object 3" "{parent}"\ndata "Transform 3" "Transform"\n\n'
            f'new ItemCombinationResult "{assembly}_1"\ndata "ResultAmount 1" "1"\n'
            f'data "Result 1" "{conversion.name}"\ndata "PreviewStatsID" "{conversion.name}"\n\n'
            f'new ItemCombination "{disassembly}"\n'
            f'data "Type 1" "Object"\ndata "Object 1" "{conversion.name}"\ndata "Transform 1" "Transform"\n'
            'data "Type 2" "Object"\ndata "Object 2" "OBJ_GSL_DisassemblyKit"\ndata "Transform 2" "Consume"\n\n'
            f'new ItemCombinationResult "{disassembly}_1"\ndata "ResultAmount 1" "1"\n'
            f'data "Result 1" "{parent}"\ndata "ResultAmount 2" "1"\n'
            f'data "Result 2" "{conversion.source}"\ndata "PreviewStatsID" "{parent}"\n'
        )
        nodes.append(template_for(existing_templates, parent, conversion, display_handle, description_handle))
        localized.extend((
            f'        <content contentuid="{display_handle}" version="1">{display_name} {conversion.kind}</content>',
            f'        <content contentuid="{description_handle}" version="1">{conversion.behavior}</content>',
        ))

    weapon_content = replace_marked(original_weapon_content.rstrip(), BEGIN, END, '\n'.join(weapons))
    combo_content = replace_marked(existing_combos.rstrip(), BEGIN, END, '\n'.join(recipes))
    root_content = existing_templates
    root_block = XML_BEGIN + '\n' + '\n'.join('                ' + line for node in nodes for line in node.splitlines()) + '\n' + XML_END
    old_start = root_content.find(XML_BEGIN)
    old_end = root_content.find(XML_END)
    if (old_start == -1) != (old_end == -1):
        raise ValueError('Unpaired generated root-template markers.')
    if old_start != -1:
        root_content = root_content[:old_start] + root_block + root_content[old_end + len(XML_END):]
    else:
        close = '            </children>\n        </node>\n    </region>\n</save>'
        if close not in root_content:
            raise ValueError('Cannot locate main root-template insertion point.')
        root_content = root_content.replace(close, root_block + '\n' + close, 1)

    passive_path = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerBaseConversionPassives.txt'
    passive_content = '\n\n'.join(
        f'new entry "{name}"\ntype "PassiveData"\ndata "Icon" "GSL_ShootFlintlock"\n'
        + ''.join(f'data "{key}" "{value}"\n' for key, value in fields.items())
        for name, fields in CUSTOM_PASSIVES.items()
    )
    passive_content = passive_content.rstrip() + '\n'
    spell_path = PUBLIC / 'Stats' / 'Generated' / 'Data' / 'GunslingerSpells_Conversions.txt'
    whirlwind_name = 'Zone_GSL_WhirlwindShot_Flintlock'
    spell_display = localized_handle(whirlwind_name, 'name')
    spell_description = localized_handle(whirlwind_name, 'description')
    spell_content = (
        f'new entry "{whirlwind_name}"\nusing "Zone_GSL_Scattershot"\n'
        'data "UseCosts" "ActionPoint:1;GunslingerFlintlockAmmo:1"\n'
        'data "Range" "6"\n'
        'data "RequirementConditions" "HasPassive(\'GSL_Flintlock_MainHand\',context.Source) and not HasStatus(\'GSL_FIREARM_MAIN_DISABLED\',context.Source)"\n'
        f'data "DisplayName" "{spell_display};1"\n'
        f'data "Description" "{spell_description};1"\n'
        'data "TooltipUseCosts" "ActionPoint:1;GunslingerFlintlockAmmo:1"\n'
    )
    localized.extend((
        f'        <content contentuid="{spell_display}" version="1">Whirlwind Shot</content>',
        f'        <content contentuid="{spell_description}" version="1">Fire a 20-foot cone shot. Each creature in the area makes a Dexterity saving throw, taking half firearm damage on a failed save and none on a success. Once per short rest.</content>',
    ))

    loc_begin = '        <!-- BEGIN GENERATED PREREQUISITE BASE CONVERSIONS -->'
    loc_end = '        <!-- END GENERATED PREREQUISITE BASE CONVERSIONS -->'
    if loc_begin not in localization:
        content_close = '</contentList>'
        if content_close not in localization:
            raise ValueError('Cannot locate localization insertion point.')
        localization = localization.replace(
            content_close,
            loc_begin + '\n' + '\n'.join(localized) + '\n' + loc_end + '\n' + content_close,
            1,
        )
    else:
        localization = replace_marked(localization, loc_begin, loc_end, '\n'.join(localized))
    return {
        weapon_path: weapon_content,
        combo_path: combo_content,
        root_path: root_content,
        localization_path: localization,
        passive_path: passive_content,
        spell_path: spell_content,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated files are stale.')
    args = parser.parse_args()
    for path, content in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8-sig') != content:
                raise SystemExit(f'Stale base conversion resource: {path}')
        else:
            path.write_text(content, encoding='utf-8', newline='\n')
    print(f'Prerequisite base conversions: {len(CONVERSIONS)}; ' +
          ('verified.' if args.check else 'generated.'))


if __name__ == '__main__':
    main()
