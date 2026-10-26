"""Generate the audited JWL tiers that already have a Gunslinger conversion."""

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from uuid import UUID, uuid5
import xml.etree.ElementTree as ET

from gun_values import apply_values
from validate_stats import StatEntry, read_stats

ROOT = Path(__file__).resolve().parent
MODULE = 'GunslingerClass_JWL_WeaponCopiesCompat'
NAMESPACE = UUID('51aab621-a09a-4b64-b0c8-76b233931dd7')
JWL_WEAPON_HASH = 'b9bf9dfdd6fc070685b610887f5db2b91d13ed791bf681df16a1e079c5e71caa'
LEGACY_SOURCE = 'JWL_GOB_GoblinKing_Warhammer_UP1'
LEGACY_NAME = 'WPN_GSL_Musket_Faithbreaker_JWL'
LEGACY_ROOT = '803d4d12-1c23-4107-836a-2c783c967a11'
DUPLICATES = {
    'JWL_GOB_DrowCommander_Mace_UP1',
    'JWL_MAG_Ketheric_Warhammer_UP1',
}
SOURCE_TEMPLATE_ALIASES = {
    'JWL_MAG_LC_Umberlee_Cold_Sickle_UP1': (
        'a4fbc198-0cf1-4e4c-96a1-22d3c3d15948',
        'a3c1e1da-7633-49f5-b807-0ae53fbf238e',
    ),
}
PREREQUISITE_BASES = {
    'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar',
    'MAG_PHB_OfSpeed_Scimitar',
    'MAG_BG_BlightBringer_Shortbow',
    'MAG_Bonded_Lethal_Longsword',
    'MAG_Drowelf_SpiderSnare_Longsword',
    'MAG_WYRM_Commander_Longsword',
    'MAG_Orthon_Hellfire_HandCrossbow',
    'MAG_Duergar_Sword_KingsKnife',
    'MAG_LC_BurnOnDamage_Scimitar',
    'MAG_Shadow_Blinding_Bow',
    'GOB_PainPriest_Scourge',
    'MAG_LC_RadiantLight_Rapier',
    'MAG_Blindside_Shortsword',
    'MAG_Throwable_Pike',
    'MAG_Bhaalist_Paralyzing_Dagger',
    'MAG_Finesse_Glaive',
    'MAG_Fire_HeatOnWeaponDamage_Battleaxe',
    'MAG_Vicious_Shortbow',
    'MAG_Vicious_Shortsword',
    'FOR_TrueSoul_Spear',
}


@dataclass(frozen=True)
class Tier:
    source: str
    parent: str
    name: str
    root: str
    fields: dict[str, str]


def records(path: Path, kind: str) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding='utf-8-sig')
    result: dict[str, dict[str, str]] = {}
    for match in re.finditer(
        rf'^new {kind} "([^"]+)"\n(.*?)(?=^new |\Z)', text, re.M | re.S
    ):
        if match[1] in result:
            raise ValueError(f'{path}: duplicate {kind} {match[1]}')
        result[match[1]] = dict(re.findall(r'^data "([^"]+)" "(.*)"$', match[2], re.M))
    return result


def read_jwl(path: Path) -> dict[str, StatEntry]:
    text = path.read_text(encoding='utf-8-sig')
    canonical = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
    if hashlib.sha256(canonical.encode()).hexdigest() != JWL_WEAPON_HASH:
        raise ValueError('JWL Weapon.txt changed; re-audit tier coverage and effects before generation.')
    entries: dict[str, StatEntry] = {}
    duplicates: set[str] = set()
    for match in re.finditer(r'^new entry "([^"]+)"\n(.*?)(?=^new |\Z)', text, re.M | re.S):
        name, body = match.groups()
        if name in entries:
            duplicates.add(name)
        parent = re.search(r'^using "([^"]+)"$', body, re.M)
        if parent is None:
            raise ValueError(f'{name}: missing JWL weapon parent')
        # The pinned source repeats these two IDs; its final declarations are Legendary.
        entries[name] = StatEntry(
            name, path, 'Weapon', parent[1],
            dict(re.findall(r'^data "([^"]+)" "(.*)"$', body, re.M)),
        )
    if duplicates != DUPLICATES:
        raise ValueError(f'Unexpected JWL duplicate declarations: {duplicates}')
    return entries


def effective(name: str, entries: dict[str, StatEntry], seen: tuple[str, ...] = ()) -> dict[str, str]:
    if name in seen:
        raise ValueError(f'Weapon inheritance cycle: {seen + (name,)}')
    if name not in entries:
        raise ValueError(f'Missing weapon stat: {name}')
    entry = entries[name]
    inherited = effective(entry.parent, entries, seen + (name,)) if entry.parent else {}
    return {**inherited, **entry.fields}


def replace(value: str, old: str, new: str) -> str:
    if old not in value:
        raise ValueError(f'Expected effect {old!r} in {value!r}; re-audit firearm parent.')
    return value.replace(old, new)


def overlays(source: str, jwl: dict[str, str], firearm: dict[str, str]) -> dict[str, str]:
    base, number = source[4:].rsplit('_UP', 1)
    fields = {'Rarity': jwl['Rarity']}
    enchantment = re.findall(r'WeaponEnchantment\((\d+)\)', jwl.get('DefaultBoosts', ''))
    if len(enchantment) > 1:
        raise ValueError(f'{source}: ambiguous weapon enchantment')
    boosts = re.sub(r'WeaponEnchantment\(\d+\);?', '', firearm.get('DefaultBoosts', ''))
    boosts = boosts.strip(';')
    if enchantment:
        boosts = f'WeaponEnchantment({enchantment[0]});{boosts}'
    if 'WeaponProperty(Magical)' not in boosts:
        boosts += ';WeaponProperty(Magical)'
    if base == 'MAG_Moonlight_Glaive':
        boosts = replace(boosts, 'WeaponDamage(1d4,Radiant)', 'WeaponDamage(1d6,Radiant)')
    if base == 'MAG_Bonded_Baneful_Shortsword' and number == '2':
        boosts += ';WeaponDamage(1d6,Lightning)'
    if base == 'MAG_Viconia_Mace':
        boosts = replace(boosts, 'AbilityOverrideMinimum(Strength,18)', 'AbilityOverrideMinimum(Strength,20)')
    fields['DefaultBoosts'] = boosts

    passive_replacements = {
        'MAG_Ambusher_Shortsword': (
            'MAG_InitiativeWeapon_Passive', f'MAG_InitiativeWeapon_Passive_{int(number) + 1}',
        ),
        'MAG_OfAwareness_Bow': (
            'MAG_InitiativeBonus_1_Passive', f'MAG_InitiativeBonus_{3 if number == "3" else 2}_Passive',
        ),
        'MAG_PHB_PactKeeper_Quarterstaff': (
            'MAG_ArcaneEnchantment_Lesser_Passive', 'MAG_ArcaneEnchantment_Passive',
        ),
        'MAG_LC_Lorroakan_Quarterstaff': (
            'MAG_ArcaneEnchantment_Lesser_Passive',
            'MAG_ArcaneEnchantment_Passive_LG' if number == '2' else 'MAG_ArcaneEnchantment_Passive',
        ),
        'MAG_BasicEnchanted_Quarterstaff': (
            'MAG_ArcaneEnchantment_Lesser_Passive',
            'MAG_ArcaneEnchantment_Passive_LG' if number == '3' else 'MAG_ArcaneEnchantment_Passive',
        ),
        'MAG_OfSpellPower_Quarterstaff': (
            'MAG_ArcaneEnchantment_Lesser_Passive', 'MAG_ArcaneEnchantment_Passive_LG',
        ),
        'END_Emperor_Staff': (
            'MAG_ArcaneEnchantment_Lesser_Passive',
            'MAG_ArcaneEnchantment_Passive_LG' if number == '2' else 'MAG_ArcaneEnchantment_Passive',
        ),
    }
    passives = firearm['PassivesOnEquip']
    if base in passive_replacements:
        passives = replace(passives, *passive_replacements[base])
    if base == 'MAG_LowHP_IncreaseDamage_Greataxe' and number == '2':
        passives = replace(passives, 'GSL_Blunderbuss_Blooded_Passive', 'GSL_JWL_Blooded_Passive')
    additions = {
        'MAG_LC_Fleshrend_Shortsword': 'GSL_JWL_Obscured_Passive',
        'MAG_WYRM_Farlin_Dagger': 'MAG_Fire_IncreasePiercingDamageToBurning_Passive',
        'MAG_Vicious_Battleaxe': 'MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive',
        'MAG_Vicious_Dagger': 'MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive',
        'MAG_Infernal_Hellbeard_Halberd': 'MAG_AdvantageOnReactionAttack_Passive',
    }
    if base in additions:
        passives += ';' + additions[base]
    if base in {'MAG_Vicious_Shortbow', 'MAG_Vicious_Shortsword'}:
        passives += ';MAG_WYR_Orin_Bhaalist_Dagger_ImprovedCritical_Passive'
    if base == 'MAG_HigherNecromancy_Staff' and number == '2':
        passives += ';MAG_GreaterNecromancyStaff_LifeEssenceHarvest_Passive'
    if passives != firearm['PassivesOnEquip']:
        fields['PassivesOnEquip'] = passives

    if base == 'UND_SwordInStone':
        fields['Boosts'] = replace(
            firearm['Boosts'], 'Skill(Performance, 1)', f'Skill(Performance, {int(number) + 1})',
        )
    if base == 'MAG_BG_Harmonium_Halberd':
        fields['Boosts'] = jwl['Boosts']
    if base == 'MAG_BG_OfEasthaven_Defender_Flail' and number == '2':
        fields['Boosts'] = 'AC(2)'
    if base == 'MAG_BG_Darkfire_Shortbow':
        fields['Boosts'] = firearm['Boosts'] + ';UnlockSpell(Shout_SteadyRanged)'
    if base == 'MAG_TheHunters_Dagger':
        fields['Boosts'] = 'UnlockSpell(Target_MAG_HuntersMark)'
    if base == 'MAG_Harpers_Harmonizing_Rapier' and number == '2':
        fields['Boosts'] = replace(
            firearm['Boosts'], 'Shout_GSL_MellowHarmony_Flintlock', 'Shout_GSL_MellowHarmony_Flintlock_JWL',
        )
    if base == 'MAG_PHB_PactKeeper_Quarterstaff' and number == '2':
        fields['BoostsOnEquipMainHand'] = replace(
            firearm['BoostsOnEquipMainHand'],
            'Shout_MAG_WarlockSpellRestoration', 'Shout_MAG_WarlockSpellRestoration_Double',
        )
    if base == 'MAG_Frost_Offhand_Dagger':
        fields['BoostsOnEquipOffHand'] = replace(
            firearm['BoostsOnEquipOffHand'], 'AC(1)', 'AC(2)',
        )
    if 'WeaponFunctors' in jwl:
        fields['WeaponFunctors'] = jwl['WeaponFunctors']
    return fields


def load_tiers(root: Path = ROOT) -> list[Tier]:
    main = root / 'GunslingerClass' / 'Public' / 'GunslingerClass'
    jwl_public = root / 'examples' / 'JWL Soul Smithing' / 'Public' / 'JWL_SoulSmithing'
    entries: dict[str, StatEntry] = {}
    for folder in ('BG3 Reference', 'BG3 Gustav Reference'):
        for path in sorted((root / 'examples' / folder).rglob('Weapon.txt')):
            if 'Honour' not in path.parts:
                entries.update(read_stats([path]))
    entries.update(read_stats([main / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt']))
    jwl = read_jwl(jwl_public / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt')
    entries.update(jwl)
    recipes = records(main / 'Stats' / 'Generated' / 'ItemCombos.txt', 'ItemCombination')
    results = records(main / 'Stats' / 'Generated' / 'ItemCombos.txt', 'ItemCombinationResult')
    parents: dict[str, str] = {}
    for name, recipe in recipes.items():
        if recipe.get('Object 1') == 'OBJ_GSL_AssemblyKit' and recipe.get('Object 3') in {
            'WPN_GSL_Flintlock', 'WPN_GSL_Musket', 'WPN_GSL_Blunderbuss',
        }:
            base = recipe['Object 2']
            if base in parents:
                raise ValueError(f'Duplicate base conversion for {base}')
            parents[base] = results[name + '_1']['Result 1']
    source_templates = {
        node.find("attribute[@id='MapKey']").get('value')
        for node in ET.parse(jwl_public / 'RootTemplates' / 'jwl-upgraded-gear.lsx').findall(
            ".//node[@id='GameObjects']"
        )
    }
    tiers = []
    for source in sorted(jwl):
        match = re.fullmatch(r'JWL_(.+)_UP(\d+)', source)
        if match is None:
            continue
        base, number = match.groups()
        if base not in parents:
            raise ValueError(f'{source}: missing audited base firearm conversion')
        parent = parents[base]
        name = LEGACY_NAME if source == LEGACY_SOURCE else f'{parent}_JWL_UP{number}'
        template = LEGACY_ROOT if source == LEGACY_SOURCE else str(uuid5(NAMESPACE, name))
        source_fields = effective(source, entries)
        if source in SOURCE_TEMPLATE_ALIASES:
            missing, actual = SOURCE_TEMPLATE_ALIASES[source]
            if source_fields['RootTemplate'] != missing or actual not in source_templates:
                raise ValueError(f'{source}: template alias no longer matches the audited source')
        elif source_fields['RootTemplate'] not in source_templates:
            raise ValueError(f'{source}: missing source template')
        fields = overlays(source, source_fields, effective(parent, entries))
        tiers.append(Tier(source, parent, name, template, fields))
    if (
        not PREREQUISITE_BASES.issubset(parents)
        or len(tiers) != 221
        or len({t.parent for t in tiers}) != 113
    ):
        raise ValueError('Audited coverage changed: expected 113 families / 221 tiers.')
    return tiers


def description(tier: Tier, original: str) -> str:
    base, number = tier.source[4:].rsplit('_UP', 1)
    enchantment = re.findall(r'WeaponEnchantment\((\d+)\)', tier.fields['DefaultBoosts'])
    text = re.sub(
        r'\+\d+ (?=(?:magical )?(?:flintlock|musket|blunderbuss))',
        f'+{enchantment[0]} ' if enchantment else '', original, flags=re.I,
    )
    if base == 'UND_SwordInStone':
        text = replace(text, '+1 Performance', f'+{int(number) + 1} Performance')
    if base == 'MAG_Ambusher_Shortsword':
        text = replace(text, '+1 Initiative', f'+{int(number) + 1} Initiative')
    if base == 'MAG_OfAwareness_Bow':
        text = replace(text, '+1 to Initiative', f'+{3 if number == "3" else 2} to Initiative')
    if base == 'MAG_LowHP_IncreaseDamage_Greataxe' and number == '2':
        text = replace(text, 'half hit points', '70% of your hit points')
    spell_bonuses = {
        'MAG_PHB_PactKeeper_Quarterstaff': 2,
        'MAG_LC_Lorroakan_Quarterstaff': int(number) + 1,
        'MAG_BasicEnchanted_Quarterstaff': 3 if number == '3' else 2,
        'MAG_OfSpellPower_Quarterstaff': 3,
        'END_Emperor_Staff': int(number) + 1,
    }
    if base in spell_bonuses:
        text = replace(text, '+1 to spell attack rolls', f'+{spell_bonuses[base]} to spell attack rolls')
    if base == 'MAG_PHB_PactKeeper_Quarterstaff' and number == '2':
        text = replace(text, 'an expended Warlock spell slot', 'two expended Warlock spell slots')
    if base == 'MAG_Frost_Offhand_Dagger':
        text = replace(text, '+1 AC', '+2 AC')
    if base == 'MAG_BG_OfEasthaven_Defender_Flail' and number == '2':
        text = replace(text, '+1 AC', '+2 AC')
    if base == 'MAG_Viconia_Mace':
        text = replace(text, 'at least 18', 'at least 20')
    if base == 'MAG_Moonlight_Glaive':
        text = replace(text, '1d4 Radiant', '1d6 Radiant')
    if base == 'MAG_BG_Harmonium_Halberd':
        text = replace(text, 'Strength by 2 (up to 23)', f'Strength by 3 (up to {24 if number == "2" else 23})')
        if number == '1':
            text = replace(text, 'Intelligence and Wisdom by 1', 'Intelligence and Wisdom by 2')
    if base == 'MAG_Harpers_Harmonizing_Rapier' and number == '2':
        text = replace(text, 'DC 15', 'DC 12')
        text = replace(text, 'Once per short rest.', 'Once per short rest per item.')
    if base in {'MAG_Vicious_Shortbow', 'MAG_Vicious_Shortsword'}:
        text += ' Your critical-hit threshold is reduced by 1.'
    additions = {
        'MAG_LC_Fleshrend_Shortsword': ' While obscured, you have Advantage on firearm attack rolls.',
        'MAG_WYRM_Farlin_Dagger': ' Hits against Burning targets deal an extra 1d4 Piercing damage.',
        'MAG_BG_Darkfire_Shortbow': ' Grants Brace (Ranged).',
        'MAG_TheHunters_Dagger': " Grants Hunter's Mark.",
        'MAG_Vicious_Battleaxe': ' Your critical-hit threshold is reduced by 1.',
        'MAG_Vicious_Dagger': ' Your critical-hit threshold is reduced by 1.',
        'MAG_Infernal_Hellbeard_Halberd': ' Grants Advantage on reaction attacks.',
    }
    text += additions.get(base, '')
    if base == 'MAG_HigherNecromancy_Staff' and number == '2':
        text += ' Grants Life Essence Harvest.'
    if base == 'MAG_Bonded_Baneful_Shortsword' and number == '2':
        text += ' Deals an extra 1d6 Lightning damage.'
    return text


def render(root: Path = ROOT) -> dict[Path, str]:
    tiers = load_tiers(root)
    main_stats = read_stats([
        root / 'GunslingerClass' / 'Public' / 'GunslingerClass' / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
    ])
    localization_path = root / 'GunslingerClass' / 'Localization' / 'English' / 'GunslingerClass.xml'
    localization = localization_path.read_text(encoding='utf-8')
    localized = {
        node.get('contentuid'): node.text
        for node in ET.fromstring(localization).findall('content')
    }
    localized_tiers: list[str] = []
    weapons: list[str] = []
    recipes: list[str] = []
    templates = ET.Element('save')
    ET.SubElement(templates, 'version', major='4', minor='0', revision='9', build='331')
    children = ET.SubElement(ET.SubElement(ET.SubElement(templates, 'region', id='Templates'), 'node', id='Templates'), 'children')
    for tier in tiers:
        handle = 'h' + str(uuid5(NAMESPACE, tier.name + ':description')).replace('-', 'g')
        original_handle = main_stats[tier.parent].fields['Description'].split(';')[0]
        original_description = localized[original_handle]
        if original_description is None:
            raise ValueError(f'{tier.parent}: missing English description')
        localized_tier = ET.Element('content', contentuid=handle, version='1')
        localized_tier.text = description(tier, original_description)
        localized_tiers.append('        ' + ET.tostring(localized_tier, encoding='unicode'))
        weapons.append(
            f'new entry "{tier.name}"\ntype "Weapon"\nusing "{tier.parent}"\n'
            f'data "RootTemplate" "{tier.root}"\n'
            + ''.join(f'data "{key}" "{value}"\n' for key, value in tier.fields.items())
            + f'data "Description" "{handle};1"\n'
        )
        suffix = tier.name.removeprefix('WPN_GSL_')
        kind = suffix.split('_', 1)[0]
        assembly, disassembly = f'GSL_Assembly_{suffix}', f'GSL_Disassembly_{suffix}'
        recipes.append(
            f'new ItemCombination "{assembly}"\n'
            'data "Type 1" "Object"\ndata "Object 1" "OBJ_GSL_AssemblyKit"\ndata "Transform 1" "Consume"\n'
            f'data "Type 2" "Object"\ndata "Object 2" "{tier.source}"\ndata "Transform 2" "Consume"\n'
            f'data "Type 3" "Object"\ndata "Object 3" "WPN_GSL_{kind}"\ndata "Transform 3" "Transform"\n\n'
            f'new ItemCombinationResult "{assembly}_1"\ndata "ResultAmount 1" "1"\n'
            f'data "Result 1" "{tier.name}"\ndata "PreviewStatsID" "{tier.name}"\n\n'
            f'new ItemCombination "{disassembly}"\n'
            f'data "Type 1" "Object"\ndata "Object 1" "{tier.name}"\ndata "Transform 1" "Transform"\n'
            'data "Type 2" "Object"\ndata "Object 2" "OBJ_GSL_DisassemblyKit"\ndata "Transform 2" "Consume"\n\n'
            f'new ItemCombinationResult "{disassembly}_1"\ndata "ResultAmount 1" "1"\n'
            f'data "Result 1" "WPN_GSL_{kind}"\ndata "ResultAmount 2" "1"\n'
            f'data "Result 2" "{tier.source}"\ndata "PreviewStatsID" "WPN_GSL_{kind}"\n'
        )
        node = ET.SubElement(children, 'node', id='GameObjects')
        for key, value, kind_type in (
            ('MapKey', tier.root, 'FixedString'), ('Name', tier.name, 'LSString'),
            ('ParentTemplateId', main_stats[tier.parent].fields['RootTemplate'], 'FixedString'),
            ('Stats', tier.name, 'FixedString'), ('Type', 'item', 'FixedString'),
        ):
            ET.SubElement(node, 'attribute', id=key, type=kind_type, value=value)
    ET.indent(templates, space='    ')
    public = root / 'GunslingerClass' / 'Public' / MODULE
    aliases = ET.Element('save')
    ET.SubElement(aliases, 'version', major='4', minor='0', revision='9', build='331')
    alias_children = ET.SubElement(
        ET.SubElement(ET.SubElement(aliases, 'region', id='Templates'), 'node', id='Templates'), 'children',
    )
    for source, (missing, actual) in SOURCE_TEMPLATE_ALIASES.items():
        node = ET.SubElement(alias_children, 'node', id='GameObjects')
        for key, value, kind_type in (
            ('MapKey', missing, 'FixedString'), ('Name', source + '_GSL_Alias', 'LSString'),
            ('ParentTemplateId', actual, 'FixedString'), ('Stats', source, 'FixedString'),
            ('Type', 'item', 'FixedString'),
        ):
            ET.SubElement(node, 'attribute', id=key, type=kind_type, value=value)
    ET.indent(aliases, space='    ')
    marker_start = '        <!-- BEGIN GENERATED JWL DESCRIPTIONS -->'
    marker_end = '        <!-- END GENERATED JWL DESCRIPTIONS -->'
    localization = re.sub(
        re.escape(marker_start) + r'.*?' + re.escape(marker_end) + r'\n',
        '', localization, flags=re.S,
    )
    localization = localization.replace(
        '</contentList>',
        marker_start + '\n' + '\n'.join(localized_tiers) + '\n' + marker_end + '\n</contentList>',
    )
    return {
        localization_path: localization,
        public / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt': apply_values('\n'.join(weapons), '\n'.join(recipes)),
        public / 'Stats' / 'Generated' / 'ItemCombos.txt': '\n'.join(recipes),
        public / 'RootTemplates' / '_merged.lsx': (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- Generated by generate_jwl_compat.py. -->\n'
            + ET.tostring(templates, encoding='unicode') + '\n'
        ),
        public / 'RootTemplates' / 'JwlSourceTemplates.lsx': (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- Generated by generate_jwl_compat.py: missing source-template aliases. -->\n'
            + ET.tostring(aliases, encoding='unicode') + '\n'
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated resources differ.')
    args = parser.parse_args()
    for path, content in render().items():
        if args.check:
            if path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Stale JWL compatibility resource: {path}')
        else:
            path.write_text(content, encoding='utf-8', newline='\n')
    print('JWL compatibility: 113 families, 221 tiers; ' + ('verified.' if args.check else 'generated.'))


if __name__ == '__main__':
    main()
