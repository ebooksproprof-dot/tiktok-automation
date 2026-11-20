"""Bounded non-forced persistence when independent cloud ledgers advance main.

Rebase conflicts stop for review. A lost push acknowledgement is reconciled by
ancestry before retrying, so an already accepted checkpoint is not duplicated.
"""
import subprocess


def git(*args, check=True):
    return subprocess.run(['git',*args],check=check,capture_output=True,text=True)


def push(attempts=4):
    if git('status','--porcelain').stdout.strip():
        raise RuntimeError('COMMIT_OWN_CHANGES_BEFORE_SYNC')
    for _ in range(attempts):
        git('fetch','origin','main')
        if git('merge-base','--is-ancestor','HEAD','origin/main',check=False).returncode==0:
            return 'ALREADY_DURABLE'
        git('rebase','origin/main')  # Never auto-resolve a concurrent file edit.
        if git('push','origin','HEAD:main',check=False).returncode==0:
            return 'PUSHED'
    raise RuntimeError('CONCURRENT_MAIN_ADVANCE_RETRY_LIMIT')

if __name__=='__main__':print(push())
