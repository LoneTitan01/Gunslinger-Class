"""Convert the generated ComfyUI icon PNGs into the DDS files the mod packages.

Reads artwork/comfyui/generated/{masters,tooltip,controller,hotbar,resource}
and writes, matching the layouts of the existing placeholder files:

* Ability icons (every MapKey in GUI/Icons_GunslingerAbilities.lsx):
    Public/Game/GUI/Assets/Tooltips/Icons/<Key>.DDS                 380x380 DXT5, full mips
    Public/Game/GUI/Assets/ControllerUIIcons/skills_png/<Key>.DDS   144x144 DXT5, full mips
* The hotbar atlas, built from a transparent canvas with each 64x64 tile placed
  at the cell given by its UVs:
    Public/GunslingerClass/Assets/Textures/Icons/Icons_GunslingerAbilities.dds  2048x2048 DXT5
* Action resources (Available/Highlight/Used/Missing in four GUI surfaces):
    Mods/GunslingerClass/GUI/<surface>/[<State>/]<Resource>.DDS     48x48 DXT5
* Character creation / level-up resources:
    Mods/GunslingerClass/GUI/{Assets,AssetsLowRes}/CC/icons_resources/<Resource>.DDS
    128x128 DXT5, with PNG counterparts and GUI texture metadata.
* Class emblems through export_class_icons.py.

Atlas UVs and the TextureBank are not modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

from export_class_icons import (
    DDPF_FOURCC, DDSCAPS_COMPLEX, DDSCAPS_MIPMAP, DDSCAPS_TEXTURE, DDSD_CAPS, DDSD_HEIGHT,
    DDSD_LINEARSIZE, DDSD_MIPMAPCOUNT, DDSD_PIXELFORMAT, DDSD_WIDTH, Image, block_bytes,
    dxt5_payload, export as export_class_icon, mip_sizes,
)

try:
    from PIL import ImageEnhance
except ImportError:  # pragma: no cover - depends on the local environment
    ImageEnhance = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GENERATED = HERE / 'generated'
MOD = ROOT / 'GunslingerClass'
GAME_GUI = MOD / 'Public' / 'Game' / 'GUI' / 'Assets'
ICON_MAP = MOD / 'Public' / 'GunslingerClass' / 'GUI' / 'Icons_GunslingerAbilities.lsx'
RESOURCE_GUI = MOD / 'Mods' / 'GunslingerClass' / 'GUI'
CLASS_ICONS = GAME_GUI / 'ClassIcons'

ABILITY_EXPORTS = {
    'tooltip': (GAME_GUI / 'Tooltips' / 'Icons', 380),
    'controller': (GAME_GUI / 'ControllerUIIcons' / 'skills_png', 144),
}
RESOURCES = (
    'GunslingerGrit', 'GunslingerFlintlockAmmo', 'GunslingerOffhandFlintlockAmmo',
    'GunslingerBlunderbussAmmo', 'GunslingerMusketAmmo', 'GunslingerCraftCharges',
)
RESOURCE_SURFACES = (
    'Assets/Shared/Resources',
    'Assets/ActionResources_c/Icons/Resources',
    'AssetsLowRes/Shared/Resources',
    'AssetsLowRes/ActionResources_c/Icons/Resources',
)
RESOURCE_STATES = ('', 'Highlight', 'Used', 'Missing')
RESOURCE_SIZE = 48
LEVEL_UP_RESOURCE_SURFACES = ('Assets/CC/icons_resources', 'AssetsLowRes/CC/icons_resources')
LEVEL_UP_RESOURCE_SIZE = 128
CLASSES = ('Gunslinger',)
SUBCLASSES = ('Marksman', 'Desperado', 'ArcaneGunsman')


def dds_header(width: int, height: int, mip_count: int) -> bytes:
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
    caps = DDSCAPS_TEXTURE
    if mip_count > 1:
        flags |= DDSD_MIPMAPCOUNT
        caps |= DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
    else:
        mip_count = 0
    pixel_format = struct.pack('<II4s5I', 32, DDPF_FOURCC, b'DXT5', 0, 0, 0, 0, 0)
    header = struct.pack('<7I', 124, flags, height, width, block_bytes(width, height), 0, mip_count)
    return b'DDS ' + header + b'\0' * 44 + pixel_format + struct.pack('<4I', caps, 0, 0, 0) + b'\0' * 4


def encode(top: 'Image.Image', mip_source: 'Image.Image | None' = None) -> bytes:
    """DXT5-encode ``top``; with ``mip_source`` also add a full chain resized from it."""
    if mip_source is None:
        return dds_header(top.width, top.height, 1) + dxt5_payload(top)
    sizes = mip_sizes(top.width)
    levels = [dxt5_payload(top)] + [
        dxt5_payload(mip_source.resize((edge, edge), Image.Resampling.LANCZOS)) for edge in sizes[1:]
    ]
    return dds_header(top.width, top.height, len(sizes)) + b''.join(levels)


def load(path: Path, size: int, master: Path | None = None) -> 'Image.Image':
    """Load a generated PNG at ``size``, falling back to resizing the master."""
    source = path if path.exists() else master
    if source is None or not source.exists():
        raise FileNotFoundError(f'Missing generated artwork: {path}')
    with Image.open(source) as opened:
        image = opened.convert('RGBA')
    if image.size != (size, size):
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image


def atlas_layout(icon_map: Path = ICON_MAP) -> tuple[Path, int, int, dict[str, tuple[int, int]]]:
    """Return atlas path, texture size, tile size and key -> pixel origin from the UV list."""
    root = ET.parse(icon_map).getroot()

    def attributes(node: ET.Element) -> dict[str, str]:
        return {a.get('id'): a.get('value') for a in node.findall('attribute')}

    nodes = {n.get('id'): n for n in root.iter('node')}
    tile = int(attributes(nodes['TextureAtlasIconSize'])['Width'])
    texture = int(attributes(nodes['TextureAtlasTextureSize'])['Width'])
    path = MOD / 'Public' / 'GunslingerClass' / attributes(nodes['TextureAtlasPath'])['Path']
    cells = {}
    for node in root.iter('node'):
        if node.get('id') == 'IconUV':
            values = attributes(node)
            cells[values['MapKey']] = (round(float(values['U1']) * texture), round(float(values['V1']) * texture))
    return path, texture, tile, cells


def resource_state(image: 'Image.Image', state: str) -> 'Image.Image':
    """Derive the Highlight/Used/Missing appearance from the available glyph."""
    if not state:
        return image
    rgb, alpha = image.convert('RGB'), image.getchannel('A')
    if state == 'Highlight':
        rgb = ImageEnhance.Brightness(ImageEnhance.Color(rgb).enhance(1.25)).enhance(1.35)
    elif state == 'Used':
        rgb = ImageEnhance.Brightness(ImageEnhance.Color(rgb).enhance(0.45)).enhance(0.5)
        alpha = alpha.point(lambda a: a * 70 // 100)
    elif state == 'Missing':
        grey = rgb.convert('L').point(lambda v: v * 40 // 100)
        rgb = Image.merge('RGB', (grey.point(lambda v: min(255, v + 25)), grey, grey))
        alpha = alpha.point(lambda a: a * 45 // 100)
    else:
        raise ValueError(f'Unknown resource state {state!r}')
    result = rgb.convert('RGBA')
    result.putalpha(alpha)
    return result


def export_abilities(generated: Path) -> list[Path]:
    atlas_path, texture, tile, cells = atlas_layout()
    atlas = Image.new('RGBA', (texture, texture), (0, 0, 0, 0))
    written = []
    for key, (x, y) in cells.items():
        master_path = generated / 'masters' / f'{key}.png'
        master = None
        if master_path.exists():
            with Image.open(master_path) as opened:
                master = opened.convert('RGBA')
        for group, (folder, size) in ABILITY_EXPORTS.items():
            top = load(generated / group / f'{key}.png', size, master_path)
            target = folder / f'{key}.DDS'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encode(top, master or top))
            written.append(target)
        atlas.alpha_composite(load(generated / 'hotbar' / f'{key}.png', tile, master_path), (x, y))
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_path.write_bytes(encode(atlas))
    written.append(atlas_path)
    return written


def export_resources(generated: Path) -> list[Path]:
    written = []
    metadata_entries = []

    def write_icon(relative: Path, image: 'Image.Image') -> None:
        target = RESOURCE_GUI / relative.with_suffix('.DDS')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encode(image))
        png_target = target.with_suffix('.png')
        image.save(png_target, format='PNG')
        written.extend((target, png_target))
        metadata_entries.append((relative, image.width, image.height))

    for name in RESOURCES:
        glyph = load(generated / 'resource' / f'{name}.png', RESOURCE_SIZE, generated / 'masters' / f'{name}.png')
        for state in RESOURCE_STATES:
            image = resource_state(glyph, state)
            for surface in RESOURCE_SURFACES:
                relative = Path(surface, *([state] if state else []))
                write_icon(relative / f'{name}.png', image)

        level_up = load(generated / 'masters' / f'{name}.png', LEVEL_UP_RESOURCE_SIZE,
                        generated / 'resource' / f'{name}.png')
        for surface in LEVEL_UP_RESOURCE_SURFACES:
            write_icon(Path(surface) / f'{name}.png', level_up)

    save_gui_metadata(RESOURCE_GUI / 'metadata.lsx', metadata_entries)
    return written


def save_gui_metadata(path: Path, entries: list[tuple[Path, int, int]]) -> None:
    root = ET.Element('save')
    ET.SubElement(root, 'version', {
        'major': '4', 'minor': '7', 'revision': '1', 'build': '3',
        'lslib_meta': 'v1,bswap_guids,lsf_keys_adjacency',
    })
    region = ET.SubElement(root, 'region', {'id': 'config'})
    config = ET.SubElement(region, 'node', {'id': 'config'})
    children = ET.SubElement(config, 'children')
    entry_list = ET.SubElement(children, 'node', {'id': 'entries'})
    entry_children = ET.SubElement(entry_list, 'children')
    for key, width, height in entries:
        entry = ET.SubElement(entry_children, 'node', {'id': 'Object'})
        ET.SubElement(entry, 'attribute', {
            'id': 'MapKey', 'type': 'FixedString', 'value': key.as_posix(),
        })
        entry_data = ET.SubElement(entry, 'children')
        values = ET.SubElement(entry_data, 'node', {'id': 'entries'})
        for attribute, value in (('h', height), ('mipcount', 1), ('w', width)):
            ET.SubElement(values, 'attribute', {
                'id': attribute, 'type': 'int8' if attribute == 'mipcount' else 'int16',
                'value': str(value),
            })

    ET.indent(root, space='    ')
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def export_classes(generated: Path) -> list[Path]:
    written = []
    # Each subclass needs its own icons and inventory badge: once a subclass is chosen,
    # the UI resolves the class icon by the subclass Name.
    for name in (*CLASSES, *SUBCLASSES):
        written += export_class_icon(generated / 'masters' / f'{name}.png', name, CLASS_ICONS)
    return written


GROUPS = {'abilities': export_abilities, 'resources': export_resources, 'classes': export_classes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--group', choices=[*GROUPS, 'all'], default='all')
    parser.add_argument('--generated', type=Path, default=GENERATED, help='ComfyUI output root')
    args = parser.parse_args(argv)
    if Image is None:
        raise SystemExit('Pillow is required: python -m pip install --user Pillow')
    groups = GROUPS if args.group == 'all' else {args.group: GROUPS[args.group]}
    for group, exporter in groups.items():
        paths = exporter(args.generated)
        print(f'{group}: wrote {len(paths)} files')
    return 0


if __name__ == '__main__':
    sys.exit(main())
