import unittest
from xgworks_reference import parse_reference_ini, effect_choices, ReferenceFormatError


class ReferenceTests(unittest.TestCase):
    def test_cp932_and_sections(self):
        table = parse_reference_ini('[REVERB]\nsize=1\n0=0,01,00,HALL1\n'.encode('cp932'))
        self.assertEqual(effect_choices(table, 'REVERB'), [(1, 0, 'HALL1')])

    def test_comma_in_label(self):
        table = parse_reference_ini('[CHORUS]\n0=0,01,01,Wide, Chorus')
        self.assertEqual(effect_choices(table, 'CHORUS')[0][2], 'Wide,Chorus')

    def test_duplicate_index_rejected(self):
        with self.assertRaises(ReferenceFormatError):
            parse_reference_ini('[REVERB]\n0=a\n0=b')

    def test_reject_outside_section(self):
        with self.assertRaises(ReferenceFormatError):
            parse_reference_ini('0=orphan')

    def test_bad_effect_value(self):
        with self.assertRaises(ReferenceFormatError):
            effect_choices(parse_reference_ini('[REVERB]\n0=0,zz,00,Bad'), 'REVERB')
