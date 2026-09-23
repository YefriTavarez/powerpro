const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let hooks,prompt,dirty=false;const buttons={},calls=[],routes=[];
 const ctx={__:s=>s,frappe:{ui:{form:{on:(dt,h)=>hooks=h}},prompt:(f,fn)=>prompt=fn,msgprint(){},
  set_route:(...args)=>routes.push(args),call:q=>{calls.push(q);return Promise.resolve({message:{}})}}};
 vm.runInNewContext(fs.readFileSync('powerpro/custom_hr/client_scripts/overtime_rest_watch.js','utf8'),ctx);
 const frm={doc:{name:'WATCH',election:'ELECTION'},is_new:()=>false,is_dirty:()=>dirty,reload_doc(){},add_custom_button:(label,fn)=>buttons[label]=fn};
 hooks.refresh(frm);buttons['Abrir elección del empleado']();assert.equal(routes[0][2],'ELECTION');
 buttons['Comprobar nuevamente']();await Promise.resolve();assert.equal(calls[0].type,'POST');assert.equal(calls[0].args.name,'WATCH');
 dirty=true;buttons['Comprobar nuevamente']();assert.equal(calls.length,1);
 dirty=false;buttons['Asignar responsable']();prompt({responsible:'reviewer',reason:'handoff'});await Promise.resolve();
 assert.equal(calls[1].args.responsible,'reviewer');assert.equal(calls[1].args.reason,'handoff');
 console.log('Rest watch UI: election link, guarded recheck POST, reasoned assignment passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
