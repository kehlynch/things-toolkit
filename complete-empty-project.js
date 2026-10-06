// Explicitly approved empty-project completion; refuses stale or nonempty projects.
function run(argv) {
 const app=Application('/Applications/Things3.app');
 const p=app.projects.byId(argv[0]);
 if(p.name()!==argv[1] || p.notes()!==argv[2] || p.status()!=='open' || p.modificationDate().toISOString()!==argv[3]) throw Error('Project changed; refresh and review');
 if(p.toDos.length!==0) throw Error('Project is not empty');
 const notes=argv[2] ? argv[2]+'\n\n'+argv[4] : argv[4];
 p.notes=notes;
 if(p.notes()!==notes) throw Error('Notes verification failed');
 p.status='completed';
 if(p.status()!=='completed') throw Error('Completion verification failed');
 return JSON.stringify({id:argv[0],notes:p.notes(),status:p.status()});
}
