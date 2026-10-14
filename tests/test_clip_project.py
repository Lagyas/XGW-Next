import sys
import json
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from clip_project import save_regions, load_regions, sidecar_path
from clip_regions import split_region
from arrangement import track_clips


def sample():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')])])

class ClipProjectTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); split_region(s,0,0,240); s.dirty=True; s.save(p)
            save_regions(p,s); loaded=Song.read(p)
            self.assertTrue(load_regions(p,loaded))
            self.assertEqual(track_clips(loaded.tracks[0],480),[(0,240),(240,480)])
    def test_event_identity_sidecar_without_regions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); s.dirty=True; s.save(p)
            self.assertIsNotNone(save_regions(p,s)); self.assertTrue(sidecar_path(p).exists())
    def test_stale_file_rejected_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); split_region(s,0,0,240); s.dirty=True; s.save(p); save_regions(p,s)
            p.write_bytes(p.read_bytes()+b'changed')
            other=sample()
            with self.assertRaises(MidiError): load_regions(p,other)
            self.assertFalse(hasattr(other.tracks[0],'clip_regions'))
    def test_invalid_region_rejected_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); split_region(s,0,0,240); s.dirty=True; s.save(p); save_regions(p,s)
            side=sidecar_path(p); data=json.loads(side.read_text()); data['tracks'][0]=[[0,300],[200,480]]; side.write_text(json.dumps(data))
            other=Song.read(p)
            with self.assertRaises(MidiError): load_regions(p,other)
            self.assertFalse(hasattr(other.tracks[0],'clip_regions'))
    def test_missing_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(load_regions(Path(d)/'missing.mid',sample()))
    def test_bool_coordinates_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); split_region(s,0,0,240); s.dirty=True; s.save(p); save_regions(p,s)
            side=sidecar_path(p); data=json.loads(side.read_text()); data['tracks'][0]=[[False,240]]; side.write_text(json.dumps(data))
            with self.assertRaises(MidiError): load_regions(p,Song.read(p))

    def test_event_and_clip_identity_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); split_region(s,0,0,240)
            expected_events=[e.uid for e in s.tracks[0].events]
            expected_clips=list(s.tracks[0].clip_region_ids)
            s.dirty=True; s.save(p); save_regions(p,s)
            restored=Song.read(p); self.assertTrue(load_regions(p,restored))
            self.assertEqual([e.uid for e in restored.tracks[0].events], expected_events)
            self.assertEqual(restored.tracks[0].clip_region_ids, expected_clips)

    def test_duplicate_identity_rejected_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'song.mid'; s=sample(); s.dirty=True; s.save(p); save_regions(p,s)
            side=sidecar_path(p); data=json.loads(side.read_text())
            data['identities'][0]['events'][1]=data['identities'][0]['events'][0]
            side.write_text(json.dumps(data))
            restored=Song.read(p); before=[e.uid for e in restored.tracks[0].events]
            with self.assertRaises(MidiError): load_regions(p,restored)
            self.assertEqual([e.uid for e in restored.tracks[0].events], before)
