import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from narration import sentences, load_engine

class NarrationTests(unittest.TestCase):
    def test_wrapped_caption_is_spoken_as_complete_sentence(self):
        self.assertEqual(sentences(['Uma gaveta cheia?', 'Separe as peças', 'por categoria.']),
                         ['Uma gaveta cheia?', 'Separe as peças por categoria.'])

    def test_unverified_engine_is_not_silently_selected(self):
        with self.assertRaises(ValueError):
            load_engine('/unused', 'unverified-cloud-voice')

    def test_explicit_female_engine_routes_to_cpu_adapter(self):
        from unittest.mock import patch
        with patch('female_narration.KokoroFemaleEngine') as engine:
            self.assertIs(load_engine('/cache', 'kokoro-female'), engine.return_value)
            engine.assert_called_once_with('/cache')

    def test_default_preserves_piper(self):
        from unittest.mock import patch
        with patch('narration.PiperEngine') as engine:
            self.assertIs(load_engine('/cache'), engine.return_value)
