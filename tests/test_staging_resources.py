from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

import stage_packages


class StagingResourceTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
