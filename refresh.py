#!/usr/bin/env python3
"""Refresh supported Things data plus a consistent SQLite snapshot; never write to Things."""
import base64, collections, datetime, json, os, pathlib, sqlite3, subprocess, tempfile
CODE=pathlib.Path(__file__).resolve().parent
ROOT=CODE/'local'
ROOT.mkdir(mode=0o700,exist_ok=True)
os.umask(0o077)

def main():
    # Only property getters are sent to Things. Failure leaves the previous export intact.
    run=subprocess.run(['/usr/bin/osascript','-l','JavaScript',str(CODE/'read-things.js')],check=True,capture_output=True,text=True,timeout=180)
    data=json.loads(run.stdout)
    candidates=list((pathlib.Path.home()/'Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac').glob('ThingsData-*/Things Database.thingsdatabase/main.sqlite'))
    if len(candidates)!=1: raise RuntimeError('Expected one Things database; refusing to guess.')
    source=candidates[0]
    # SQLite read-only mode plus query_only: live database is never a write destination.
    # Online backup includes committed WAL data, unlike simply copying main.sqlite.
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        snapshot=pathlib.Path(temp)/'things-snapshot.sqlite'
        src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=10)
        src.execute('PRAGMA query_only=ON')
        dst=sqlite3.connect(snapshot)
        try: src.backup(dst)
        finally: src.close(); dst.close()
        db=sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True)
        db.row_factory=sqlite3.Row
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        tables={name:[dict(row) for row in db.execute('SELECT * FROM "'+name+'"')] for name in ['TMTask','TMArea','TMTag','TMTaskTag','TMAreaTag','TMChecklistItem']}
        db.close()
        data['databaseSupplement']={'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourcePath':str(source),'tables':tables,'encoding':'BLOB values use base64; raw internal dates/enums are not interpreted. Supported fields above are authoritative.'}
        ids={r['uuid'] for r in tables['TMTask']}
        assert all(r['id'] in ids for r in data['tasks']+data['projects'])
        def encode(value):
            if isinstance(value,bytes): return {'base64':base64.b64encode(value).decode()}
            raise TypeError(type(value).__name__)
        export=pathlib.Path(temp)/'things-data.json'
        export.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=encode)+'\n')
        snapshot.replace(ROOT/'things-snapshot.sqlite')
        export.replace(ROOT/'things-data.json')
    project_ids={p['id'] for p in data['projects']}
    tasks=[t for t in data['tasks'] if t['id'] not in project_ids]
    summary={'exportedAt':data['exportedAt'],'tasksExcludingProjects':len(tasks),'taskStatuses':dict(collections.Counter(t['status'] for t in tasks)),'projects':len(data['projects']),'areas':len(data['areas']),'tags':len(data['tags']),'checklistRows':len(tables['TMChecklistItem']),'databaseTaskRows':len(tables['TMTask']),'lists':{l['name']:len(l['itemIds']) for l in data['lists']}}
    (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
