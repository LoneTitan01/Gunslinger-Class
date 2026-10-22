import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'GunslingerClass'
RULES = SOURCE / 'Mods/GunslingerClass/ScriptExtender/Lua/GritRules.lua'
TEMPLATES = SOURCE / 'Public/GunslingerClass/RootTemplates/_merged.lsx'
BOOKS = SOURCE / 'Mods/GunslingerClass/Localization/GunslingerClass_Books.lsx'
LOCALIZATION = SOURCE / 'Localization/English/GunslingerClass.xml'


def attributes(node: ET.Element) -> dict[str, ET.Element]:
    return {attribute.get('id'): attribute for attribute in node.findall('attribute')}


class UpgradeNoteTests(unittest.TestCase):
    def test_each_crafted_firearm_gives_a_readable_note(self) -> None:
        rules = RULES.read_text(encoding='utf-8')
        block = re.search(r'Rules\.CraftNotes = \{(.*?)\}', rules, re.S).group(1)
        notes = dict(re.findall(r'(GSL_CRAFT_\w+) = "([0-9a-f-]{36})"', block))
        self.assertEqual(set(notes), {'GSL_CRAFT_FLINTLOCK', 'GSL_CRAFT_MUSKET', 'GSL_CRAFT_BLUNDERBUSS'})

        templates = {
            attributes(node)['MapKey'].get('value'): node
            for node in ET.parse(TEMPLATES).findall(".//node[@id='GameObjects']")
        }
        books = {
            attributes(node)['UUID'].get('value'): attributes(node)['Content'].get('handle')
            for node in ET.parse(BOOKS).findall(".//node[@id='TranslatedStringKey']")
        }
        text = {
            content.get('contentuid'): content.text
            for content in ET.parse(LOCALIZATION).getroot().iter('content')
        }

        for marker, uuid in notes.items():
            kind = marker.removeprefix('GSL_CRAFT_').title()
            with self.subTest(kind=kind):
                node = templates[uuid]
                fields = attributes(node)
                self.assertEqual(fields['Name'].get('value'), f'BOOK_GSL_UpgradeNotes_{kind}')
                self.assertIn(kind, text[fields['DisplayName'].get('handle')])
                self.assertTrue(text[fields['Description'].get('handle')])
                action = node.find(".//node[@id='Action']")
                self.assertEqual(attributes(action)['ActionType'].get('value'), '11')
                book_id = attributes(action.find(".//node[@id='Attributes']"))['BookId'].get('value')
                self.assertIn(book_id, books)
                self.assertIn('Assembly Kit', text[books[book_id]])


if __name__ == '__main__':
    unittest.main()
