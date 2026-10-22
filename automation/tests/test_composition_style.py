import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from composition_style import BASE_CROP, shot_filter, overlay


class CompositionStyleTests(unittest.TestCase):
    def test_vertical_source_keeps_safe_center(self):
        self.assertEqual(shot_filter(1080,1920,1),(BASE_CROP,0))

    def test_wide_4k_alternates_inside_source(self):
        self.assertEqual([shot_filter(3840,2160,i)[1] for i in range(3)],[-60,60,-60])

    def test_low_resolution_is_not_given_additional_crop(self):
        self.assertEqual(shot_filter(1920,1080,0),(BASE_CROP,0))

    def test_long_headline_is_omitted_not_truncated(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(overlay(Path(directory),'palavra '*40,17),[])

    def test_headline_keeps_full_text_with_two_line_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertTrue(overlay(root,'Seu sabonete fica escorregando na pia?',17))
            self.assertEqual(' '.join((root/'hook-v4.txt').read_text().split()),'Seu sabonete fica escorregando na pia?')
