import unittest
from midi import MidiError
from xg_mixer_bridge import channel_for_part
from xg_effects import describe_effect_parameter

class BlockBFinishTests(unittest.TestCase):
    def test_mapped_channel(self):
        self.assertEqual(channel_for_part({2:(7,3), 4:(8,3)},7,3),2)
        self.assertIsNone(channel_for_part({2:(7,3)},7,4))
    def test_ambiguous_mapping_never_guesses(self):
        self.assertIsNone(channel_for_part({2:(7,3), 4:(7,3)},7,3))
    def test_invalid_mapping(self):
        for mapping in ({True:(7,3)}, {2:(7,16)}, {2:(7,)}, []):
            with self.assertRaises(MidiError): channel_for_part(mapping,7,3)
    def test_named_effect_type(self):
        row=(0,0,'reverb',(2,1,0),bytes([1,0]))
        self.assertIn('Hall 1',describe_effect_parameter(row))
    def test_unknown_type_is_not_invented(self):
        row=(0,0,'variation',(2,1,0x40),bytes([127,127]))
        self.assertIn('Unknown',describe_effect_parameter(row))
