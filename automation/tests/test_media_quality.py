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


class AVTimingTests(unittest.TestCase):
    def test_aac_padding_tolerance(self):
        from media_quality import av_timing
        r = av_timing(dict(start_time='0',duration='20'),dict(start_time='0',duration='20.03'))
        self.assertEqual(r['av_end_delta_seconds'], .03)
        self.assertFalse(r['lip_sync_verified'])
    def test_audio_offset_rejected(self):
        from media_quality import av_timing
        with self.assertRaises(ValueError):
            av_timing(dict(start_time='0',duration='20'),dict(start_time='.3',duration='20'))
    def test_truncated_audio_rejected(self):
        from media_quality import av_timing
        with self.assertRaises(ValueError):
            av_timing(dict(start_time='0',duration='20'),dict(start_time='0',duration='18'))
    def test_missing_and_nonfinite_timing_rejected(self):
        from media_quality import av_timing
        for audio in ({}, dict(start_time='nan',duration='20'),dict(start_time='0',duration='inf')):
            with self.assertRaises(ValueError):
                av_timing(dict(start_time='0',duration='20'),audio)
