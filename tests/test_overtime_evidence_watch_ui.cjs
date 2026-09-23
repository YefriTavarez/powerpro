const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let handler;const buttons=[],calls=[],routes=[];let reloaded=false;
 const ctx={__:x=>x,frappe:{ui:{form:{on(dt,h){assert.equal(dt,'Overtime Evidence Watch');handler=h;}}},
  set_route(...args){routes.push(args);},call(args){calls.push(args);return Promise.resolve({message:{status:'Needs Review'}});}}};
 vm.runInNewContext(fs.readFileSync('powerpro/custom_hr/client_scripts/overtime_evidence_watch.js','utf8'),ctx);
 const frm={doc:{name:'WATCH',source_type:'Retroactive Overtime Adjustment',source_name:'AJUSTE'},is_new:()=>false,
  add_custom_button(label,fn){buttons.push({label,fn});},reload_doc(){reloaded=true;}};
 handler.refresh(frm);assert.equal(buttons.length,2);
 buttons[0].fn();assert.deepEqual(routes[0],['Form','Retroactive Overtime Adjustment','AJUSTE']);
 await buttons[1].fn();assert.equal(calls[0].type,'POST');assert.equal(calls[0].args.name,'WATCH');assert(reloaded);
 console.log('Evidence watch UI: correct source route and explicit recheck POST passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
