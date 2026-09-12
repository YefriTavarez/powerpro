const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let handlers;const calls=[],messages=[];
const context={__:x=>x,frappe:{ui:{form:{on(dt,h){handlers=h}}},msgprint:x=>messages.push(x),
 call(q){calls.push(q);return Promise.resolve({message:{overtime_policy_whole_night:1,overtime_policy_version:q.args.name}})}}};
vm.runInNewContext(fs.readFileSync('powerpro/power_pro/doctype/dgii_payroll_settings/dgii_payroll_settings.js','utf8'),context);
const frm={doc:{},set_value(data){Object.assign(this.doc,data);return Promise.resolve()},set_query(){},add_custom_button(){}};
(async()=>{
 await handlers.manage_overtime_pay_policy(frm);assert.equal(frm.doc.overtime_policy_night_percent,undefined);
 frm.doc.manage_overtime_pay_policy=1;await handlers.manage_overtime_pay_policy(frm);
 assert.equal(frm.doc.overtime_policy_night_percent,15);assert.equal(frm.doc.overtime_policy_regular_percent,35);
 frm.doc.overtime_policy_night_percent=20;await handlers.manage_overtime_pay_policy(frm);
 assert.equal(frm.doc.overtime_policy_night_percent,20);
 await handlers.overtime_policy_load(frm);assert.equal(calls.length,0);assert.equal(messages.length,1);
 frm.doc.overtime_policy_version='POL-1';await handlers.overtime_policy_load(frm);
 assert.equal(calls[0].method,'powerpro.controllers.overtime_policy_settings.load_version');
 assert.equal(frm.doc.overtime_policy_whole_night,1);
 frm.doc.overtime_policy_compensatory=1;await handlers.overtime_policy_compensatory(frm);
 assert.equal(frm.doc.overtime_policy_rest_duration,36);assert.equal(frm.doc.overtime_policy_leave_increment,.5);
 assert(!calls.some(c=>c.method.includes('save')));
 console.log('Settings UI: explicit load, defaults, preserved choices, no implicit save passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
