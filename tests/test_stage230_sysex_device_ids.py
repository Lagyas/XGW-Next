"""SysEx reset detection must respect device-ID variations and strict payloads."""
from midi import Event, Song, Track
from midi_compat import sysex_profiles


def profiles(payload):
    return sysex_profiles(Song(0, 480, [Track([Event(0, 0xf0, payload)])]))


def test_xg_reset_accepts_yamaha_device_numbers():
    for device in range(0x10, 0x20):
        assert profiles(bytes([0x43, device, 0x4c, 0, 0, 0x7e, 0, 0xf7])) == {'XG'}


def test_universal_gm_reset_accepts_device_ids():
    for device in (0, 1, 0x10, 0x7e, 0x7f):
        assert profiles(bytes([0x7e, device, 9, 1, 0xf7])) == {'GM'}
        assert profiles(bytes([0x7e, device, 9, 3, 0xf7])) == {'GM2'}


def test_reset_detection_rejects_near_matches():
    for payload in (b'\x43\x20\x4c\x00\x00\x7e\x00\xf7',
                    b'\x43\x10\x4c\x00\x00\x7e\x00\xf7\x00',
                    b'\x7e\x7f\x09\x01', b'\x7e\x7f\x09\x02\xf7'):
        assert profiles(payload) == set()
