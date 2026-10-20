import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_acquisition as a
import media_providers as p


def commons(license_url='https://creativecommons.org/licenses/by/4.0/'):
    return dict(pageid=42, title='File:Cleaning kitchen.webm', imageinfo=[dict(
        width=1080, height=1920, mime='video/webm', size=12345,
        url='https://upload.wikimedia.org/wikipedia/commons/a/ab/Kitchen.webm',
        descriptionurl='https://commons.wikimedia.org/wiki/File:Cleaning_kitchen.webm',
        extmetadata={'Artist': {'value': '<a>Author</a>'},
                     'LicenseUrl': {'value': license_url}})])


def pixabay():
    return dict(id=42, tags='cleaning, kitchen', duration=35, user='Creator',
        pageURL='https://pixabay.com/videos/id-42/', videos={'large': dict(width=1080,
        height=1920, size=12345, url='https://cdn.pixabay.com/video/42.mp4')})


class ProviderTests(unittest.TestCase):
    def test_pixabay_context_and_credits(self):
        provider = p.PixabayProvider('mock-key', {})
        with patch.object(provider, 'json', return_value={'hits': [pixabay()]}):
            r = provider.search('cozinha', 'cleaning kitchen', ['cleaning', 'kitchen'])[0]
        self.assertFalse(r['editorial_approved'])
        self.assertEqual(r['author'], 'Creator')
        self.assertIn('Pixabay', p.credits([r]))

    def test_pixabay_rejects_unrelated_and_horizontal(self):
        for field in ['context', 'geometry']:
            hit = pixabay()
            if field == 'context': hit['tags'] = 'garden'
            else: hit['videos']['large']['width'] = 1920
            provider = p.PixabayProvider('mock-key', {})
            with patch.object(provider, 'json', return_value={'hits': [hit]}):
                self.assertEqual(provider.search('cozinha', 'kitchen', ['kitchen']), [])

    def test_missing_pixabay_key(self):
        with self.assertRaisesRegex(a.AcquisitionError, 'PIXABAY_API_KEY_MISSING'):
            p.PixabayProvider('', {})

    def test_cache_never_contains_request_key(self):
        cache = {}; provider = p.PixabayProvider('secret-test-value', cache, now=100)
        with patch.object(p, 'request', return_value=io.BytesIO(b'{"hits": []}')) as request:
            provider.search('cozinha', 'kitchen', ['kitchen'])
            provider.search('cozinha', 'kitchen', ['kitchen'])
        self.assertEqual(request.call_count, 1)
        self.assertNotIn('secret-test-value', json.dumps(cache))

    def test_expired_cache_requests_again(self):
        provider = p.WikimediaProvider({'wikimedia:q': {'at': 1, 'data': {}}}, now=90000)
        with patch.object(p, 'request', return_value=io.BytesIO(b'{}')) as request:
            provider.json('q', 'https://commons.wikimedia.org/w/api.php')
        self.assertEqual(request.call_count, 1)

    def test_request_budget(self):
        provider = p.WikimediaProvider({}); provider.requests = 4
        with self.assertRaisesRegex(a.AcquisitionError, 'BUDGET'):
            provider.json('q', 'https://commons.wikimedia.org/w/api.php')

    def test_maxlag_is_not_cached(self):
        cache = {}; provider = p.WikimediaProvider(cache)
        with patch.object(p, 'request', return_value=io.BytesIO(b'{"error":{"code":"maxlag"}}')):
            with self.assertRaises(a.AcquisitionError): provider.json('q', 'https://commons.wikimedia.org/w/api.php')
        self.assertEqual(cache, {})

    def test_commons_ccby_credit_includes_license_author_and_changes(self):
        r = p.commons_record(commons(), 'cozinha', 'kitchen', ['kitchen'])
        self.assertIsNotNone(r)
        text = p.credits([r])
        for required in ['Author', 'CC BY 4.0', 'creativecommons.org', 'Adapted:', 'commons.wikimedia.org']:
            self.assertIn(required, text)

    def test_commons_rejects_unknown_restrictive_and_sharealike(self):
        for license_url in ['', 'https://creativecommons.org/licenses/by-nc/4.0/',
            'https://creativecommons.org/licenses/by-nd/4.0/',
            'https://creativecommons.org/licenses/by-sa/4.0/', 'https://evil.example/license']:
            self.assertIsNone(p.commons_record(commons(license_url), 'cozinha', 'kitchen', ['kitchen']))

    def test_commons_missing_author_or_restrictions_rejected(self):
        for key, value in [('Artist', ''), ('Restrictions', 'personality rights')]:
            record = commons(); record['imageinfo'][0]['extmetadata'][key] = {'value': value}
            self.assertIsNone(p.commons_record(record, 'cozinha', 'kitchen', ['kitchen']))

    def test_commons_cc0_accepted(self):
        r = p.commons_record(commons('https://creativecommons.org/publicdomain/zero/1.0/'),
                             'cozinha', 'kitchen', ['kitchen'])
        self.assertFalse(r['attribution_required'])

    def test_provider_origin_binding(self):
        self.assertFalse(a.media_allowed(dict(provider='pixabay', url='https://videos.pexels.com/a.mp4')))
        self.assertTrue(a.media_allowed(dict(provider='wikimedia', url='https://upload.wikimedia.org/a.webm')))

    def test_fallback_without_keys_and_provider_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'automation'; root.mkdir()
            with patch.object(a, 'ROOT', root), patch.dict(a.os.environ,
                {'MEDIA_PROVIDER_ORDER': 'pixabay,wikimedia,pexels', 'PEXELS_API_KEY': '', 'PIXABAY_API_KEY': ''}), \
                patch.object(p.WikimediaProvider, 'search', side_effect=a.AcquisitionError('PROVIDER_REQUEST_FAILED')) as search:
                with self.assertRaisesRegex(a.AcquisitionError, 'NO_NEW_REVIEWABLE_MEDIA'): a.run()
            self.assertEqual(search.call_count, 1)
            self.assertTrue((root/'media_inbox.json').exists())

    def test_wikimedia_recovery_preserves_webm_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'automation'; root.mkdir()
            record = p.commons_record(commons(), 'cozinha', 'kitchen', ['kitchen'])
            record['sha256'] = hashlib.sha256(b'video').hexdigest()
            (root/'media_inbox.json').write_text(json.dumps({'items': [record]}))
            with patch.object(a, 'ROOT', root), patch.object(a, 'request', return_value=io.BytesIO(b'video')):
                a.recover('wikimedia:42')
            self.assertTrue((root.parent/'tmp/media-inbox/wikimedia-42.webm').exists())
            self.assertIn('Author', (root.parent/'tmp/media-inbox/wikimedia-42.credits.txt').read_text())

    def test_rejected_first_provider_does_not_starve_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'automation'; root.mkdir()
            first = dict(provider='pixabay', provider_id='1')
            second = p.commons_record(commons(), 'cozinha', 'kitchen', ['kitchen'])
            measured = dict(second, sha256='a'*64, dhash=['0'*16]*5)
            def measure(record, folder, previous):
                if record['provider'] == 'pixabay': raise a.AcquisitionError('MEDIA_TECHNICAL_REJECTED')
                return measured
            with patch.object(a, 'ROOT', root), patch.dict(a.os.environ,
                {'MEDIA_PROVIDER_ORDER': 'pixabay,wikimedia', 'PIXABAY_API_KEY': 'mock'}), \
                patch.object(p.PixabayProvider, 'search', return_value=[first]*10), \
                patch.object(p.WikimediaProvider, 'search', return_value=[second]), \
                patch.object(a, 'download_and_measure', side_effect=measure):
                a.run()
            saved = json.loads((root/'media_inbox.json').read_text())
            self.assertEqual(saved['items'][0]['provider'], 'wikimedia')
