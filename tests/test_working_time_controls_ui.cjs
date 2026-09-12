const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let prompt;const buttons=[],calls=[],dialogs=[],messages=[];let dirty=false;
 const result={reference:'<unsafe>',controls:[{code:'daily_work',status:'Review',observed:11,limit:8,unit:'hours',message:'<unsafe>'}],notes:['Evidence incomplete'],evidence_issues:[]};
 const ctx={__:s=>s,powerpro:{working_time_controls:{}},frappe:{provide(){},prompt(_f,fn){prompt=fn},msgprint:m=>messages.push(m),
  utils:{escape_html:s=>s.replaceAll('<','&lt;').replaceAll('>','&gt;')},call:q=>{calls.push(q);return Promise.resolve({message:result})},
  ui:{Dialog:function(d){dialogs.push(d);this.show=()=>{}}}}};
 vm.runInNewContext(fs.readFileSync('powerpro/public/js/working_time_controls.js','utf8'),ctx);
 const frm={doc:{doctype:'Overtime Authorization',name:'AUTH',docstatus:1,evidence_enrolled:0},is_dirty:()=>dirty,add_custom_button:(l,f)=>buttons.push(f)};
 ctx.powerpro.working_time_controls.add_button(frm);assert.equal(buttons.length,0);
 frm.doc.evidence_enrolled=1;ctx.powerpro.working_time_controls.add_button(frm);dirty=true;buttons[0]();assert.equal(prompt,undefined);
 dirty=false;buttons[0]();prompt({profile:'General',break_rule:'Una hora después de cuatro',quarterly_basis:'Pendiente de clasificar'});await Promise.resolve();
 assert.equal(calls[0].method,'powerpro.controllers.working_time_controls.preview');assert.equal(calls[0].args.source_name,'AUTH');
 assert.equal(calls[0].args.quarterly_basis,'Unclassified');assert(!dialogs[0].fields[0].options.includes('<unsafe>'));
 assert(dialogs[0].fields[0].options.includes('Requiere revisión'));assert(!dialogs[0].primary_action);
 console.log('Working-time UI: enrolled/submitted scope, dirty guard, selected scenario, escaped read-only preview passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
