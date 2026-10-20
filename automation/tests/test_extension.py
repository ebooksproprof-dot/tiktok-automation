import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalog_extension as e

class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.item = dict(id='novo-tema', reviewed=True, reviewed_at='2026-10-20',
            category='organizacao', hook='Organize uma gaveta.', steps='Organize os objetos por categoria. '*6,
            cta='Salve esta dica.', media=[dict(id='novo-clip',
            url='https://videos.pexels.com/video-files/123/clip.mp4',
            source_page='https://www.pexels.com/video/123/', license_url='https://www.pexels.com/license/',
            author='Test fixture only', context='Gaveta organizada por categoria.', sha256='a'*64)])
    def load(self, items):
        with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'read_text',
                return_value=json.dumps(dict(version=1, items=items))):
            return e.load(Path('/not-a-real-catalog'))
    def test_valid_reviewed_pack(self):
        self.assertEqual(len(self.load([self.item])[1]), 1)
    def test_no_review_refuses(self):
        self.item['reviewed'] = False
        with self.assertRaises(ValueError): self.load([self.item])
    def test_unknown_host_refuses(self):
        self.item['media'][0]['url'] = 'https://example.com/video.mp4'
        with self.assertRaises(ValueError): self.load([self.item])
    def test_license_required(self):
        del self.item['media'][0]['license_url']
        with self.assertRaises(ValueError): self.load([self.item])
    def test_duplicate_id_refuses(self):
        with self.assertRaises(ValueError): self.load([self.item, copy.deepcopy(self.item)])
    def test_traversal_refuses(self):
        self.item['media'][0]['id'] = '../escape'
        with self.assertRaises(ValueError): self.load([self.item])
