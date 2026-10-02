"""Check spell execution wiring before staging; this is not a BG3 engine parser."""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable


@dataclass
class StatEntry:
    name: str
    path: Path
    kind: str = ''
    parent: str = ''
    fields: dict[str, str] = field(default_factory=dict)


def read_stats(paths: Iterable[Path]) -> dict[str, StatEntry]:
    entries: dict[str, StatEntry] = {}
    for path in paths:
        current = None
        for line_number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            line = line.strip()
            match = re.fullmatch(r'new entry "([^"]+)"', line)
            if match:
                name = match[1]
                if name in entries:
                    raise ValueError(f'{path}:{line_number}: duplicate stat entry {name}')
                current = StatEntry(name, path)
                entries[name] = current
            elif current is not None:
                match = re.fullmatch(r'(type|using) "([^"]+)"', line)
                if match:
                    if match[1] == 'type':
                        current.kind = match[2]
                    else:
                        current.parent = match[2]
                else:
                    match = re.fullmatch(r'data "([^"]+)" "(.*)"', line)
                    if match:
                        current.fields[match[1]] = match[2]
    return entries


VANILLA_SPELL_PARENTS = {'Projectile_MainHandAttack', 'Projectile_OffhandAttack'}
LOCAL_REFERENCE = re.compile(r'\b(?:GSL_|(?:Shout|Target|Zone|Projectile|Interrupt)_GSL_)\w+')
UNSUPPORTED_EXPRESSIONS = (
    'IsFirearmAttack()',
    'ProficiencyBonus()',
    'AbilityModifier(Intelligence)',
    'RandomFloat()',
    'CastSpell(',
)


def resolve_spell(
    name: str,
    entries: dict[str, StatEntry],
    external: dict[str, StatEntry],
    visiting: tuple[str, ...] = (),
) -> tuple[dict[str, str], str]:
    if name in visiting:
        raise ValueError(f'Spell inheritance cycle: {" -> ".join((*visiting, name))}')
    entry = entries.get(name)
    if entry is None:
        entry = external.get(name)
    if entry is None:
        if name in VANILLA_SPELL_PARENTS and not external:
            return {}, name
        raise ValueError(f'Missing spell parent: {name}')
    fields: dict[str, str] = {}
    unresolved = ''
    if entry.parent:
        fields, unresolved = resolve_spell(entry.parent, entries, external, (*visiting, name))
    return {**fields, **entry.fields}, unresolved


def validation_errors(
    entries: dict[str, StatEntry],
    external: dict[str, StatEntry],
) -> list[str]:
    errors: list[str] = []
    for entry in entries.values():
        if 'Two-Handed' in entry.fields.get('Weapon Properties', '').split(';'):
            errors.append(f'{entry.name}: invalid weapon property Two-Handed; use Twohanded')
        for key, value in entry.fields.items():
            for expression in UNSUPPORTED_EXPRESSIONS:
                if expression in value:
                    errors.append(f'{entry.name}: unsupported/unbundled expression {expression} in {key}')
            for reference in LOCAL_REFERENCE.findall(value) if key != 'Icon' else ():
                if reference not in entries:
                    errors.append(f'{entry.name}: missing local stat reference {reference} in {key}')
            if key in {'SpellProperties', 'SpellSuccess', 'StatsFunctors'}:
                if 'GainTemporaryHitPoints(' in value:
                    errors.append(f'{entry.name}: temporary HP must use a status with a TemporaryHP boost')
        if entry.kind != 'SpellData':
            continue
        try:
            fields, unresolved = resolve_spell(entry.name, entries, external)
        except ValueError as error:
            errors.append(f'{entry.name}: {error}')
            continue
        flags = fields.get('SpellFlags', '').split(';')
        if 'ImmediateCast' not in flags:
            for key in ('SpellAnimation', 'CastTextEvent'):
                if not fields.get(key) and not unresolved:
                    errors.append(f'{entry.name}: missing effective {key}')
        if fields.get('SpellType') == 'Projectile' and not unresolved:
            if not fields.get('Trajectories'):
                errors.append(f'{entry.name}: missing projectile Trajectories')
        if fields.get('SpellType') == 'Zone':
            if fields.get('Shape') not in {'Square', 'Cone'}:
                errors.append(f'{entry.name}: unsupported or missing zone Shape')
            shape_key = 'Angle' if fields.get('Shape') == 'Cone' else 'Base'
            for key in ('Range', shape_key):
                if not fields.get(key):
                    errors.append(f'{entry.name}: missing zone {key}')
        if entry.name.startswith('Shout_GSL_Reload_'):
            if 'RestoreResource(' not in fields.get('SpellProperties', ''):
                errors.append(f'{entry.name}: reload must restore ammo in SpellProperties')
            if fields.get('SpellSuccess'):
                errors.append(f'{entry.name}: unconditional reload effect left in SpellSuccess')
        if entry.name.startswith('GSL_MainHand_'):
            if 'CanDualWield' in flags or 'CastOffhand[' in ';'.join(
                fields.get(key, '') for key in ('SpellProperties', 'SpellRoll', 'SpellSuccess')
            ):
                errors.append(f'{entry.name}: bundled offhand shot bypasses the separate offhand ammo cost')
    return errors


def validate_stats(public_root: Path, repo_root: Path) -> None:
    entries = read_stats(sorted((public_root / 'Stats' / 'Generated' / 'Data').glob('*.txt')))
    reference = (
        repo_root / 'examples' / 'BG3 Reference' / 'Public' / 'Shared'
        / 'Stats' / 'Generated' / 'Data' / 'Spell_Projectile.txt'
    )
    external = read_stats([reference]) if reference.is_file() else {}
    errors = validation_errors(entries, external)
    if errors:
        raise SystemExit('Stats validation failed:\n' + '\n'.join(errors))
    if not external:
        print(
            'NOTE: vanilla reference is absent; external vanilla animation/trajectory fields '
            'were not checked. Local spell wiring was checked.'
        )
    spells = sum(entry.kind == 'SpellData' for entry in entries.values())
    print(f'Validated {spells} custom spell definitions and local stats references.')


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    validate_stats(root / 'GunslingerClass' / 'Public' / 'GunslingerClass', root)
