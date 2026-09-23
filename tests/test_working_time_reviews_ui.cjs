const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let hooks,prompt;const buttons={},calls=[],routes=[];let dirty=false;
 const ctx={__:s=>s,frappe:{ui:{form:{on:(dt,h)=>hooks=h}},prompt:(fields,fn)=>prompt=fn,msgprint(){},
  set_route:(...args)=>routes.push(args),call:q=>{calls.push(q);return Promise.resolve({message:{}})}}};
 vm.runInNewContext(fs.readFileSync('powerpro/custom_hr/client_scripts/working_time_review.js','utf8'),ctx);
 const frm={doc:{name:'REVIEW',status:'Active',source_type:'Overtime Authorization',source_name:'AUTH'},
  is_new:()=>false,is_dirty:()=>dirty,reload_doc(){},add_custom_button:(label,fn)=>buttons[label]=fn};
 hooks.refresh(frm);buttons['Configurar vigilancia']();prompt({status:'Pausada',responsible:'reviewer',reason:'pause'});await Promise.resolve();
 assert.equal(calls[0].args.status,'Paused');assert.equal(calls[0].type,'POST');assert.equal(calls[0].args.name,'REVIEW');
 dirty=true;prompt({status:'Activa',responsible:'reviewer',reason:'resume'});assert.equal(calls.length,1);
 buttons['Ver incidencias']();assert.equal(routes[0][2].working_time_review,'REVIEW');
 console.log('Review UI: explicit pause/resume/assignment mapping, POST, dirty guard and scoped cases link passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
