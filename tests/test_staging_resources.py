from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

import stage_packages


class StagingResourceTests(unittest.TestCase):
    def test_optional_weapon_modules_stage_separately_and_compile_templates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            name = 'GunslingerClass_Test_WeaponCopiesCompat'
            meta = source / 'Mods' / name / 'meta.lsx'
            template = source / 'Public' / name / 'RootTemplates' / '_merged.lsx'
            stats = source / 'Public' / name / 'Stats' / 'Generated' / 'ItemCombos.txt'
            for path in (meta, template, stats):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('<save/>' if path.suffix == '.lsx' else 'recipes', encoding='utf-8')

            def convert(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                Path(command[command.index('-d') + 1]).write_bytes(b'compiled')
                return subprocess.CompletedProcess(command, 0, '', '')

            staging = root / 'Weapon_Compat_Staging'
            with patch.object(stage_packages, 'source_root', source), \
                    patch.object(stage_packages, 'weapon_compat_staging', staging), \
                    patch.object(stage_packages.subprocess, 'run', side_effect=convert):
                packages, unconverted = stage_packages.stage_weapon_compat(Path('Divine.exe'))
            self.assertEqual(packages, ((staging / name, f'{name}.pak'),))
            self.assertEqual(unconverted, [])
            self.assertTrue((staging / name / meta.relative_to(source)).is_file())
            self.assertEqual((staging / name / stats.relative_to(source)).read_text(), 'recipes')
            self.assertFalse((staging / name / template.relative_to(source)).exists())
            self.assertEqual(
                (staging / name / template.relative_to(source).with_suffix('.lsf')).read_bytes(),
                b'compiled',
            )

    def test_optional_weapon_modules_require_source_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(stage_packages, 'source_root', Path(directory)):
                with self.assertRaisesRegex(SystemExit, 'No weapon-copy compatibility modules'):
                    stage_packages.stage_weapon_compat(None)

    def test_pack_includes_explicit_optional_packages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / 'weapon-compat'
            staging.mkdir()
            (staging / 'resource.lsf').write_bytes(b'compiled')

            def divine(command: Path, *args: str) -> tuple[int, str]:
                if args[1] == 'create-package':
                    Path(args[args.index('-d') + 1]).write_bytes(b'package')
                    return 0, ''
                return 0, 'resource.lsf\tmetadata'

            with patch.object(stage_packages, 'packages', ()), \
                    patch.object(stage_packages, 'packages_dir', root / 'Packages'), \
                    patch.object(stage_packages, 'run_divine', side_effect=divine):
                built = stage_packages.pack(Path('Divine.exe'), ((staging, 'Optional.pak'),))
            self.assertEqual(built, [(root / 'Packages' / 'Optional.pak', 1)])
            self.assertTrue((root / 'Packages' / 'Optional.zip').is_file())

    def test_pack_creates_and_replaces_compressed_archives_for_both_packages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / 'Packages'
            output_dir.mkdir()
            packages = tuple((root / staging.name, name) for staging, name in stage_packages.packages)
            payload = b'package contents' * 100
            for staging, name in packages:
                staging.mkdir()
                (staging / 'resource.lsf').write_bytes(b'compiled')
                (output_dir / Path(name).with_suffix('.zip')).write_bytes(b'stale archive')

            def divine(command: Path, *args: str) -> tuple[int, str]:
                if args[1] == 'create-package':
                    Path(args[args.index('-d') + 1]).write_bytes(payload)
                    return 0, ''
                return 0, 'resource.lsf\tmetadata'

            with patch.object(stage_packages, 'packages', packages), \
                    patch.object(stage_packages, 'packages_dir', output_dir), \
                    patch.object(stage_packages, 'run_divine', side_effect=divine):
                built = stage_packages.pack(Path('Divine.exe'))

            self.assertEqual(built, [(output_dir / name, 1) for _, name in packages])
            for pak, _ in built:
                self.assertEqual(pak.read_bytes(), payload)
                with ZipFile(pak.with_suffix('.zip')) as archive:
                    self.assertEqual(archive.namelist(), [pak.name])
                    self.assertEqual(archive.read(pak.name), payload)
                    self.assertEqual(archive.getinfo(pak.name).compress_type, ZIP_DEFLATED)
                    self.assertLess(archive.getinfo(pak.name).compress_size, len(payload))
                    self.assertIsNone(archive.testzip())

    def test_failed_package_creation_does_not_create_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(stage_packages, 'packages', ((root / 'staging', 'GunslingerClass.pak'),)), \
                    patch.object(stage_packages, 'packages_dir', root / 'Packages'), \
                    patch.object(stage_packages, 'run_divine', return_value=(1, 'packing failed')):
                with self.assertRaisesRegex(SystemExit, 'packing failed'):
                    stage_packages.pack(Path('Divine.exe'))
            self.assertFalse((root / 'Packages' / 'GunslingerClass.zip').exists())

    def test_unverified_package_does_not_create_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / 'staging'
            staging.mkdir()
            (staging / 'resource.lsf').write_bytes(b'compiled')

            def divine(command: Path, *args: str) -> tuple[int, str]:
                if args[1] == 'create-package':
                    Path(args[args.index('-d') + 1]).write_bytes(b'package')
                return 0, ''

            with patch.object(stage_packages, 'packages', ((staging, 'GunslingerClass.pak'),)), \
                    patch.object(stage_packages, 'packages_dir', root / 'Packages'), \
                    patch.object(stage_packages, 'run_divine', side_effect=divine):
                with self.assertRaisesRegex(SystemExit, 'missing staged files'):
                    stage_packages.pack(Path('Divine.exe'))
            self.assertFalse((root / 'Packages' / 'GunslingerClass.zip').exists())

    def test_converts_root_templates_and_content_banks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            resources = (
                stage_packages.content_dir / 'Assets' / 'Firearms' / '_merged.lsx',
                Path('Public/GunslingerClass/RootTemplates/_merged.lsx'),
                stage_packages.tags_dir / 'd4237481-5fe3-4120-9c9c-2c89b72b774d.lsx',
                stage_packages.gui_metadata,
                stage_packages.multi_effect_infos_dir / '1926d069-4ddf-4f80-ae75-897cf666fb16.lsx',
                stage_packages.books_dir / 'GunslingerClass_Books.lsx',
            )
            effect = stage_packages.effects_dir / 'Effects_Banks' / 'GSL_Firearm_Shot_SoundFX.lsx'
            for resource in (*resources, effect):
                source = staging / resource
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text('<save/>', encoding='utf-8')

            def convert(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                Path(command[command.index('-d') + 1]).write_bytes(b'compiled')
                return subprocess.CompletedProcess(command, 0, '', '')

            with patch.object(stage_packages, 'main_staging', staging):
                with patch.object(stage_packages.subprocess, 'run', side_effect=convert):
                    self.assertEqual(stage_packages.stage_content_banks(Path('Divine.exe')), [])
            for resource in resources:
                self.assertFalse((staging / resource).exists())
                self.assertEqual((staging / resource.with_suffix('.lsf')).read_bytes(), b'compiled')
            self.assertFalse((staging / effect).exists())
            self.assertEqual((staging / effect.with_suffix('.lsfx')).read_bytes(), b'compiled')

    def test_without_divine_reports_all_required_conversions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            root_template = staging / 'Public/GunslingerClass/RootTemplates/_merged.lsx'
            gui_metadata = staging / stage_packages.gui_metadata
            root_template.parent.mkdir(parents=True)
            root_template.write_text('<save/>', encoding='utf-8')
            gui_metadata.parent.mkdir(parents=True)
            gui_metadata.write_text('<save/>', encoding='utf-8')
            with patch.object(stage_packages, 'main_staging', staging):
                self.assertEqual(
                    stage_packages.stage_content_banks(None),
                    sorted([root_template, gui_metadata]),
                )
            self.assertTrue(root_template.exists())
            self.assertTrue(gui_metadata.exists())

    def test_failed_conversion_preserves_source_and_stops(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            source = staging / stage_packages.content_dir / '_merged.lsx'
            source.parent.mkdir(parents=True)
            source.write_text('<save/>', encoding='utf-8')
            with patch.object(stage_packages, 'main_staging', staging):
                with patch.object(
                    stage_packages.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 1, '', 'conversion failed'),
                ):
                    with self.assertRaisesRegex(SystemExit, 'conversion failed'):
                        stage_packages.stage_content_banks(Path('Divine.exe'))
            self.assertTrue(source.exists())

    def test_stage_weapon_compat_discovers_every_compat_module(self) -> None:
        packages, unconverted = stage_packages.stage_weapon_compat(None)
        expected_names = {
            'GunslingerClass_ATE_WeaponCopiesCompat.pak',
            'GunslingerClass_CL_WeaponCopiesCompat.pak',
            'GunslingerClass_EO_WeaponCopiesCompat.pak',
            'GunslingerClass_JWL_WeaponCopiesCompat.pak',
        }
        self.assertEqual({name for _, name in packages}, expected_names)
        self.assertTrue(unconverted)

    def test_main_stages_weapon_compat_by_default(self) -> None:
        with patch.object(stage_packages, 'copy_dirs'), \
                patch.object(stage_packages, 'stage_localization', return_value=True), \
                patch.object(stage_packages, 'stage_content_banks', return_value=[]), \
                patch.object(stage_packages, 'stage_weapon_compat', return_value=((), [])) as mock_compat, \
                patch.object(stage_packages, 'print_tree'):
            stage_packages.main(['--skip-validation', '--no-pack'])
            mock_compat.assert_called_once_with(None)

    def test_main_omits_weapon_compat_with_flag(self) -> None:
        with patch.object(stage_packages, 'copy_dirs'), \
                patch.object(stage_packages, 'stage_localization', return_value=True), \
                patch.object(stage_packages, 'stage_content_banks', return_value=[]), \
                patch.object(stage_packages, 'stage_weapon_compat') as mock_compat, \
                patch.object(stage_packages, 'print_tree'):
            stage_packages.main(['--skip-validation', '--no-pack', '--no-weapon-compat'])
            mock_compat.assert_not_called()


if __name__ == '__main__':
    unittest.main()
