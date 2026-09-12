const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 const calls=[],dialogs=[],messages=[];let requested,reloaded=false,dirty=false;
 const preview={token:'TOKEN',reason:'<img src=x onerror=alert(1)>',before:{verified_hours:2},after:{verified_hours:1},financial_before:{settlement_amount:280},proposed_amount:140,settlement_blockers:[],dependencies:[]};
 const ctx={__:x=>x,powerpro:{checkin_overtime:{}},frappe:{provide(){},utils:{escape_html:s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')},
  prompt(fields,fn){assert(fields[0].reqd);requested=fn;},msgprint(m){messages.push(m)},call(args){calls.push(args);return Promise.resolve({message:preview})},ui:{Dialog:function(args){Object.assign(this,args);this.show=()=>{};this.hide=()=>{};dialogs.push(this);}}}};
 vm.runInNewContext(fs.readFileSync('powerpro/public/js/checkin_overtime.js','utf8'),ctx);
 const frm={doc:{name:'AUTH'},is_dirty:()=>dirty,reload_doc(){reloaded=true;}};
 dirty=true;ctx.powerpro.checkin_overtime.review(frm);assert.equal(requested,undefined);
 dirty=false;ctx.powerpro.checkin_overtime.review(frm);requested({reason:'reason'});await Promise.resolve();
 assert.equal(calls[0].method,'powerpro.controllers.checkin_overtime_review.preview_review');
 assert(dialogs[0].fields[0].options.includes('&lt;img'));assert(!dialogs[0].fields[0].options.includes('<img'));
 assert(dialogs[0].fields[0].options.includes('140'));
 dirty=true;dialogs[0].primary_action();assert.equal(calls.length,1);
 dirty=false;dialogs[0].primary_action();await Promise.resolve();
 assert.equal(calls[1].type,'POST');assert.equal(calls[1].args.token,'TOKEN');assert.equal(calls[1].args.authorization,'AUTH');assert(reloaded);
 console.log('HR review UI: required reason, escaped preview, before/after amount, dirty guards and explicit token-bound POST passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
