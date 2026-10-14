"""End-to-end real-world XWS -> demixed SMF1 export checks."""
import sys
from collections import Counter
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song
from midi_demix import demix_to_format1
from xws_import import import_xws

ROOT = Path(__file__).resolve().parents[3]
FILES = ['A Dream of a Dream3.XWS', 'A Dream of a Dream4.XWS',
         'A Dream of a Dream_ch(1).XWS']


def signature(song):
    return Counter((e.tick, e.status, e.meta_type, bytes(e.data))
                   for track in song.tracks for e in track.events
                   if not (e.status == 0xff and e.meta_type in (3, 47)))


@pytest.mark.parametrize('filename', FILES)
def test_real_xws_demixed_midi_roundtrip(filename):
    path = ROOT / filename
    if not path.exists():
        pytest.skip('Optional external XWS reference unavailable')
    source = import_xws(path)
    before = signature(source)
    exported = demix_to_format1(source)
    reopened = Song.from_bytes(exported.to_bytes())
    assert reopened.fmt == 1
    assert reopened.division == source.division
    assert signature(reopened) == before
    assert all(len({e.status & 15 for e in t.events if 0x80 <= e.status <= 0xef}) <= 1
               for t in reopened.tracks)
    assert sum(1 for t in reopened.tracks for e in t.events
               if 0x80 <= e.status <= 0xef) == sum(1 for t in source.tracks
               for e in t.events if 0x80 <= e.status <= 0xef)


def test_xgworks_v3_v4_midi_content_matches():
    older, newer = (ROOT / FILES[0], ROOT / FILES[1])
    if not older.exists() or not newer.exists():
        pytest.skip('Optional XWS v3/v4 pair unavailable')
    assert signature(import_xws(older)) == signature(import_xws(newer))
