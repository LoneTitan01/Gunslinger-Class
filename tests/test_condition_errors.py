import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'GunslingerClass'
KHN = ROOT / 'Mods/GunslingerClass/Scripts/thoth/helpers/GunslingerConditions.khn'
ERRORS = ROOT / 'Public/GunslingerClass/ErrorDescriptions/ConditionErrors.lsx'
LOCALIZATION = ROOT / 'Localization/English/GunslingerClass.xml'
RULES = ROOT / 'Mods/GunslingerClass/ScriptExtender/Lua/GritRules.lua'
STATS = ROOT / 'Mods/GunslingerClass/ScriptExtender/Lua/FirearmStats.lua'


class ConditionErrorTests(unittest.TestCase):
    """GunslingerFirearmReady names its own failure reasons, which must resolve to text in game."""

    def errors(self):
        tree = ET.parse(ERRORS)
        result = {}
        for node in tree.iter('node'):
            if node.get('id') != 'ConditionErrors':
                continue
            attributes = {a.get('id'): a for a in node.findall('attribute')}
            result[attributes['Identifier'].get('value')] = attributes['DisplayName'].get('handle')
        return result

    def test_every_reason_has_text(self):
        script = KHN.read_text(encoding='utf-8')
        used = set(re.findall(r'ConditionError\("([^"]+)"\)', script))
        self.assertEqual(used, {'GSL_NoAmmo', 'GSL_FirearmBroken'})
        errors = self.errors()
        texts = {c.get('contentuid'): c.text for c in ET.parse(LOCALIZATION).getroot()}
        for identifier in used:
            self.assertIn(identifier, errors)
            self.assertIn(errors[identifier], texts)
        self.assertEqual(texts[errors['GSL_NoAmmo']], 'No Ammo')
        self.assertEqual(texts[errors['GSL_FirearmBroken']], 'Firearm Broken')

    def test_script_covers_every_gun(self):
        script = KHN.read_text(encoding='utf-8')
        kinds = re.findall(r'^\s+(\w+) = \{capacity', RULES.read_text(encoding='utf-8'), re.M)
        self.assertEqual(sorted(kinds), ['Blunderbuss', 'Flintlock', 'Musket'])
        for kind in kinds:
            self.assertIn(f"HasPassive('GSL_{kind}_MainHand', entity)", script)
            self.assertIn(f"ammo = 'Gunslinger{kind}Ammo'", script)
        self.assertIn("HasPassive('GSL_Flintlock_OffHand', entity)", script)
        self.assertIn("ammo = 'GunslingerOffhandFlintlockAmmo'", script)
        self.assertIn("'GSL_FIREARM_ITEM_DESTROYED'", script)

    def test_stats_call_the_script(self):
        stats = STATS.read_text(encoding='utf-8')
        self.assertIn('"GunslingerFirearmReady("', stats)
        self.assertIn('"GunslingerFirearmWorking("', stats)
        script = KHN.read_text(encoding='utf-8')
        self.assertIn('function GunslingerFirearmWorking(offHand)', script)
        self.assertIn('function GunslingerFirearmReady(offHand)', script)


if __name__ == '__main__':
    unittest.main()
