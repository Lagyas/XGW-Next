"""Lyrics / karaoke editing on MIDI lyric meta events (FF 05).

Karaoke markers follow Yamaha XF and common .kar files: a syllable starting
with "/" begins a new line, "<" (XF) or "\\" (.kar) begins a new page. Words
end with a space; syllables of one word are joined without one. Text is
stored in the selected MIDI text encoding (midi.encode_text).
"""
from midi import Event, MidiError, decode_text, encode_text

LYRIC = 0x05
LINE_MARK = "/"
PAGE_MARKS = ("<", "\\")


def lyric_events(track):
    """[(event index, tick, text)] of the track's lyric events in time order."""
    found = [(i, e.tick, e.order, decode_text(e.data)) for i, e in enumerate(track.events)
             if e.status == 0xFF and e.meta_type == LYRIC]
    return [(i, tick, text) for i, tick, _, text in sorted(found, key=lambda x: (x[1], x[2], x[0]))]


def _extend_end_of_track(track, tick):
    for e in track.events:
        if e.status == 0xFF and e.meta_type == 0x2F and e.tick < tick:
            e.tick = tick


def insert_lyric(song, track_index, tick, text):
    """Add one lyric event; returns its event index."""
    if type(tick) is not int or tick < 0 or tick > 0x0FFFFFFF:
        raise MidiError("Invalid lyric position")
    data = encode_text(text)
    if not data or len(data) > 255:
        raise MidiError("A lyric must have 1–255 bytes")
    track = song.tracks[track_index]
    order = max((e.order for e in track.events), default=-1) + 1
    track.events.append(Event(tick, 0xFF, data, LYRIC, order=order))
    _extend_end_of_track(track, tick)
    song.dirty = True
    return len(track.events) - 1


def edit_lyric(song, track_index, event_index, tick=None, text=None):
    track = song.tracks[track_index]
    if not 0 <= event_index < len(track.events):
        raise MidiError("Lyric event not found")
    e = track.events[event_index]
    if not (e.status == 0xFF and e.meta_type == LYRIC):
        raise MidiError("Selected event is not a lyric")
    if tick is not None:
        if type(tick) is not int or tick < 0 or tick > 0x0FFFFFFF:
            raise MidiError("Invalid lyric position")
    data = encode_text(text) if text is not None else e.data
    if not data or len(data) > 255:
        raise MidiError("A lyric must have 1–255 bytes")
    if tick is not None:
        e.tick = tick
        _extend_end_of_track(track, tick)
    e.data = data
    song.dirty = True


def delete_lyrics(song, track_index, event_indices):
    track = song.tracks[track_index]
    indices = sorted(set(event_indices), reverse=True)
    for i in indices:
        if not 0 <= i < len(track.events):
            raise MidiError("Lyric event not found")
        e = track.events[i]
        if not (e.status == 0xFF and e.meta_type == LYRIC):
            raise MidiError("Only lyric events can be deleted here")
    for i in indices:
        del track.events[i]
    if indices:
        song.dirty = True
    return len(indices)


def parse_lyrics_text(text):
    """Typed song text → syllables with karaoke markers.

    Words are separated by spaces, syllables by "-" ("Ka-ra-o-ke"); a new
    line becomes "/", one or more empty lines a new page "<".
    """
    syllables = []
    page_break = False
    for line in text.splitlines():
        words = line.split()
        if not words:
            if syllables:
                page_break = True
            continue
        first_of_line = True
        for w_index, word in enumerate(words):
            parts = [p for p in word.split("-") if p]
            if not parts:
                continue
            for p_index, part in enumerate(parts):
                s = part
                last_part = p_index == len(parts) - 1
                if last_part and w_index < len(words) - 1:
                    s += " "
                if first_of_line and syllables:
                    s = ("<" if page_break else LINE_MARK) + s
                first_of_line = False
                syllables.append(s)
        page_break = False
    return syllables


def note_starts(track, from_tick=0, channel=None):
    """Distinct note-on ticks (velocity > 0) at or after `from_tick`; chords count once."""
    starts = set()
    for e in track.events:
        if e.status & 0xF0 == 0x90 and len(e.data) == 2 and e.data[1] > 0 and e.tick >= from_tick:
            if channel is None or (e.status & 0x0F) + 1 == channel:
                starts.add(e.tick)
    return sorted(starts)


def assign_syllables(song, lyric_track, syllables, starts, replace=False):
    """Place syllables on successive note starts. With `replace`, existing
    lyrics in the covered range of `lyric_track` are removed first.
    Returns the number placed. Everything is validated before any change."""
    count = min(len(syllables), len(starts))
    if count == 0:
        return 0
    for s in syllables[:count]:
        data = encode_text(s)
        if not data or len(data) > 255:
            raise MidiError(f"Invalid syllable: {s!r}")
    if replace:
        first, last = starts[0], starts[count - 1]
        old = [i for i, tick, _ in lyric_events(song.tracks[lyric_track]) if first <= tick <= last]
        delete_lyrics(song, lyric_track, old)
    for s, tick in zip(syllables[:count], starts[:count]):
        insert_lyric(song, lyric_track, tick, s)
    return count


def display_text(syllable):
    """Syllable without its karaoke line/page marker."""
    s = syllable
    while s[:1] in (LINE_MARK,) + PAGE_MARKS:
        s = s[1:]
    return s.replace("\r", "").replace("\n", "")


def karaoke_pages(lyrics):
    """[(tick, text)] → pages → lines → [(tick, display text)]."""
    pages = []
    for tick, text in sorted(lyrics, key=lambda x: x[0]):
        new_page = text[:1] in PAGE_MARKS or not pages
        new_line = text[:1] == LINE_MARK or text.endswith(("\r", "\n"))
        if new_page:
            pages.append([[]])
        elif new_line and pages[-1][-1]:
            pages[-1].append([])
        pages[-1][-1].append((tick, display_text(text)))
        if text.endswith(("\r", "\n")):
            pages[-1].append([])
    for page in pages:
        while len(page) > 1 and not page[-1]:
            page.pop()
    return pages


def page_index_at(pages, tick):
    """Index of the page sung at `tick` (the last page that has started)."""
    current = 0
    for i, page in enumerate(pages):
        first = next((s[0] for line in page for s in line), None)
        if first is not None and first <= tick:
            current = i
    return current
