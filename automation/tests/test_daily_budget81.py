"""The ZeroGPU daily budget is a fail-closed estimate, not a free GPU guarantee."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import daily_budget as b

START = datetime(2026, 11, 3, 12, 30, tzinfo=timezone.utc)
def digest(n):
    return f'{n:064x}'

class Budget81Tests(unittest.TestCase):
    def test_anonymous_two_five_second_clips_only(self):
        state=b.fresh()
        state=b.reserve(state,digest(1),START)
        state=b.reserve(state,digest(2),START+timedelta(minutes=1))
        self.assertEqual(len(state['window_claim_ids']),2)
        with self.assertRaisesRegex(b.QuotaError,'DAILY_QUOTA'):
            b.reserve(state,digest(3),START+timedelta(minutes=2))

    def test_verified_free_tier_still_cannot_generate_six_at_four_steps(self):
        state=b.fresh()
        for n in range(5):
            state=b.reserve(state,digest(n+1),START+timedelta(minutes=n),tier='free')
        with self.assertRaisesRegex(b.QuotaError,'DAILY_QUOTA'):
            b.reserve(state,digest(6),START+timedelta(minutes=7),tier='free')
        self.assertFalse(b.estimate_full_video(tier='free')['fits_theoretical_cap'])

    def test_reset_is_24h_from_first_use_not_midnight(self):
        state=b.reserve(b.fresh(),digest(1),START)
        with self.assertRaisesRegex(b.QuotaError,'DUPLICATE'):
            b.reserve(state,digest(1),START+timedelta(days=1))
        renewed=b.reserve(state,digest(2),START+timedelta(days=1))
        self.assertEqual(renewed['window_claim_ids'],[digest(2)])
        self.assertEqual(len(renewed['claims']),2)

    def test_future_or_naive_dates_rejected(self):
        with self.assertRaisesRegex(b.QuotaError,'UTC_AWARE'):
            b.reserve(b.fresh(),digest(1),datetime(2026,11,3))
        state=b.reserve(b.fresh(),digest(1),START)
        with self.assertRaisesRegex(b.QuotaError,'CLOCK_MOVED'):
            b.reserve(state,digest(2),START-timedelta(seconds=1))

    def test_nonfree_tiers_forbidden_and_tier_switch_blocked(self):
        with self.assertRaisesRegex(b.QuotaError,'PAID_TIER'):
            b.reserve(b.fresh(),digest(1),START,tier='pro')
        state=b.reserve(b.fresh(),digest(1),START)
        with self.assertRaisesRegex(b.QuotaError,'TIER_CHANGE'):
            b.reserve(state,digest(2),START+timedelta(minutes=1),tier='free')

    def test_failed_unknown_claim_cannot_be_retried(self):
        state=b.reserve(b.fresh(),digest(1),START)
        with self.assertRaisesRegex(b.QuotaError,'NO_RETRY'):
            b.reserve(state,digest(1),START+timedelta(seconds=1))

    def test_results_not_guaranteed_even_if_math_fits(self):
        estimate=b.estimate_full_video(clips=1)
        self.assertTrue(estimate['fits_theoretical_cap'])
        self.assertFalse(estimate['guaranteed_production'])
        self.assertFalse(estimate['observed_actual_quota_debit'])

if __name__ == '__main__':
    unittest.main()
