import importlib.util
from pathlib import Path
import struct
import sys
import unittest


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


if __name__ == '__main__':
    unittest.main()
