import copy
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import batch_approval as b

NOW = dt.datetime(2026, 10, 22, 12, tzinfo=dt.timezone.utc)


def post(index=1):
    lines = ['Um roteiro original número ' + str(index) + '.']
    sha = str(index)*64
    return dict(id=f'casasem-2026-10-22-{index}',
                video_url=f'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-10/proof{index}.mp4',
                script_lines=lines, script_sha256=b.fingerprint(lines),
                title='Um roteiro original.', scheduled_at=f'2026-10-22T{10 if index==1 else 18}:00:00-03:00',
                approved=False, consented_at=None,
                quality=dict(technical_pass=True, editorial_approved=False, sha256=sha,
                             visual_policy_version=1, visual_distinct=True,
                             visual_sources=[dict(source_id='source-'+str(index), sha256=chr(96+index)*64,
                                                  dhash=[('0' if index==1 else 'f')*16]*5)]))


class BatchApprovalTests(unittest.TestCase):
    def setUp(self):
        self.queue = dict(posts=[post(1), post(2)])
        self.state = dict(posts={})
        self.manifest = b.export_manifest(self.queue, self.state)
        self.manifest.update(approved=True, consented_at='2026-10-22T11:59:00Z')
        for item in self.manifest['items']:
            item.update(editorial_approved=True, review='Exact MP4, script, visual context and credits reviewed.')

    def test_export_does_not_fabricate_consent_or_editorial_review(self):
        exported = b.export_manifest(self.queue,self.state)
        self.assertFalse(exported['approved'])
        self.assertIsNone(exported['consented_at'])
        self.assertTrue(all(not x['editorial_approved'] for x in exported['items']))

    def test_explicit_batch_approves_copy_without_submitting(self):
        updated = b.approve(self.queue,self.state,self.manifest,NOW)
        self.assertTrue(all(p['approved'] and p['quality']['editorial_approved'] for p in updated['posts']))
        self.assertTrue(all(not p['approved'] for p in self.queue['posts']))
        self.assertEqual(self.state, {'posts':{}})

    def test_changed_queue_or_state_invalidates_snapshot(self):
        for target in ('queue','state'):
            q,s=copy.deepcopy(self.queue),copy.deepcopy(self.state)
            (q if target=='queue' else s)['modified']=True
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):
                b.approve(q,s,self.manifest,NOW)

    def test_explicit_consent_and_editorial_review_required(self):
        for field,value in [('approved',False),('route','metricool'),('consented_at',None),
                            ('consented_at','2026-10-22'),('consented_at','2026-10-23T00:00:00Z')]:
            m=copy.deepcopy(self.manifest);m[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                b.approve(self.queue,self.state,m,NOW)
        self.manifest['items'][1]['review']=''
        with self.assertRaisesRegex(ValueError,'EDITORIAL_REVIEW'):
            b.approve(self.queue,self.state,self.manifest,NOW)

    def test_each_reviewed_identity_field_is_bound(self):
        for field in ('sha256','script_hash','video_url','scheduled_at','post_snapshot_sha256'):
            m=copy.deepcopy(self.manifest);m['items'][0][field]='changed'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'REVIEWED_POST_CHANGED'):
                b.approve(self.queue,self.state,m,NOW)

    def test_expired_slot_is_not_silently_rescheduled(self):
        with self.assertRaisesRegex(ValueError,'SLOT_EXPIRED'):
            b.approve(self.queue,self.state,self.manifest,NOW+dt.timedelta(hours=2))

    def test_duplicate_item_rejected(self):
        self.manifest['items'].append(copy.deepcopy(self.manifest['items'][0]))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_POST_ID'):
            b.approve(self.queue,self.state,self.manifest,NOW)

    def test_already_submitted_item_cannot_be_approved(self):
        self.state['posts'][self.queue['posts'][0]['id']]={'status':'SUBMISSION_UNKNOWN'}
        self.manifest['state_snapshot_sha256']=b.digest(self.state)
        with self.assertRaisesRegex(ValueError,'ALREADY_SUBMITTED'):
            b.approve(self.queue,self.state,self.manifest,NOW)

    def test_duplicate_media_and_visuals_rejected(self):
        for field in ('sha256','visual_sources'):
            q=copy.deepcopy(self.queue)
            q['posts'][1]['quality'][field]=q['posts'][0]['quality'][field]
            m=b.export_manifest(q,self.state)
            m.update(approved=True,consented_at='2026-10-22T11:59:00Z')
            for x in m['items']:x.update(editorial_approved=True,review='Exact MP4 and all editorial content reviewed.')
            with self.subTest(field=field),self.assertRaises(ValueError):
                b.approve(q,self.state,m,NOW)

    def test_dry_run_leaves_files_identical_and_apply_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,data in [('queue.json',self.queue),('state.json',self.state),('manifest.json',self.manifest)]:
                (root/name).write_text(json.dumps(data))
            before=(root/'queue.json').read_bytes()
            result=b.run(root,root/'manifest.json',now=NOW)
            self.assertFalse(result['applied'])
            self.assertEqual(before,(root/'queue.json').read_bytes())
            result=b.run(root,root/'manifest.json',apply=True,now=NOW)
            self.assertTrue(result['applied'])
            self.assertFalse(result['published'])
            self.assertTrue(json.loads((root/'queue.json').read_text())['posts'][0]['approved'])

    def test_invalid_second_item_never_partially_writes(self):
        self.manifest['items'][1]['sha256']='a'*64
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,data in [('queue.json',self.queue),('state.json',self.state),('manifest.json',self.manifest)]:
                (root/name).write_text(json.dumps(data))
            before=(root/'queue.json').read_bytes()
            with self.assertRaises(ValueError):
                b.run(root,root/'manifest.json',apply=True,now=NOW)
            self.assertEqual(before,(root/'queue.json').read_bytes())
