"""Create an explicitly approved JSON list of tasks via the official Things URL scheme.
Each record has title, notes, deadline (YYYY-MM-DD), list-id. A receipt prevents
blind retries. Refresh and verify returned fields after dispatch.
"""
import datetime,json,os,pathlib,subprocess,sys,urllib.parse
os.umask(0o077)
p=pathlib.Path(sys.argv[1]);requests=json.loads(p.read_text())
assert isinstance(requests,list) and requests
for r in requests:
 assert set(r)=={'title','notes','deadline','list-id'}
 assert all(isinstance(v,str) for v in r.values())
 assert r['title'].strip() and r['list-id']
 assert datetime.date.fromisoformat(r['deadline']).isoformat()==r['deadline']
receipt=p.with_suffix('.receipt.json');state={'state':'started','requests':requests,'dispatched':0}
with receipt.open('x') as f:json.dump(state,f)
for r in requests:
 subprocess.run(['/usr/bin/open','-g','things:///add?'+urllib.parse.urlencode(r,quote_via=urllib.parse.quote)],check=True)
 state['dispatched']+=1;receipt.write_text(json.dumps(state,indent=2))
state['state']='dispatched_unverified';receipt.write_text(json.dumps(state,indent=2))
print('Dispatched',len(requests),'tasks; verify before retrying.')
