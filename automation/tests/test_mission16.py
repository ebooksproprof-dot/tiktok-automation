"""Mission16 regression fixtures are simulations, never perceptual evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import photoreal_policy as policy


class RejectedIllustration16(unittest.TestCase):
    def quality(self):
        return json.loads((Path(policy.__file__).parent/'mission15-evidence/episode/video-review.json').read_text())

    def test_approved_voice_cannot_reactivate_owners_visual_rejection(self):
        from mission15_stage import finalized_quality
        q=self.quality();q.update(technical_pass=True,visual_editorial_approved=True)
        with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):
            finalized_quality({'status':'APPROVED','perceptual_review_approved':True},q,{}, {},q['sha256'],'a'*64)

    def test_removing_origin_metadata_does_not_remove_rejection_of_the_file(self):
        q=self.quality();q.pop('video_origin',None);q.update(visual_style='photorealistic')
        with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):policy.reject_incompatible(q)

    def test_visual_rejection_precedes_voice_and_fingerprint_approval(self):
        from mission14_policy import require_output
        from visual_library import require_evidence
        q=self.quality()
        for check in (lambda:require_output(q),lambda:require_evidence({'quality':q})):
            with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):check()

    def test_buffer_never_receives_rejected_visual_even_if_prepare_and_voice_pass(self):
        import buffer_runner
        from unittest.mock import Mock
        client=Mock()
        with patch.object(buffer_runner,'prepare',return_value={}),self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):
            buffer_runner.submit(client,{'quality':self.quality()},{'posts':{}},'fixture-channel')
        client.call.assert_not_called();client.check_budget.assert_not_called()


class WanQualityTrial16(unittest.TestCase):
    def test_trial_stays_inside_documented_controls_and_preserves_legacy_profile(self):
        from experimental81 import wan16,wan104
        profile=json.loads(wan104.PROFILE.read_text());before=copy.deepcopy(profile)
        request=wan16.spec(profile,0)
        self.assertEqual((request['width'],request['height'],request['steps']),(576,1024,8))
        self.assertEqual(profile,before)
        self.assertEqual(request['reference_kind'],'authored_text_only')
        self.assertEqual(request['space_revision'],profile['space_revision'])

    def test_known_request_is_not_submitted_again(self):
        from experimental81 import wan16,wan104,hf_probe
        from unittest.mock import Mock
        profile=json.loads(wan104.PROFILE.read_text());fingerprint=hf_probe.fingerprint(wan16.spec(profile,0))
        store=Mock();store.load.return_value=({'requests':{fingerprint:{'status':'UNKNOWN_NO_RETRY'}}},'v1')
        with patch.dict('os.environ',{'GH_TOKEN':'fixture-only'}),patch.object(wan16,'GitHubStore',return_value=store),patch.object(wan104,'profile_check'),patch.object(wan16.auto_collect,'free_hf_identity',return_value=('anonymous',None)):
            self.assertEqual(wan16.run(slot=0)['new_gpu_calls'],0)
        store.save.assert_not_called()

    def test_auto_plan_does_not_retry_missing_or_uncertain_first_shots(self):
        from experimental81 import wan16
        inv={'requests':{'first':{'spec':{'seed':160001},'status':'UNKNOWN_NO_RETRY'},
            'second':{'spec':{'seed':160002},'status':'GENERATED_DURABLE_PENDING_VISUAL_REVIEW'}}}
        self.assertEqual(wan16.next_unrequested(inv),2)
        for seed in range(160003,160009):inv['requests'][str(seed)]={'spec':{'seed':seed},'status':'FAILED_PROVIDER_NO_OUTPUT'}
        self.assertIsNone(wan16.next_unrequested(inv))

    def test_legacy_scheduled_collector_does_not_generate_480p_for_professional_stock(self):
        from experimental81 import wan104
        with patch('sys.argv',['wan104.py']),patch.dict('os.environ',{'GITHUB_ACTIONS':'true',
            'GITHUB_WORKFLOW':'CasaSemEsforco AI30 Free Collector','GITHUB_REF_NAME':'main'}),patch.object(wan104,'collect') as generate:
            self.assertEqual(wan104.main()['new_gpu_calls'],0)
        generate.assert_not_called()


class SourceDefinition16(unittest.TestCase):
    def test_upscaling_low_resolution_does_not_approve_original_definition(self):
        from visual_source_probe import probe
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'original.mp4';export=Path(folder)/'1080p.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=480x832:rate=1',
                '-t','1','-c:v','libx264','-threads','1',str(src)],check=True)
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-vf','scale=1080:1920',
                '-c:v','libx264','-threads','1',str(export)],check=True)
            self.assertEqual(probe(export)['native_dimensions'],[1080,1920])
            original=probe(src)
            with self.assertRaisesRegex(ValueError,'NATIVE_DEFINITION_INSUFFICIENT'):
                policy.definition(*original['native_dimensions'],original['portrait_crop'])

    def test_1024_material_needs_comparison_and_cannot_be_called_native_full_hd(self):
        with self.assertRaisesRegex(ValueError,'COMPARISON'):policy.definition(576,1024,[0,0,576,1024])
        review={'approved':True,'method':'lanczos','invented_detail':False,'reviewer':'SIMULATED TEST ONLY','comparison_artifact':'fixture'}
        result=policy.definition(576,1024,[0,0,576,1024],review)
        self.assertFalse(result['native_full_hd']);self.assertEqual(result['upscale_factor'],1.875)
        self.assertTrue(policy.definition(1080,1920,[0,0,1080,1920])['native_full_hd'])


class PhotorealEvidence16(unittest.TestCase):
    def fixture(self):
        # Explicit synthetic registry used only in unit tests.
        source='a'*64;video='b'*64
        registry={'sources':{source:{'source_sha256':source,'status':'APPROVED','style':'photorealistic',
            'commercial_rights_verified':True,'reviewer':'SIMULATED FIXTURE','human_review':False,
            'sequence_artifact':'fixture','native_probe_artifact':'fixture','native_dimensions':[720,1280],
            'portrait_crop':[0,0,720,1280],'criteria':{k:True for k in policy.CRITERIA}}},
            'videos':{video:{'video_sha256':video,'status':'APPROVED','policy_version':16,'id':'fixture',
                'reviewer':'SIMULATED FIXTURE','human_review':False,'sequence_artifact':'fixture',
                'method':'assistant_sequence_review_with_decoded_motion','criteria':{k:True for k in policy.CRITERIA},'source_sha256':[source]}}}
        q={'sha256':video,'photorealistic_review_id':'fixture','visual_editorial_approved':True,'visual_sources':[{'sha256':source}]}
        return registry,q

    def test_technical_and_style_labels_cannot_substitute_for_a_visual_review(self):
        with self.assertRaisesRegex(ValueError,'FINAL_VISUAL_REVIEW'):
            policy.require_photoreal({'sha256':'b'*64,'technical_pass':True,'visual_style':'photorealistic'},{'sources':{},'videos':{}})

    def test_bound_full_review_requires_all_eight_criteria(self):
        registry,q=self.fixture();self.assertEqual(policy.require_photoreal(q,registry)['id'],'fixture')
        for key in policy.CRITERIA:
            bad=copy.deepcopy(registry);bad['videos'][q['sha256']]['criteria'][key]=False
            with self.assertRaises(ValueError):policy.require_photoreal(q,bad)

    def test_changed_source_cannot_reuse_review_and_native_dimensions(self):
        registry,q=self.fixture();q['visual_sources'][0]['sha256']='c'*64
        with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):policy.require_photoreal(q,registry)

    def test_source_rights_and_review_are_independent(self):
        registry,q=self.fixture();next(iter(registry['sources'].values()))['commercial_rights_verified']=False
        with self.assertRaisesRegex(ValueError,'SOURCE_REVIEW'):policy.require_photoreal(q,registry)

    def test_four_weeks_without_qualified_sources_do_not_create_stock_or_publications(self):
        from experimental81 import daily_budget
        import datetime as dt
        ledger=daily_budget.fresh();events=[];state={'requests':{},'outputs':{}}
        start=dt.datetime(2026,12,1,tzinfo=dt.timezone.utc)
        for day in range(28):
            now=start+dt.timedelta(days=day)
            for attempt in range(3):
                key=format(day*3+attempt+1,'064x')
                try:ledger=daily_budget.reserve(ledger,key,now,tier='free',estimated_seconds=110)
                except daily_budget.QuotaError:
                    events.append({'day':day,'status':'WAIT_FREE_QUOTA','simulation':True});continue
                status='PROVIDER_FAILED' if day%7==0 else 'GENERATED_AWAITING_VISUAL_REVIEW'
                state['requests'][key]={'status':status,'simulation':True}
                q={'sha256':key,'technical_pass':True,'visual_style':'photorealistic'}
                with self.assertRaises(ValueError):policy.require_photoreal(q,{'sources':{},'videos':{}})
            ledger,state=json.loads(json.dumps([ledger,state]))  # Durable restart.
        self.assertEqual(len(ledger['claims']),56)
        self.assertEqual(len(events),28)
        self.assertTrue(any(r['status']=='PROVIDER_FAILED' for r in state['requests'].values()))
        self.assertEqual(state['outputs'],{})
        self.assertFalse(any(e.get('publicly_verified') for e in events))


class OfficialAcquisition16(unittest.TestCase):
    def test_nonphotoreal_provider_tags_are_rejected_before_download(self):
        from media_providers import PixabayProvider
        hit={'id':42,'tags':'kitchen, glass, vector animation','duration':8,'user':'Fixture',
            'pageURL':'https://pixabay.com/videos/id-42/','videos':{'large':{'width':1080,'height':1920,
            'size':1000,'url':'https://cdn.pixabay.com/video/42.mp4'}}}
        provider=PixabayProvider('fixture-key',{})
        with patch.object(provider,'json',return_value={'hits':[hit]}):
            self.assertEqual(provider.search('kitchen','glass',['glass']),[])
        self.assertEqual(provider.last_diagnostics['incompatible_style_rejected'],1)

    def test_http403_keeps_fixed_error_code_and_status_without_a_retry(self):
        import media_acquisition as acquisition
        import urllib.error
        from unittest.mock import Mock
        opener=Mock();opener.open.side_effect=urllib.error.HTTPError('https://example.invalid',403,'Denied',{},None)
        with patch.object(acquisition.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(acquisition.AcquisitionError) as caught:acquisition.request('https://example.invalid')
        self.assertEqual(caught.exception.http_status,403)
        self.assertEqual(str(caught.exception),'PROVIDER_AUTH_REJECTED');self.assertEqual(opener.open.call_count,1)
