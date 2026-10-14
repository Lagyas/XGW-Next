import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from project_recovery import recovery_path, write_recovery, read_recovery, discard_recovery

class RecoveryTests(unittest.TestCase):
    def sample(self):
        return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')])])

    def test_recovery_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'test.mid'
            target = write_recovery(source, self.sample(), directory=Path(d)/'recovery')
            self.assertTrue(target.exists())
            song, routes = read_recovery(source, Path(d)/'recovery')
            self.assertEqual(song.to_bytes(), self.sample().to_bytes())
            self.assertEqual(routes, {})

    def test_recovery_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'song.mid'
            source.write_bytes(b'original')
            write_recovery(source, self.sample(), directory=Path(d)/'recovery')
            self.assertEqual(source.read_bytes(), b'original')

    def test_distinct_paths_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / 'a.mid'
            b = Path(d) / 'b.mid'
            self.assertNotEqual(recovery_path(a, d), recovery_path(b, d))
            write_recovery(a, self.sample(), directory=d)
            discard_recovery(a, d)
            self.assertIsNone(read_recovery(a, d))

    def test_missing_backup(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(read_recovery(Path(d)/'absent.mid', d))
