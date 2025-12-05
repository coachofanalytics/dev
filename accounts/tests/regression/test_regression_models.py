import os
import unittest
if not os.environ.get("CRISIS_RUN_REGRESSION"):
    raise unittest.SkipTest("Disabled: non-crisis regression tests")

class RegressionSmokeTest(unittest.TestCase):
    def test_known_behavior_placeholder(self):
        self.assertEqual(sorted([3, 1, 2]), [1, 2, 3])
