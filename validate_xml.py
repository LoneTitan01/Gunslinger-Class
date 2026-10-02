from pathlib import Path
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
