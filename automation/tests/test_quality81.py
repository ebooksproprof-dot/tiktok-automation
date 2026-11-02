import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import quality as q


class Quality81Tests(unittest.TestCase):
    def test_legacy_delegates_unchanged(self):
        with patch.object(q.media_quality, 'validate', return_value={'legacy': True}) as old:
            self.assertEqual(q.validate('old.mp4', profile='legacy'), {'legacy': True})
            old.assert_called_once_with('old.mp4')
        with self.assertRaises(ValueError):
            q.validate('old.mp4', profile='legacy', policy=q.Policy())

    def test_invalid_policies(self):
        for policy in (q.Policy(target_seconds=float('nan')), q.Policy(tolerance_seconds=2),
                       q.Policy(width=1079), q.Policy(max_bytes=0)):
            with self.assertRaises(ValueError):
                policy.check()
        with self.assertRaises(ValueError):
            q.validate('none.mp4', profile='fake')

    def test_black_and_silence_reuse_measured_detector(self):
        got = q.media_quality.temporal_findings('black_duration:0.5 silence_start: 3.0')
        self.assertEqual(got, {'black_intervals_over_300ms': 1, 'silence_intervals_over_800ms': 1})


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Real FFmpeg required')
class RealQuality81Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.path = Path(cls.folder.name)/'synthetic-not-ai.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
            'color=c=0x285f72:s=1080x1920:r=24', '-f', 'lavfi', '-i',
            'sine=frequency=440:sample_rate=48000', '-t', '30', '-c:v', 'libx264',
            '-preset', 'ultrafast', '-threads', '2', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(cls.path)],
            check=True, capture_output=True, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_real_30s_valid_and_old_validator_rejects(self):
        result = q.validate(self.path)
        self.assertTrue(result['technical_pass'])
        self.assertFalse(result['editorial_approved'])
        self.assertFalse(result['publication_enabled'])
        self.assertAlmostEqual(result['duration'],30,delta=.15)
        with self.assertRaisesRegex(ValueError, '15–28'):
            q.validate(self.path, profile='legacy')

    def test_wrong_duration_resolution_and_size(self):
        for policy in (q.Policy(target_seconds=28), q.Policy(width=720), q.Policy(max_bytes=101000)):
            with self.assertRaises(ValueError):
                q.validate(self.path, policy=policy)

    def test_corrupt_file_rejected(self):
        broken = Path(self.folder.name)/'corrupt.mp4'
        broken.write_bytes(b'x'*150000)
        with self.assertRaises(ValueError):
            q.validate(broken)

    def test_missing_audio_rejected(self):
        silent = Path(self.folder.name)/'missing-audio.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.path), '-c:v', 'copy',
                        '-an', str(silent)], check=True, capture_output=True, timeout=30)
        with self.assertRaises(ValueError):
            q.validate(silent, policy=q.Policy(min_bytes=1))


if __name__ == '__main__':
    unittest.main()
