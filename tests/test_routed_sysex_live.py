import pytest
from midi import MidiError
from midi_output import MidiPlayer
from xg_sysex import parameter_change


class FakePort:
    def __init__(self):
        self.sent = []
    def send(self, message):
        self.sent.append(message)


class FakeMessage:
    def __init__(self, kind, **kwargs):
        self.kind, self.kwargs = kind, kwargs


class FakeMido:
    Message = FakeMessage


def test_routed_sysex_validation_atomic():
    player = MidiPlayer()
    for payload in (b'', b'\xf0\x43', b'\xf0\xff\xf7', b'\xf0\x43\x00'):
        with pytest.raises(MidiError):
            player.send_routed_sysex('A', payload)
    assert player._routed_sysex == []


def test_routed_sysex_inactive_returns_false():
    player = MidiPlayer()
    assert player.send_routed_sysex('A', parameter_change((8, 0, 11), (90,))) is False


def test_routed_sysex_drains_only_target_port():
    player = MidiPlayer()
    payload = parameter_change((8, 0, 11), (90,))
    player._routed_sysex = [('B', payload)]
    player._routed_enabled = {('A', 0), ('B', 0)}
    a, b = FakePort(), FakePort()
    player._drain_routed({'A': a, 'B': b}, FakeMido)
    assert a.sent == []
    assert len(b.sent) == 1
    assert b.sent[0].kind == 'sysex'
    assert bytes(b.sent[0].kwargs['data']) == payload[1:-1]
    assert player._routed_sysex == []


def test_routed_sysex_queue_rejects_unknown_port(monkeypatch):
    player = MidiPlayer()
    player._routed_active = True
    player._routed_ports = {'A'}
    monkeypatch.setattr(MidiPlayer, 'playing', property(lambda self: True))
    with pytest.raises(MidiError):
        player.send_routed_sysex('B', parameter_change((8, 0, 11), (90,)))
    assert player._routed_sysex == []


def test_routed_sysex_queue_copies_payload(monkeypatch):
    player = MidiPlayer()
    player._routed_active = True
    player._routed_ports = {'A'}
    monkeypatch.setattr(MidiPlayer, 'playing', property(lambda self: True))
    payload = bytearray(parameter_change((8, 0, 11), (90,)))
    assert player.send_routed_sysex('A', payload)
    payload[7] = 5
    assert player._routed_sysex[0][1][7] == 90
