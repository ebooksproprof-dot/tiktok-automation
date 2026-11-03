from datetime import datetime, timezone
from pathlib import Path
import base64
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experimental81 import daily_budget, github_ledger as g


def record(i=1):
    return {'request_sha256': f'{i:064x}',
            'request': {'space': g.SPACE, 'steps': 4, 'duration_seconds': 5}}


class FakeGitHub:
    def __init__(self):
        self.data = daily_budget.fresh()
        self.sha = 'old-file-sha'
        self.writes = 0

    def __call__(self, method, url, token, payload=None):
        if method == 'GET':
            return {'sha': self.sha, 'encoding': 'base64',
                    'content': base64.b64encode(json.dumps(self.data).encode()).decode()}
        if method == 'PUT':
            if payload['sha'] != self.sha:
                raise g.LedgerError('GITHUB_LEDGER_HTTP_409')
            self.data = json.loads(base64.b64decode(payload['content']))
            self.writes += 1
            self.sha = 'new-file-sha-' + str(self.writes)
            return {'commit': {'sha': 'c' * 40}}
        raise AssertionError(method)


class Ledger81Tests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'GITHUB_ACTIONS': 'true',
                       'GITHUB_REF_NAME': g.BRANCH, 'GITHUB_TOKEN': 'fake-secret'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_one_durable_reservation_then_no_retry(self):
        f = FakeGitHub()
        response = g.reserve_remote(record(1), now=datetime(2026, 11, 3, tzinfo=timezone.utc), transport=f)
        self.assertTrue(response['reserved'])
        self.assertFalse(response['publication_allowed'])
        self.assertEqual(f.writes, 1)
        with self.assertRaisesRegex(daily_budget.QuotaError, 'NO_RETRY'):
            g.reserve_remote(record(1), now=datetime(2026, 11, 3, tzinfo=timezone.utc), transport=f)
        self.assertEqual(f.writes, 1)

    def test_wrong_branch_does_not_access_remote(self):
        f = FakeGitHub()
        # Scheduled GitHub Actions legitimately runs on main, but only from
        # the EXACT dedicated AI30 workflow. An unrelated main job is denied.
        with patch.dict(os.environ, {'GITHUB_REF_NAME': 'main',
                    'GITHUB_WORKFLOW': 'Unrelated Main Workflow',
                    'GITHUB_EVENT_NAME': 'schedule',
                    'AI30_MAIN_SCHEDULER_ALLOW': 'true'}):
            with self.assertRaisesRegex(g.LedgerError, 'BRANCH_REQUIRED'):
                g.reserve_remote(record(1), transport=f)
        self.assertEqual(f.writes, 0)

    def test_unreviewed_steps_or_space_rejected(self):
        f = FakeGitHub()
        for key, val in [('steps', 3), ('space', 'https://not-the-reviewed-space.example')]:
            r = record(1)
            r['request'][key] = val
            with self.assertRaisesRegex(g.LedgerError, 'UNVERIFIED'):
                g.reserve_remote(r, transport=f)
        self.assertEqual(f.writes, 0)

    def test_sha_conflict_never_submits_generating_callback(self):
        f = FakeGitHub()
        def conflict(method, url, token, payload=None):
            if method == 'PUT':
                raise g.LedgerError('GITHUB_LEDGER_HTTP_409')
            return f(method, url, token, payload)
        with self.assertRaisesRegex(g.LedgerError, '409'):
            g.reserve_remote(record(1), transport=conflict)
        self.assertEqual(f.writes, 0)

    def test_readback_mismatch_fails_closed(self):
        f = FakeGitHub()
        def changed(method, url, token, payload=None):
            if method == 'PUT':
                return {'commit': {'sha': 'c'*40}}
            return f(method, url, token, payload)
        with self.assertRaisesRegex(g.LedgerError, 'READBACK'):
            g.reserve_remote(record(1), transport=changed)
        self.assertEqual(f.writes, 0)

    def test_bad_ledger_cannot_be_reserved(self):
        f = FakeGitHub()
        f.data = {'schema_version': 0}
        with self.assertRaisesRegex(daily_budget.QuotaError, 'BAD_LEDGER_SCHEMA'):
            g.reserve_remote(record(1), transport=f)
        self.assertEqual(f.writes, 0)

if __name__ == '__main__':
    unittest.main()
