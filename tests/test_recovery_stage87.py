import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor'))
from midi import Song, Track, Event
from project_recovery import write_recovery, recovery_is_current, snapshot_fingerprint
from project_bundle import load_project_workspace


class RecoveryStage87Tests(unittest.TestCase):
    def song(self):
        return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'), Event(480, 0x80, b'\x3c\x00')])])

    def test_unsaved_snapshot_is_current(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'new.mid'
            write_recovery(source, self.song(), directory=Path(d)/'backup')
            self.assertTrue(recovery_is_current(source, Path(d)/'backup'))

    def test_snapshot_older_than_explicit_save_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'song.mid'
            backup = write_recovery(source, self.song(), directory=Path(d)/'backup')
            source.write_bytes(b'new save')
            import os
            stamp = backup.stat().st_mtime_ns
            os.utime(source, ns=(stamp + 2000000000, stamp + 2000000000))
            self.assertFalse(recovery_is_current(source, Path(d)/'backup'))

    def test_workspace_roundtrip_in_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            state = {'geometry': {}, 'open_editors': [], 'playhead_tick': 42,
                     'loop_start': 10, 'loop_end': 99}
            target = write_recovery(Path(d)/'song.mid', self.song(), workspace=state, directory=Path(d)/'backup')
            self.assertEqual(load_project_workspace(target), state)

    def test_fingerprint_changes_with_workspace_and_routing(self):
        song = self.song()
        a = snapshot_fingerprint(song, {}, 'port1', {'playhead_tick': 1})
        self.assertNotEqual(a, snapshot_fingerprint(song, {}, 'port1', {'playhead_tick': 2}))
        self.assertNotEqual(a, snapshot_fingerprint(song, {}, 'port2', {'playhead_tick': 1}))
        self.assertNotEqual(a, snapshot_fingerprint(song, {1: 'port1'}, 'port1', {'playhead_tick': 1}))
