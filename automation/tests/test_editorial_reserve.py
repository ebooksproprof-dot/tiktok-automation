import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_daily as r


class ReserveTests(unittest.TestCase):
    def test_rejects_unbounded_horizon(self):
        for horizon in (0, 8, -1, True, 3.5):
            with self.assertRaises(ValueError):
                r.planned_reserve_slots(dt.date(2026, 12, 31), horizon)

    def test_year_boundary_has_unique_two_slots_per_day(self):
        plans = r.planned_reserve_slots(dt.date(2026, 12, 31), 3)
        self.assertEqual(len(set(plans)), 6)
        self.assertEqual(plans[-1], (dt.date(2027, 1, 2), 2, 18))

    def test_existing_today_is_preserved_future_reserve_stays_unapproved(self):
        today = dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        existing = [dict(id=f'casasem-{today}-{i}', composition_revision=r.COMPOSITION_REVISION,
                         approved=False, quality={'editorial_approved': False}) for i in (1,2)]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'automation').mkdir()
            queue=root/'automation/queue.json';queue.write_text(json.dumps({'posts':existing}))
            (root/'automation/state.json').write_text('{"posts":{}}')
            ideas=[('reserve-one',[],['Organize a bancada.']),('reserve-two',[],['Separe seus panos.']),('reserve-three',[],['Confira a gaveta.'])]
            quality=dict(duration=20,technical_pass=True,editorial_approved=False)
            with patch.dict('os.environ', {'EDITORIAL_RESERVE_DAYS':'3','MEDIA_STORAGE':'git'}), patch.object(r,'ROOT',root),patch.object(r,'QUEUE',queue),patch.object(r,'ASSETS',root/'tmp'),patch.object(r,'OUT',root/'public/rendered'),patch.object(r,'IDEAS',ideas),patch.object(r,'load_voice',return_value=object()),patch.object(r,'render',return_value=(Path('test.mp4'),quality)) as render:
                r.main()
            posts=json.loads(queue.read_text())['posts']
            self.assertEqual(posts[:2],existing)
            self.assertEqual(render.call_count,2)
            self.assertEqual(len(posts),4)
            for post in posts[2:]:
                self.assertFalse(post['approved']);self.assertIsNone(post['consented_at'])
                self.assertFalse(post['quality']['editorial_approved'])
                self.assertNotIn('route',post)
                self.assertIn(str(today+dt.timedelta(days=1)),post['id'])
