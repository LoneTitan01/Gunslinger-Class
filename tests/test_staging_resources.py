from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import stage_packages


class StagingResourceTests(unittest.TestCase):
    def test_converts_root_templates_and_content_banks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            resources = (
                stage_packages.content_dir / 'Assets' / 'Firearms' / '_merged.lsx',
                Path('Public/GunslingerClass/RootTemplates/_merged.lsx'),
            )
            for resource in resources:
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

    def test_without_divine_reports_all_required_conversions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            root_template = staging / 'Public/GunslingerClass/RootTemplates/_merged.lsx'
            root_template.parent.mkdir(parents=True)
            root_template.write_text('<save/>', encoding='utf-8')
            with patch.object(stage_packages, 'main_staging', staging):
                self.assertEqual(stage_packages.stage_content_banks(None), [root_template])
            self.assertTrue(root_template.exists())

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
