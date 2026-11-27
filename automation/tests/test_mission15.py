"""Mission15 regressions; synthetic test recordings are not licensing evidence."""
import copy
import hashlib
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
