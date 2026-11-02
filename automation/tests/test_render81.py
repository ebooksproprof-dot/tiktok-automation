import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experimental81 import render

class Render81Tests(unittest.TestCase):
    def clips(self, ai, real):
        return [dict(kind='ai',duration=ai),dict(kind='real',duration=real)]

    def test_mix_selection_uses_actual_capacity(self):
        self.assertEqual(render.select_profile(self.clips(10,20)),'A')
        self.assertEqual(render.select_profile(self.clips(15,15)),'B')
        self.assertEqual(render.select_profile(self.clips(5,25)),'C')
        self.assertEqual(render.select_profile(self.clips(0,30)),'REFERENCE_ONLY')
        with self.assertRaises(ValueError):render.select_profile(self.clips(4,25))

    def test_no_fictional_ai_fallback(self):
        with self.assertRaises(ValueError):render.select_profile(self.clips(0,30),'A')
        self.assertEqual(render.PROFILES['REFERENCE_ONLY'],(0,30))

    def test_three_mix_plans_total_30_unique_intervals(self):
        for name,(ai,real) in render.PROFILES.items():
            clips=self.clips(ai,real); shots=render.plan(clips,name)
            self.assertAlmostEqual(sum(s['duration'] for s in shots),30)
            for index in range(2):
                selected=[s for s in shots if s['source_index']==index]
                previous=0
                for s in selected:
                    self.assertGreaterEqual(s['start'],previous)
                    previous=s['start']+s['duration']
                self.assertLessEqual(previous,clips[index]['duration']+.001)

    def test_plan_refuses_looping(self):
        with self.assertRaises(ValueError):render.plan(self.clips(0,5),'REFERENCE_ONLY')

    def test_duplicate_or_changed_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'clip.mp4';path.write_bytes(b'real fixture bytes')
            clip=dict(path=str(path),kind='real',sha256=render.sha(path),source_url='https://example.org/source',license_url='https://example.org/license')
            meta=dict(streams=[dict(codec_type='video',width=1080,height=1920)],format=dict(duration='30'))
            with patch.object(render,'probe',return_value=meta):
                with self.assertRaisesRegex(ValueError,'duplicate'):render.inspect_clips([clip,clip])
                wrong=dict(clip,sha256='0'*64)
                with self.assertRaisesRegex(ValueError,'hash'):render.inspect_clips([wrong])

    def test_ai_needs_evidence_and_review(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'clip.mp4';path.write_bytes(b'fixture')
            item=dict(path=str(path),kind='ai',sha256=render.sha(path),source_url='https://example.org/source',license_url='https://example.org/license')
            with self.assertRaisesRegex(ValueError,'generation evidence'):render.inspect_clips([item])

    def test_requires_experimental_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'experimental-only'):render.compose({},folder)

    def test_identity_survives_new_workspace_and_changes_with_bytes(self):
        manifest={'clips':[{'path':'/old/a.mp4','sha256':'a'}], 'narration':{'path':'/old/n.wav','sha256':'b'}}
        moved=copy.deepcopy(manifest)
        moved['clips'][0]['path']='/new/a.mp4';moved['narration']['path']='/new/n.wav'
        self.assertEqual(render.input_identity(manifest,'A'),render.input_identity(moved,'A'))
        moved['clips'][0]['sha256']='c'
        self.assertNotEqual(render.input_identity(manifest,'A'),render.input_identity(moved,'A'))

    def test_explicit_source_offset_preserved_no_repeat(self):
        clips=[dict(kind='real',duration=5,source_offset=5),dict(kind='real',duration=25)]
        shots=render.plan(clips,'REFERENCE_ONLY')
        self.assertEqual(shots[0]['start'],5)
        self.assertEqual(shots[0]['duration'],5)

    def test_no_production_state_paths_or_publish_calls(self):
        code=Path(render.__file__).read_text()
        for forbidden in ('queue.json','state.json','createPost','video/init','stock_publish','BUFFER_API_KEY','TIKTOK_ACCESS_TOKEN'):
            self.assertNotIn(forbidden,code)

if __name__=='__main__':unittest.main()
