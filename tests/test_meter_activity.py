import unittest
from meter_activity import update_activity_meters


class MeterActivityTests(unittest.TestCase):
    def test_activity_holds_for_three_polls(self):
        counters = (0, 1) + (0,) * 14
        hold, lit = update_activity_meters((0,) * 16, counters, [0] * 16)
        self.assertTrue(lit[1])
        for expected in (2, 1, 0):
            hold, lit = update_activity_meters(counters, counters, hold)
            self.assertEqual(hold[1], expected)
        self.assertFalse(lit[1])

    def test_counter_reset_does_not_light_idle_channels(self):
        hold, lit = update_activity_meters((8,) * 16, (0,) * 16, [0] * 16)
        self.assertEqual(hold, [0] * 16)
        self.assertFalse(any(lit))

    def test_new_run_with_activity_lights_channel(self):
        hold, lit = update_activity_meters((8,) * 16, (0, 2) + (0,) * 14, [0] * 16)
        self.assertEqual(hold[1], 3)
        self.assertTrue(lit[1])

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            update_activity_meters(None, (0,), [0] * 16)
        with self.assertRaises(ValueError):
            update_activity_meters(None, (0,) * 16, [0] * 16, 0)
