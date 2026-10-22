import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_quality import temporal_findings


class TemporalQualityTests(unittest.TestCase):
    def test_black_intervals_are_measured_not_single_dark_frames(self):
        r = temporal_findings('black_start:0 black_end:0.2 black_duration:0.2\n'
                              'black_start:3 black_end:3.5 black_duration:0.5')
        self.assertEqual(r['black_intervals_over_300ms'], 1)

    def test_silence_start_catches_trailing_silence_without_end(self):
        r = temporal_findings('[silencedetect] silence_start: 12.4\n')
        self.assertEqual(r['silence_intervals_over_800ms'], 1)

    def test_normal_decode_has_no_temporal_findings(self):
        self.assertEqual(sum(temporal_findings('mean_volume: -16.3 dB').values()), 0)
