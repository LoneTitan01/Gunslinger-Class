from pathlib import Path
import xml.etree.ElementTree as ET

source_root = Path('Source')
xml_files = sorted(source_root.rglob('*.lsx')) + sorted(source_root.rglob('*.xml'))

if not xml_files:
    raise SystemExit('No XML files found under Source/.')

for path in xml_files:
    ET.parse(path)
    print(f'OK {path}')

print(f'Validated {len(xml_files)} XML files.')
