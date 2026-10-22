import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from daily_coverage import inspect


class DailyCoverageTests(unittest.TestCase):
    def check(self, hour, queue=None, posts=None):
        return inspect({'posts': queue or []}, {'posts': posts or {}},
                       dt.datetime(2026, 10, 22, hour, tzinfo=dt.timezone.utc))

    def entry(self, hour=10, **kwargs):
        return dict(scheduled_at=f'2026-10-22T{hour}:00:00-03:00', **kwargs)

    def test_before_creation_does_not_alert_for_missing_future_slots(self):
        self.assertFalse(self.check(10)['blocked'])

    def test_missing_or_unapproved_video_alerts_at_lead_window(self):
        self.assertTrue(self.check(12)['blocked'])
        self.assertTrue(self.check(12, [self.entry(approved=False)])['blocked'])

    def test_existing_remote_schedule_covers_slot_without_resubmission(self):
        result = self.check(13, posts={'a': self.entry(status='SCHEDULED')})
        self.assertFalse(result['blocked'])

    def test_unknown_and_overdue_are_not_success(self):
        for status in ('SUBMISSION_UNKNOWN', 'FAILED', 'SCHEDULED'):
            self.assertTrue(self.check(16, posts={'a': self.entry(status=status)})['blocked'])

    def test_publication_requires_evidence_and_old_drafts_do_not_block(self):
        post = self.entry(status='PUBLISH_COMPLETE', publicly_verified=True, public_urls=['https://tiktok.com/example'])
        self.assertFalse(self.check(16, [{'scheduled_at': '2026-10-21T18:00:00-03:00'}], {'a': post})['blocked'])
        post['public_urls'] = []
        self.assertTrue(self.check(16, posts={'a': post})['blocked'])

    def test_two_publications_cover_day(self):
        posts = {str(h): self.entry(h, status='PUBLISH_COMPLETE', publicly_verified=True,
                                   public_urls=['https://tiktok.com/example']) for h in (10,18)}
        self.assertFalse(self.check(23, posts=posts)['blocked'])

    def test_duplicate_reservations_alert(self):
        p = self.entry(status='SCHEDULED')
        self.assertTrue(self.check(13, posts={'a': p, 'b': p})['blocked'])
