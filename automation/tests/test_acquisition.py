import sys
import unittest
import tempfile
import hashlib
import io
import json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_acquisition as m


def video():
    return dict(id=123, url='https://www.pexels.com/video/cleaning-kitchen-123/',
        duration=35, user={'name': 'Author'}, video_files=[dict(file_type='video/mp4',
        width=1080, height=1920, link='https://videos.pexels.com/video-files/123/a.mp4')])


class AcquisitionTests(unittest.TestCase):
    def test_recovery_requires_original_sha(self):
        for expected, succeeds in [(hashlib.sha256(b'original').hexdigest(), True), ('0'*64, False)]:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)/'automation'; root.mkdir()
                record = dict(provider='pexels', provider_id='123', sha256=expected,
                              url='https://videos.pexels.com/video-files/123/a.mp4')
                (root/'media_inbox.json').write_text(json.dumps({'items': [record]}))
                with patch.object(m, 'ROOT', root), patch.object(m, 'request', return_value=io.BytesIO(b'original')):
                    if succeeds:
                        m.recover('123')
                    else:
                        with self.assertRaisesRegex(m.AcquisitionError, 'RECOVERY_SHA_MISMATCH'):
                            m.recover('123')
                self.assertEqual((Path(tmp)/'tmp/media-inbox/pexels-123.mp4').exists(), succeeds)

    def select(self, v):
        return m.candidates([v], 'cozinha', 'cleaning kitchen', ['cleaning', 'kitchen'])

    def test_contextual_vertical_candidate_is_not_approval(self):
        result = self.select(video())[0]
        self.assertFalse(result['editorial_approved'])
        self.assertFalse(result['semantic_verified'])
        self.assertIn('Author', result['attribution'])

    def test_unrelated_scene_rejected(self):
        v = video(); v['url'] = 'https://www.pexels.com/video/a-garden-123/'
        self.assertEqual(self.select(v), [])

    def test_short_scene_rejected(self):
        v = video(); v['duration'] = 12
        self.assertEqual(self.select(v), [])

    def test_horizontal_rejected(self):
        v = video(); v['video_files'][0].update(width=1920, height=1080)
        self.assertEqual(self.select(v), [])

    def test_unknown_origin_rejected(self):
        v = video(); v['video_files'][0]['link'] = 'https://evil.example/a.mp4'
        self.assertEqual(self.select(v), [])

    def test_author_required(self):
        v = video(); v['user']['name'] = ''
        self.assertEqual(self.select(v), [])

    def test_url_credentials_query_and_port_rejected(self):
        for url in ['https://user@videos.pexels.com/a', 'https://videos.pexels.com:444/a',
                    'https://videos.pexels.com/a?key=hidden', 'http://videos.pexels.com/a']:
            self.assertFalse(m.safe_url(url, 'videos.pexels.com'))

    def test_cache_prevents_request(self):
        p = m.PexelsProvider('test-only', {'q': {'at': 100, 'videos': [video()]}}, now=101)
        with patch.object(m, 'request', side_effect=AssertionError('network')):
            self.assertEqual(len(p.search('q')), 1)

    def test_missing_key_explicit(self):
        with self.assertRaisesRegex(m.AcquisitionError, 'PEXELS_API_KEY_MISSING'):
            m.PexelsProvider('', {})

    def test_redirect_rejected(self):
        with self.assertRaises(m.AcquisitionError):
            m.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example')
