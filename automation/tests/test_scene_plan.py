import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_plan import plan

class ScenePlanTests(unittest.TestCase):
    def test_unequal_sources_use_available_footage_without_looping(self):
        shots = plan([(0,8,'a'),(8,16,'b')],16,[6.68,10.01])
        self.assertAlmostEqual(sum(s[2] for s in shots),16)
        for source, offset, length in shots:
            self.assertLessEqual(offset + length, [6.63,9.96][source] + 1e-8)
        self.assertEqual([s[0] for s in shots], sorted(s[0] for s in shots))

    def test_windows_do_not_overlap(self):
        self.assertEqual(plan([(0,3,'a'),(3,7,'b'),(7,10,'c')],10,[12]),
                         [(0,0.0,3),(0,3.0,4),(0,7.0,3)])
    def test_short_source_cannot_loop(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_TOO_SHORT'):
            plan([(0,8,'a'),(8,16,'b')],16,[10])
    def test_multiple_sources_keep_independent_offsets(self):
        self.assertEqual(plan([(0,4,'a'),(4,8,'b'),(8,12,'c'),(12,16,'d')],16,[10,10]),
                         [(0,0.,4),(0,4.,4),(1,0.,4),(1,4.,4)])
