import pytest
from midi import MidiError
from midi_output import MidiPlayer


def player():
    p = MidiPlayer()
    p._routed_active = True
    p._routed_ports = {'A', 'B'}
    p._routed_enabled = {('A', 0), ('B', 0)}
    p._routed_silence = set()
    return p


def test_invalid_routed_cc():
    p = MidiPlayer()
    for args in [('', 0, 7, 80), ('A', 16, 7, 80), ('A', 0, 120, 80), ('A', 0, 7, 128)]:
        with pytest.raises(MidiError):
            p.send_routed_cc(*args)


def test_routed_activity_is_snapshot_copy():
    p = MidiPlayer()
    p._routed_activity = {('A', 0): 3, ('B', 0): 5}
    snapshot = p.routed_activity_snapshot()
    snapshot[('A', 0)] = 99
    assert p.routed_activity_snapshot() == {('A', 0): 3, ('B', 0): 5}


def test_routed_mask_is_port_specific():
    p = MidiPlayer()
    p._routed_enabled = {('A', 0), ('B', 0)}
    p.set_routed_enabled({('B', 0)})
    assert p._routed_silence == {('A', 0)}
    assert p._routed_enabled == {('B', 0)}


def test_invalid_routed_mask_is_atomic():
    p = MidiPlayer()
    p._routed_enabled = {('A', 0)}
    with pytest.raises(MidiError):
        p.set_routed_enabled({('A', True)})
    assert p._routed_enabled == {('A', 0)}


class FakeMessage:
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs

class FakeMidi:
    Message = FakeMessage

class FakePort:
    def __init__(self):
        self.sent = []
    def send(self, message):
        self.sent.append(message)


def test_drain_routes_cc_to_correct_port_only():
    p = MidiPlayer()
    p._routed_enabled = {('A', 0), ('B', 0)}
    p._routed_cc = {('B', 0, 7): 99}
    a, b = FakePort(), FakePort()
    p._drain_routed({'A': a, 'B': b}, FakeMidi)
    assert not a.sent
    assert len(b.sent) == 1 and b.sent[0].kwargs['value'] == 99
