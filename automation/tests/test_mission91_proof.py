import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mission91_proof as proof


class RecoveryProofTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 6, 8, tzinfo=dt.timezone.utc)
        self.queue = {'posts': []}
        self.state = {'posts': {}}

    def test_regular_schedule_keeps_brazil_slots(self):
        when = proof.schedule(self.queue, self.state, self.now)
        self.assertEqual(when.hour, 10)
        self.assertEqual(when.utcoffset(), dt.timedelta(hours=-3))

    def test_live_proof_consumes_existing_two_per_day_capacity(self):
        self.state['posts'] = {str(n): {'scheduled_at': f'2026-11-06T{hour}:00:00-03:00'}
                               for n, hour in enumerate(('10', '18'))}
        with self.assertRaisesRegex(ValueError, 'DAILY_CAPACITY_RESERVED'):
            proof.schedule(self.queue, self.state, self.now, soon=True)

    def test_unknown_reservation_still_occupies_slot(self):
        self.state['posts']['unknown'] = {'scheduled_at': '2026-11-06T10:00:00-03:00',
                                          'status': 'SUBMISSION_UNKNOWN'}
        self.assertEqual(proof.schedule(self.queue, self.state, self.now).hour, 18)

    def test_rerun_cannot_restage_after_partial_handoff(self):
        self.queue['posts'].append({'concept': proof.CONCEPT})
        with self.assertRaisesRegex(ValueError, 'ALREADY_RESERVED'):
            proof.check_unused(self.queue, self.state)

    def test_matching_script_under_another_concept_is_blocked(self):
        self.state['posts']['previous'] = {'script_lines': proof.LINES, 'concept': 'other'}
        with self.assertRaisesRegex(ValueError, 'SCRIPT_ALREADY_USED'):
            proof.check_unused(self.queue, self.state)
