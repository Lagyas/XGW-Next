import unittest
from mixer_follow import follow_automation


class MixerFollowTests(unittest.TestCase):
    def test_untouched_fader_follows_automation(self):
        self.assertEqual(follow_automation({'Volume': 100}, {'Volume': 100}, {'Volume': 72}),
                         ({'Volume': 72}, {'Volume': 72}))

    def test_manual_edit_is_preserved(self):
        self.assertEqual(follow_automation({'Volume': 85}, {'Volume': 100}, {'Volume': 72}),
                         ({'Volume': 85}, {'Volume': 72}))

    def test_independent_controllers(self):
        self.assertEqual(follow_automation({'Volume': 85, 'Pan': 64},
                                           {'Volume': 100, 'Pan': 64},
                                           {'Volume': 72, 'Pan': 32}),
                         ({'Volume': 85, 'Pan': 32}, {'Volume': 72, 'Pan': 32}))

    def test_reject_invalid_controller_values(self):
        with self.assertRaises(ValueError):
            follow_automation({'Pan': 64}, {'Pan': 64}, {'Pan': 128})

    def test_reject_mismatched_keys(self):
        with self.assertRaises(ValueError):
            follow_automation({'Pan': 64}, {'Pan': 64}, {'Volume': 64})
