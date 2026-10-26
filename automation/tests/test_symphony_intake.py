import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import symphony_intake as s


class SymphonyIntakeTests(unittest.TestCase):
    def setUp(self):
        self.config = s.load_config(s.ROOT/'automation/symphony.json')
        self.queue = {'schema_version': 1, 'items': []}
        self.script = 'Sua bancada vive cheia? Separe os utensílios que você usa todo dia e guarde o restante.'

    def test_config_cannot_enable_unimplemented_generation_or_change_identity(self):
        for key, value in [('generation_enabled', True), ('voice_name', 'Kokoro'),
                           ('avatar_id', 'another'), ('locale', 'pt-PT'),
                           ('fallback_voice_allowed', True), ('additional_budget_brl', 1)]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                data = dict(self.config, **{key: value})
                path = Path(folder)/'config.json'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    s.load_config(path)

    def test_duplicate_script_survives_disk_roundtrip(self):
        s.enqueue(self.queue, self.script, self.config)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'queue.json'
            s.save_queue(path, self.queue)
            recovered = json.loads(path.read_text())
            with self.assertRaises(ValueError):
                s.enqueue(recovered, '  ' + self.script.upper() + '\n', self.config)
            self.assertFalse(recovered['items'][0]['approved'])

    def candidate(self, folder):
        item = s.enqueue(self.queue, self.script, self.config)
        path = Path(folder)/'test.mp4'
        path.write_bytes(b'unit-test-placeholder' * 6000)
        manifest = dict(item['requested_identity'], script_sha256=item['script_sha256'],
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        source_evidence='Unit test only, not real Studio export')
        return item, path, manifest

    def test_identity_hash_script_or_evidence_mismatch_never_calls_validator(self):
        with tempfile.TemporaryDirectory() as folder:
            item, path, manifest = self.candidate(folder)
            for key, value in [('voice_name', 'other'), ('avatar_id', 'other'),
                               ('locale', 'en-US'), ('sha256', 'bad'),
                               ('script_sha256', 'bad'), ('source_evidence', '')]:
                with self.subTest(key=key), patch.object(s, 'validate') as validator:
                    before = copy.deepcopy(self.queue)
                    with self.assertRaises(ValueError):
                        s.attach(self.queue, item['id'], path, dict(manifest, **{key:value}), self.config)
                    validator.assert_not_called()
                    self.assertEqual(before, self.queue)

    def test_decode_failure_preserves_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            item, path, manifest = self.candidate(folder)
            before = copy.deepcopy(self.queue)
            with patch.object(s, 'validate', side_effect=ValueError('Decode failed')):
                with self.assertRaises(ValueError):
                    s.attach(self.queue, item['id'], path, manifest, self.config)
            self.assertEqual(before, self.queue)

    def test_technical_pass_does_not_verify_identity_lipsync_or_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            item, path, manifest = self.candidate(folder)
            with patch.object(s, 'validate', return_value={'technical_pass': True, 'lip_sync_verified': False}):
                s.attach(self.queue, item['id'], path, manifest, self.config)
            self.assertFalse(item['approved'])
            self.assertFalse(item['identity_verified'])
            self.assertFalse(item['lip_sync_verified'])
            self.assertEqual(item['local_media_path'], str(path.resolve()))
            self.assertFalse(item['media_persisted'])
            self.assertNotIn('publication_provider', item)
            with self.assertRaises(ValueError):
                s.attach(self.queue, item['id'], path, manifest, self.config)

    def test_duplicate_media_blocked_across_different_scripts(self):
        with tempfile.TemporaryDirectory() as folder:
            item, path, manifest = self.candidate(folder)
            with patch.object(s, 'validate', return_value={'technical_pass': True}):
                s.attach(self.queue, item['id'], path, manifest, self.config)
            other = s.enqueue(self.queue, 'Organize sua gaveta separando os objetos por uso, para encontrar tudo com mais facilidade.', self.config)
            manifest['script_sha256'] = other['script_sha256']
            with self.assertRaises(ValueError):
                s.attach(self.queue, other['id'], path, manifest, self.config)


if __name__ == '__main__':
    unittest.main()
