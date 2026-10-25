import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from caption_layout import filters, layout, FONT, MAX_WIDTH
try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None

@unittest.skipUnless(ImageFont is not None and Path(FONT).exists(), 'Optional measured captions require Pillow and DejaVu; required by v51 render workflow')
class CaptionLayoutTests(unittest.TestCase):
    def test_measured_wide_letters_stay_inside_safe_width(self):
        text='WWW WWW WWW WWW WWW WWW WWW WWW'
        result,size=layout(text)
        font=ImageFont.truetype(FONT,size)
        self.assertLessEqual(len(result.splitlines()),2)
        self.assertTrue(all(font.getlength(x)<=MAX_WIDTH for x in result.splitlines()))
        self.assertEqual(result.split(),text.split())

    def test_unbreakable_text_fails_instead_of_clipping(self):
        with self.assertRaises(ValueError): layout('W'*100)

    def test_literal_percent_and_half_open_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            result=filters(Path(d),[(0.,1.,'100% ilustrativo'),(1.,2.,'Não é um teste.')])
            self.assertIn('expansion=none',result[0])
            self.assertIn('lt(t,1.000000)',result[0])
            self.assertIn('gte(t,1.000000)',result[1])
            self.assertEqual((Path(d)/'caption-v51-0.txt').read_text(),'100% ilustrativo')

    def test_invalid_timings_rejected(self):
        for timings in [[(0,0,'a')],[(float('nan'),1,'a')],[(0,2,'a'),(1,3,'b')]]:
            with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError): filters(Path(d),timings)

    def test_unsafe_path_rejected(self):
        with self.assertRaises(ValueError): filters(Path("bad'name"),[(0,1,'a')])
