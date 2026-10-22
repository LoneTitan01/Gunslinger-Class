"""Stage (and optionally pack and zip) the files LSLib needs for each PAK.

Main_Staging                                                  -> Packages/GunslingerClass.pak
5e_Compat_Staging                                             -> Packages/GunslingerClass_5eSpellsCompat.pak
Weapon_Compat_Staging/GunslingerClass_ATE_WeaponCopiesCompat  -> Packages/GunslingerClass_ATE_WeaponCopiesCompat.pak
Weapon_Compat_Staging/GunslingerClass_CL_WeaponCopiesCompat   -> Packages/GunslingerClass_CL_WeaponCopiesCompat.pak
Weapon_Compat_Staging/GunslingerClass_EO_WeaponCopiesCompat   -> Packages/GunslingerClass_EO_WeaponCopiesCompat.pak
Weapon_Compat_Staging/GunslingerClass_JWL_WeaponCopiesCompat  -> Packages/GunslingerClass_JWL_WeaponCopiesCompat.pak

Usage:
    python stage_packages.py [--divine PATH_TO_Divine.exe | --no-divine] [--no-pack] [--skip-validation] [--no-weapon-compat]

Compatibility add-ons for Act Two Expansion, Community Library, Encounters
Overhaul, and JWL Soul Smithing are staged and built as well by default. Use --no-weapon-compat to omit them.

By default the bundled examples/LSLib Divine Tool/Tools/Divine.exe is used
(override with --divine): localization is converted to .loca, Content banks, root
templates, tags, MultiEffectInfos and book text to .lsf, effect sources to .lsfx, and all staging folders are packed into Packages/*.pak
and compressed into matching Packages/*.zip archives (unless --no-pack).
Each ZIP contains only its PAK at the archive root; the original PAK is retained.
With --no-divine, the localization .xml and resource .lsx files are
staged as-is and must be converted (.loca / .lsf / .lsfx) and packed with LSLib's
ConverterApp.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

repo_root = Path(__file__).resolve().parent
source_root = repo_root / 'GunslingerClass'
main_staging = repo_root / 'Main_Staging'
compat_staging = repo_root / '5e_Compat_Staging'
weapon_compat_staging = repo_root / 'Weapon_Compat_Staging'
packages_dir = repo_root / 'Packages'
default_divine = repo_root / 'examples' / 'LSLib Divine Tool' / 'Tools' / 'Divine.exe'
packages = (
    (main_staging, 'GunslingerClass.pak'),
    (compat_staging, 'GunslingerClass_5eSpellsCompat.pak'),
)

main_dirs = (
    Path('Mods/GunslingerClass'),
    Path('Public/GunslingerClass'),
    Path('Public/Game'),
    Path('Generated/Public/GunslingerClass'),
)
compat_dirs = (
    Path('Mods/GunslingerClass_5eSpellsCompat'),
    Path('Public/GunslingerClass_5eSpellsCompat'),
)
localization_xml = Path('Localization/English/GunslingerClass.xml')
content_dir = Path('Public/GunslingerClass/Content')
root_templates_dir = Path('Public/GunslingerClass/RootTemplates')
tags_dir = Path('Public/GunslingerClass/Tags')
multi_effect_infos_dir = Path('Public/GunslingerClass/MultiEffectInfos')
effects_dir = Path('Public/GunslingerClass/Assets/Effects')
gui_metadata = Path('Mods/GunslingerClass/GUI/metadata.lsx')
books_dir = Path('Mods/GunslingerClass/Localization')


def fail(message):
    raise SystemExit(f'ERROR: {message}')


def reset(folder):
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()


def copy_dirs(relative_dirs, destination):
    for relative in relative_dirs:
        source = source_root / relative
        if not source.is_dir():
            fail(f'Missing required folder: {source.relative_to(repo_root)}')
        shutil.copytree(source, destination / relative)


def stage_localization(divine):
    source = source_root / localization_xml
    if not source.is_file():
        fail(f'Missing localization file: {source.relative_to(repo_root)}')

    target_dir = main_staging / localization_xml.parent
    target_dir.mkdir(parents=True)

    if divine is None:
        shutil.copy2(source, target_dir / source.name)
        return False

    loca = target_dir / source.with_suffix('.loca').name
    result = subprocess.run(
        [str(divine), '-g', 'bg3', '-a', 'convert-loca', '-s', str(source), '-d', str(loca)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not loca.is_file():
        fail(f'Divine.exe failed to convert localization:\n{result.stdout}{result.stderr}')
    return True


def converted_path(lsx):
    """Effect sources compile to .lsfx; every other resource compiles to .lsf."""
    staged_effects = main_staging / effects_dir
    return lsx.with_suffix('.lsfx' if staged_effects in lsx.parents else '.lsf')


def stage_content_banks(divine):
    """Compile visual/effect banks, MultiEffectInfos, effect sources, GUI texture metadata,
    item root templates, tags and book text to LSF/LSFX."""
    banks = sorted(
        path
        for directory in (content_dir, root_templates_dir, tags_dir, multi_effect_infos_dir, effects_dir, books_dir)
        for path in (main_staging / directory).rglob('*.lsx')
    )
    gui_metadata_path = main_staging / gui_metadata
    if gui_metadata_path.is_file():
        banks.append(gui_metadata_path)
        banks.sort()
    return convert_banks(divine, banks)


def convert_banks(divine, banks):
    if divine is None:
        return banks
    for lsx in banks:
        lsf = converted_path(lsx)
        result = subprocess.run(
            [str(divine), '-g', 'bg3', '-a', 'convert-resource', '-s', str(lsx), '-d', str(lsf)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not lsf.is_file():
            fail(f'Divine.exe failed to convert {lsx.name}:\n{result.stdout}{result.stderr}')
        lsx.unlink()
    return []


def stage_weapon_compat(divine):
    modules = sorted((source_root / 'Mods').glob('*_WeaponCopiesCompat'))
    if not modules:
        fail('No weapon-copy compatibility modules found.')
    reset(weapon_compat_staging)
    staged_packages = []
    unconverted = []
    for module in modules:
        staging = weapon_compat_staging / module.name
        copy_dirs((Path('Mods') / module.name, Path('Public') / module.name), staging)
        banks = sorted((staging / 'Public' / module.name / 'RootTemplates').glob('*.lsx'))
        if not banks:
            fail(f'Missing weapon-copy root templates: {module.name}')
        unconverted.extend(convert_banks(divine, banks))
        staged_packages.append((staging, f'{module.name}.pak'))
    return tuple(staged_packages), unconverted


def print_tree(folder):
    print(f'\n{folder.name}/')
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            print(f'  {path.relative_to(folder).as_posix()}')


def run_divine(divine, *args):
    result = subprocess.run([str(divine), '-g', 'bg3', *args], capture_output=True, text=True)
    return result.returncode, f'{result.stdout}{result.stderr}'


def pack(divine, extra_packages=()):
    packages_dir.mkdir(exist_ok=True)
    built = []
    for staging, name in (*packages, *extra_packages):
        pak = packages_dir / name
        if pak.exists():
            pak.unlink()
        code, output = run_divine(divine, '-a', 'create-package', '-c', 'lz4', '-s', str(staging), '-d', str(pak))
        if code != 0 or not pak.is_file():
            fail(f'Divine.exe failed to create {name}:\n{output}')

        staged = {p.relative_to(staging).as_posix().lower() for p in staging.rglob('*') if p.is_file()}
        code, output = run_divine(divine, '-a', 'list-package', '-s', str(pak))
        packed = {line.split('\t')[0].strip().replace('\\', '/').lower() for line in output.splitlines() if line.strip()}
        missing = staged - packed
        if code != 0 or missing:
            fail(f'{name} is missing staged files: {sorted(missing) or output}')
        with ZipFile(pak.with_suffix('.zip'), 'w', compression=ZIP_DEFLATED) as archive:
            archive.write(pak, arcname=pak.name)
        built.append((pak, len(staged)))
    return built


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    divine_group = parser.add_mutually_exclusive_group()
    divine_group.add_argument(
        '--divine',
        type=Path,
        default=default_divine,
        help=f'Path to LSLib Divine.exe; converts files and creates Packages/*.pak and *.zip (default: {default_divine.relative_to(repo_root)})',
    )
    divine_group.add_argument(
        '--no-divine',
        dest='divine',
        action='store_const',
        const=None,
        help='Do not use Divine.exe; stage unconverted files for manual conversion and packing',
    )
    parser.add_argument('--no-pack', action='store_true', help='Convert and stage with Divine.exe but do not create .pak or .zip files')
    parser.add_argument('--skip-validation', action='store_true', help='Do not run validate_xml.py first')
    parser.add_argument(
        '--weapon-compat',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Build weapon-copy compatibility PAKs (enabled by default; use --no-weapon-compat to skip)',
    )
    args = parser.parse_args(argv)

    if args.divine is not None and not args.divine.is_file():
        fail(f'Divine.exe not found: {args.divine}')

    if not args.skip_validation:
        result = subprocess.run([sys.executable, str(repo_root / 'validate_xml.py')], capture_output=True, text=True)
        if result.returncode != 0:
            fail(f'validate_xml.py failed; fix errors before staging:\n{result.stdout}{result.stderr}')
        print('validate_xml.py passed.')

    reset(main_staging)
    reset(compat_staging)

    copy_dirs(main_dirs, main_staging)
    converted = stage_localization(args.divine)
    unconverted_banks = stage_content_banks(args.divine)
    copy_dirs(compat_dirs, compat_staging)
    extra_packages = ()
    if args.weapon_compat:
        extra_packages, unconverted_weapons = stage_weapon_compat(args.divine)
        unconverted_banks.extend(unconverted_weapons)

    print_tree(main_staging)
    print_tree(compat_staging)
    for staging, _ in extra_packages:
        print_tree(staging)

    if not converted:
        staged_xml = main_staging / localization_xml
        print(
            '\nNEXT: convert localization before packing Main_Staging:\n'
            f'  LSLib ConverterApp > Localization tab\n'
            f'    Input:  {staged_xml}\n'
            f'    Output: {staged_xml.with_suffix(".loca")}\n'
            f'  Then delete {staged_xml.name} from Main_Staging.'
        )
    if unconverted_banks:
        print('\nNEXT: convert these resources to the listed .lsf/.lsfx '
              '(ConverterApp > LSX / LSB / LSF / LSJ), then delete the .lsx:')
        for lsx in unconverted_banks:
            print(f'  {lsx} -> {converted_path(lsx).name}')

    if args.divine is not None and not args.no_pack:
        print('\nPackages:')
        for pak, count in pack(args.divine, extra_packages):
            print(f'  {pak} ({count} files, {pak.stat().st_size:,} bytes)')
            archive = pak.with_suffix('.zip')
            print(f'  {archive} ({archive.stat().st_size:,} bytes)')
        print('\nInstall: copy the .pak files to %LOCALAPPDATA%\\Larian Studios\\Baldur\'s Gate 3\\Mods '
              'and enable them in the mod manager (compat PAK only if 5e Spells is installed).')
        if extra_packages:
            print('Weapon-copy add-ons: enable only with their required source mods, '
                  'after GunslingerClass and those mods in the load order.')
        return

    print(
        '\nPack each folder with ConverterApp > PAK / Packages > Create Package '
        '(Version: V18, Baldur\'s Gate 3 Release, Compression: LZ4):\n'
        f'  {main_staging} -> GunslingerClass.pak\n'
        f'  {compat_staging} -> GunslingerClass_5eSpellsCompat.pak'
    )
    for staging, name in extra_packages:
        print(f'  {staging} -> {name}')


if __name__ == '__main__':
    main()
