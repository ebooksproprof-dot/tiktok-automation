import copy
import datetime as dt
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_batch44 as r
from content_catalog import fingerprint

NOW = dt.datetime(2026, 10, 23, 19, 59, tzinfo=dt.timezone.utc)


def post(n=1, due='2026-10-22T10:00:00-03:00'):
    lines = ['Roteiro ' + str(n)]
    return dict(id='post-'+str(n), title='Título', script_lines=lines,
                script_sha256=fingerprint(lines), scheduled_at=due, approved=False,
                video_url=f'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-10/{n}.mp4',
                quality=dict(sha256=f'{n:064x}', technical_pass=True, visual_policy_version=1, visual_distinct=True,
                             visual_sources=[dict(source_id=f'source-{n}',sha256=hashlib.sha256(str(n).encode()).hexdigest(),
                                                  dhash=[hashlib.sha256(str(n).encode()).hexdigest()[:16]]*5)]))


class ReviewBatchTests(unittest.TestCase):
    def test_no_state_mutation_or_fabricated_consent(self):
        queue,state=dict(posts=[post()]),dict(posts={})
        before=copy.deepcopy((queue,state));m=r.build_preview(queue,state,NOW)
        self.assertEqual((queue,state),before)
        self.assertFalse(m['approved']);self.assertIsNone(m['consented_at'])
        self.assertFalse(m['submitted']);self.assertFalse(m['items'][0]['approved'])
        self.assertEqual(m['items'][0]['editorial_review'],'PENDING')

    def test_maps_every_unsubmitted_including_rejected_without_hiding(self):
        posts=[post(i) for i in range(1,9)]
        posts[1]['editorial_rejection']='Repetido';posts[2].pop('script_lines')
        posts[7]['buffer_post_id']='already-remote'
        m=r.build_preview(dict(posts=posts),dict(posts={'post-7':{}}),NOW)
        self.assertEqual(m['pending_count'],6)
        self.assertEqual(m['selectable_count'],4)
        self.assertFalse(m['items'][1]['selectable']);self.assertFalse(m['items'][2]['selectable'])

    def test_all_proposals_future_brt_and_not_reserved(self):
        posts=[post(1),post(2,'2026-10-23T18:00:00-03:00'),post(3)]
        state=dict(posts={'past':{'scheduled_at':{'dateTime':'2026-10-24T10:00:00','timezone':'America/Sao_Paulo'}}})
        m=r.build_preview(dict(posts=posts),state,NOW)
        slots=[x['proposed_scheduled_at'] for x in m['items']]
        self.assertEqual(slots[1],'2026-10-25T10:00:00-03:00')
        self.assertTrue(all(r.stamp(value).date() > NOW.astimezone(r.TZ).date() for value in slots))
        self.assertNotIn('2026-10-24T10:00:00-03:00',slots)
        self.assertEqual(len(set(slots)),3)
        for value in slots:
            stamp=r.stamp(value);self.assertTrue(r.slot_valid(stamp,NOW));self.assertEqual(stamp.utcoffset(),dt.timedelta(hours=-3))
        self.assertTrue(m['items'][0]['schedule_changed'])

    def test_six_kokoro_first_fill_next_three_full_days_without_mutation(self):
        posts=[post(n) for n in range(1,8)]
        posts[0]['quality']['voice']='pt_BR-faber-medium'
        for p in posts[1:]:
            p['quality']['voice']='kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br'
        queue,state={'posts':posts},{'posts':{}}
        before=copy.deepcopy((queue,state))
        m=r.build_preview(queue,state,NOW)
        self.assertEqual((queue,state),before)
        self.assertEqual([p['id'] for p in m['items']],['post-'+str(n) for n in range(2,8)]+['post-1'])
        expected=[f'2026-10-{day}T{hour}:00:00-03:00' for day in (24,25,26) for hour in (10,18)]
        self.assertEqual([p['proposed_scheduled_at'] for p in m['items'][:6]],expected)
        self.assertEqual(m['items'][6]['proposed_scheduled_at'],'2026-10-27T10:00:00-03:00')
        self.assertEqual(m['items'][6]['voice'],'pt_BR-faber-medium')
        self.assertFalse(m['approved']);self.assertIsNone(m['consented_at'])
        self.assertIn('Voz registrada: kokoro-',r.render_html(m))

    def test_excludes_today_by_brasilia_date_even_when_utc_is_tomorrow(self):
        now=dt.datetime(2026,10,24,1,tzinfo=dt.timezone.utc)  # Oct23 22h BRT
        self.assertTrue(r.slot_valid(r.stamp('2026-10-24T10:00:00-03:00'),now))
        morning=dt.datetime(2026,10,23,10,tzinfo=dt.timezone.utc)
        self.assertFalse(r.slot_valid(r.stamp('2026-10-23T18:00:00-03:00'),morning))

    def test_script_and_entire_snapshots_bound(self):
        q=dict(posts=[post()]);s=dict(posts={});m=r.build_preview(q,s,NOW)
        self.assertEqual(m['items'][0]['post_snapshot_sha256'],r.digest(q['posts'][0]))
        self.assertEqual(m['queue_snapshot_sha256'],r.digest(q))
        self.assertEqual(m['state_snapshot_sha256'],r.digest(s))
        copy_m=copy.deepcopy(m);sha=copy_m.pop('manifest_sha256');self.assertEqual(sha,r.digest(copy_m))
        q['posts'][0]['script_lines']=['changed']
        self.assertFalse(r.build_preview(q,s,NOW)['items'][0]['selectable'])

    def test_urls_reject_active_content_other_hosts_and_encoded_paths(self):
        for url in ['javascript:alert(1)','https://evil.test/x.mp4','https://github.com.evil.test/x.mp4',
                    'https://user@github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-x/a.mp4',
                    'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-x/%2e%2e/a.mp4']:
            with self.subTest(url=url):
                q=dict(posts=[post()]);q['posts'][0]['video_url']=url
                m=r.build_preview(q,dict(posts={}),NOW)
                self.assertIsNone(m['items'][0]['video_url']);self.assertFalse(m['items'][0]['selectable'])

    def test_html_escapes_untrusted_markup_no_auto_selection(self):
        q=dict(posts=[post()]);q['posts'][0]['title']='</script><img src=x onerror=alert(1)>'
        m=r.build_preview(q,dict(posts={}),NOW);page=r.render_html(m)
        self.assertNotIn('<img src=x',page);self.assertIn('&lt;img',page)
        self.assertNotIn(' checked',page)
        self.assertNotIn('fetch(',page)
        self.assertIn('Proposta vencida',page)
        self.assertIn('\\nManifesto:',page)

    def test_known_source_reuse_blocks_despite_distinct_flag(self):
        p=post(); archived={'source_urls':['source-1']}
        m=r.build_preview(dict(posts=[p]),dict(posts={}),NOW,archived=archived)
        self.assertFalse(m['items'][0]['selectable'])
        self.assertIn('VISUAL_SOURCE_REUSED',str(m['items'][0]['blockers']))
        self.assertEqual(m['archived_history_sha256'],r.digest(archived))
        old=copy.deepcopy(p);old['id']='submitted'
        m=r.build_preview(dict(posts=[p]),dict(posts={'submitted':old}),NOW)
        self.assertFalse(m['items'][0]['selectable'])

    def test_audit_notes_only_match_exact_media_and_never_approve(self):
        p=post(); audit=[dict(id=p['id'],sha256=p['quality']['sha256'],video_url=p['video_url'],
                             hash_matches_queue=True,editorial_review='Sampled frames only')]
        m=r.build_preview(dict(posts=[p]),dict(posts={}),NOW,audit=audit)
        self.assertEqual(m['items'][0]['audit_notes']['editorial_review'],'Sampled frames only')
        self.assertFalse(m['items'][0]['approved'])
        audit[0]['sha256']='changed'
        self.assertIsNone(r.build_preview(dict(posts=[p]),dict(posts={}),NOW,audit=audit)['items'][0]['audit_notes'])

    def test_duplicate_queue_ids_fail(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_QUEUE_IDS'):
            r.build_preview(dict(posts=[post(),post()]),dict(posts={}),NOW)

    def test_cli_exports_only_new_files_preserving_queue_state(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'automation').mkdir()
            for name,data in [('queue.json',dict(posts=[post()])),('state.json',dict(posts={}))]:
                (root/'automation'/name).write_text(json.dumps(data))
            before=[p.read_bytes() for p in sorted((root/'automation').iterdir())]
            cmd=[sys.executable,str(Path(r.__file__)), '--root',str(root),'--output-dir',str(root/'public')]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(before,[p.read_bytes() for p in sorted((root/'automation').iterdir())])
            self.assertFalse(json.loads((root/'public/review44.json').read_text())['approved'])
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)


if __name__=='__main__': unittest.main()
