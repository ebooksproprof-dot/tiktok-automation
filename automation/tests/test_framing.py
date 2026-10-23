import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from framing import product_geometry, product_frame_filter


class FramingTests(unittest.TestCase):
    def test_product_box_never_overlaps_headline_or_captions(self):
        for size in [(3840,2160),(2160,3840),(1080,1080),(8000,1000),(1000,8000)]:
            box=product_geometry(*size)
            self.assertGreaterEqual(box['y'],500)
            self.assertLessEqual(box['y']+box['height'],1220)
            self.assertGreaterEqual(box['x'],0)
            self.assertLessEqual(box['x']+box['width'],1080)
            self.assertLess(abs((box['width']/box['height'])/(size[0]/size[1])-1),.02)

    def test_foreground_is_not_cropped(self):
        foreground=product_frame_filter(3840,2160).split('[foreground]',1)[1].split(';',1)[0]
        self.assertNotIn('crop',foreground)
        self.assertNotIn('zoom',foreground)
        self.assertEqual(product_geometry(3840,2160),dict(width=1080,height=606,x=0,y=557))

    def test_bad_metadata_rejected(self):
        for size in [(0,2),(-1,1080),(float('nan'),1920),(True,2),(20000,20000)]:
            with self.assertRaises(ValueError): product_geometry(*size)
