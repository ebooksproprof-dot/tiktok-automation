import copy
import datetime as dt
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from approve_preview44 import approve_preview
from batch_approval import digest
from content_catalog import fingerprint
from review_batch44 import build_preview

NOW=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)


def post(n):
    lines=['Roteiro distinto '+str(n)]
    sha=hashlib.sha256(str(n).encode()).hexdigest()
    return dict(id='post-'+str(n), approved=False, consented_at=None, title='Rotina doméstica',
                scheduled_at='2026-10-22T10:00:00-03:00',script_lines=lines,script_sha256=fingerprint(lines),
                video_url=f'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-test/{n}.mp4',
                quality=dict(technical_pass=True,editorial_approved=False,sha256=sha,
                             visual_policy_version=1,visual_distinct=True,
                             visual_sources=[dict(source_id='source-'+str(n),sha256=sha,dhash=[sha[:16]]*5)]))


class ApprovePreviewTests(unittest.TestCase):
    def setUp(self):
        self.queue={'posts':[post(1),post(2)]};self.state={'posts':{}};self.archive={}
        self.preview=build_preview(self.queue,self.state,NOW,archived=self.archive)

    def invoke(self, **overrides):
        values=dict(queue=self.queue,state=self.state,archived=self.archive,preview=self.preview,
                    selected_ids=['post-1'],consented_at=NOW.isoformat(),
                    review='Assisti ao MP4 exato, revisei cenas, voz, créditos e roteiro.',
                    authorized_manifest_sha256=self.preview['manifest_sha256'],approved=True,now=NOW)
        values.update(overrides);return approve_preview(**values)

    def test_explicit_consent_changes_only_selected_post_in_copy(self):
        before=copy.deepcopy((self.queue,self.state,self.archive,self.preview))
        result=self.invoke()
        self.assertEqual((self.queue,self.state,self.archive,self.preview),before)
        self.assertTrue(result['posts'][0]['approved'])
        self.assertEqual(result['posts'][0]['scheduled_at'],self.preview['items'][0]['proposed_scheduled_at'])
        self.assertEqual(result['posts'][1],self.queue['posts'][1])
        self.assertEqual(result['posts'][0]['publishing_status'],'APPROVED_FOR_BUFFER_NOT_SUBMITTED')

    def test_no_inferred_consent_or_time_or_empty_selection(self):
        for changes in [dict(approved=False),dict(approved=1),dict(consented_at=None),
                        dict(consented_at='2026-10-23T12:00:00'),dict(selected_ids=[]),
                        dict(selected_ids=['post-1','post-1']),dict(review=''),
                        dict(authorized_manifest_sha256=''),dict(consented_at='2026-10-23T13:00:00Z')]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.invoke(**changes)

    def test_stale_queue_state_or_archive_rejected(self):
        for which in ('queue','state','archive'):
            with self.subTest(which=which):
                target=copy.deepcopy(getattr(self,which));target['changed']=True
                with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):
                    self.invoke(**{('archived' if which=='archive' else which):target})

    def test_expired_preview_is_not_rescheduled(self):
        with self.assertRaisesRegex(ValueError,'PREVIEW_EXPIRED'):
            self.invoke(now=dt.datetime.fromisoformat(self.preview['expires_at'])+dt.timedelta(seconds=1))

    def test_edited_media_or_slot_even_if_rehashed_is_rejected(self):
        for field,value in [('sha256','f'*64),('proposed_scheduled_at','2026-10-25T18:00:00-03:00')]:
            preview=copy.deepcopy(self.preview);preview['items'][0][field]=value
            with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):self.invoke(preview=preview)
            preview.pop('manifest_sha256');preview['manifest_sha256']=digest(preview)
            with self.assertRaisesRegex(ValueError,'PREVIEW_ITEM_CHANGED'):
                self.invoke(preview=preview,authorized_manifest_sha256=preview['manifest_sha256'])

    def test_already_submitted_after_export_cannot_be_reauthorized(self):
        state={'posts':{'post-1':{'buffer_post_id':'remote-1'}}}
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):self.invoke(state=state)
        preview=build_preview(self.queue,state,NOW,archived=self.archive)
        with self.assertRaisesRegex(ValueError,'NOT_ELIGIBLE'):
            self.invoke(state=state,preview=preview,authorized_manifest_sha256=preview['manifest_sha256'])

    def test_blocked_visuals_not_authorized(self):
        self.queue['posts'][0]['quality']['visual_distinct']=False
        self.preview=build_preview(self.queue,self.state,NOW,archived=self.archive)
        with self.assertRaisesRegex(ValueError,'NOT_ELIGIBLE'):self.invoke()

    def test_existing_credit_gate_stays_enforced(self):
        self.queue['posts'][0]['quality']['required_public_credits']=['Missing author attribution']
        self.preview=build_preview(self.queue,self.state,NOW,archived=self.archive)
        with self.assertRaisesRegex(ValueError,'NOT_ELIGIBLE'):self.invoke()


if __name__=='__main__':unittest.main()
