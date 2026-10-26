"""Price magical firearms at their source item's value plus half the base firearm's value.

Every magical firearm has a disassembly recipe that returns its base firearm and the
original item. Those two items are priced with the game's gold-value rules, and the
firearm gets a ValueOverride of original + base / 2.

Run directly to update every module's Weapon.txt; the generators also call
apply_values() so regenerated files keep the prices.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from validate_stats import StatEntry

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / 'examples'
SOURCE_PUBLIC = ROOT / 'GunslingerClass' / 'Public'
GOLD_VALUES = EXAMPLES / 'BG3 Reference' / 'Public' / 'Shared' / 'Levelmaps' / 'GoldValues.lsx'
MODULES = (
    'GunslingerClass',
    'GunslingerClass_ATE_WeaponCopiesCompat',
    'GunslingerClass_CL_WeaponCopiesCompat',
    'GunslingerClass_EO_WeaponCopiesCompat',
    'GunslingerClass_JWL_WeaponCopiesCompat',
)
# Later folders override earlier ones, matching game load order.
SOURCE_FOLDERS = (
    EXAMPLES / 'BG3 Reference' / 'Public' / 'Shared',
    EXAMPLES / 'BG3 Reference' / 'Public' / 'SharedDev',
    EXAMPLES / 'BG3 Gustav Reference' / 'Public' / 'Gustav',
    EXAMPLES / 'BG3 Gustav Reference' / 'Public' / 'GustavDev',
    EXAMPLES / 'Act Two Expansion' / 'Public' / 'ActTwoExpansion_41ec643a-e2ad-e69d-52c2-920a6f4a98ad',
    EXAMPLES / 'Encounters Overhaul' / 'Public' / 'EncountersOverhaul',
    EXAMPLES / 'JWL Soul Smithing' / 'Public' / 'JWL_SoulSmithing',
)
STAT_FILES = ('Weapon.txt', 'Armor.txt', 'Object.txt')
KITS = {'OBJ_GSL_AssemblyKit', 'OBJ_GSL_DisassemblyKit'}
# Recipes that name a root template instead of its stats entry.
TEMPLATE_STATS = {'WPN_HUM_Scimitar_Adamantine_A': 'MAG_MeleeDebuff_AttackDebuff1_OnDamage_Scimitar'}


@lru_cache(maxsize=1)
def gold_tables() -> dict[str, dict]:
    tables = {}
    for node in ET.parse(GOLD_VALUES).getroot().iter('node'):
        if node.get('id') != 'GoldValue':
            continue
        attrs = {a.get('id'): a.get('value') for a in node.findall('attribute')}
        tables[attrs['UUID']] = {
            'parent': attrs.get('ParentUUID'),
            'scale': float(attrs.get('ParentScale', '1')),
            'levels': {int(k[5:]): int(v) for k, v in attrs.items() if re.fullmatch(r'Level\d+', k)},
        }
    return tables


def table_value(uuid: str, level: int) -> float:
    table = gold_tables()[uuid]
    if table['levels']:
        # Tables like Tools only define Level1; use the highest level at or below the request.
        defined = [lv for lv in table['levels'] if lv <= level] or [min(table['levels'])]
        return table['levels'][max(defined)]
    return table_value(table['parent'], level) * table['scale']


def load_stats(extra: dict[str, StatEntry] | None = None) -> dict[str, StatEntry]:
    """Source items plus every firearm module, with later definitions winning."""
    stats: dict[str, StatEntry] = {}
    for folder in SOURCE_FOLDERS:
        for name in STAT_FILES:
            path = folder / 'Stats' / 'Generated' / 'Data' / name
            if path.exists():
                stats.update(read_stats_text(path.read_text(encoding="utf-8-sig")))
    for module in MODULES:
        path = SOURCE_PUBLIC / module / 'Stats' / 'Generated' / 'Data' / 'Weapon.txt'
        if path.exists():
            stats.update(read_stats_text(path.read_text(encoding="utf-8-sig")))
    stats.update(extra or {})
    return stats


def field(name: str, key: str, stats: dict[str, StatEntry]) -> str | None:
    while name in stats:
        entry = stats[name]
        if key in entry.fields:
            return entry.fields[key]
        name = entry.parent
    return None


def item_value(name: str, stats: dict[str, StatEntry]) -> int:
    """Gold value of a stat entry, following the game's ValueOverride / gold-table rules."""
    if name not in stats:
        raise KeyError(name)
    override = int(field(name, 'ValueOverride', stats) or 0)
    if override > 0:
        return override
    uuid = field(name, 'ValueUUID', stats)
    if not uuid:
        return 0
    value = table_value(uuid, int(field(name, 'ValueLevel', stats) or 1))
    value *= float(field(name, 'ValueScale', stats) or 1)
    # ValueRounding N rounds to the nearest 10^N gold.
    step = 10 ** int(field(name, 'ValueRounding', stats) or 0)
    return int(round(value / step) * step) if value else 0


def disassembly_sources(combo_text: str) -> dict[str, tuple[str, str]]:
    """Map each firearm to (base firearm, original item) from its disassembly recipe."""
    firearms: dict[str, str] = {}
    results: dict[str, list[str]] = {}
    for block in re.split(r'\n(?=new )', combo_text.replace('\r\n', '\n')):
        header = re.match(r'new (ItemCombination|ItemCombinationResult) "([^"]+)"', block.strip())
        if not header or not header[2].startswith('GSL_Disassembly_'):
            continue
        fields = dict(re.findall(r'data "([^"]+)" "([^"]*)"', block))
        if header[1] == 'ItemCombination':
            firearms[header[2]] = next(
                v for k, v in sorted(fields.items()) if k.startswith('Object ') and v not in KITS
            )
        else:
            results[header[2].rsplit('_', 1)[0]] = [
                fields[k] for k in sorted((k for k in fields if k.startswith('Result ')), key=lambda k: int(k.split()[1]))
            ]
    sources = {}
    for recipe, firearm in firearms.items():
        base, original = results[recipe][:2]
        sources[firearm] = (base, TEMPLATE_STATS.get(original, original))
    return sources


def set_value(weapon_text: str, name: str, value: int) -> str:
    pattern = re.compile(r'(^new entry "' + re.escape(name) + r'"\n)(.*?)(?=^new entry |\Z)', re.M | re.S)
    match = pattern.search(weapon_text)
    if not match:
        raise ValueError(f'{name}: entry not found')
    body = re.sub(r'^data "ValueOverride" "[^"]*"\n', '', match[2], flags=re.M)
    line = f'data "ValueOverride" "{value}"\n'
    for anchor in (r'^data "Rarity" "[^"]*"\n', r'^data "RootTemplate" "[^"]*"\n', r'^using "[^"]*"\n'):
        found = re.search(anchor, body, re.M)
        if found:
            body = body[:found.end()] + line + body[found.end():]
            break
    else:
        body = line + body
    return weapon_text[:match.start()] + match[1] + body + weapon_text[match.end():]


def firearm_values(weapon_text: str, combo_text: str, stats: dict[str, StatEntry] | None = None) -> dict[str, int]:
    """New ValueOverride per firearm defined in weapon_text.

    - Converted from a weapon: original weapon's value + half the base firearm's value.
    - Upgrade chain (built from a material on top of an earlier firearm): 1.5x that earlier firearm.
    Firearms whose original is missing from the reference data keep their inherited value.
    """
    defined = read_stats_text(weapon_text)
    stats = load_stats(defined) if stats is None else {**stats, **defined}
    rules = {}
    for firearm, (base, original) in disassembly_sources(combo_text).items():
        if firearm not in defined or not firearm.startswith('WPN_GSL_'):
            continue
        if original in stats and stats[original].kind == 'Weapon':
            rules[firearm] = ('magic', base, original)
        elif is_material(original, stats) and base.startswith('WPN_GSL_'):
            rules[firearm] = ('upgrade', base, original)

    resolved: dict[str, int] = {}

    def value(name: str) -> int:
        if name not in rules:
            return item_value(name, stats)
        if name not in resolved:
            kind, base, original = rules[name]
            if kind == 'magic':
                resolved[name] = item_value(original, stats) + half_up(value(base) / 2)
            else:
                resolved[name] = half_up(value(base) * 1.5)
        return resolved[name]

    values = {}
    for firearm in rules:
        new = value(firearm)
        # Thin copies (e.g. EO duplicates) already inherit the right value from their parent.
        parent = defined[firearm].parent
        if 'ValueOverride' not in defined[firearm].fields and parent in stats and value(parent) == new:
            continue
        values[firearm] = new
    return values


def is_material(name: str, stats: dict[str, StatEntry]) -> bool:
    """Upgrade materials are non-weapon items (gems, metals, loot), not missing magic weapons."""
    if name in stats:
        return stats[name].kind != 'Weapon'
    return name.startswith(('LOOT_', 'OBJ_'))


def half_up(number: float) -> int:
    return int(number + 0.5)


def apply_values(weapon_text: str, combo_text: str, stats: dict[str, StatEntry] | None = None) -> str:
    newline = '\r\n' if '\r\n' in weapon_text else '\n'
    text = weapon_text.replace('\r\n', '\n')
    for firearm, value in firearm_values(text, combo_text, stats).items():
        text = set_value(text, firearm, value)
    return text.replace('\n', newline)


def read_stats_text(text: str) -> dict[str, StatEntry]:
    entries: dict[str, StatEntry] = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        match = re.fullmatch(r'new entry "([^"]+)"', line)
        if match:
            current = entries[match[1]] = StatEntry(match[1], Path('<memory>'))
        elif current is not None:
            match = re.fullmatch(r'(type|using) "([^"]+)"', line)
            if match:
                if match[1] == 'type':
                    current.kind = match[2]
                else:
                    current.parent = match[2]
            elif match := re.fullmatch(r'data "([^"]+)" "(.*)"', line):
                current.fields[match[1]] = match[2]
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if any firearm value is stale.')
    parser.add_argument('--report', action='store_true', help='Print each firearm and its value breakdown.')
    args = parser.parse_args()
    total = 0
    for module in MODULES:
        generated = SOURCE_PUBLIC / module / 'Stats' / 'Generated'
        weapon_path = generated / 'Data' / 'Weapon.txt'
        combo_path = generated / 'ItemCombos.txt'
        if not (weapon_path.exists() and combo_path.exists()):
            continue
        current = weapon_path.read_text(encoding='utf-8-sig')
        combos = combo_path.read_text(encoding='utf-8-sig')
        stats = load_stats()
        values = firearm_values(current, combos, stats)
        if args.report:
            for firearm, (base, original) in disassembly_sources(combos).items():
                if firearm not in values:
                    print(f'{firearm}: unchanged (inherits its parent value or original is unknown)')
                elif original in stats and stats[original].kind == 'Weapon':
                    print(f'{firearm}: {original}={item_value(original, stats)} + half of {base} -> {values[firearm]}')
                else:
                    print(f'{firearm}: 1.5x {base} (upgraded with {original}) -> {values[firearm]}')
        content = apply_values(current, combos, stats)
        total += len(values)
        if args.check:
            if content != current:
                raise SystemExit(f'Stale firearm values: {weapon_path}')
        elif content != current:
            weapon_path.write_text(content, encoding='utf-8', newline='')
    print(f'Firearm values: {total}; ' + ('verified.' if args.check else 'applied.'))


if __name__ == '__main__':
    main()
