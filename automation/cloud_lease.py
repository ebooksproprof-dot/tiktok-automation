"""CAS cloud lease for shared queue/state, independent of GitHub pending eviction.

Only metadata serialization. Never reconciles or retries video/API submissions.
An interrupted owner expires after 90 minutes, beyond every workflow time limit.
"""
import datetime as dt
import os
import sys
import time
from video_stock import GitHubStore, Conflict

PATH='automation/cloud_lease.json'


def claim(state, owner, now):
    current=state.get('owner')
    expiry=state.get('expires_at')
    if current and current!=owner:
        try: expired=dt.datetime.fromisoformat(expiry)<=now
        except (ValueError,TypeError): expired=False
        if not expired:return None
    return {'version':1,'owner':owner,'acquired_at':now.isoformat(),
            'expires_at':(now+dt.timedelta(minutes=90)).isoformat()}


def acquire(store, owner, max_wait=900):
    deadline=time.monotonic()+max_wait
    while True:
        state,revision=store.load()
        updated=claim(state,owner,dt.datetime.now(dt.timezone.utc))
        if updated:
            try:
                store.save(updated,revision)
                return 'LEASE_ACQUIRED'
            except Conflict:pass  # Another worker won; no external video call.
        if time.monotonic()>=deadline:raise RuntimeError('SHARED_STATE_LEASE_BUSY_RETRY_NEXT_CRON')
        print('SHARED_STATE_LEASE_WAIT',flush=True)
        time.sleep(15)


def release(store,owner):
    state,revision=store.load()
    if state.get('owner')==owner:
        store.save({'version':1,'owner':None,'released_at':dt.datetime.now(dt.timezone.utc).isoformat()},revision)
    return 'LEASE_RELEASED_OR_NOT_OWNED'


if __name__=='__main__':
    if os.getenv('GITHUB_ACTIONS')!='true':raise RuntimeError('CLOUD_CONTEXT_REQUIRED')
    owner=os.environ['GITHUB_RUN_ID']+':'+os.environ.get('GITHUB_JOB','job')
    store=GitHubStore(os.environ['GH_TOKEN'],path=PATH,validate=False)
    print(release(store,owner) if '--release' in sys.argv else acquire(store,owner))
