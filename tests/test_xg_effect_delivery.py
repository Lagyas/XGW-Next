import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from midi import MidiError
from xg_effects import effect_parameter_message
from xg_effect_delivery import resolve_effect_port, deliver_effect_messages


def app(playing=False, routes=None):
    a = types.SimpleNamespace()
    a.output_name = types.SimpleNamespace(get=lambda: 'default')
    a.track_routes = {} if routes is None else routes
    a.player = types.SimpleNamespace(playing=playing, send_routed_sysex=MagicMock(return_value=True))
    return a


class EffectDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.wire = effect_parameter_message('reverb', 3, [70], 2)

    def test_selected_track_route(self):
        a = app(routes={1: ('port B', 4)})
        self.assertEqual(resolve_effect_port(a, 1), 'port B')
        self.assertEqual(resolve_effect_port(a, 0), 'default')

    def test_routed_player_does_not_open_port(self):
        a = app(True, {1: ('port B', 4)})
        with patch.dict(sys.modules, {'mido': None}):
            self.assertEqual(deliver_effect_messages(a, 1, [self.wire]), ('port B', 'queued'))
        a.player.send_routed_sysex.assert_called_once_with('port B', self.wire)

    def test_playback_without_routes_rejected(self):
        a = app(True)
        with self.assertRaises(MidiError):
            deliver_effect_messages(a, 0, [self.wire])

    def test_inactive_route_rejected(self):
        a = app(True, {0: ('B', None)})
        a.player.send_routed_sysex.return_value = False
        with self.assertRaises(MidiError):
            deliver_effect_messages(a, 0, [self.wire])

    def test_stopped_uses_mido_output(self):
        a = app(False, {0: ('B', None)})
        mido = MagicMock()
        with patch.dict(sys.modules, {'mido': mido}):
            self.assertEqual(deliver_effect_messages(a, 0, [self.wire]), ('B', 'sent'))
        mido.open_output.assert_called_once_with('B')
        mido.Message.assert_called_once_with('sysex', data=list(self.wire[1:-1]))

    def test_invalid_message_is_atomic_before_output(self):
        a = app()
        with patch.dict(sys.modules, {'mido': MagicMock()}) as modules:
            with self.assertRaises(MidiError):
                deliver_effect_messages(a, 0, [self.wire, b'\xf0\x80\xf7'])
            modules['mido'].open_output.assert_not_called()

    def test_invalid_route_and_index(self):
        a = app(routes={1: ('', None)})
        for idx in (True, -1, 1):
            with self.subTest(idx=idx), self.assertRaises(MidiError):
                resolve_effect_port(a, idx)

    def test_multiple_messages_keep_order(self):
        a = app(True, {0: ('A', None)})
        other = effect_parameter_message('chorus', 4, [23], 2)
        deliver_effect_messages(a, 0, [self.wire, other])
        self.assertEqual(a.player.send_routed_sysex.call_args_list[0].args, ('A', self.wire))
        self.assertEqual(a.player.send_routed_sysex.call_args_list[1].args, ('A', other))
