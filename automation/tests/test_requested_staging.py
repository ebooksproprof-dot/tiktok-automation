import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stage_requested_proofs as s

NOW=dt.datetime(2026,10,20,18,tzinfo=dt.timezone.utc)

def proof(index=1):
    body=('video'+str(index)).encode()
    digest=hashlib.sha256(body).hexdigest()
    source=dict(source_id=f'https://cdn.pixabay.com/{index}.mp4',sha256=f'{index:064x}',
                dhash=[('0' if index == 1 else 'f')*16]*5)
    quality=dict(technical_pass=True,sha256=digest,editorial_approved=False,
                 visual_policy_version=1,visual_distinct=True,visual_sources=[source],
                 required_public_credits=['Credit Creator; Pixabay'])
    report=dict(concept='concept-'+str(index),file=f'proof-{index}.mp4',quality=quality,script=['Um exemplo de roteiro.'])
    request=dict(concept=report['concept'],status='rendered_for_review',report=[report],
                 approval=dict(sha256=digest,approved_at='2026-10-20T17:00:00Z',route='buffer'))
    return body, request


class RequestedStagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.folder=self.root/'proofs';self.folder.mkdir()
        self.save('queue.json',{'posts':[]});self.save('state.json',{'posts':{}})

    def save(self,name,data):
        (self.root/name).write_text(json.dumps(data))

    def seed(self,count=1):
        requests=[]
        for i in range(1,count+1):
            body,request=proof(i);requests.append(request)
            (self.folder/request['report'][0]['file']).write_bytes(body)
        self.save('review_requests.json',{'requests':requests})
        return requests

    def invoke(self,publisher=None):
        def validated(path):
            return dict(technical_pass=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),editorial_approved=False)
        with patch.object(s,'validate',side_effect=validated),patch.object(s,'publish',side_effect=publisher or
                (lambda path,identity,quality: 'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-10/'+identity+'.mp4')) as upload:
            result=s.main(self.root,self.folder,NOW)
        return result,upload

    def test_no_approval_is_noop(self):
        requests=self.seed();requests[0].pop('approval');self.save('review_requests.json',{'requests':requests})
        result,upload=self.invoke();self.assertEqual(result,0);upload.assert_not_called()

    def test_sha_exact_approval_and_credits(self):
        self.seed();result,upload=self.invoke()
        self.assertEqual(result,1)
        entry=json.loads((self.root/'queue.json').read_text())['posts'][0]
        self.assertEqual(entry['id'],'casasem-2026-10-20-2')
        self.assertTrue(entry['approved']);self.assertTrue(entry['quality']['editorial_approved'])
        self.assertEqual(entry['publication_provider'],'buffer')
        self.assertIn('Credit Creator; Pixabay',entry['title'])
        self.assertEqual(entry['consented_at'],'2026-10-20T17:00:00Z')
        result,upload=self.invoke();self.assertEqual(result,0);upload.assert_not_called()

    def test_changed_bytes_not_uploaded(self):
        self.seed();(self.folder/'proof-1.mp4').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):self.invoke()
        self.assertEqual(json.loads((self.root/'queue.json').read_text())['posts'],[])

    def test_missing_or_future_approval_timestamp_rejected(self):
        for stamp in ['', '2026-10-21T17:00:00Z']:
            requests=self.seed();requests[0]['approval']['approved_at']=stamp
            self.save('review_requests.json',{'requests':requests})
            with self.assertRaises(ValueError):self.invoke()

    def test_existing_ambiguous_id_not_reused(self):
        self.seed();self.save('state.json',{'posts':{'casasem-2026-10-20-2':{'status':'SUBMISSION_UNKNOWN'}}})
        self.invoke();entry=json.loads((self.root/'queue.json').read_text())['posts'][0]
        self.assertEqual(entry['id'],'casasem-2026-10-21-1')

    def test_two_day_slots_max_with_other_ids(self):
        self.seed();self.save('queue.json',{'posts':[
            {'id':'legacy-a','scheduled_at':'2026-10-20T08:00:00-03:00'},
            {'id':'legacy-b','scheduled_at':'2026-10-20T14:00:00-03:00'}]})
        self.invoke();entry=json.loads((self.root/'queue.json').read_text())['posts'][-1]
        self.assertEqual(entry['id'],'casasem-2026-10-21-1')

    def test_upload_ambiguity_preserved_and_not_retried(self):
        self.seed()
        def failure(*args):raise RuntimeError('uncertain')
        with self.assertRaises(RuntimeError):self.invoke(failure)
        request=json.loads((self.root/'review_requests.json').read_text())['requests'][0]
        self.assertIn('UNKNOWN',request['staging_status'])
        self.assertEqual(request['staging_post_id'],'casasem-2026-10-20-2')
        result,upload=self.invoke();self.assertEqual(result,0);upload.assert_not_called()

    def test_each_queue_entry_saved_before_next_upload(self):
        self.seed(2);calls=[]
        def upload(path,identity,quality):
            calls.append(len(json.loads((self.root/'queue.json').read_text())['posts']))
            return 'https://github.com/example/'+identity+'.mp4'
        result,_=self.invoke(upload);self.assertEqual(result,2);self.assertEqual(calls,[0,1])

    def test_same_visual_source_within_batch_rejected(self):
        requests=self.seed(2)
        requests[1]['report'][0]['quality']['visual_sources']=requests[0]['report'][0]['quality']['visual_sources']
        self.save('review_requests.json',{'requests':requests})
        with self.assertRaisesRegex(ValueError,'VISUAL_DUPLICATE'):self.invoke()
        self.assertEqual(len(json.loads((self.root/'queue.json').read_text())['posts']),1)

    def test_path_escape_rejected(self):
        requests=self.seed();requests[0]['report'][0]['file']='../proof-1.mp4'
        self.save('review_requests.json',{'requests':requests})
        with self.assertRaisesRegex(ValueError,'INVALID_PROOF_PATH'):self.invoke()

    def test_published_visual_source_rejected(self):
        requests=self.seed()
        self.save('state.json',{'posts':{'old':dict(visual_sources=requests[0]['report'][0]['quality']['visual_sources'])}})
        with self.assertRaisesRegex(ValueError,'VISUAL_DUPLICATE'):self.invoke()
