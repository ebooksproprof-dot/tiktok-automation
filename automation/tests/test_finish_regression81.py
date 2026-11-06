"""Regressions from the six existing clips. No AI or publication API calls."""
import copy
import hashlib
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import auto_collect, auto_finish, render, rights
import buffer_runner as buffer

ROOT = Path(__file__).resolve().parents[1]


def cleared_source(index=1):
    digest = f'{index:064x}'
    return dict(sha256=digest, commercial_license_clearance=True,
                commercial_license_evidence=dict(source_sha256=digest,
                    reviewed_at='2026-01-01T00:00:00Z', **{name:dict(
                        license_url='https://example.org/test-license',
                        commercial_use=True, revision='mock-test-only')
                        for name in ('model','derivative','reference','voice')}))


class FinishRegressionTests(unittest.TestCase):
    def test_real_inventory_stays_blocked_for_commercial_use(self):
        state=json.loads((ROOT/'experimental81/auto_inventory.json').read_text())
        with self.assertRaisesRegex(ValueError,'AI_COMMERCIAL_CLEARANCE_REQUIRED'):
            rights.require_clearance(state['clips'])
        with patch.object(auto_collect,'content_get') as remote:
            with self.assertRaisesRegex(ValueError,'AI_COMMERCIAL_CLEARANCE_REQUIRED'):
                auto_finish.build_post(state,'not-uploaded',{},[],datetime.now(timezone.utc))
        remote.assert_not_called()

    def test_each_license_component_and_source_hash_is_required(self):
        self.assertEqual(rights.require_clearance([cleared_source()])[0]['sha256'], f'{1:064x}')
        for name in ('model','derivative','reference','voice'):
            source=cleared_source()
            source['commercial_license_evidence'][name]['commercial_use']=False
            with self.subTest(name=name), self.assertRaisesRegex(ValueError,'UNCONFIRMED'):
                rights.require_clearance([source])
        source=cleared_source()
        source['commercial_license_evidence']['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'CLEARANCE_REQUIRED'):
            rights.require_clearance([source])

    def test_no_quota_confirmation_never_renders_partial_episode(self):
        for count in (3,4,5):
            state=dict(schema_version=1,episode_sequence=1,status='COLLECTING',
                       clips=[dict(sha256=f'{i:064x}') for i in range(count)],last_attempt=None)
            with patch.object(auto_collect,'content_get',return_value=('sha',state)),\
                    patch.object(auto_finish,'render_episode') as media:
                self.assertEqual(auto_finish.finish()['status'],'WAITING_FOR_QUOTA_CONFIRMATION')
            media.assert_not_called()

    def test_license_block_after_render_never_uploads_or_changes_inventory(self):
        state=json.loads((ROOT/'experimental81/auto_inventory.json').read_text())
        before=copy.deepcopy(state)
        with patch.object(auto_collect,'content_get',side_effect=[('sha',state),('q',{'posts':[]})]),\
                patch.object(auto_finish,'render_episode',return_value=({}, {}, [])),\
                patch.object(auto_finish,'publish_existing_release') as upload,\
                patch.object(auto_collect,'content_put') as write:
            with self.assertRaisesRegex(ValueError,'AI_COMMERCIAL_CLEARANCE_REQUIRED'):
                auto_finish.finish()
        upload.assert_not_called();write.assert_not_called()
        self.assertEqual(state,before)

    def test_schedule_preserves_evening_and_metricool_dict_reservations(self):
        now=datetime(2026,11,3,12,tzinfo=timezone.utc)
        queue={'posts':[{'scheduled_at':'2026-11-03T10:00:00-03:00'}]}
        state={'posts':{'old':{'scheduled_at':{'dateTime':'2026-11-03T18:00:00',
                                             'timezone':'America/Sao_Paulo'}}}}
        chosen=auto_finish.choose_time(queue,state,now)
        self.assertEqual(chosen.isoformat(),'2026-11-04T10:00:00-03:00')

    def test_safe_error_reports_policy_but_never_provider_bodies(self):
        self.assertEqual(auto_finish.safe_reason(ValueError('AI30_VISUAL_REPETITION')),'AI30_VISUAL_REPETITION')
        self.assertEqual(auto_finish.safe_reason(RuntimeError('secret remote body')),'UNEXPECTED_FINISH_ERROR_BODY_OMITTED')

    def test_required_finish_workflow_propagates_failure(self):
        workflow=(ROOT.parent/'.github/workflows/ai30-free-collector.yml').read_text()
        finish=workflow.split('- name: Complete and queue ONLY fully verified AI30 output')[1].split('- name: Accurate final run summary')[0]
        self.assertNotIn('continue-on-error',finish)
        self.assertIn("if: always() && steps.finish.outcome != 'success'",workflow)

    def test_pending_without_evidence_is_failure_even_when_throttled(self):
        entry=dict(provider='buffer',status='AWAITING_PUBLIC_EVIDENCE',
                   buffer_post_id='remote',last_checked_at=buffer.common.iso_now())
        self.assertEqual(buffer.pending_reconciliation({'posts':{'p':entry}}),[])
        self.assertEqual(buffer.unresolved_count({'posts':{'p':entry}}),1)
        entry['status']='CANCELLED_EDITORIAL'
        self.assertEqual(buffer.pending_reconciliation({'posts':{'p':entry}}),[])
        self.assertEqual(buffer.unresolved_count({'posts':{'p':entry}}),0)

    def test_fallback_and_full_video_keep_same_publisher_gates(self):
        for count in (3,4,5,6):
            sources=[cleared_source(i+1) for i in range(count)]
            visuals=[dict(source_id=f'https://example.org/mock-{i}',sha256=source['sha256'],
                          dhash=[hashlib.sha256(f'{i}-{j}'.encode()).hexdigest()[:16] for j in range(5)])
                     for i,source in enumerate(sources)]
            post=dict(id='casasem-mock',publication_provider='buffer',video_origin='ai_only30',
                      approval_scope='owner_authorized_ai30_first_live_test_and_ongoing_automation',
                      ai_disclosure_required=True,approved=True,consented_at='2026-01-01T00:00:00Z',
                      scheduled_at=(buffer.common.utc_now()+timedelta(hours=1)).isoformat(),
                      title='Conteúdo gerado por IA',
                      video_url='https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-test/mock.mp4',
                      quality=dict(technical_pass=True,editorial_approved=False,owner_waived_preview=True,
                                   ai_generated_seconds=count*5,duration=count*5,machine_checks_only=True,
                                   commercial_license_clearance=True,licensed_sources=sources,
                                   sha256='a'*64,visual_policy_version=1,visual_distinct=True,visual_sources=visuals))
            with self.subTest(count=count):
                payload=buffer.prepare(post,{'posts':{}},'channel')
                self.assertTrue(payload['metadata']['tiktok']['isAiGenerated'])
                post['quality']['licensed_sources'][0]['commercial_license_clearance']=False
                with self.assertRaisesRegex(ValueError,'AI_COMMERCIAL_CLEARANCE_REQUIRED'):
                    buffer.prepare(post,{'posts':{}},'channel')

    def test_malformed_sent_time_cannot_confirm_publication(self):
        entry={'buffer_post_id':'remote','public_urls':['stale'],'publicly_available_post_id':['123']}
        buffer.record_remote(entry,dict(id='remote',channelId='channel',status='sent',
            schedulingType='automatic',sentAt='not-a-time',
            externalLink='https://www.tiktok.com/@.casasemesforo/video/123'),'channel')
        self.assertFalse(entry['publicly_verified'])
        self.assertNotIn('public_urls',entry)
        self.assertNotIn('publicly_available_post_id',entry)


try:
    from PIL import ImageFont
except ImportError:
    ImageFont=None


@unittest.skipUnless(ImageFont, 'Measured captions require Pillow')
class CaptionRegressionTests(unittest.TestCase):
    def test_full_production_script_fits_preserving_all_words_and_times(self):
        from caption_layout import filters, layout
        timings=[[i*5,(i+1)*5,line] for i,line in enumerate(auto_collect.SCRIPT)]
        with self.assertRaisesRegex(ValueError,'cannot fit safely'):
            for _,_,line in timings: layout(line)
        split=render.caption_timings(timings)
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(len(filters(folder,split)),len(split))
        self.assertEqual(' '.join(x[2] for x in split).split(),' '.join(auto_collect.SCRIPT).split())
        self.assertEqual(split[0][0],0);self.assertEqual(split[-1][1],30)
        for a,b in zip(split,split[1:]):self.assertAlmostEqual(a[1],b[0])

    def test_unbreakable_caption_still_fails(self):
        with self.assertRaises(ValueError):render.caption_timings([[0,5,'W'*100]])

    def test_short_plans_do_not_loop_or_reuse_source_intervals(self):
        for count in (3,4,5,6):
            shots=render.plan([dict(kind='ai',duration=5.0625) for _ in range(count)],'AI_ONLY',count*5)
            self.assertEqual(len(shots),count)
            self.assertEqual(len({s['source_index'] for s in shots}),count)
            self.assertEqual(sum(s['duration'] for s in shots),count*5)


if __name__=='__main__':unittest.main()
