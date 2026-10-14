import unittest
from midi import MidiError
from xg_effects import effect_parameter_message
from xg_sysex import decode_parameter_change


class EffectParameterSendTests(unittest.TestCase):
    def test_effect_blocks_and_device(self):
        for effect, offset, address in [('reverb', 3, (2, 1, 3)),
                                        ('chorus', 4, (2, 1, 0x24)),
                                        ('variation', 31, (2, 1, 0x5f))]:
            decoded = decode_parameter_change(effect_parameter_message(effect, offset, [12], 5))
            self.assertEqual((decoded['address'], decoded['data'], decoded['device']),
                             (address, b'\x0c', 5))

    def test_type_requires_two_bytes(self):
        with self.assertRaises(MidiError):
            effect_parameter_message('reverb', 0, [1])

    def test_invalid_inputs(self):
        for args in [('other', 1, [1], 0), ('reverb', True, [1], 0),
                     ('reverb', 32, [1], 0), ('reverb', 1, [128], 0),
                     ('reverb', 1, [True], 0), ('reverb', 1, [], 0),
                     ('reverb', 1, [1], 16)]:
            with self.subTest(args=args), self.assertRaises(MidiError):
                effect_parameter_message(*args)

    def test_type_message_roundtrip(self):
        decoded = decode_parameter_change(effect_parameter_message('chorus', 0, (65, 0)))
        self.assertEqual(decoded['data'], b'\x41\x00')
