const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function fixture(doc,dirty=false){
 const buttons=[],calls=[],dialogs=[],alerts=[];let handler;
 const context={__:s=>s,frappe:{ui:{form:{on(_name,config){handler=config}},Dialog:class{
  constructor(config){this.config=config;dialogs.push(this)}show(){}hide(){this.hidden=true}
 }},call(options){calls.push(options);return Promise.resolve({message:{status:'Overdue'}})},msgprint(s){alerts.push(s)}}};
 vm.runInNewContext(fs.readFileSync('powerpro/custom_hr/client_scripts/overtime_settlement_election.js','utf8'),context);
 const frm={doc,is_new:()=>false,is_dirty:()=>dirty,add_custom_button(label,fn){buttons.push({label,fn})},reload_doc(){alerts.push('reloaded')},dashboard:{set_headline_alert(s){alerts.push(s)}}};
 handler.refresh(frm);return {buttons,calls,dialogs,alerts};
}
(async()=>{
 let x=fixture({name:'ELECT',docstatus:0});assert.equal(x.buttons.length,1);
 await x.buttons[0].fn();assert.equal(x.calls[0].type,'POST');assert.equal(x.calls[0].method,'powerpro.controllers.overtime_rest.approve_election');
 x=fixture({name:'ELECT',docstatus:0},true);x.buttons[0].fn();assert.equal(x.calls.length,0);
 x=fixture({name:'ELECT',docstatus:1,choice:'Compensatory Rest',status:'Credited',employee:'EMP',planned_start:'2026-09-15 18:00',planned_end:'2026-09-17 06:00'});
 await Promise.resolve();assert(x.alerts.some(s=>s.includes('vencido')));
 x.buttons.find(b=>b.label==='Confirmar descanso disfrutado').fn();
 const d=x.dialogs[0];assert(d.config.fields.find(f=>f.fieldname==='reference').reqd);
 d.config.primary_action({actual_start:'2026-09-15 18:00',actual_end:'2026-09-17 06:00',reference:'HR evidence'});
 await Promise.resolve();assert.equal(x.calls.at(-1).type,'POST');assert.equal(x.calls.at(-1).args.name,'ELECT');assert.equal(x.calls.at(-1).args.reference,'HR evidence');
 x=fixture({name:'ELECT',docstatus:1,choice:'Compensatory Rest',status:'Enjoyed'});
 assert(x.buttons.some(b=>b.label==='Corregir confirmación de disfrute'));
 assert(!x.buttons.some(b=>b.label==='Confirmar descanso disfrutado'));
 x.buttons.find(b=>b.label==='Corregir confirmación de disfrute').fn();assert(x.dialogs[0].config.fields[0].reqd);
 x=fixture({name:'ELECT',docstatus:2,choice:'Compensatory Rest'});assert.equal(x.buttons.length,0);
 console.log('Rest UI: managed approval, explicit POST, dirty guard, overdue alert and corrective action passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
