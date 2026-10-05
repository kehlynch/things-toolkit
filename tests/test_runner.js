const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../change-items.js'),'utf8');
function exercise(action,mode='apply',stale=false) {
 const values={name:'Example',notes:'Original',status:'open',modificationDate:'today'};
 const before={...values};if(stale)before.name='Old';
 const op={id:'a',action,before,value:'New',destinationId:'s'};
 let writes=0,trash=[],dest=[];
 const item={};for(const k of Object.keys(values)) Object.defineProperty(item,k,{get:()=>()=>values[k],set:v=>{writes++;values[k]=v}});
 const app={toDos:{byId:()=>item},lists:{byId:()=>({name:()=> 'Someday',toDos:{id:()=>dest}}),byName:()=>({toDos:{id:()=>trash}})},move:()=>{writes++;dest.push('a')},delete:()=>{writes++;trash.push('a')}};
 const context={Application:()=>app,ObjC:{import:()=>{},unwrap:x=>x},$:{NSString:{stringWithContentsOfFileEncodingError:()=>JSON.stringify({operations:[op]})},NSUTF8StringEncoding:4}};
 vm.createContext(context);vm.runInContext(source,context);
 if(stale){assert.throws(()=>context.run(['test',mode]),/Stale/);assert.equal(writes,0);return;}
 const result=JSON.parse(context.run(['test',mode]));
 if(mode==='preview'){assert.equal(writes,0);assert.equal(result.preflight,'passed');}
 else {assert.equal(writes,1);assert.equal(result.complete,true);}
}
for(const action of ['rename','notes','move','complete','trash']) {exercise(action);exercise(action,'preview');exercise(action,'apply',true);}
console.log('15 runner checks passed (mock Things; no live writes).');
