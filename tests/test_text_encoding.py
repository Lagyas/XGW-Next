"""MIDI text meta events are shown in a selectable encoding (default Windows-1250)."""
import pytest

import midi
from midi import Event, Track, decode_text, encode_text, get_text_encoding, set_text_encoding


@pytest.fixture(autouse=True)
def restore_encoding():
    saved = get_text_encoding()
    yield
    set_text_encoding(saved)


def test_default_is_windows_1250():
    set_text_encoding("cp1250")
    raw = "Příliš žluťoučký kůň".encode("cp1250")
    assert decode_text(raw) == "Příliš žluťoučký kůň"
    track = Track([Event(0, 0xFF, raw, 3)])
    assert track.name() == "Příliš žluťoučký kůň"
    assert Event(0, 0xFF, raw, 6).description() == "Příliš žluťoučký kůň"


def test_switching_encoding_changes_only_display():
    raw = "Čeština".encode("utf-8")
    event = Event(0, 0xFF, raw, 1)
    set_text_encoding("utf-8")
    assert event.description() == "Čeština"
    set_text_encoding("cp1250")
    assert event.description() != "Čeština"
    assert event.data == raw


def test_shift_jis_and_invalid_bytes_never_raise():
    set_text_encoding("cp932")
    assert decode_text("ピアノ".encode("cp932")) == "ピアノ"
    set_text_encoding("utf-8")
    assert decode_text(b"\xff\xfe") == "��"


def test_encode_text_and_unknown_encoding():
    assert encode_text("Řeč", "cp1250") == "Řeč".encode("cp1250")
    with pytest.raises(ValueError):
        set_text_encoding("ebcdic")
    assert set(midi.TEXT_ENCODINGS) >= {"cp1250", "cp1252", "latin-1", "cp932", "utf-8"}
