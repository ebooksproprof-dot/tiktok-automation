import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import female_narration as f


class FemaleNarrationTests(unittest.TestCase):
    def test_reuses_verified_asset_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.bin'; path.write_bytes(b'voice')
            assets={'test.bin': (5,hashlib.sha256(b'voice').hexdigest())}
            with patch.object(f,'ASSETS',assets), patch.object(f.urllib.request,'urlopen') as network:
                f.acquire(directory)
            network.assert_not_called()

    def test_corrupt_cached_asset_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.bin'; path.write_bytes(b'wrong')
            with patch.object(f,'ASSETS',{'test.bin':(5,'0'*64)}), self.assertRaises(ValueError):
                f.acquire(directory)

    def test_oversized_download_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(f,'ASSETS',{'test.bin':(2,'0'*64)}), patch.object(f.urllib.request,'urlopen',return_value=io.BytesIO(b'toolong')):
                with self.assertRaisesRegex(ValueError,'exceeds'):
                    f.acquire(directory)
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_failed_download_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(f,'ASSETS',{'test.bin':(2,'0'*64)}), patch.object(f.urllib.request,'urlopen',side_effect=TimeoutError):
                with self.assertRaises(TimeoutError): f.acquire(directory)
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_bad_text_rejected_before_synthesis(self):
        engine=object.__new__(f.KokoroFemaleEngine); engine.voice=Mock()
        for text in ('', ' '*5, 'x'*601, None):
            with self.assertRaises(ValueError): engine.speak(text,'unused.wav')
        engine.voice.create.assert_not_called()
