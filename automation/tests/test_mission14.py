"""Current mission gates. Synthetic media/simulated provider outcomes are labeled."""
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import chatterbox_v3 as cb
from framing import full_frame_filter
import mission14_policy as policy
import media_quality
import autonomous_production as producer


class VoiceAndPublishing14(unittest.TestCase):
    def test_missing_reference_blocks_before_model_download(self):
        with patch.object(cb,'acquire') as load:
            with self.assertRaisesRegex(ValueError,'REFERENCE_AND_REVIEW_PENDING'):
                cb.ChatterboxBrazilEngine('/unused')
            load.assert_not_called()

    def test_legacy_voice_or_unreviewed_output_never_publishes(self):
        with self.assertRaisesRegex(ValueError,'VOICE_IDENTITY_PENDING'):
            policy.require_output({'voice':'kokoro','duration':30,'technical_pass':True})
        import buffer_runner
        client=Mock()
        with patch.object(buffer_runner,'prepare',return_value={}), self.assertRaises(ValueError):
            buffer_runner.submit(client,{'quality':{}},{'posts':{}},'channel')
        client.call.assert_not_called()

    def test_both_publishers_enforce_contract_before_reservation(self):
        import stock_publish
        store=Mock();store.load.return_value=({'items':[{'id':'new','quality':{}}]},'v1')
        client=Mock()
        with self.assertRaises(ValueError): stock_publish.submit_one(store,client,'new','c',{},dt.datetime.now(dt.timezone.utc))
        client.call.assert_not_called();store.save.assert_not_called()

    def test_portrait_framing_rejects_horizontal_and_low_resolution(self):
        self.assertIn('setsar=1',full_frame_filter(1080,1920))
        with self.assertRaisesRegex(ValueError,'RECOMPOSITION'):full_frame_filter(1920,1080)
        with self.assertRaisesRegex(ValueError,'RESOLUTION_INSUFFICIENT'):full_frame_filter(480,832)

    def test_published_regression_cannot_be_reordered_into_new_tip(self):
        from editorial_policy import reason
        root=Path(cb.__file__).parent
        queue=json.loads((root/'queue.json').read_text());state=json.loads((root/'state.json').read_text())
        checked=0
        for key,receipt in state['posts'].items():
            lines=receipt.get('script_lines')
            if receipt.get('status')=='PUBLISH_COMPLETE' and lines and len(lines)>3:
                candidate={'id':'never-publish','concept':'new-id','script_lines':[lines[0],*reversed(lines[1:-1]),lines[-1]]}
                self.assertIsNotNone(reason(candidate,queue,state));checked+=1
        self.assertGreater(checked,5)


class Media14(unittest.TestCase):
    def test_real_ffmpeg_metadata_and_embedded_bars(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'full.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=s=1080x1920:r=30',
                '-t','1','-c:v','libx264','-threads','2','-preset','ultrafast','-pix_fmt','yuv420p',
                '-vf','setsar=1','-movflags','+faststart',str(path)],check=True,timeout=60)
            self.assertTrue(media_quality.vertical_contract(path)['faststart'])
            self.assertTrue(media_quality.embedded_borders(path)['embedded_border_check_pass'])
            barred=Path(folder)/'bars.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',
                'drawbox=x=0:y=0:w=iw:h=100:color=black:t=fill',
                '-c:v','libx264','-threads','2','-preset','ultrafast',str(barred)],check=True,timeout=60)
            with self.assertRaisesRegex(ValueError,'EMBEDDED_BLACK_BORDERS'): media_quality.embedded_borders(barred)


class Continuity14(unittest.TestCase):
    def test_eight_weeks_with_quota_wait_failure_restart_and_refill(self):
        queue={'posts':[]};state={'posts':{}};events=[]
        start=dt.datetime(2027,1,1,tzinfo=dt.timezone.utc)
        for day in range(56):
            now=start+dt.timedelta(days=day)
            # Simulated scarcity; no provider calls, generated visuals or fake public receipts.
            quota=day%4!=0
            temporary_failure=day%9==0
            if quota and not temporary_failure and producer.stock_status(queue,state,now)['ready']<2:
                key,when=producer.choose_slot(queue,state,now)
                queue['posts'].append({'id':key,'scheduled_at':when.isoformat(),'approved':True,
                    'consented_at':now.isoformat(),'quality':{'technical_pass':True},'simulation':True})
                events.append({'kind':'simulated_supply','at':when.isoformat(),'id':key})
            for post in queue['posts']:
                if dt.datetime.fromisoformat(post['scheduled_at']) <= now and post['id'] not in state['posts']:
                    state['posts'][post['id']]={'status':'SIMULATED_CONSUMED','scheduled_at':post['scheduled_at'],'simulation':True}
            queue,state=json.loads(json.dumps([queue,state]))  # Process restart.
        times=sorted(dt.datetime.fromisoformat(p['scheduled_at']) for p in queue['posts'])
        self.assertGreater(len(times),12)
        self.assertEqual(len({p['id'] for p in queue['posts']}),len(queue['posts']))
        for i,t in enumerate(times):
            self.assertLessEqual(sum(t-dt.timedelta(days=7)<x<=t for x in times),3)
            if i:self.assertGreaterEqual(t-times[i-1],dt.timedelta(hours=48))
        self.assertFalse(any(r.get('publicly_verified') for r in state['posts'].values()))


class AudioContent14(unittest.TestCase):
    def test_omission_repetition_and_pronunciation_uncertainty_are_held(self):
        from audio_review import compare
        self.assertTrue(compare('Confira a borda do copo.','Confira a borda do copo!')['audio_content_verified'])
        for observed in ['Confira o copo.','Confira a borda a borda do copo.','Confira a porta do copo.']:
            self.assertFalse(compare('Confira a borda do copo.',observed)['audio_content_verified'])

    def test_wan_30_requires_six_distinct_retained_slots(self):
        from experimental81.wan104 import next_scene
        from experimental81.wan104 import PROFILE
        profile=json.loads(PROFILE.read_text())
        inv={'episode':6,'editorial_id':'copos-secos','clips':[{'slot':i} for i in range(5)],'rejected_clips':[]}
        slot,spec=next_scene(inv,profile)
        self.assertEqual(slot,5)
        self.assertIn('Final wide view',spec['prompt'])
        inv['clips'].append({'slot':5})
        self.assertIsNone(next_scene(inv,profile))
