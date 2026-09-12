const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let hooks,prompt;const buttons={},calls=[];let dirty=false,reloads=0;
 const ctx={__:s=>s,frappe:{ui:{form:{on:(dt,h)=>hooks=h}},prompt:(f,fn)=>prompt=fn,
  call:q=>{calls.push(q);return Promise.resolve({message:{}})},set_route(){},msgprint(){}}};
 vm.runInNewContext(fs.readFileSync('powerpro/power_pro/doctype/working_time_incident/working_time_incident.js','utf8'),ctx);
 const frm={doc:{name:'CASE',status:'Open',evidence_hash:'original',responsible:'reviewer'},is_new:()=>false,is_dirty:()=>dirty,
  reload_doc:()=>reloads++,add_custom_button:(label,fn)=>buttons[label]=fn};
 hooks.refresh(frm);buttons['Registrar resolución']();frm.doc.evidence_hash='changed';
 prompt({resolution:'Excepción documentada',reason:'documented reason',reference:'reference'});await Promise.resolve();
 assert.equal(calls[0].args.expected_hash,'original');assert.equal(calls[0].args.resolution,'Documented Exception');assert.equal(calls[0].type,'POST');
 dirty=true;buttons['Comprobar nuevamente']();assert.equal(calls.length,1);
 dirty=false;buttons['Asignar responsable']();prompt({responsible:'other',reason:'handoff'});await Promise.resolve();
 assert.equal(calls[1].args.responsible,'other');assert.equal(reloads,2);
 console.log('Incident UI: captured evidence token, resolution mapping, explicit assignment, dirty guard and reload passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
