"""Lyrics / karaoke editor core."""
import pytest

from midi import Event, MidiError, Song, Track, get_text_encoding, set_text_encoding
from lyrics_ops import (assign_syllables, delete_lyrics, display_text, edit_lyric, insert_lyric,
                        karaoke_pages, lyric_events, note_starts, page_index_at, parse_lyrics_text)


@pytest.fixture(autouse=True)
def cp1250():
    saved = get_text_encoding()
    set_text_encoding("cp1250")
    yield
    set_text_encoding(saved)


def song(notes=()):
    events = []
    for tick, pitch in notes:
        events += [Event(tick, 0x90, bytes((pitch, 100))), Event(tick + 100, 0x80, bytes((pitch, 0)))]
    events.append(Event(500, 0xFF, b"", 0x2F))
    return Song(1, 480, [Track([Event(0, 0xFF, b"Melody", 3)] + events)])


def test_parse_lyrics_text_markers():
    text = "Ka-ra-o-ke je\nzá-ba\n\nDru-há sloka"
    assert parse_lyrics_text(text) == ["Ka", "ra", "o", "ke ", "je", "/zá", "ba", "<Dru", "há ", "sloka"]
    assert parse_lyrics_text("") == []


def test_insert_edit_delete_round_trip_in_cp1250():
    s = song()
    i = insert_lyric(s, 0, 960, "Řeč")
    assert s.tracks[0].events[i].data == "Řeč".encode("cp1250")
    assert lyric_events(s.tracks[0]) == [(i, 960, "Řeč")]
    # end of track follows a lyric placed after it
    assert max(e.tick for e in s.tracks[0].events if e.meta_type == 0x2F) == 960
    edit_lyric(s, 0, i, tick=480, text="žluť")
    assert lyric_events(s.tracks[0]) == [(i, 480, "žluť")]
    assert delete_lyrics(s, 0, [i]) == 1
    assert lyric_events(s.tracks[0]) == []


def test_invalid_edits_are_rejected():
    s = song()
    with pytest.raises(MidiError):
        insert_lyric(s, 0, -1, "a")
    with pytest.raises(MidiError):
        insert_lyric(s, 0, 0, "")
    with pytest.raises(MidiError):
        edit_lyric(s, 0, 0, text="x")  # event 0 is the track name
    with pytest.raises(MidiError):
        delete_lyrics(s, 0, [0])


def test_assign_syllables_to_note_starts_counts_chords_once():
    s = song([(0, 60), (0, 64), (240, 62), (480, 64)])
    starts = note_starts(s.tracks[0])
    assert starts == [0, 240, 480]
    placed = assign_syllables(s, 0, ["Ka", "ra", "o", "ke"], starts)
    assert placed == 3
    assert [(t, x) for _, t, x in lyric_events(s.tracks[0])] == [(0, "Ka"), (240, "ra"), (480, "o")]
    # replace mode removes the previous lyrics of the covered range
    assign_syllables(s, 0, ["A", "B", "C"], starts, replace=True)
    assert [x for _, _, x in lyric_events(s.tracks[0])] == ["A", "B", "C"]


def test_karaoke_pages_and_current_page():
    lyrics = [(0, "Ka"), (10, "ra "), (20, "/je"), (30, "<Dru"), (40, "há")]
    pages = karaoke_pages(lyrics)
    assert pages == [[[(0, "Ka"), (10, "ra ")], [(20, "je")]], [[(30, "Dru"), (40, "há")]]]
    assert page_index_at(pages, 25) == 0
    assert page_index_at(pages, 30) == 1
    assert display_text("<Ahoj") == "Ahoj"
    # .kar style: backslash starts a page
    assert len(karaoke_pages([(0, "a"), (5, "\\b")])) == 2
