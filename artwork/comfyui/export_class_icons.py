"""Export a class emblem master PNG to the textures BG3 reads for class icons.

BG3 looks up class icons by the ClassDescription ``Name``:
  Public/Game/GUI/Assets/ClassIcons/<Name>.DDS/.png         300x300 (level-up / character sheet)
  Public/Game/GUI/Assets/ClassIcons/hotbar/<Name>.DDS/.png  140x140 (hotbar class/spellbook button)
  Public/Game/GUI/Assets/Class/ico_class_m_<name>.DDS/.png  72x72 (inventory / party class badge)
The ClassIcons DDS files are DXT5 (BC3) with a full mip chain; the small badge has a single
level. The UI resolves ``.png`` paths, so a PNG copy ships next to every DDS, matching the
Artificer class mod.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import struct
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - depends on the local environment
    Image = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CLASS_ICONS = ROOT / 'GunslingerClass' / 'Public' / 'Game' / 'GUI' / 'Assets' / 'ClassIcons'
SIZES = {'': 300, 'hotbar': 140}
BADGE_FOLDER = 'Class'
BADGE_SIZE = 72


def badge_name(name: str) -> str:
    return f'ico_class_m_{name.lower()}'

DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PIXELFORMAT = 0x1, 0x2, 0x4, 0x1000
DDSD_MIPMAPCOUNT, DDSD_LINEARSIZE = 0x20000, 0x80000
DDPF_FOURCC = 0x4
DDSCAPS_COMPLEX, DDSCAPS_TEXTURE, DDSCAPS_MIPMAP = 0x8, 0x1000, 0x400000


def block_bytes(width: int, height: int) -> int:
    return max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 16


def mip_sizes(size: int) -> list[int]:
    sizes = [size]
    while sizes[-1] > 1:
        sizes.append(max(1, sizes[-1] // 2))
    return sizes


def dxt5_payload(image: 'Image.Image') -> bytes:
    buffer = BytesIO()
    image.save(buffer, 'DDS', pixel_format='DXT5')
    data = buffer.getvalue()
    header = 128 + (20 if data[84:88] == b'DX10' else 0)
    payload = data[header:]
    expected = block_bytes(*image.size)
    if len(payload) != expected:
        raise ValueError(f'Unexpected DXT5 size {len(payload)} for {image.size}; expected {expected}')
    return payload


def dds_header(size: int, mip_count: int) -> bytes:
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE
    pixel_format = struct.pack('<II4s5I', 32, DDPF_FOURCC, b'DXT5', 0, 0, 0, 0, 0)
    caps = struct.pack('<4I', DDSCAPS_COMPLEX | DDSCAPS_TEXTURE | DDSCAPS_MIPMAP, 0, 0, 0)
    header = struct.pack('<7I', 124, flags, size, size, block_bytes(size, size), 0, mip_count)
    return b'DDS ' + header + b'\0' * 44 + pixel_format + caps + b'\0' * 4


def encode_dds(master: 'Image.Image', size: int, mipmaps: bool = True) -> bytes:
    sizes = mip_sizes(size) if mipmaps else [size]
    levels = [dxt5_payload(master.resize((edge, edge), Image.Resampling.LANCZOS)) for edge in sizes]
    return dds_header(size, len(sizes)) + b''.join(levels)


def write_texture(master: 'Image.Image', target: Path, size: int, mipmaps: bool = True) -> list[Path]:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encode_dds(master, size, mipmaps))
    png_target = target.with_suffix('.png')
    master.resize((size, size), Image.Resampling.LANCZOS).save(png_target, format='PNG')
    return [target, png_target]


def export(master_path: Path, name: str, destination: Path, badge: bool = True) -> list[Path]:
    if Image is None:
        raise SystemExit('Pillow is required: python -m pip install --user Pillow')
    with Image.open(master_path) as opened:
        master = opened.convert('RGBA')
    if master.width != master.height:
        raise SystemExit(f'Master must be square, got {master.size}')
    written = []
    for folder, size in SIZES.items():
        written += write_texture(master, destination / folder / f'{name}.DDS', size)
    if badge:
        target = destination.parent / BADGE_FOLDER / f'{badge_name(name)}.DDS'
        written += write_texture(master, target, BADGE_SIZE, mipmaps=False)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', default='Gunslinger', help='ClassDescription Name (also the DDS file name)')
    parser.add_argument('--master', type=Path, help='Square RGBA PNG; defaults to generated/masters/<name>.png')
    parser.add_argument('--destination', type=Path, default=CLASS_ICONS)
    args = parser.parse_args(argv)
    master = args.master or HERE / 'generated' / 'masters' / f'{args.name}.png'
    for path in export(master, args.name, args.destination):
        print(f'Wrote {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
