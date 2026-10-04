"""Stage (and optionally pack) the files LSLib needs for each PAK.

Main_Staging       -> Packages/GunslingerClass.pak
5e_Compat_Staging  -> Packages/GunslingerClass_5eSpellsCompat.pak

Usage:
    python stage_packages.py [--divine PATH_TO_Divine.exe] [--no-pack] [--skip-validation]

With --divine, localization is converted to .loca, Content banks, root
templates and MultiEffectInfos to .lsf, effect sources to .lsfx, and both staging folders are packed into Packages/*.pak
(unless --no-pack). Without --divine, the localization .xml and resource .lsx files are
staged as-is and must be converted (.loca / .lsf / .lsfx) and packed with LSLib's
ConverterApp.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys

repo_root = Path(__file__).resolve().parent
source_root = repo_root / 'GunslingerClass'
main_staging = repo_root / 'Main_Staging'
compat_staging = repo_root / '5e_Compat_Staging'
packages_dir = repo_root / 'Packages'
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
multi_effect_infos_dir = Path('Public/GunslingerClass/MultiEffectInfos')
effects_dir = Path('Public/GunslingerClass/Assets/Effects')
gui_metadata = Path('Mods/GunslingerClass/GUI/metadata.lsx')


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
    and item root templates to LSF/LSFX."""
    banks = sorted(
        path
        for directory in (content_dir, root_templates_dir, multi_effect_infos_dir, effects_dir)
        for path in (main_staging / directory).rglob('*.lsx')
    )
    gui_metadata_path = main_staging / gui_metadata
    if gui_metadata_path.is_file():
        banks.append(gui_metadata_path)
        banks.sort()
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


def print_tree(folder):
    print(f'\n{folder.name}/')
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            print(f'  {path.relative_to(folder).as_posix()}')


def run_divine(divine, *args):
    result = subprocess.run([str(divine), '-g', 'bg3', *args], capture_output=True, text=True)
    return result.returncode, f'{result.stdout}{result.stderr}'


def pack(divine):
    packages_dir.mkdir(exist_ok=True)
    built = []
    for staging, name in packages:
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
        built.append((pak, len(staged)))
    return built


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--divine', type=Path, help='Path to LSLib Divine.exe; converts files and packs Packages/*.pak')
    parser.add_argument('--no-pack', action='store_true', help='With --divine, convert and stage but do not create .pak files')
    parser.add_argument('--skip-validation', action='store_true', help='Do not run validate_xml.py first')
    args = parser.parse_args()

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

    print_tree(main_staging)
    print_tree(compat_staging)

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
        for pak, count in pack(args.divine):
            print(f'  {pak} ({count} files, {pak.stat().st_size:,} bytes)')
        print('\nInstall: copy both .pak files to %LOCALAPPDATA%\\Larian Studios\\Baldur\'s Gate 3\\Mods '
              'and enable them in the mod manager (compat PAK only if 5e Spells is installed).')
        return

    print(
        '\nPack each folder with ConverterApp > PAK / Packages > Create Package '
        '(Version: V18, Baldur\'s Gate 3 Release, Compression: LZ4):\n'
        f'  {main_staging} -> GunslingerClass.pak\n'
        f'  {compat_staging} -> GunslingerClass_5eSpellsCompat.pak'
    )


if __name__ == '__main__':
    main()
