import unittest
import zipfile
from pathlib import Path
from xg_reference_browser import (load_voice_catalog, load_effect_catalog,
                                  find_voice, search_voices)
from xgworks_reference import ReferenceFormatError


class ReferenceBrowserTests(unittest.TestCase):
    def test_voice_lookup_exact_bank(self):
        rows = [(0, 0, 0, 'Grand'), (0, 41, 0, 'Dream')]
        self.assertEqual(find_voice(rows, 0, 41, 0), 'Dream')
        self.assertIsNone(find_voice(rows, 0, 42, 0))

    def test_search_case_insensitive(self):
        self.assertEqual(search_voices([(0, 41, 0, 'Dream Piano')], '  dReAm '),
                         [(0, 41, 0, 'Dream Piano')])

    def test_reject_unknown_model(self):
        with self.assertRaises(ReferenceFormatError):
            load_voice_catalog('/missing.zip', '../evil')

    def test_reject_unknown_effect(self):
        with self.assertRaises(ReferenceFormatError):
            load_effect_catalog('/missing.zip', '../evil')

    def test_load_from_user_supplied_zip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'original.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('XG4/XGEditor/MU1000_VceList.ini',
                           '[Melody]\nmode=0,128\n0=0,Piano\n[Piano]\n0=0,41,Dream\n')
                z.writestr('XG4/XGEditor/EfMenu.ini',
                           '[REVERB]\n0=0,01,00,Hall\n')
            self.assertEqual(load_voice_catalog(archive), [(0, 41, 0, 'Dream')])
            self.assertEqual(load_effect_catalog(archive, 'REVERB'), [(1, 0, 'Hall')])

    def test_real_xgworks_archive_if_available(self):
        archive = Path('/mnt/data/XG4.ZIP')
        if not archive.exists():
            self.skipTest('Original Yamaha archive not supplied')
        self.assertGreater(len(load_voice_catalog(archive, 'MU1000')), 100)
        self.assertGreater(len(load_effect_catalog(archive, 'VARIATION')), 30)
