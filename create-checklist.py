"""Create one explicitly approved checklist via Things' supported URL scheme.
Input JSON: title, notes, list-id, checklist-items (list of strings).
Writes a started receipt before dispatch; never automatically retries.
Verify the resulting task with refresh.py before removing any source items.
"""
import json,os,pathlib,subprocess,sys,urllib.parse
os.umask(0o077)
p=pathlib.Path(sys.argv[1]);r=json.loads(p.read_text())
assert set(r)=={'title','notes','list-id','checklist-items'}
assert all(isinstance(r[k],str) for k in ('title','notes','list-id'))
assert isinstance(r['checklist-items'],list) and 0<len(r['checklist-items'])<=100
assert all(isinstance(v,str) and v and '\n' not in v and '\r' not in v for v in r['checklist-items'])
receipt=p.with_suffix('.receipt.json')
with receipt.open('x') as f:json.dump({'state':'started','request':r},f)
params={**r,'checklist-items':'\n'.join(r['checklist-items']),'when':'someday'}
subprocess.run(['/usr/bin/open','-g','things:///add?'+urllib.parse.urlencode(params, quote_via=urllib.parse.quote)],check=True)
receipt.write_text(json.dumps({'state':'dispatched_unverified','request':r},indent=2))
print('Dispatched; read-back verification required.')
