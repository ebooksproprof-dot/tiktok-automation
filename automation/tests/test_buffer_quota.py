import datetime as dt
from email.message import Message
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import buffer_quota as q

NOW=dt.datetime(2026,10,20,18,tzinfo=dt.timezone.utc)


def headers(remaining=2, seconds=900, window=900):
    return {'RateLimit':f'"policy-{window}"; r={remaining}; t={seconds}',
            'RateLimit-Policy':f'"policy-{window}"; q=100; w={window}; pk=:secret-partition:'}


class BufferQuotaTests(unittest.TestCase):
    def test_run_budget_reserves_readback(self):
        self.assertTrue(q.check({},NOW,required=2,calls=6))
        with self.assertRaisesRegex(q.BudgetExceeded,'RUN_LIMIT'):
            q.check({},NOW,required=2,calls=7)

    def test_daily_90_replaces_internal_60(self):
        state={'buffer_api_usage':[q.stamp(NOW-dt.timedelta(hours=1))]*60}
        self.assertTrue(q.check(state,NOW))
        state['buffer_api_usage']*=2
        with self.assertRaises(q.BudgetExceeded) as result:q.check(state,NOW)
        self.assertEqual(result.exception.next_allowed_at,q.stamp(NOW+dt.timedelta(hours=23)))

    def test_short_window_rolls_at_exact_boundary(self):
        state={'buffer_api_usage':[q.stamp(NOW-dt.timedelta(minutes=15))]*90}
        with patch.dict(q.WINDOWS,{900:90},clear=True):
            self.assertTrue(q.check(state,NOW))

    def test_monthly_limit_and_required_count(self):
        state={'buffer_api_usage':[q.stamp(NOW-dt.timedelta(days=2))]*1799}
        self.assertTrue(q.check(state,NOW,required=1))
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW,required=2)

    def test_old_attempts_pruned_future_attempts_retained(self):
        state={'buffer_api_usage':[q.stamp(NOW-dt.timedelta(days=31)),q.stamp(NOW+dt.timedelta(hours=1))]}
        q.check(state,NOW)
        self.assertEqual(len(state['buffer_api_usage']),1)

    def test_repeated_and_combined_headers_drop_partition_key(self):
        h=Message()
        h.add_header('RateLimit','"100-in-15min"; r=98; t=897')
        h.add_header('RateLimit','"250-in-1day"; r=248; t=86397, "3000-in-30days";r=2969;t=696980')
        h.add_header('RateLimit-Policy','"100-in-15min"; q=100; w=900; pk=:secret:')
        h.add_header('RateLimit-Policy','"250-in-1day";q=250;w=86400;pk=:secret:, "3000-in-30days";q=3000;w=2592000;pk=:secret:')
        state={};q.record_headers(state,h,NOW)
        windows=state['buffer_quota']['windows']
        self.assertEqual(set(windows),{'900','86400','2592000'})
        self.assertEqual(windows['900']['remaining'],98)
        self.assertEqual(windows['2592000']['quota'],3000)
        self.assertNotIn('secret',json.dumps(state));self.assertNotIn('pk',json.dumps(state))

    def test_attempt_decrements_even_when_response_has_no_headers(self):
        state={};q.record_headers(state,headers(),NOW)
        q.record_attempt(state,NOW);q.record_headers(state,{},NOW)
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],1)
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW,required=2)
        q.record_attempt(state,NOW)
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],0)
        self.assertEqual(len(state['buffer_api_usage']),2)

    def test_server_response_updates_after_attempt_not_double_decrement(self):
        state={};q.record_headers(state,headers(remaining=2),NOW)
        q.record_attempt(state,NOW);q.record_headers(state,headers(remaining=1),NOW)
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],1)

    def test_reset_expiry_drops_header_constraint(self):
        state={};q.record_headers(state,headers(remaining=0,seconds=20),NOW)
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW)
        self.assertTrue(q.check(state,NOW+dt.timedelta(seconds=20)))

    def test_retry_after_seconds_429_persists_across_instances(self):
        state={};q.record_error(state,429,{'retry-after':'753'},NOW)
        restored=json.loads(json.dumps(state))
        with self.assertRaises(q.BudgetExceeded) as result:q.check(restored,NOW+dt.timedelta(seconds=752))
        self.assertEqual(result.exception.next_allowed_at,q.stamp(NOW+dt.timedelta(seconds=753)))
        self.assertTrue(q.check(restored,NOW+dt.timedelta(seconds=753)))

    def test_retry_after_http_date_503(self):
        state={};q.record_error(state,503,{'Retry-After':'Tue, 20 Oct 2026 19:00:00 GMT'},NOW)
        self.assertEqual(state['buffer_quota']['next_allowed_at'],'2026-10-20T19:00:00Z')

    def test_rate_headers_exhausted_without_retry_after(self):
        state={};q.record_error(state,429,headers(remaining=0,seconds=900),NOW)
        self.assertEqual(state['buffer_quota']['next_allowed_at'],q.stamp(NOW+dt.timedelta(seconds=900)))

    def test_auth_backoff_six_hours(self):
        for code in (401,403):
            state={};q.record_error(state,code,{},NOW)
            self.assertEqual(state['buffer_quota']['next_allowed_at'],q.stamp(NOW+dt.timedelta(hours=6)))

    def test_transient_backoff_exponential_persistent_and_capped(self):
        state={}
        for count in range(1,10):
            state=json.loads(json.dumps(state))
            q.record_error(state,None,None,NOW)
            delay=min(60*2**(count-1),3600)
            self.assertEqual(state['buffer_quota']['next_allowed_at'],q.stamp(NOW+dt.timedelta(seconds=delay)))

    def test_success_resets_failures_but_not_active_wait(self):
        state={};q.record_error(state,503,{'Retry-After':'900'},NOW)
        q.record_success(state)
        self.assertEqual(state['buffer_quota']['consecutive_errors'],0)
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW)

    def test_case_insensitive_mapping_and_partial_headers(self):
        state={};q.record_headers(state,{k.lower():v for k,v in headers().items()},NOW)
        q.record_headers(state,{'ratelimit':'"policy-900";r=1;t=899'},NOW)
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],1)

    def test_malformed_headers_dont_remove_existing_constraints(self):
        state={};q.record_headers(state,headers(remaining=0),NOW)
        q.record_headers(state,{'RateLimit':'bad; r=-10', 'RateLimit-Policy':'untrusted'},NOW)
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW)

    def test_invalid_retry_after_uses_fallback(self):
        for value in ('bad','-100','Tue, 20 Oct 2026 17:00:00 GMT'):
            state={};q.record_error(state,503,{'Retry-After':value},NOW)
            self.assertEqual(state['buffer_quota']['next_allowed_at'],q.stamp(NOW+dt.timedelta(seconds=60)))

    def test_check_invalid_args_and_corrupt_history_fail_closed(self):
        for required in (0,9,True,1.5):
            with self.assertRaises(ValueError):q.check({},NOW,required=required)
        with self.assertRaises(ValueError):q.check({'buffer_api_usage':['bad']},NOW)
        with self.assertRaises(ValueError):q.check({},NOW.replace(tzinfo=None))

    def test_known_headers_survive_missing_response_error(self):
        state={};q.record_headers(state,headers(remaining=2),NOW)
        q.record_attempt(state,NOW);q.record_error(state,None,None,NOW)
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],1)
        self.assertEqual(len(state['buffer_api_usage']),1)

    def test_status_without_policy_still_throttles_and_later_maps(self):
        state={}
        q.record_headers(state,{'RateLimit':'"policy-900";r=0;t=500'},NOW)
        with self.assertRaises(q.BudgetExceeded):q.check(state,NOW)
        q.record_headers(state,{'RateLimit-Policy':'"policy-900";q=100;w=900;pk=:secret:'},NOW)
        self.assertEqual(set(state['buffer_quota']['windows']),{'900'})
        self.assertEqual(state['buffer_quota']['windows']['900']['remaining'],0)
