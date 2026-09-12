const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let prompt;const buttons=[],calls=[],dialogs=[];let dirty=false,reloads=0;
 const result={token:'historical-token',note:'<untrusted>',worked_hours_before:8,worked_hours_after:6,
  worked_intervals:[{start:'<start>',end:'2026-09-15 01:00:00'}]};
 const ctx={__:s=>s,powerpro:{ordinary_night_history:{}},frappe:{provide(){},msgprint(){},prompt:(f,fn)=>prompt={fields:f,fn},
  utils:{escape_html:s=>s.replaceAll('<','&lt;').replaceAll('>','&gt;')},call:q=>{calls.push(q);return Promise.resolve({message:result})},
  ui:{Dialog:function(d){dialogs.push(d);this.show=()=>{};this.hide=()=>{}}}}};
 vm.runInNewContext(fs.readFileSync('powerpro/public/js/ordinary_night_history.js','utf8'),ctx);
 const frm={doc:{doctype:'Ordinary Night Settlement',name:'NIGHT',docstatus:1},is_dirty:()=>dirty,reload_doc:()=>reloads++,add_custom_button:(l,f)=>buttons.push(f)};
 const add=s=>ctx.powerpro.ordinary_night_history.add_button(frm,s);
 add({can_review:true});assert.equal(buttons.length,0);
 frm.doc.docstatus=2;add({can_review:false});assert.equal(buttons.length,0);
 add({can_review:true,manual_review_allowed:true});assert.equal(buttons.length,1);
 dirty=true;buttons[0]();assert.equal(prompt,undefined);
 dirty=false;buttons[0]();assert(prompt.fields.some(f=>f.fieldname==='manual'));
 prompt.fn({reason:'Historical correction',manual:1,reference:'Signed record',intervals:[{start:'2026-09-14 18:00:00',end:'2026-09-15 01:00:00',idx:1}]});
 await Promise.resolve();assert.equal(calls.length,1);assert.equal(calls[0].method,'powerpro.controllers.ordinary_night_history.preview_review');
 const declaration=JSON.parse(calls[0].args.manual_declaration);assert(declaration.full_session);assert.equal(declaration.intervals[0].idx,undefined);
 assert(!dialogs[0].fields[0].options.includes('<untrusted>'));assert(dialogs[0].fields[0].options.includes('&lt;start&gt;'));
 dirty=true;dialogs[0].primary_action();assert.equal(calls.length,1);
 dirty=false;dialogs[0].primary_action();await Promise.resolve();
 assert.equal(calls[1].method,'powerpro.controllers.ordinary_night_history.apply_review');assert.equal(calls[1].type,'POST');
 assert.equal(calls[1].args.token,result.token);assert.equal(calls[1].args.manual_declaration,calls[0].args.manual_declaration);assert.equal(reloads,1);
 add({can_review:true,manual_review_allowed:false});buttons[1]();assert(!prompt.fields.some(f=>f.fieldname==='manual'));
 console.log('Night historical UI: cancelled/role scope, optional complete declaration, escaped review, exact captured token/declaration POST and dirty guards passed');
})().catch(e=>{console.error(e);process.exitCode=1});
