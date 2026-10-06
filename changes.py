#!/usr/bin/env python3
"""Build, preview, and explicitly apply guarded changes through Things automation."""
import argparse, datetime, hashlib, json, os, pathlib, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parent
LOCAL=ROOT/'local'
FIELDS=('name','notes','status','modificationDate')

def build(data, requests):
    current={x['id']:x for x in data['tasks']}
    projects={p['id'] for p in data['projects']}
    raw={x['uuid']:x for x in data['databaseSupplement']['tables']['TMTask']}
    lists={x['id']:x for x in data['lists']}
    result=[]; seen=set()
    if not isinstance(requests,list) or not requests: raise ValueError('Expected a nonempty request list')
    for r in requests:
        if r['id'] in seen: raise ValueError('One operation per item per plan; refresh between dependent changes')
        seen.add(r['id'])
        if r['id'] not in current or r['id'] in projects: raise ValueError('Only current individual tasks are supported')
        t=current[r['id']]; db=raw[r['id']]
        if any(db.get(k) for k in ('repeater','rt1_repeatingTemplate','rt1_recurrenceRule')): raise ValueError('Recurring items are protected')
        if t['status']!='open': raise ValueError('Only open tasks are supported')
        action=r['action']
        if action not in ('rename','notes','move','complete','trash'): raise ValueError('Unsupported action')
        op={'id':r['id'],'action':action,'before':{k:t[k] for k in FIELDS}}
        if action in ('rename','notes'):
            if not isinstance(r.get('value'),str): raise ValueError('value must be a string')
            if action=='rename' and not r['value'].strip(): raise ValueError('Empty title')
            op['value']=r['value']
        if action=='move':
            if r.get('destinationId') not in lists: raise ValueError('Unknown destination ID')
            op['destinationId']=r['destinationId'];op['destinationName']=lists[r['destinationId']]['name']
        result.append(op)
    return {'version':1,'exportedAt':data['exportedAt'],'operations':result}

def digest(plan): return hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
def run(plan,mode):
    if mode == 'apply' and any(op['action']=='move' for op in plan['operations']):
        run(plan,'preview')
        results=[]
        for op in plan['operations']:
            try:
                single={**plan,'operations':[op]}
                if op['action']=='move':
                    run(single,'preview')
                    subprocess.run(['/usr/bin/osascript',str(ROOT/'move-item.applescript'),op['id'],op['destinationId'],op['before']['name'],op['before']['notes']],capture_output=True,text=True,check=True,timeout=60)
                    results.append({'id':op['id'],'ok':True})
                else:
                    result=run(single,'apply');results.extend(result['results'])
                    if not result['complete']: break
            except Exception as e:
                results.append({'id':op['id'],'ok':False,'error':str(e)});break
        return {'results':results,'complete':len(results)==len(plan['operations']) and all(r['ok'] for r in results)}
    # Freeze the validated document; do not reread an editable request file in the runner.
    with tempfile.NamedTemporaryFile(mode='w',suffix='.json',dir=LOCAL) as frozen:
        json.dump(plan,frozen); frozen.flush()
        p=subprocess.run(['/usr/bin/osascript','-l','JavaScript',str(ROOT/'change-items.js'),frozen.name,mode],capture_output=True,text=True,timeout=180,check=True)
    return json.loads(p.stdout)
def main():
    os.umask(0o077);LOCAL.mkdir(mode=0o700,exist_ok=True)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','preview','apply']);p.add_argument('file',type=pathlib.Path);p.add_argument('--confirm');a=p.parse_args()
    data=json.loads((LOCAL/'things-data.json').read_text())
    document=json.loads(a.file.read_text())
    if a.command=='plan':
        plan=build(data,document); out=LOCAL/'plan.json';out.write_text(json.dumps(plan,indent=2));print(out);print('Review token:',digest(plan));return
    plan=document
    # Reconstruct against the last export to reject forged/invalid plan structure.
    if build(data,plan['operations'])!=plan: raise ValueError('Plan differs from snapshot; rebuild it')
    if a.command=='preview':
        print(json.dumps(plan,indent=2)); print(run(plan,'preview'));print('Review token:',digest(plan));return
    if a.confirm!=digest(plan): raise ValueError('Apply requires --confirm with the exact reviewed plan token')
    # Exclusive lock + durable started receipt: never silently retry an ambiguous application.
    lock=LOCAL/'apply.lock'
    with lock.open('x') as f: f.write(digest(plan))
    receipt=LOCAL/('receipt-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')+'.json')
    receipt.write_text(json.dumps({'state':'started','plan':plan},indent=2))
    try:
        result=run(plan,'apply')
        receipt.write_text(json.dumps({'state':'finished','plan':plan,'result':result},indent=2));print(json.dumps(result,indent=2))
        if not result['complete']: raise RuntimeError('Partial result; inspect receipt and refresh before further changes')
    except BaseException:
        print('Apply lock retained. Inspect Things and receipt before clearing it:',lock);raise
    else: lock.unlink()
if __name__=='__main__': main()
