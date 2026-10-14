import unittest
from xg_effect_catalog import effect_type_name, effect_type_choices


class EffectCatalogTests(unittest.TestCase):
    def test_common_names(self):
        self.assertEqual(effect_type_name('reverb', 1, 0), 'Hall 1')
        self.assertEqual(effect_type_name('reverb', 2, 0), 'Room 1')
        self.assertEqual(effect_type_name('chorus', 65, 0), 'Chorus 1')
        self.assertEqual(effect_type_name('variation', 0, 0), 'No Effect')

    def test_unknown_preserved(self):
        self.assertEqual(effect_type_name('variation', 127, 127),
                         'Unknown / device-specific')

    def test_choices_match_labels(self):
        for effect in ('reverb', 'chorus', 'variation'):
            choices = effect_type_choices(effect)
            self.assertTrue(choices)
            self.assertEqual(len(choices), len(set((m, l) for m, l, _ in choices)))
            for msb, lsb, name in choices:
                self.assertEqual(effect_type_name(effect, msb, lsb), name)

    def test_validation(self):
        for effect, msb, lsb in [('other', 0, 0), ('reverb', -1, 0),
                                 ('reverb', 128, 0), ('reverb', True, 0),
                                 ('chorus', 1, 3.5)]:
            with self.assertRaises(ValueError):
                effect_type_name(effect, msb, lsb)
        with self.assertRaises(ValueError):
            effect_type_choices('other')
