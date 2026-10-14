import unittest
from midi import MidiError
from midi_output import MidiPlayer


class LiveMixerTests(unittest.TestCase):
    def test_reject_invalid_controller(self):
        player = MidiPlayer()
        for args in [(-1, 7, 100), (16, 7, 100), (0, 120, 1), (0, 7, 128), (True, 7, 1)]:
            with self.subTest(args=args), self.assertRaises(MidiError):
                player.send_live_cc(*args)

    def test_no_live_output_when_stopped(self):
        player = MidiPlayer()
        self.assertFalse(player.send_live_cc(0, 7, 90))
        self.assertEqual(player.activity_snapshot(), (0,) * 16)

    def test_live_cc_coalesces_latest_value(self):
        player = MidiPlayer()
        class Running:
            def is_alive(self): return True
        player._thread = Running()
        self.assertTrue(player.send_live_cc(2, 7, 20))
        self.assertTrue(player.send_live_cc(2, 7, 100))
        class Message:
            def __init__(self, *args, **kwargs): self.args, self.kwargs = args, kwargs
        class Mido:
            @staticmethod
            def Message(*args, **kwargs): return args, kwargs
        class Port:
            def __init__(self): self.sent = []
            def send(self, message): self.sent.append(message)
        port = Port()
        player._drain_live_cc(port, Mido)
        self.assertEqual(len(port.sent), 1)
        self.assertEqual(port.sent[0][1]['value'], 100)
        self.assertEqual(player._live_cc, {})

    def test_muted_channel_does_not_receive_live_cc(self):
        player = MidiPlayer()
        player._enabled_channels = {0}
        player._live_cc[(1, 7)] = 50
        class Mido:
            @staticmethod
            def Message(*args, **kwargs): return args, kwargs
        class Port:
            def __init__(self): self.sent = []
            def send(self, message): self.sent.append(message)
        port = Port()
        player._drain_live_cc(port, Mido)
        self.assertEqual(port.sent, [])
