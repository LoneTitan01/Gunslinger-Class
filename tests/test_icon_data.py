from pathlib import Path
import struct
import unittest
import xml.etree.ElementTree as ET

from validate_stats import read_stats


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'GunslingerClass'
PUBLIC = SOURCE / 'Public' / 'GunslingerClass'
ASSETS = SOURCE / 'Public' / 'Game' / 'GUI' / 'Assets'
PARENTS = {'Projectile_GSL_FirearmAttack', 'Shout_GSL_ClassAction', 'Shout_GSL_Reload'}


class IconDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = read_stats(sorted((PUBLIC / 'Stats' / 'Generated' / 'Data').glob('*.txt')))
        self.atlas = ET.parse(PUBLIC / 'GUI' / 'Icons_GunslingerAbilities.lsx')
        self.cells = [
            {a.get('id'): a.get('value') for a in node.findall('attribute')}
            for node in self.atlas.findall('.//node[@id="IconUV"]')
        ]

    def assert_dds_size(self, path: Path, width: int, height: int) -> None:
        with path.open('rb') as image:
            header = image.read(128)
        self.assertEqual(header[:4], b'DDS ', str(path))
        self.assertEqual(struct.unpack_from('<II', header, 12), (height, width), str(path))

    def test_all_custom_abilities_passives_and_statuses_have_mapped_icons(self) -> None:
        mapped = {cell['MapKey'] for cell in self.cells}
        referenced = set()
        for entry in self.entries.values():
            if entry.kind not in {'SpellData', 'PassiveData', 'StatusData', 'InterruptData'} or entry.name in PARENTS:
                continue
            icon = entry.fields.get('Icon')
            if not icon or not icon.startswith('GSL_'):
                continue
            with self.subTest(entry=entry.name):
                self.assertIn(icon, mapped)
                referenced.add(icon)
        self.assertEqual(referenced, mapped)

    def test_class_icons_match_vanilla_class_icon_format(self) -> None:
        descriptions = ET.parse(PUBLIC / 'ClassDescriptions' / 'ClassDescriptions.lsx')
        base_class = next(
            node for node in descriptions.findall('.//node[@id="ClassDescription"]')
            if node.find('attribute[@id="ParentGuid"]') is None
        )
        name = base_class.find('attribute[@id="Name"]').get('value')
        self.assertEqual(name, 'Gunslinger')
        subclasses = [
            node.find('attribute[@id="Name"]').get('value')
            for node in descriptions.findall('.//node[@id="ClassDescription"]')
            if node.find('attribute[@id="ParentGuid"]') is not None
        ]
        self.assertEqual(sorted(subclasses), ['ArcaneGunsman', 'Desperado', 'Marksman'])
        textures = []
        for class_name in (name, *subclasses):
            textures += [
                (ASSETS / 'Class' / f'ico_class_m_{class_name.lower()}.DDS', 72, 1),
                (ASSETS / 'ClassIcons' / f'{class_name}.DDS', 300, 9),
                (ASSETS / 'ClassIcons' / 'hotbar' / f'{class_name}.DDS', 140, 8),
            ]
        main_icons = {path.read_bytes() for path, size, _ in textures if size == 300}
        self.assertEqual(len(main_icons), 4, 'each subclass needs its own artwork')
        for path, size, mips in textures:
            with self.subTest(path=path.relative_to(ASSETS)):
                self.assert_dds_size(path, size, size)
                header = path.read_bytes()[:128]
                self.assertEqual(header[84:88], b'DXT5')
                self.assertEqual(struct.unpack_from('<I', header, 28)[0], mips)
                expected = 128
                edge = size
                for _ in range(mips):
                    expected += ((edge + 3) // 4) ** 2 * 16
                    edge = max(1, edge // 2)
                self.assertEqual(path.stat().st_size, expected)
                png = path.with_suffix('.png').read_bytes()
                self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack_from('>II', png, 16), (size, size))

    def test_atlas_cells_are_unique_and_use_expected_slots(self) -> None:
        self.assertEqual(len(self.cells), 81)
        coordinates = set()
        for cell in self.cells:
            column = round(float(cell['U1']) * 32)
            row = round(float(cell['V1']) * 32)
            coordinates.add((column, row))
            with self.subTest(icon=cell['MapKey']):
                self.assertEqual(float(cell['U1']), column / 32)
                self.assertEqual(float(cell['U2']), (column + 1) / 32)
                self.assertEqual(float(cell['V1']), row / 32)
                self.assertEqual(float(cell['V2']), (row + 1) / 32)
                self.assertLess(column, 32)
                self.assertLess(row, 32)
        self.assertEqual(len(coordinates), len(self.cells))

    def test_all_ability_exports_have_required_dimensions(self) -> None:
        for cell in self.cells:
            name = cell['MapKey']
            with self.subTest(icon=name):
                self.assert_dds_size(ASSETS / 'Tooltips' / 'Icons' / f'{name}.DDS', 380, 380)
                self.assert_dds_size(ASSETS / 'ControllerUIIcons' / 'skills_png' / f'{name}.DDS', 144, 144)

    def test_atlas_bank_uuid_path_and_texture_agree(self) -> None:
        atlas_path = {
            a.get('id'): a.get('value')
            for a in self.atlas.findall('.//node[@id="TextureAtlasPath"]/attribute')
        }
        self.assert_dds_size(PUBLIC / atlas_path['Path'], 2048, 2048)
        resources = [
            {a.get('id'): a.get('value') for a in node.findall('attribute')}
            for node in ET.parse(PUBLIC / 'Content' / 'UI' / '[PAK]_UI' / '_merged.lsx').findall('.//node[@id="Resource"]')
        ]
        matches = [resource for resource in resources if resource['ID'] == atlas_path['UUID']]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['SourceFile'], f"Public/GunslingerClass/{atlas_path['Path']}")
        self.assertEqual(matches[0]['Template'], 'Icons_Items')

    def test_resource_icons_match_resource_names_in_all_ui_states(self) -> None:
        resources = ET.parse(PUBLIC / 'ActionResourceDefinitions' / 'ActionResourceDefinitions.lsx')
        names = [a.get('value') for a in resources.findall('.//attribute[@id="Name"]')]
        self.assertEqual(len(names), 6)
        gui = SOURCE / 'Mods' / 'GunslingerClass' / 'GUI'
        metadata = ET.parse(gui / 'metadata.lsx')
        texture_entries = {
            node.find('attribute[@id="MapKey"]').get('value'): {
                attribute.get('id'): attribute.get('value')
                for attribute in node.findall('.//attribute')
            }
            for node in metadata.findall('.//node[@id="Object"]')
        }
        self.assertEqual(len(texture_entries), 108)
        for name in names:
            for quality in ('Assets', 'AssetsLowRes'):
                relative = Path(quality, 'CC', 'icons_resources', f'{name}.png')
                with self.subTest(level_up=relative):
                    self.assert_dds_size(gui / relative.with_suffix('.DDS'), 128, 128)
                    self.assertTrue((gui / relative).is_file())
                    entry = texture_entries[relative.as_posix()]
                    self.assertEqual((entry['w'], entry['h'], entry['mipcount']), ('128', '128', '1'))
            for quality in ('Assets', 'AssetsLowRes'):
                for surface in (('Shared', 'Resources'), ('ActionResources_c', 'Icons', 'Resources')):
                    for state in ('', 'Highlight', 'Used', 'Missing'):
                        with self.subTest(resource=name, quality=quality, surface=surface, state=state):
                            relative = Path(quality, *surface, *([state] if state else []))
                            self.assert_dds_size(gui / relative / f'{name}.DDS', 48, 48)
                            self.assertTrue((gui / relative / f'{name}.png').is_file())
                            entry = texture_entries[(relative / f'{name}.png').as_posix()]
                            self.assertEqual(
                                (entry['w'], entry['h'], entry['mipcount']),
                                ('48', '48', '1'),
                            )


if __name__ == '__main__':
    unittest.main()
