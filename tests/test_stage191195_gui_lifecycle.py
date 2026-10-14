"""Headless integration regressions for Tk mixer lifecycle (no display required)."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
from midi_mixer import MidiMixer


def mixer(song=object()):
    obj = object.__new__(MidiMixer)
    obj._closing = False
    obj._meter_after_id = None
    obj.app = SimpleNamespace(song=song)
    obj.winfo_exists = lambda: True
    obj.after = Mock(return_value='next')
    obj.after_cancel = Mock()
    obj.destroy = Mock()
    return obj


def test_close_cancels_pending_callback():
    m = mixer()
    m._meter_after_id = 'old'
    MidiMixer.close_mixer(m)
    m.after_cancel.assert_called_once_with('old')
    m.destroy.assert_called_once()
    assert m._closing and m._meter_after_id is None


def test_close_idempotent():
    m = mixer()
    MidiMixer.close_mixer(m)
    MidiMixer.close_mixer(m)
    m.destroy.assert_called_once()


def test_missing_song_keeps_meter_timer_alive():
    m = mixer(song=None)
    MidiMixer.refresh_meters(m)
    m.after.assert_called_once_with(70, m.refresh_meters)
    assert m._meter_after_id == 'next'


def test_closed_mixer_does_not_reschedule():
    m = mixer(song=None)
    m._closing = True
    MidiMixer.refresh_meters(m)
    m.after.assert_not_called()


def test_reload_resets_guard_on_failure():
    m = mixer()
    m.tick = SimpleNamespace(get=lambda: 0)
    m.xg_mode = SimpleNamespace(get=lambda: False)
    m.controls = {1: {'Volume': SimpleNamespace(set=Mock(side_effect=RuntimeError('test')))}}
    m.baseline = {}
    with patch('midi_mixer.channel_values', return_value={'Volume': 100}):
        try:
            MidiMixer.reload(m)
        except RuntimeError:
            pass
    assert m._reloading is False
