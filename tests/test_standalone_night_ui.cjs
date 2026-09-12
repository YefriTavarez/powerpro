const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let handlers;const calls=[],messages=[],buttons=[],routes=[];
 const ctx={__:s=>s,frappe:{ui:{form:{on(_name,h){handlers=h}}},msgprint:m=>messages.push(m),set_route:(...a)=>routes.push(a),call:q=>{calls.push(q);return Promise.resolve({message:[]})}}};
 vm.runInNewContext(fs.readFileSync('powerpro/power_pro/doctype/ordinary_night_automation/ordinary_night_automation.js','utf8'),ctx);
 let dirty=false,reloads=0;
 const frm={doc:{name:'SCHEDULE',docstatus:0,days:[]},is_dirty:()=>dirty,reload_doc:()=>reloads++,add_custom_button:(label,fn)=>buttons.push({label,fn}),dashboard:{set_headline_alert(){}}};
 handlers.refresh(frm);assert.equal(buttons.length,0);
 frm.doc.docstatus=1;frm.doc.days=[{settlement:'NIGHT'},{settlement:'NIGHT'}];handlers.refresh(frm);
 assert.equal(buttons.length,2);dirty=true;buttons[0].fn();assert.equal(calls.length,0);assert.equal(messages.length,1);
 dirty=false;buttons[0].fn();await Promise.resolve();assert.equal(calls[0].type,'POST');assert.equal(calls[0].args.schedule,'SCHEDULE');assert.equal(reloads,1);
 buttons[1].fn();assert.equal(routes[0][2],'NIGHT');
 console.log('Standalone night UI: submitted-only actions, dirty guard, scoped POST and unique settlement links passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
