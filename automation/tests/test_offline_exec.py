import ctypes.util
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(sys.platform == 'linux' and ctypes.util.find_library('seccomp'), 'Linux seccomp required')
class OfflineExecTests(unittest.TestCase):
    def test_network_denied_and_child_inherits(self):
        wrapper=Path(__file__).resolve().parents[1]/'offline_exec.py'
        code="""import socket,subprocess,sys
try:
    socket.socket()
except PermissionError:
    pass
else:
    raise SystemExit('Network unexpectedly allowed')
child=subprocess.run([sys.executable,'-c','import socket; socket.socket()'],capture_output=True,text=True)
assert child.returncode != 0 and 'PermissionError' in child.stderr
print('OFFLINE_ENFORCED')
"""
        run=subprocess.run([sys.executable,str(wrapper),sys.executable,'-c',code],capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn('OFFLINE_ENFORCED',run.stdout)
