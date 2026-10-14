import unittest
import zipfile
from pathlib import Path
from xgworks_reference import (parse_model_voice_ini, hierarchical_effect_choices,
                               parse_reference_ini, ReferenceFormatError)


class ModelCatalogTests(unittest.TestCase):
    def test_model_voice_bank_mapping(self):
        sample = '[Melody]\nmode=0,128\n0=0,Piano\n[Piano]\n0=0,41,Dream\n1=1,0,Bright Piano\n'
        self.assertEqual(parse_model_voice_ini(sample), [(0, 41, 0, 'Dream'), (0, 0, 1, 'Bright Piano')])

    def test_voice_rejects_bad_bank(self):
        with self.assertRaises(ReferenceFormatError):
            parse_model_voice_ini('[Melody]\nmode=0,128\n0=0,Piano\n[Piano]\n0=0,200,Invalid')

    def test_voice_missing_section(self):
        with self.assertRaises(ReferenceFormatError):
            parse_model_voice_ini('[Melody]\nmode=0,128\n0=0,Missing')

    def test_nested_effect(self):
        ini = '[VARIATION]\n0=1,DELAY,*Delay\n1=0,40,00,THRU\n[DELAY]\n0=0,05,01,Cross Delay\n'
        self.assertEqual(hierarchical_effect_choices(parse_reference_ini(ini), 'VARIATION'),
                         [(5, 1, 'Delay / Cross Delay'), (64, 0, 'THRU')])

    def test_effect_cycle_rejected(self):
        ini = '[VARIATION]\n0=1,DELAY,*Delay\n[DELAY]\n0=1,VARIATION,*Loop\n'
        with self.assertRaises(ReferenceFormatError):
            hierarchical_effect_choices(parse_reference_ini(ini), 'VARIATION')

    def test_original_reference_if_available(self):
        archive = Path('/mnt/data/XG4.ZIP')
        if not archive.exists():
            self.skipTest('Original XGworks archive not supplied')
        with zipfile.ZipFile(archive) as z:
            voices = parse_model_voice_ini(z.read('XG4/XGEditor/MU1000_VceList.ini'))
            effects = hierarchical_effect_choices(parse_reference_ini(z.read('XG4/XGEditor/EfMenu.ini')), 'VARIATION')
        self.assertIn((0, 41, 0, 'Dream'), voices)
        self.assertGreater(len(voices), 100)
        self.assertGreater(len(effects), 30)
