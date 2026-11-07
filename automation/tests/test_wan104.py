import copy
import datetime as dt
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import wan104 as wan, daily_budget


class Store:
    def __init__(self, value, calls, label, fail=False):
        self.value, self.calls, self.label, self.fail = copy.deepcopy(value), calls, label, fail

    def load(self):
        self.calls.append(self.label+' load')
        return copy.deepcopy(self.value), 'revision'

    def save(self, value, revision):
        self.calls.append(self.label+' save')
        if self.fail:
            raise RuntimeError('checkpoint rejected')
        self.value = copy.deepcopy(value)
        return 'new-revision'


class LicensedWanTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads(wan.PROFILE.read_text())

    def metadata(self, url):
        key = next(k for k in ('model', 'backbone', 'voice', 'space') if url.endswith('/'+self.profile[k]))
        result = {'sha': self.profile[key+'_revision'], 'cardData': {'license': 'apache-2.0'}}
        if key == 'space':
            result['runtime'] = {'sha': result['sha'], 'stage': 'RUNNING', 'hardware': {'current': 'zero-a10g'}}
        return result

    def test_complete_explicit_license_profile(self):
        self.assertTrue(wan.profile_check(self.profile, self.metadata))

    def test_runtime_and_license_drift_fail_before_generation(self):
        for component, field in [('model', 'sha'), ('backbone', 'license'), ('space', 'runtime')]:
            def changed(url):
                result = self.metadata(url)
                if url.endswith('/'+self.profile[component]):
                    if field == 'sha': result['sha'] = 'changed'
                    elif field == 'license': result['cardData']['license'] = 'cc-by-nc-4.0'
                    else: result['runtime']['sha'] = 'not-the-reviewed-deployment'
                return result
            with self.subTest(component=component), self.assertRaises(ValueError):
                wan.profile_check(self.profile, changed)

    def test_legacy_components_cannot_borrow_new_clearance(self):
        for name in ['use_lora', 'use_cbensimon_weights', 'use_aoti_package']:
            value = dict(self.profile, **{name: True})
            with self.assertRaisesRegex(ValueError, 'UNAPPROVED_WAN_PROFILE'):
                wan.profile_check(value, lambda _: self.fail('must stop without network'))

    def test_shared_quota_counts_legacy_requests_without_reset(self):
        date = dt.datetime.now(dt.timezone.utc)
        ledger = daily_budget.reserve(daily_budget.fresh(), 'a'*64, date, tier='free', estimated_seconds=45)
        for symbol in 'bcd':
            ledger = daily_budget.reserve(ledger, symbol*64, date, tier='free', estimated_seconds=75)
        self.assertEqual(len(ledger['claims']), 4)
        self.assertEqual(sum(x['estimated_seconds'] for x in ledger['claims']), 270)
        with self.assertRaises(daily_budget.QuotaError):
            daily_budget.reserve(ledger, 'e'*64, date, tier='free', estimated_seconds=75)

    def test_quota_then_intent_checkpoint_precedes_submission(self):
        calls = []
        inventory = {'requests': {}}
        inv = Store(inventory, calls, 'inventory')
        budget = Store(daily_budget.fresh(), calls, 'budget')
        spec = wan.request_spec(self.profile, 1, 0)
        digest, _ = wan.reserve(inv, budget, inventory, 'r', spec, 'free')
        self.assertEqual(calls, ['budget load', 'budget save', 'inventory save'])
        self.assertEqual(inv.value['requests'][digest]['status'], 'INTENT_RECORDED_NO_RETRY')
        with self.assertRaisesRegex(ValueError, 'KNOWN_OR_UNCERTAIN'):
            wan.reserve(inv, budget, inventory, 'r', spec, 'free')
        self.assertEqual(len(budget.value['claims']), 1)

    def test_failed_intent_does_not_unreserve_budget(self):
        calls = []
        budget = Store(daily_budget.fresh(), calls, 'budget')
        inv = Store({}, calls, 'inventory', fail=True)
        with self.assertRaises(RuntimeError):
            wan.reserve(inv, budget, {'requests': {}}, 'r', wan.request_spec(self.profile, 1, 0), 'free')
        self.assertEqual(len(budget.value['claims']), 1)

    def test_text_only_new_model_is_distinct_from_old_clip_provenance(self):
        spec = wan.request_spec(self.profile, 1, 0)
        self.assertEqual(spec['model'], 'FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers')
        self.assertEqual(spec['reference_kind'], 'authored_text_only')
        self.assertNotIn('reference_sha256', spec)
        self.assertNotEqual(spec['seed'], wan.request_spec(self.profile, 2, 0)['seed'])
        self.assertNotEqual(spec['prompt'], wan.request_spec(self.profile, 2, 0)['prompt'])


if __name__ == '__main__':
    unittest.main()
