"""30s all-AI mode must not silently include legacy stock or repeat a clip."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import render


class AIOnly81Tests(unittest.TestCase):
    def test_full_ai_requires_thirty_unique_seconds(self):
        five = [dict(kind='ai', duration=5.0) for _ in range(5)]
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            render.select_profile(five, 'AI_ONLY')
        six = five + [dict(kind='ai', duration=5.0)]
        self.assertEqual(render.select_profile(six, 'AI_ONLY'), 'AI_ONLY')
        self.assertEqual(render.select_profile(six, 'auto'), 'AI_ONLY')

    def test_plan_six_distinct_five_second_sources(self):
        sources = [dict(kind='ai', duration=5.0625, source_offset=0) for _ in range(6)]
        shots = render.plan(sources, 'AI_ONLY')
        self.assertEqual(len(shots), 6)
        self.assertEqual({shot['source_index'] for shot in shots}, set(range(6)))
        self.assertAlmostEqual(sum(x['duration'] for x in shots), 30)
        self.assertTrue(all(x['duration'] == 5.0 for x in shots))

    def test_ai_only_does_not_require_stock(self):
        clips = [dict(kind='ai', duration=10.0) for _ in range(3)]
        self.assertEqual(render.select_profile(clips, 'AI_ONLY'), 'AI_ONLY')
        shots = render.plan(clips, 'AI_ONLY')
        self.assertEqual({s['source_index'] for s in shots}, {0, 1, 2})
        self.assertEqual(len(shots), 6)
        self.assertAlmostEqual(sum(s['duration'] for s in shots), 30)

    def test_mixed_five_second_ai_cannot_claim_all_ai(self):
        source = [dict(kind='ai', duration=5)] + [dict(kind='real', duration=25)]
        self.assertEqual(render.select_profile(source), 'C')
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            render.select_profile(source, 'AI_ONLY')

    def test_no_silent_stretch_or_loop(self):
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            render.plan([dict(kind='ai', duration=24.99)], 'AI_ONLY')

    def test_ai_only_is_experimental_not_publisher(self):
        code = Path(render.__file__).read_text()
        for forbidden in ('BUFFER_API_KEY', 'TIKTOK_ACCESS_TOKEN', 'stock_publish', 'createPost'):
            self.assertNotIn(forbidden, code)


if __name__ == '__main__':
    unittest.main()
