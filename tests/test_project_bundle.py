import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event, MidiError
from project_bundle import save_project, load_project
from clip_regions import split_region

class ProjectBundleTests(unittest.TestCase):
    def sample(self):
        return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')])])

    def test_roundtrip_regions_and_ids(self):
        with tempfile.TemporaryDirectory() as d:
            song = self.sample()
            split_region(song, 0, 0, 240)
            target = Path(d) / 'song.xgwn'
            save_project(target, song)
            loaded, routes = load_project(target)
            self.assertEqual(loaded.tracks[0].clip_regions, song.tracks[0].clip_regions)
            self.assertEqual([e.uid for e in loaded.tracks[0].events], [e.uid for e in song.tracks[0].events])

    def test_reject_unknown_member(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'bad.xgwn'
            with zipfile.ZipFile(target, 'w') as z:
                z.writestr('manifest.json', '{}')
                z.writestr('../evil', 'oops')
            with self.assertRaises(MidiError):
                load_project(target)

    def test_reject_corrupt_zip(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'bad.xgwn'
            target.write_bytes(b'not zip')
            with self.assertRaises(MidiError):
                load_project(target)

class Stage105RoutingPersistenceTests(unittest.TestCase):
    def sample(self):
        return Song(1, 480, [Track([Event(0, 0x92, b"\x3c\x64"), Event(480, 0x82, b"\x3c\x00")])])

    def test_output_channel_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "routing.xgwn"
            save_project(path, self.sample(), {0: ("Port A", 4)}, "Port A")
            song, routes = load_project(path, "Port A")
            self.assertEqual(routes, {0: ("Port A", 4)})
            self.assertEqual(song.tracks[0].events[0].status, 0x92)

    def test_keep_original_channel_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "keep.xgwn"
            save_project(path, self.sample(), {0: ("Port B", None)}, "Port B")
            self.assertEqual(load_project(path, "Port B")[1], {0: ("Port B", None)})

    def test_legacy_project_without_routing(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "legacy.xgwn"
            save_project(path, self.sample())
            with zipfile.ZipFile(path) as archive:
                entries = {name: archive.read(name) for name in archive.namelist()
                           if name != "song.mid.xgw-routing.json"}
            with zipfile.ZipFile(path, "w") as archive:
                for name, content in entries.items():
                    archive.writestr(name, content)
            self.assertEqual(load_project(path)[1], {})

    def test_reject_invalid_channel_on_save(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(MidiError):
                save_project(Path(d) / "invalid.xgwn", self.sample(), {0: ("Port A", 16)})
