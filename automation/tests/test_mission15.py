"""Mission15 regressions; synthetic test recordings are not licensing evidence."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import chatterbox_v3 as cb
import voice_candidate_review as candidates
from asr_confirmation import resolve


class References15(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder);path=root/'unmute-lara.wav'
        with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(bytes(24000*2*8))
        path.chmod(0o600);sha=cb.digest(path)
        cfg={'license':'CC0-1.0','rights_evidence':['test-evidence-a','test-evidence-b'],'candidates':[{'id':'unmute-lara','sha256':sha,'commercial_synthesis_authorized':True}]}
        config=root/'candidates.json';config.write_text(json.dumps(cfg));return config,path,cfg

    def test_licensed_candidate_recovers_privately_and_consistently(self):
        with tempfile.TemporaryDirectory() as folder:
            config,path,cfg=self.fixture(folder)
            with patch.object(candidates,'CANDIDATES',config),patch('urllib.request.urlopen') as network:
                self.assertEqual(candidates.reference('unmute-lara',folder)[2],path)
                self.assertEqual(candidates.reference('unmute-lara',folder)[1]['sha256'],cb.digest(path))
            network.assert_not_called();self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)

    def test_unauthorized_reference_is_rejected_before_download(self):
        with tempfile.TemporaryDirectory() as folder:
            config,path,cfg=self.fixture(folder);cfg['candidates'][0]['commercial_synthesis_authorized']=False;config.write_text(json.dumps(cfg))
            with patch.object(candidates,'CANDIDATES',config),self.assertRaisesRegex(ValueError,'RIGHTS'):candidates.reference('unmute-lara',folder)

    def test_wrong_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            config,path,cfg=self.fixture(folder);path.write_bytes(b'changed')
            with patch.object(candidates,'CANDIDATES',config),self.assertRaisesRegex(ValueError,'HASH'):candidates.reference('unmute-lara',folder)

    def test_rights_alone_do_not_activate_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'identity.json';p.write_text(json.dumps({'status':'PENDING_PERCEPTUAL_REVIEW','commercial_synthesis_authorized':True,'perceptual_review_approved':False}))
            with self.assertRaisesRegex(ValueError,'REVIEW_PENDING'):cb.identity(p)

    def test_valid_approved_identity_stays_bound_to_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            _,path,_=self.fixture(folder);identity=Path(folder)/'identity.json'
            identity.write_text(json.dumps({'status':'APPROVED','locale':'pt-BR','gender':'female','commercial_synthesis_authorized':True,'rights_evidence':['test-synthetic-fixture'],'holder':'test fixture only','perceptual_review_approved':True,'reference_sha256':cb.digest(path)}))
            with patch.dict(os.environ,{'CHATTERBOX_REFERENCE_PATH':str(path)}):
                first=cb.identity(identity);second=cb.identity(identity)
                self.assertEqual(first,second)


class ASRConfirmation15(unittest.TestCase):
    def result(self,prob=.2):
        return {'audio_content_verified':False,'mismatches':[{'operation':'replace','recognized':['incerto']}],
                'words':[{'word':'incerto','probability':prob}]}
    def secondary(self):return {'audio_content_verified':True,'words':[{'word':'correto','probability':.99}]}

    def test_confident_conflict_is_not_approved(self):
        self.assertFalse(resolve(self.result(.99),self.secondary())['audio_content_verified'])
    def test_low_confidence_disputed_word_can_use_second_exact_observation(self):
        self.assertTrue(resolve(self.result(.2),self.secondary())['audio_content_verified'])
    def test_unrelated_uncertainty_does_not_erase_confident_wrong_word(self):
        p=self.result(.99);p['words'].append({'word':'a','probability':.1})
        self.assertFalse(resolve(p,self.secondary())['audio_content_verified'])
    def test_omission_or_truncation_needs_review(self):
        p=self.result();p['mismatches'].append({'operation':'delete','recognized':[]})
        self.assertFalse(resolve(p,self.secondary())['audio_content_verified'])
    def test_both_mismatching_models_do_not_approve(self):
        self.assertFalse(resolve(self.result(),self.result())['audio_content_verified'])


@unittest.skipUnless(importlib.util.find_spec('PIL') is not None,'Optional captions require Pillow; installed by mission proof workflow')
class Captions15(unittest.TestCase):
    def test_caption_does_not_begin_in_previous_utterances_pause(self):
        from caption_alignment import align
        rec={'audio_content_verified':True,'words':[{'word':'Confira.','start':0,'end':1},
            {'word':'Guarde.','start':1,'end':3}]}
        original=copy.deepcopy(rec)
        self.assertEqual(align(['Confira.','Guarde.'],rec,[(0,2,'Confira.'),(2,4,'Guarde.')]),
            [[0,1,'Confira.'],[2,3,'Guarde.']])
        self.assertEqual(rec,original)

    def test_wrong_utterance_provenance_does_not_retime_captions(self):
        from caption_alignment import align
        rec={'audio_content_verified':True,'words':[{'word':'Confira.','start':0,'end':1}]}
        with self.assertRaisesRegex(ValueError,'WINDOWS_INVALID'):
            align(['Confira.'],rec,[(0,2,'Guarde.')])

    def test_observed_words_define_caption_time_without_replacing_transcript(self):
        from caption_alignment import align
        rec={'audio_content_verified':True,'words':[{'word':'Confira','start':.2,'end':.5},{'word':'o','start':.5,'end':.6},{'word':'copo.','start':.6,'end':1.1}]}
        result=align(['Confira o copo.'],rec)
        self.assertEqual(result,[[.2,1.1,'Confira o copo.']])
        bad=copy.deepcopy(rec);bad['words'][-1]['word']='prato'
        with self.assertRaises(ValueError):align(['Confira o copo.'],bad)


class Resumption15(unittest.TestCase):
    def test_preferred_hours_do_not_create_phantom_publication_obligations(self):
        import datetime as dt
        from operational_health import missing_reservations
        now=dt.datetime(2026,11,27,20,tzinfo=dt.timezone.utc)
        self.assertEqual(missing_reservations({'posts':[]},{'posts':{}},now),[])
        due=(now-dt.timedelta(hours=3)).isoformat()
        queue={'posts':[{'id':'actual','approved':True,'scheduled_at':due}]}
        self.assertEqual(missing_reservations(queue,{'posts':{}},now),[due])
        state={'posts':{'actual':{'status':'CANCELLED_EDITORIAL','buffer_status':'deleted'}}}
        self.assertEqual(missing_reservations(queue,state,now),[])

    def test_old_complete_receipt_without_public_evidence_remains_an_incident(self):
        import datetime as dt
        import operational_health as health
        now=dt.datetime(2026,11,27,20,tzinfo=dt.timezone.utc)
        state={'posts':{'old':{'status':'PUBLISH_COMPLETE','publicly_verified':False}}}
        with patch.object(health,'stock_status',return_value={'refill_needed':0}):
            result=health.inspect({'posts':[]},state,{}, {},now)
        self.assertIn('old',result['active_incidents']['PUBLICATION_RECONCILIATION_REQUIRED']['details']['ids'])

    def test_three_saved_wan_scenes_wait_for_quota_instead_of_falsely_reporting_ready(self):
        from unittest.mock import Mock
        from experimental81 import wan104
        inventory={'version':1,'episode':6,'clips':[{'slot':i} for i in range(3)],'requests':{},'editorial_id':'copos-secos'}
        store=Mock();store.load.return_value=(inventory,'a');budget=Mock();budget.load.return_value=({},'b');client=Mock()
        with patch.object(wan104,'stores',return_value=(store,budget)),patch.object(wan104,'profile_check'),patch.object(wan104.legacy,'free_hf_identity',return_value=('anonymous',None)),patch.object(wan104,'quota_wait',return_value={'status':'WAIT_FREE_QUOTA','new_gpu_calls':0}) as wait:
            result=wan104.collect(trial=True,client_factory=client)
        self.assertEqual(result['status'],'WAIT_FREE_QUOTA');client.assert_not_called()
        self.assertEqual(len(inventory['clips']),3);self.assertEqual(wait.call_args.args[1]['seed'],104000+6*101+3)

    def test_repaired_queue_handoff_does_not_downgrade_publication_evidence(self):
        from unittest.mock import Mock
        from mission15_stage import register_output
        store=Mock();store.load.return_value=({'outputs':{'p':{'sha256':'a'*64,'status':'PUBLISH_COMPLETE','publicly_verified':True}}},'v1')
        with patch('video_stock.GitHubStore',return_value=store):register_output({'id':'p','quality':{'sha256':'a'*64}},'test-only')
        store.save.assert_not_called()


class OwnerApproval15(unittest.TestCase):
    def test_automatic_transcript_cannot_become_a_listening_approval(self):
        from voice_approval import approve
        with self.assertRaisesRegex(ValueError,'OWNER_LISTENING'):
            approve({}, {'actor':'ebooksproprof-dot','source':'ASR','run_id':'test','approved':True}, {})

    def test_changed_audio_reference_or_profile_stays_held(self):
        from mission15_stage import finalized_quality
        with self.assertRaisesRegex(ValueError,'VOICE_LISTENING'):
            finalized_quality({'status':'PENDING_PERCEPTUAL_REVIEW'}, {}, {}, {}, 'a'*64,'b'*64)


@unittest.skipUnless(importlib.util.find_spec('numpy') is not None,'Optional decoded frame analysis requires NumPy; installed by mission proof workflow')
class AuthoredMotion15(unittest.TestCase):
    def test_two_second_frozen_action_is_not_accepted_as_animation(self):
        from authored_motion import validate
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            video=Path(folder)/'frozen.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=white:s=1080x1920:r=30','-t','2',
                '-c:v','libx264','-threads','2','-preset','ultrafast',str(video)],check=True,timeout=30)
            with self.assertRaisesRegex(ValueError,'STATIC_OR_INVALID'):validate(video)


class ApprovedTransition15(unittest.TestCase):
    def fixture(self):
        from voice_approval import profile_digest
        root=Path(cb.__file__).parent
        voice=json.loads((root/'voice_identity.json').read_text())
        voice.update(status='APPROVED',gender='female',perceptual_review_approved=True)
        voice['review_receipt']={'engine_name':cb.NAME,'inference_sha256':profile_digest(voice['inference']),'source':'UNIT_TEST_FIXTURE_ONLY'}
        pack=root/'mission15-evidence/episode'
        return voice,json.loads((pack/'video-review.json').read_text()),json.loads((pack/'asr.json').read_text()),json.loads((pack/'audio-manifest.json').read_text())

    def test_approved_fixture_allows_transition_only_with_exact_bound_evidence(self):
        from mission15_stage import finalized_quality
        voice,q,a,m=self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'identity.json';path.write_text(json.dumps(voice))
            with patch.object(cb,'IDENTITY',path):
                result=finalized_quality(voice,q,a,m,q['sha256'],m['wav_sha256'])
                self.assertTrue(result['editorial_approved'])
                for mutation in ('wrong_wav','missing_content','unreviewed_visual'):
                    aa=copy.deepcopy(a);qq=copy.deepcopy(q);wav=m['wav_sha256']
                    if mutation=='wrong_wav':wav='0'*64
                    elif mutation=='missing_content':aa['audio_content_verified']=False
                    else:qq['visual_editorial_approved']=False
                    with self.assertRaises(ValueError):finalized_quality(voice,qq,aa,m,q['sha256'],wav)

    def test_unreviewed_parameter_change_cannot_reuse_identity_approval(self):
        from mission14_policy import require_output
        voice,q,a,m=self.fixture();voice['inference']['temperature']=.7
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'identity.json';path.write_text(json.dumps(voice))
            with patch.object(cb,'IDENTITY',path),self.assertRaisesRegex(ValueError,'PARAMETERS_CHANGED'):require_output(q)
