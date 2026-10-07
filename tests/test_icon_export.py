import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'artwork' / 'comfyui'
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location('export_icons', HERE / 'export_icons.py')
assert SPEC is not None and SPEC.loader is not None
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


@unittest.skipIf(exporter.Image is None, 'Pillow is not installed')
class IconExportTests(unittest.TestCase):
    def header(self, data: bytes) -> tuple[int, int, int, int, int]:
        height, width = struct.unpack_from('<II', data, 12)
        return width, height, struct.unpack_from('<I', data, 28)[0], struct.unpack_from('<I', data, 8)[0], struct.unpack_from('<I', data, 108)[0]

    def test_atlas_layout_places_every_key_in_a_unique_cell(self) -> None:
        path, texture, tile, cells = exporter.atlas_layout()
        self.assertEqual(path.name, 'Icons_GunslingerAbilities.dds')
        self.assertEqual((texture, tile, len(cells)), (2048, 64, 83))
        self.assertEqual(len(set(cells.values())), len(cells))
        self.assertEqual(cells['GSL_MercilessShot'], (0, 0))
        self.assertEqual(cells['GSL_Scattershot'], (17 * 64, 64))
        self.assertEqual(cells['GSL_RicochetShot'], (14 * 64, 2 * 64))
        for x, y in cells.values():
            self.assertEqual((x % tile, y % tile), (0, 0))

    def test_encoding_matches_placeholder_dds_layouts(self) -> None:
        image = exporter.Image.new('RGBA', (144, 144), (200, 100, 0, 255))
        with_mips = exporter.encode(image, image)
        self.assertEqual(self.header(with_mips), (144, 144, 8, 0xA1007, 0x401008))
        self.assertEqual(len(with_mips), 128 + sum(exporter.block_bytes(s, s) for s in exporter.mip_sizes(144)))
        flat = exporter.encode(image.resize((48, 48)))
        self.assertEqual(self.header(flat), (48, 48, 0, 0x81007, 0x1000))
        self.assertEqual(len(flat), 128 + exporter.block_bytes(48, 48))

    def test_resource_states_are_visually_distinct(self) -> None:
        glyph = exporter.Image.new('RGBA', (48, 48), (180, 120, 40, 255))
        states = {state: exporter.resource_state(glyph, state).getpixel((24, 24)) for state in exporter.RESOURCE_STATES}
        self.assertEqual(states[''], (180, 120, 40, 255))
        self.assertGreater(sum(states['Highlight'][:3]), sum(states[''][:3]))
        self.assertLess(states['Used'][3], 255)
        self.assertLess(states['Missing'][3], states['Used'][3])
        self.assertEqual(len(set(states.values())), 4)

    def test_resource_exports_include_pngs_and_complete_gui_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / 'generated'
            gui = Path(directory) / 'GUI'
            (generated / 'resource').mkdir(parents=True)
            for name in exporter.RESOURCES:
                exporter.Image.new('RGBA', (48, 48), (180, 120, 40, 255)).save(
                    generated / 'resource' / f'{name}.png'
                )

            with patch.object(exporter, 'RESOURCE_GUI', gui):
                outputs = exporter.export_resources(generated)

            metadata = ET.parse(gui / 'metadata.lsx')
            entries = {
                node.find('attribute[@id="MapKey"]').get('value'): {
                    attribute.get('id'): attribute.get('value')
                    for attribute in node.findall('.//attribute')
                }
                for node in metadata.findall('.//node[@id="Object"]')
            }
            self.assertEqual(len(outputs), 216)
            self.assertEqual(len(entries), 108)
            for surface in ('Assets/CC/icons_resources', 'AssetsLowRes/CC/icons_resources'):
                for name in exporter.RESOURCES:
                    relative = Path(surface) / f'{name}.png'
                    with self.subTest(level_up=relative):
                        self.assertEqual(
                            self.header((gui / relative.with_suffix('.DDS')).read_bytes()),
                            (128, 128, 0, 0x81007, 0x1000),
                        )
                        with exporter.Image.open(gui / relative) as image:
                            self.assertEqual(image.size, (128, 128))
                        entry = entries[relative.as_posix()]
                        self.assertEqual((entry['w'], entry['h'], entry['mipcount']), ('128', '128', '1'))
            for surface in exporter.RESOURCE_SURFACES:
                for name in exporter.RESOURCES:
                    for state in exporter.RESOURCE_STATES:
                        relative = Path(surface, *([state] if state else []))
                        with self.subTest(surface=surface, name=name, state=state):
                            self.assertTrue((gui / relative / f'{name}.DDS').is_file())
                            self.assertTrue((gui / relative / f'{name}.png').is_file())
                            entry = entries[(relative / f'{name}.png').as_posix()]
                            self.assertEqual((entry['w'], entry['h'], entry['mipcount']), ('48', '48', '1'))

    def test_level_up_resource_icons_use_master_artwork(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / 'generated'
            gui = Path(directory) / 'GUI'
            for folder in ('resource', 'masters'):
                (generated / folder).mkdir(parents=True)
            for name in exporter.RESOURCES:
                exporter.Image.new('RGBA', (48, 48), (255, 0, 0, 255)).save(
                    generated / 'resource' / f'{name}.png'
                )
                exporter.Image.new('RGBA', (1024, 1024), (0, 255, 0, 255)).save(
                    generated / 'masters' / f'{name}.png'
                )
            with patch.object(exporter, 'RESOURCE_GUI', gui):
                exporter.export_resources(generated)
            for name in exporter.RESOURCES:
                with exporter.Image.open(gui / 'Assets' / 'CC' / 'icons_resources' / f'{name}.png') as image:
                    self.assertEqual(image.getpixel((64, 64)), (0, 255, 0, 255))


if __name__ == '__main__':
    unittest.main()
