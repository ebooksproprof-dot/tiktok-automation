import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stock_import as s
import video_stock as v


SCRIPT = 'Sua bancada vive cheia? Separe os utensílios que você usa todo dia e guarde o restante.'


def asset(name, size=123456, asset_id=1):
    return dict(id=asset_id, name=name, size=size, state='uploaded',
                browser_download_url=f'https://github.com/{s.REPO}/releases/download/stock-inbox/{name}',
                created_at='2026-10-27T10:00:00Z')


def manifest(digest='a'*64):
    return dict(s.IDENTITY, **{key: True for key in s.ATTESTATIONS},
                script=SCRIPT, topic='Organização de bancada', caption='Organize sua bancada hoje.',
                source_evidence='Symphony export reviewed by owner; test fixture only', sha256=digest,
                reviewed_at='2026-10-27T11:00:00Z', commercial_content=False)


class StockImportTests(unittest.TestCase):
    def test_manifest_preserves_identity_and_requires_all_reviews(self):
        good = manifest()
        s.manifest_check(good)
        mutations = [(key, False) for key in s.ATTESTATIONS]
        mutations += [('voice_name', 'Other'), ('avatar_id', 'wrong'), ('locale', 'pt-PT'),
                      ('commercial_content', None), ('reviewed_at', '2026-10-27'),
                      ('reviewed_at', '2999-01-01T00:00:00Z'), ('sha256', 'bad'),
                      ('source_evidence', 'https://example.com/?token=secret')]
        for key, value in mutations:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                s.manifest_check(dict(good, **{key: value}))

    def test_only_known_public_release_downloads(self):
        good = asset('video.mp4')
        self.assertTrue(s.safe_asset_url(good).endswith('video.mp4'))
        for key, value in [('browser_download_url', 'https://attacker.example/video.mp4'),
                           ('name', '../video.mp4'), ('state', 'starter')]:
            with self.assertRaises(ValueError):
                s.safe_asset_url(dict(good, **{key: value}))

    def test_missing_pair_and_known_assets_do_not_download(self):
        with patch.object(s, 'list_assets', return_value=[asset('one.mp4'), asset('two.mp4', asset_id=2)]), \
             patch.object(s, 'download') as download:
            report = s.scan('test', lambda _: True, known_asset_ids=[2])
        self.assertEqual(report['waiting_for_manifest'], [1])
        self.assertEqual(report['skipped'], [2])
        download.assert_not_called()

    def test_hash_and_legacy_duplicate_rejected_before_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder)/'test.mp4'
            media.write_bytes(b'simulated only')
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            with patch.object(s, 'validate') as validator:
                with self.assertRaisesRegex(ValueError, 'HASH'):
                    s.prepare_candidate(asset('one.mp4'), manifest(), media)
                with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
                    s.prepare_candidate(asset('one.mp4'), manifest(digest), media,
                                        legacy_state={'posts': {'old': {'sha256': digest}}})
                with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
                    s.prepare_candidate(asset('one.mp4'), manifest(digest), media,
                                        legacy_queue={'posts': [{'script_lines': [SCRIPT]} ]})
                validator.assert_not_called()

    def test_incomplete_download_reports_retry_without_approval(self):
        pairs = [asset('one.mp4'), asset('one.json', asset_id=2)]
        with patch.object(s, 'list_assets', return_value=pairs), \
             patch.object(s, 'download', side_effect=ValueError('secret content')), \
             patch.object(s, 'prepare_candidate') as prepare:
            report = s.scan('test', lambda _: self.fail('No insertion after failed download'))
        self.assertEqual(report['errors'], [{'asset_id': 1, 'error': 'ValueError', 'code': 'IMPORT_FAILED', 'retryable_import': True}])
        self.assertNotIn('secret', json.dumps(report))
        prepare.assert_not_called()

    def test_new_pair_detected_and_stored_once_after_restart(self):
        data = b'simulated MP4 not real media' * 5000
        digest = hashlib.sha256(data).hexdigest()
        video = asset('one.mp4', len(data))
        pairs = [video, asset('one.json', asset_id=2)]
        def download(a, path, limit):
            Path(path).write_bytes(json.dumps(manifest(digest)).encode() if a['name'].endswith('.json') else data)
        with tempfile.TemporaryDirectory() as folder:
            store = v.LocalStore(Path(folder)/'stock.json')
            def accept(item):
                state, rev = store.load()
                v.add_video(state, item, v.instant('2026-10-28T00:00:00Z'))
                store.save(state, rev)
            quality = dict(technical_pass=True, sha256=digest, duration=16, lip_sync_verified=False)
            with patch.object(s, 'list_assets', return_value=pairs), patch.object(s, 'download', side_effect=download), \
                 patch.object(s, 'validate', return_value=quality):
                self.assertEqual(s.scan('test', accept)['imported'], [1])
                restarted = v.LocalStore(Path(folder)/'stock.json')
                state, _ = restarted.load()
                self.assertEqual(len(state['items']), 1)
                self.assertEqual(state['items'][0]['status'], 'READY')
                self.assertFalse(state['items'][0]['quality']['lip_sync_verified'])
                result = s.scan('test', accept, known_asset_ids=[1])
                self.assertEqual(result['skipped'], [1])
                self.assertEqual(len(restarted.load()[0]['items']), 1)

    def test_manifest_cli_hashes_exact_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            media, script = Path(folder)/'sample.mp4', Path(folder)/'script.txt'
            media.write_bytes(b'unit-test-only')
            script.write_text(SCRIPT)
            argv = ['stock_import.py', 'manifest', '--video', str(media), '--script-file', str(script),
                    '--topic', 'Organization', '--caption', 'Example', '--source-evidence', 'Unit test only',
                    '--commercial-content', 'false', '--reviewed-all']
            with patch.object(sys, 'argv', argv), patch('builtins.print'):
                s.main()
                with self.assertRaises(FileExistsError):
                    s.main()
            data = json.loads(media.with_suffix('.json').read_text())
            self.assertEqual(data['sha256'], hashlib.sha256(media.read_bytes()).hexdigest())
            self.assertIs(data['commercial_content'], False)
            self.assertTrue(data['publication_approved'])

    def test_import_metadata_survives_core_and_publication_preflight(self):
        import stock_publish
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder)/'test.mp4'
            media.write_bytes(b'simulated only')
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            quality = dict(technical_pass=True, sha256=digest, duration=16)
            with patch.object(s, 'validate', return_value=quality):
                candidate = s.prepare_candidate(asset('one.mp4'), manifest(digest), media)
            now = v.instant('2026-10-28T10:00:00Z')
            state = v.empty()
            item = v.add_video(state, candidate, now)
            v.schedule(state, now)
            self.assertEqual(stock_publish.check_item(item, {'posts': {}}, {'posts': []}, now),
                             v.instant('2026-10-28T13:00:00Z'))
            item['commercial_content'] = True
            with self.assertRaisesRegex(ValueError, 'Commercial'):
                stock_publish.check_item(item, {'posts': {}}, {'posts': []}, now)

    def test_release_pagination_and_draft_rejection(self):
        with patch.object(s, 'request', side_effect=[{'id': 3, 'tag_name': s.TAG, 'draft': False},
                                                     [asset(f'{i}.mp4', asset_id=i) for i in range(100)], []]) as req:
            self.assertEqual(len(s.list_assets('test')), 100)
            self.assertIn('page=2', req.call_args.args[0])
        with patch.object(s, 'request', return_value={'id': 3, 'tag_name': s.TAG, 'draft': True}):
            with self.assertRaises(ValueError):
                s.list_assets('test')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Real FFmpeg required')
class StockImportMediaIntegrationTests(unittest.TestCase):
    """Real synthetic MP4 decode tests. No Symphony identity or publication proof."""
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.good = Path(cls.temp.name)/'good.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=1080x1920:rate=5',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '16',
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '29', '-threads', '2',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.good)], check=True, timeout=60)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_mp4_import_and_format_duration_audio_failures(self):
        digest = hashlib.sha256(self.good.read_bytes()).hexdigest()
        result = s.prepare_candidate(asset('good.mp4', self.good.stat().st_size), manifest(digest), self.good)
        self.assertEqual(result['duration'], 16)
        self.assertTrue(result['quality']['technical_pass'])
        self.assertFalse(result['quality']['lip_sync_verified'])
        cases = {'short': ['-t', '2', '-c', 'copy'], 'noaudio': ['-an', '-c:v', 'copy'],
                 'wrongshape': ['-vf', 'scale=540:960', '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '2', '-c:a', 'copy']}
        for name, options in cases.items():
            with self.subTest(name=name):
                path = Path(self.temp.name)/(name + '.mp4')
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(self.good), *options, str(path)],
                               check=True, timeout=60)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):
                    s.prepare_candidate(asset(name + '.mp4', path.stat().st_size), manifest(digest), path)


if __name__ == '__main__':
    unittest.main()
