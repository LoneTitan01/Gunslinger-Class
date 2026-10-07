from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from validate_stats import validate_stats

xml_files_root = Path(__file__).resolve().parent
source_root = xml_files_root / 'GunslingerClass'
main_module_root = source_root / 'Mods' / 'GunslingerClass'
public_root = source_root / 'Public' / 'GunslingerClass'
localization_root = source_root / 'Localization'
english_localization = localization_root / 'English' / 'GunslingerClass.xml'

required_paths = (main_module_root / 'meta.lsx', public_root, english_localization)
missing_paths = [path for path in required_paths if not path.exists()]
if missing_paths:
    missing = ', '.join(str(path.relative_to(xml_files_root)) for path in missing_paths)
    raise SystemExit(f'Missing required mod files or directories: {missing}')

if (main_module_root / 'Localization').exists():
    raise SystemExit(
        'Localization must be under GunslingerClass/Localization/<Language>/, '
        'not inside Mods/GunslingerClass/.'
    )

xml_files = sorted(source_root.rglob('*.lsx')) + sorted(source_root.rglob('*.xml'))

if not xml_files:
    raise SystemExit('No XML files found under GunslingerClass/.')

parsed_files = {}
for path in xml_files:
    parsed_files[path] = ET.parse(path).getroot()
    print(f'OK {path}')

for meta_path in sorted((source_root / 'Mods').glob('*/meta.lsx')):
    module_info = parsed_files[meta_path].find('.//node[@id="ModuleInfo"]')
    if module_info is None:
        raise SystemExit(f'Missing ModuleInfo node: {meta_path}')
    folder = module_info.find('attribute[@id="Folder"]')
    if folder is None or folder.get('value') != meta_path.parent.name:
        raise SystemExit(f'ModuleInfo Folder must equal "{meta_path.parent.name}": {meta_path}')
    for node_id in ('PublishVersion', 'TargetModes'):
        if module_info.find(f'children/node[@id="{node_id}"]') is None:
            raise SystemExit(f'{node_id} must be nested inside ModuleInfo/children: {meta_path}')

gui_root = main_module_root / 'GUI'
gui_metadata_path = gui_root / 'metadata.lsx'
if gui_metadata_path not in parsed_files:
    raise SystemExit(f'Missing GUI texture metadata: {gui_metadata_path}')
gui_entries = {}
for node in parsed_files[gui_metadata_path].findall('.//node[@id="Object"]'):
    key = node.find('attribute[@id="MapKey"]')
    if key is None or not key.get('value'):
        raise SystemExit(f'Missing texture MapKey in {gui_metadata_path}')
    if key.get('value') in gui_entries:
        raise SystemExit(f'Duplicate GUI texture MapKey: {key.get("value")}')
    gui_entries[key.get('value')] = {
        attribute.get('id'): attribute.get('value')
        for attribute in node.findall('children/node[@id="entries"]/attribute')
    }
resource_definitions = parsed_files[public_root / 'ActionResourceDefinitions' / 'ActionResourceDefinitions.lsx']
for definition in resource_definitions.findall('.//node[@id="ActionResourceDefinition"]'):
    hidden = definition.find('attribute[@id="IsHidden"]')
    if hidden is not None and hidden.get('value') == 'true':
        continue
    name = definition.find('attribute[@id="Name"]')
    for quality in ('Assets', 'AssetsLowRes'):
        relative = Path(quality, 'CC', 'icons_resources', f'{name.get("value")}.png')
        values = gui_entries.get(relative.as_posix(), {})
        if (values.get('w'), values.get('h'), values.get('mipcount')) != ('128', '128', '1'):
            raise SystemExit(f'Missing or invalid level-up resource texture metadata: {relative}')
        png = gui_root / relative
        dds = png.with_suffix('.DDS')
        if not png.is_file() or not dds.is_file():
            raise SystemExit(f'Missing level-up resource PNG/DDS: {relative}')
        with dds.open('rb') as image:
            header = image.read(128)
        if len(header) != 128 or header[:4] != b'DDS ' or struct.unpack_from('<II', header, 12) != (128, 128):
            raise SystemExit(f'Invalid level-up resource DDS dimensions: {dds}')

localization_root_element = parsed_files[english_localization]
localized_handles = [
    content.get('contentuid')
    for content in localization_root_element.findall('.//content')
]
if any(handle is None for handle in localized_handles):
    raise SystemExit(f'Localization entries need contentuid attributes: {english_localization}')
if len(localized_handles) != len(set(localized_handles)):
    raise SystemExit(f'Duplicate contentuid values in {english_localization}')

referenced_handles = {
    attribute.get('handle')
    for path, root in parsed_files.items()
    if public_root in path.parents
    for attribute in root.findall('.//attribute[@type="TranslatedString"]')
    if attribute.get('handle')
}
missing_handles = sorted(referenced_handles - set(localized_handles))
if missing_handles:
    raise SystemExit(
        f'Unlocalized TranslatedString handles in {english_localization}: '
        + ', '.join(missing_handles)
    )

print(
    f'Validated {len(xml_files)} XML files, the primary module folder layout, '
    f'and {len(referenced_handles)} localized handles.'
)

validate_stats(public_root, xml_files_root)
