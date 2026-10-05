// Read-only Things automation: property getters only; no item mutations.
function run() {
 const app = Application('/Applications/Things3.app');
 const fields = ['id','name','status','notes','tagNames','creationDate','modificationDate','dueDate','activationDate','completionDate','cancellationDate'];
 function items(collection) {
  const ids=collection.id(); const rows=ids.map(id=>({id:id}));
  fields.slice(1).forEach(key=>{const values=collection[key](); values.forEach((v,i)=>rows[i][key]=v);});
  return rows;
 }
 const tasks=items(app.toDos), projects=items(app.projects);
 const areas=app.areas().map(a=>({id:a.id(),name:a.name(),tagNames:a.tagNames(),itemIds:a.toDos.id()}));
 const lists=app.lists().map(l=>({id:l.id(),name:l.name(),itemIds:l.toDos.id()}));
 projects.forEach(p=>p.itemIds=app.projects.byId(p.id).toDos.id());
 const tags=app.tags().map(t=>({id:t.id(),name:t.name(),keyboardShortcut:t.keyboardShortcut(),childTagIds:t.tags.id(),itemIds:t.toDos.id()}));
 const history = ['Logbook','Trash'].map(name=>({list:name,items:items(app.lists.byName(name).toDos)}));
 return JSON.stringify({history,exportedAt:new Date().toISOString(),version:app.version(),source:'Things supported AppleScript interface',tasks,projects,areas,tags,lists},null,2);
}
