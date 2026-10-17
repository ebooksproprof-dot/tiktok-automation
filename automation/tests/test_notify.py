import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import notify_failure as n

class FailureAlertTests(unittest.TestCase):
    def test_existing_alert_is_updated_instead_of_duplicated(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_RUN_ID':'123'}), patch.object(n,'call',side_effect=[[{'number':4,'title':n.TITLE}],{'html_url':'https://github.com/test/issues/4'}]) as api:
            n.main()
            self.assertEqual(api.call_args.args[0],'/issues/4')
            self.assertEqual(api.call_args.args[1],'PATCH')

    def test_truncated_inventory_does_not_create_duplicate(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_RUN_ID':'123'}), patch.object(n,'call',return_value=[{'title':'other'}]*100) as api:
            with self.assertRaises(RuntimeError):n.main()
            self.assertEqual(api.call_count,1)
