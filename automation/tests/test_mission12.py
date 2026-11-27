"""Real historical fixtures, perceptual media tests, and explicitly simulated days."""
import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import editorial_policy as policy
import editorial_topics as tips
import autonomous_production as production
import visual_library as visual
import operational_health as health
from experimental81 import wan104, wan104_finish, daily_budget
ROOT=Path(__file__).resolve().parents[1]


class Originality12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real=json.loads((ROOT/'fixtures/mission12_repeated_scripts.json').read_text())['posts']

    def test_real_7_to_13_november_recombinations_all_block(self):
        used={'posts':[self.real[0]]}
        for post in self.real[1:]:
            self.assertTrue(policy.reason(post,used,{'posts':{}}),post['id'])
            used['posts'].append(post)

    def test_fake_ids_and_shuffled_steps_do_not_make_new_editorial(self):
        old=self.real[0]
        new=dict(old,id='new',concept='different-mp4-hash',script_lines=[old['script_lines'][0],*reversed(old['script_lines'][1:])])
        self.assertTrue(policy.reason(new,{'posts':[old]},{}))

    def test_different_kitchen_problems_pass_in_same_room(self):
        old=tips.BY_ID['ralo-coletor']; new=tips.BY_ID['utensilios-peso']
        self.assertIsNone(policy.reason({'concept':'tip12-'+new['id'],'script_lines':new['script_lines']},
          {'posts':[{'concept':'tip12-'+old['id'],'script_lines':old['script_lines']}]},{}))

    def test_last30_and_14days_are_union_not_intersection(self):
        old=dict(self.real[0],scheduled_at='2025-01-01T10:00:00-03:00')
        new=dict(old,script_lines=[old['script_lines'][0],'Uma informação totalmente diferente.'])
        self.assertEqual(policy.reason(new,{'posts':[old]},{}),'EDITORIAL_TOPIC_COOLDOWN')
        distinct=[{'id':str(i),'concept':'unique'+str(i),'script_lines':['Hook '+str(i),'body '+str(i)],'scheduled_at':'2026-11-20T10:00:00-03:00'} for i in range(35)]
        old['scheduled_at']='2026-11-19T10:00:00-03:00'
        new['scheduled_at']='2026-11-21T10:00:00-03:00'
        self.assertTrue(policy.reason(new,{'posts':[old]+distinct},{}))

    def test_receipt_only_history_survives_restart(self):
        old=self.real[0]
        state=json.loads(json.dumps({'posts':{old['id']:dict(old,status='PUBLISH_COMPLETE')}}))
        self.assertTrue(policy.reason(self.real[-1],{'posts':[]},state))

    def test_wan_17_november_scripts_are_same_concept(self):
        q=json.loads((ROOT/'queue.json').read_text())
        posts=[p for p in q['posts'] if p.get('id') in ('casasem-2026-11-17-1','casasem-2026-11-17-2')]
        self.assertEqual(len(posts),2)
        self.assertTrue(policy.reason(posts[1],{'posts':[posts[0]]},{}))

    def test_fifty_authored_concepts_have_stable_non_hash_ids(self):
        self.assertEqual(len(tips.TOPICS),50)
        self.assertEqual(len(tips.BY_ID),50)
        for tip in tips.TOPICS:
            self.assertTrue(tip['problem_id']);self.assertTrue(tip['solution_id'])
            self.assertIn(len(tip['script_lines']),(3,5,6))

    def test_wan_replans_without_discarding_sources_or_new_gpu_call(self):
        q={'posts':[dict(self.real[0],concept='licensed-wan104-episode-2')]}
        inv={'episode':6,'clips':[{'slot':0,'sha256':'a'*64,'prompt':'kitchen pantry glass jars shelf'}], 'requests':{'keep':{'status':'GENERATED'}}}
        with patch.object(wan104,'script_choices',return_value=[]):
            self.assertTrue(wan104.plan_episode(inv,q,{}))
        self.assertEqual(inv['editorial_id'],'potes-borda')
        self.assertEqual(len(inv['clips']),1); self.assertEqual(len(inv['scene_bank']),1)
        self.assertEqual(inv['requests'],{'keep':{'status':'GENERATED'}})
        spec=wan104.request_spec(json.loads(wan104.PROFILE.read_text()),6,1,inv['editorial_id'])
        self.assertIn('jar',spec['prompt']);self.assertNotIn('linen cupboard',spec['prompt'])

    def test_new_tip_review_cannot_borrow_legacy_or_other_tip_approval(self):
        from semantic_review import assess_generated_organization
        self.assertTrue(assess_generated_organization(2,['Three pans hang from a rail.']*3))
        self.assertFalse(assess_generated_organization(2,['Three books on a shelf.']*3))
        self.assertTrue(assess_generated_organization(1,['Clear glass jars on a shelf.']*3,'potes-borda'))
        self.assertFalse(assess_generated_organization(1,['White towels on a shelf.']*3,'potes-borda'))


class Continuity12(unittest.TestCase):
    def setUp(self):
        legacy_cadence = patch("mission14_policy.allowed_slot", return_value=True)
        legacy_cadence.start(); self.addCleanup(legacy_cadence.stop)

    def test_overdue_reservation_is_not_available_stock(self):
        now=dt.datetime(2026,11,20,23,tzinfo=dt.timezone.utc)
        post={'id':'old','approved':True,'consented_at':'yes','quality':{'technical_pass':True},'scheduled_at':(now-dt.timedelta(days=1)).isoformat()}
        self.assertEqual(production.stock_status({'posts':[post]},{'posts':{'old':{'status':'SCHEDULED'}}},now)['ready'],0)

    def test_14_days_consumption_quota_provider_outage_and_restart(self):
        now=dt.datetime(2026,11,21,tzinfo=dt.timezone.utc)
        queue={'posts':[]};state={'posts':{}};budget=daily_budget.fresh();consumed=[];origins=[];shortage=[]
        for day in range(14):
            clock=now+dt.timedelta(days=day)
            # Model free quota renewal; failures consume claims; no reset hack.
            for run in range(2):
                if production.stock_status(queue,state,clock)['refill_needed']:
                    available=tips.ideas(queue,state)
                    if not available: continue
                    concept,_,lines=available[0]
                    if day in (3,4):  # Both providers unavailable, retain state.
                        shortage.append(day);continue
                    origin='licensed'
                    if day%2==0:
                        try:
                            for slot in range(3):
                                import hashlib
                                request=hashlib.sha256(f'{day}-{run}-{slot}'.encode()).hexdigest()
                                budget=daily_budget.reserve(budget,request,clock,tier='free',estimated_seconds=60)
                            origin='wan'
                        except daily_budget.QuotaError: origin='licensed'
                    post_id,when=production.choose_slot(queue,state,clock)
                    post={'id':post_id,'concept':concept,'script_lines':lines,'scheduled_at':when.isoformat(),
                          'approved':True,'consented_at':clock.isoformat(),'quality':{'technical_pass':True}}
                    self.assertIsNone(policy.reason(post,queue,state,now=clock))
                    queue['posts'].append(post);origins.append(origin)
            # Simulated provider receipts explicitly marked; no live API here.
            for post in queue['posts']:
                if policy.date(post) < clock+dt.timedelta(days=1) and post['id'] not in state['posts']:
                    state['posts'][post['id']]=dict(post,status='PUBLISH_COMPLETE',publicly_verified=True,simulation=True)
                    consumed.append(post['id'])
            queue,state=json.loads(json.dumps([queue,state]))
        self.assertEqual(len(consumed),len(set(consumed)))
        self.assertIn('wan',origins);self.assertIn('licensed',origins);self.assertEqual(set(shortage),{3,4})
        self.assertGreater(len(consumed),18)
        self.assertTrue(all(v['simulation'] for v in state['posts'].values()))

    def test_incidents_deduplicate_and_resolve(self):
        now=dt.datetime.now(dt.timezone.utc)
        snap={'active_incidents':{'WAN_FREE_QUOTA_WAIT':{'details':'quota'}}}
        first=health.reconcile({},snap,now);second=health.reconcile(first,snap,now)
        self.assertEqual(len(second['incidents']),1)
        self.assertEqual(second['incidents']['WAN_FREE_QUOTA_WAIT']['occurrences'],2)
        self.assertFalse(health.reconcile(second,{'active_incidents':{}},now)['incidents']['WAN_FREE_QUOTA_WAIT']['active'])


class PerceptualMedia12(unittest.TestCase):
    def test_real_encoded_scenes_crop_color_and_identical_footage(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);a=folder/'a.mp4';b=folder/'b.mp4';c=folder/'c.mp4'
            def ff(args):subprocess.run(['ffmpeg','-v','error','-threads','1',*args,'-threads','1','-y'],check=True,timeout=40)
            ff(['-f','lavfi','-i','testsrc2=size=320x480:rate=12:duration=2','-c:v','libx264',str(a)])
            ff(['-i',str(a),'-vf','crop=iw*.9:ih*.9,eq=brightness=.08:saturation=.5','-c:v','libx264',str(b)])
            ff(['-f','lavfi','-i','smptebars=size=320x480:rate=12:duration=2','-c:v','libx264',str(c)])
            one,two,three=[visual.fingerprint(f,str(f)) for f in (a,b,c)]
            self.assertTrue(visual.similar(one,two));self.assertFalse(visual.similar(one,three))
            with self.assertRaisesRegex(ValueError,'VISUAL_NEAR_DUPLICATE'):visual.check_sources([two],[{'visual_sources':[one]}])
            with self.assertRaisesRegex(ValueError,'VISUAL_DUPLICATE_SOURCE'):visual.check_sources([dict(one,source_id='renamed')],[{'visual_sources':[one]}])
            self.assertTrue(visual.check_sources([three],[{'visual_sources':[one]}]))

class Persistence12(unittest.TestCase):
    def test_concurrent_main_advance_rebases_without_force(self):
        import persist_main
        from types import SimpleNamespace
        calls=[]; pushes=[]
        def fake(*args,check=True):
            calls.append(args)
            if args[0]=='merge-base':return SimpleNamespace(returncode=1,stdout='')
            if args[0]=='push':
                pushes.append(args);return SimpleNamespace(returncode=1 if len(pushes)==1 else 0,stdout='')
            return SimpleNamespace(returncode=0,stdout='')
        with patch.object(persist_main,'git',side_effect=fake):self.assertEqual(persist_main.push(),'PUSHED')
        self.assertEqual(len(pushes),2)
        self.assertFalse(any('--force' in a or '--force-with-lease' in a for a in calls))

    def test_lost_push_ack_reconciles_remote_ancestry(self):
        import persist_main
        from types import SimpleNamespace
        calls=[];ancestries=[]
        def fake(*args,check=True):
            calls.append(args)
            if args[0]=='merge-base':
                ancestries.append(args);return SimpleNamespace(returncode=1 if len(ancestries)==1 else 0,stdout='')
            return SimpleNamespace(returncode=1 if args[0]=='push' else 0,stdout='')
        with patch.object(persist_main,'git',side_effect=fake):self.assertEqual(persist_main.push(),'ALREADY_DURABLE')
        self.assertEqual(sum(a[0]=='push' for a in calls),1)

class Lease12(unittest.TestCase):
    def test_active_owner_is_not_stolen_and_expired_lease_recovers(self):
        import cloud_lease
        now=dt.datetime.now(dt.timezone.utc)
        first=cloud_lease.claim({},'one',now)
        self.assertIsNone(cloud_lease.claim(first,'two',now))
        self.assertEqual(cloud_lease.claim(first,'two',now+dt.timedelta(minutes=91))['owner'],'two')
        self.assertEqual(cloud_lease.claim(first,'one',now)['owner'],'one')

    def test_release_never_unlocks_another_workflow(self):
        import cloud_lease
        store=unittest.mock.Mock();store.load.return_value=({'owner':'other'},'r')
        cloud_lease.release(store,'mine');store.save.assert_not_called()

class FileCas12(unittest.TestCase):
    def test_other_file_branch_race_retries_only_unchanged_cas(self):
        from video_stock import GitHubStore, Conflict
        store=GitHubStore('mock',validate=False)
        with patch.object(store,'request',side_effect=[Conflict('branch race'),{'content':{'sha':'new'}}]) as req, patch.object(store,'load',return_value=({},'same')):
            self.assertEqual(store.save({},'same'),'new')
        self.assertEqual(req.call_count,2)

    def test_changed_file_is_never_overwritten(self):
        from video_stock import GitHubStore, Conflict
        store=GitHubStore('mock',validate=False)
        with patch.object(store,'request',side_effect=Conflict('stale')) as req, patch.object(store,'load',return_value=({},'changed')):
            with self.assertRaises(Conflict):store.save({},'same')
        self.assertEqual(req.call_count,1)

class Replan12(unittest.TestCase):
    def setUp(self):
        legacy_cadence = patch("mission14_policy.allowed_slot", return_value=True)
        legacy_cadence.start(); self.addCleanup(legacy_cadence.stop)

    def test_context_rejection_preserves_scene_for_the_correct_subject(self):
        inv={'episode':6,'editorial_id':'bancada-area-preparo','requests':{},'clips':[],
             'scene_bank':[{'slot':2,'sha256':'a'*64,'prompt':'Utensils hanging from a rail above an empty counter','consumed_by':'REJECTED'}],
             'rejected_clips':[{'slot':0,'sha256':'a'*64,'editorial_id':'bancada-area-preparo',
                               'rejection_reason':'PORTRAIT_VISUAL_CONTEXT_REJECTED'}]}
        wan104.plan_episode(inv,{'posts':[]},{'posts':{}})
        self.assertEqual(inv['editorial_id'],'utensilios-peso')
        self.assertNotIn('consumed_by',inv['scene_bank'][0])
        self.assertIn('bancada-area-preparo',inv['scene_bank'][0]['editorial_holds'])
        self.assertEqual(len(inv['clips']),1)

    def test_14_days_with_resources_can_keep_four_ahead_in_simulation(self):
        queue={'posts':[]};state={'posts':{}};start=dt.datetime(2026,11,21,tzinfo=dt.timezone.utc)
        published=[]
        for day in range(14):
            now=start+dt.timedelta(days=day)
            while production.stock_status(queue,state,now)['refill_needed']:
                concept,_,lines=tips.ideas(queue,state)[0]
                post_id,when=production.choose_slot(queue,state,now)
                queue['posts'].append({'id':post_id,'concept':concept,'script_lines':lines,'scheduled_at':when.isoformat(),
                 'approved':True,'consented_at':now.isoformat(),'quality':{'technical_pass':True}})
            self.assertEqual(production.stock_status(queue,state,now)['ready'],4)
            for p in queue['posts']:
                if now <= policy.date(p) < now+dt.timedelta(days=1):
                    self.assertNotIn(p['id'],state['posts']);published.append(p['id'])
                    state['posts'][p['id']]=dict(p,status='PUBLISH_COMPLETE',simulation=True)
            queue,state=json.loads(json.dumps([queue,state]))
        self.assertEqual(len(published),28)
        self.assertEqual(len(set(published)),28)

class SubjectEvidence12(unittest.TestCase):
    def test_wooden_shelf_does_not_establish_wooden_spoons(self):
        from semantic_review import assess_generated_organization
        self.assertFalse(assess_generated_organization(0,['Metal spoons hang above a wooden shelf.']*3,'madeira-molho'))
        self.assertTrue(assess_generated_organization(0,['Three wooden cooking spoons hang separately.']*3,'madeira-molho'))
        self.assertFalse(tips.matches_visual(tips.BY_ID['livros-apoio'],['Books on a shelf.']*3))

class LeaseRecovery12(unittest.TestCase):
    def test_only_confirmed_completed_run_releases_abandoned_lease(self):
        import cloud_lease
        from types import SimpleNamespace
        now=dt.datetime.now(dt.timezone.utc)
        store=unittest.mock.Mock();store.token='mock'
        store.load.return_value=({'owner':'123:job','expires_at':(now+dt.timedelta(minutes=60)).isoformat()},'old')
        with patch.object(cloud_lease,'owner_completed',return_value=True),patch.object(cloud_lease.time,'sleep') as delay:
            self.assertEqual(cloud_lease.acquire(store,'456:job'),'LEASE_ACQUIRED')
        self.assertEqual(store.save.call_args.args[0]['owner'],'456:job');delay.assert_not_called()

    def test_unknown_owner_api_result_does_not_grant_access(self):
        import cloud_lease
        with patch.object(cloud_lease.urllib.request,'urlopen',side_effect=TimeoutError):
            self.assertFalse(cloud_lease.owner_completed('123:job','mock'))

class ExactObjects12(unittest.TestCase):
    def test_glass_material_does_not_turn_a_jar_into_a_drinking_cup(self):
        self.assertFalse(tips.matches_visual(tips.BY_ID['copos-secos'],['Glass jars on a shelf.']*3))
        self.assertTrue(tips.matches_visual(tips.BY_ID['copos-secos'],['Empty drinking cups in a kitchen.']*3))

    def test_room_or_shared_background_is_not_object_evidence(self):
        self.assertFalse(tips.matches_visual(tips.BY_ID['espelho-fiapos'],['A window in a bathroom.']*3))
        self.assertFalse(tips.matches_visual(tips.BY_ID['varal-espaco'],['A washing machine with laundry.']*3))

class SceneSelection12(unittest.TestCase):
    def test_shared_laundry_family_does_not_include_machine_in_a_clothesline_tip(self):
        def scene(key,text):return {'record':{'id':key},'visual_review':{'family':'laundry','captions':[text]*3}}
        ideas=production.scripts([scene('machine','A washing machine.'),scene('line','Clothes drying on a clothesline.')],{'posts':[]},{'posts':{}})
        self.assertTrue(ideas)
        self.assertTrue(all('machine' not in idea[1] for idea in ideas))
        self.assertTrue(all(idea[1]==['line'] for idea in ideas))

class ResolvedAlerts12(unittest.TestCase):
    def test_cancelled_future_duplicate_is_not_reported_as_pending_content(self):
        now=dt.datetime(2026,11,21,tzinfo=dt.timezone.utc)
        old={'id':'old','concept':'auto-books-aaaaaaaaaaaa','script_lines':['Sua estante está confusa?','Separe os livros.'],'scheduled_at':(now-dt.timedelta(days=1)).isoformat()}
        new=dict(old,id='future',approved=False,scheduled_at=(now+dt.timedelta(days=1)).isoformat())
        result=health.inspect({'posts':[old,new]},{'posts':{'future':{'status':'CANCELLED_EDITORIAL','buffer_status':'deleted'}}},{'candidates':{}},{'clips':[]},now)
        self.assertNotIn('SIMILAR_FUTURE_CONTENT',result['active_incidents'])
