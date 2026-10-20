import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import visual_library as v

class VisualTests(unittest.TestCase):
    def test_same_footage_twice_within_one_video_blocks(self):
        record = dict(source_id='clip', sha256='a'*64, dhash=['0'*16]*5)
        with self.assertRaises(ValueError):
            v.check_sources([record, dict(record, source_id='renamed')], [])

    def test_flags_without_fingerprints_block(self):
        with self.assertRaises(ValueError):
            v.require_evidence({'quality': dict(visual_policy_version=1, visual_distinct=True)})

    def test_send_rechecks_archived_history(self):
        record = dict(source_id='used', sha256='a'*64, dhash=['0'*16]*5)
        post = {'quality': dict(visual_policy_version=1, visual_distinct=True, visual_sources=[record])}
        with self.assertRaises(ValueError):
            v.require_evidence(post, [dict(visual_sources=[record])])

    def test_same_asset_blocks_even_with_new_caption(self):
        with self.assertRaises(ValueError):
            v.check_sources([dict(source_id='old', sha256='a', dhash=[])], [dict(source_urls=['old'])])

    def test_renamed_identical_bytes_block(self):
        old = dict(source_id='old', sha256='a', dhash=[])
        with self.assertRaises(ValueError):
            v.check_sources([dict(old, source_id='new')], [dict(visual_sources=[old])])

    def test_reencoded_similar_frames_block(self):
        old = dict(source_id='old', sha256='a', dhash=['0'*16]*5)
        new = dict(source_id='new', sha256='b', dhash=['0'*15+'1']*5)
        with self.assertRaises(ValueError):
            v.check_sources([new], [dict(visual_sources=[old])])

    def test_different_scene_passes(self):
        old = dict(source_id='old', sha256='a', dhash=['0'*16]*5)
        new = dict(source_id='new', sha256='b', dhash=['f'*16]*5)
        self.assertTrue(v.check_sources([new], [dict(visual_sources=[old])])['visual_distinct'])

    def test_archived_sources_still_block(self):
        previous = v.history({'posts': []}, {'posts': {'published': {'source_urls': ['used']}}})
        self.assertFalse(v.preflight(['used'], previous))

    def test_unmeasured_media_is_not_publishable(self):
        with self.assertRaises(ValueError):
            v.require_evidence({'quality': {'technical_pass': True, 'editorial_approved': True}})
