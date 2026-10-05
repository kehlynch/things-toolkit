// Fixed operation allowlist. Never evaluates plan text as code.
ObjC.import('Foundation');
function run(argv) {
 const plan=JSON.parse(ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError(argv[0],$.NSUTF8StringEncoding,null)));
 const app=Application('/Applications/Things3.app');
 const fields=['name','notes','status','modificationDate'];
 function state(t) { const s={}; fields.forEach(k=>s[k]=t[k]()); return JSON.parse(JSON.stringify(s)); }
 function check(op) {
   const t=app.toDos.byId(op.id);
   const actual=state(t);
   fields.forEach(k=>{if(JSON.stringify(actual[k])!==JSON.stringify(op.before[k])) throw Error('Stale item: '+op.id+' field '+k);});
   if(op.action==='move') { const dest=app.lists.byId(op.destinationId); dest.name(); }
   return t;
 }
 // All-item preflight before the first write; then check again immediately before each.
 plan.operations.forEach(check);
 if(argv[1]!=='apply') return JSON.stringify({preflight:'passed',count:plan.operations.length});
 const results=[];
 for (const op of plan.operations) {
   try {
     const t=check(op);
     if(op.action==='rename') t.name=op.value;
     else if(op.action==='notes') t.notes=op.value;
     else if(op.action==='trash') app.delete(t);
     else if(op.action==='complete') t.status='completed';
     else if(op.action==='move') app.move(t,{to:app.lists.byId(op.destinationId)});
     else throw Error('Unsupported operation');
     let verified;
     if(op.action==='trash') verified=app.lists.byName('Trash').toDos.id().indexOf(op.id)>=0;
     else if(op.action==='move') verified=app.lists.byId(op.destinationId).toDos.id().indexOf(op.id)>=0;
     else verified=t[op.action==='rename'?'name':op.action==='notes'?'notes':'status']()===(op.action==='complete'?'completed':op.value);
     if(!verified) throw Error('Read-back verification failed');
     results.push({id:op.id,ok:true});
   } catch(e) { results.push({id:op.id,ok:false,error:String(e)}); break; }
 }
 return JSON.stringify({results:results,complete:results.length===plan.operations.length&&results.every(r=>r.ok)});
}
