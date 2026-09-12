const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const file='powerpro/power_pro/doctype/retroactive_overtime_adjustment/retroactive_overtime_adjustment.js';
async function fixture(state,options={}) {
 const calls=[],buttons=[],messages=[],routes=[],drafts=[],headlines=[];
 const reviews=[];
 const ctx={powerpro:{checkin_overtime:{review:(...args)=>reviews.push(args)}},__: (s,args=[])=>s.replace(/\{(\d+)\}/g,(_,i)=>args[i]),frappe:{ui:{form:{on(){}}},
  require(path,fn){fn();},call(q){calls.push(q);return Promise.resolve({message:state});},msgprint(s){messages.push(s);},
  confirm(s,fn){fn();},new_doc(...args){drafts.push(args);},set_route(...args){routes.push(args);},datetime:{get_today:()=>'2026-09-15'}}};
 vm.runInNewContext(fs.readFileSync(file,'utf8'),ctx);
 const frm={doc:{docstatus:1,reconciliation_engine:'Verified Checkins',name:'AJUSTE',employee:'EMP',work_date:'2026-09-07',
  settlement_payroll_date:'2026-09-15',planned_settlement:'Cash',settlement_status:'Pending',...options.doc},
  is_new:()=>!!options.is_new,is_dirty:()=>!!options.dirty,add_custom_button(label,fn){buttons.push({label,fn});},reload_doc(){messages.push('reload');},
  dashboard:{set_headline_alert(...args){headlines.push(args);}}};
 ctx.add_evidence_actions(frm);await Promise.resolve();
 return {ctx,frm,calls,buttons,messages,routes,drafts,headlines,reviews};
}
(async()=>{
 let x=await fixture({}, {doc:{reconciliation_engine:'Legacy'}});assert.equal(x.calls.length,0);
 x=await fixture({state:'Verified',settlement_ready:false,ordinary_night_hours:1,can_night:true});
 assert.equal(x.headlines.length,1);x.buttons[0].fn();assert.equal(x.drafts[0][0],'Ordinary Night Settlement');
 assert.equal(x.drafts[0][1].employee,'EMP');assert.equal(x.drafts[0][1].settlement_payroll_date,'2026-09-15');
 x=await fixture({state:'Verified',can_night:true,ordinary_night:'NIGHT'});x.buttons[0].fn();assert.equal(x.routes[0][2],'NIGHT');
 x=await fixture({state:'Verified',can_night:false});assert.equal(x.buttons.length,0);
 x=await fixture({state:'Needs Review',can_night:true},{dirty:true});assert.equal(x.headlines.length,1);x.buttons[0].fn();assert.equal(x.drafts.length,0);assert.equal(x.messages.length,1);
 x.ctx.add_cash_settlement_actions(x.frm);x.buttons.find(b=>b.label==='Create Cash Settlement').fn();assert.equal(x.calls.length,1);
 x=await fixture({state:'Verified',can_night:false});x.ctx.add_cash_settlement_actions(x.frm);x.buttons[0].fn();
 assert.equal(x.calls[1].type,'POST');assert.equal(x.calls[1].method,'powerpro.controllers.overtime_cash_settlement.create_cash_settlement');
 await Promise.resolve();assert(x.messages.includes('reload'));
 x=await fixture({state:'Verified',can_elect:true});x.buttons[0].fn();assert.equal(x.drafts[0][0],'Overtime Settlement Election');assert.equal(x.drafts[0][1].retroactive_adjustment,'AJUSTE');
 x=await fixture({state:'Verified',election:'ELECT'});x.buttons[0].fn();assert.equal(x.routes[0][2],'ELECT');
 x=await fixture({state:'Verified',can_credit:true});await x.buttons[0].fn();assert.equal(x.calls[1].type,'POST');assert.equal(x.calls[1].method,'powerpro.controllers.retroactive_evidence.create_compensatory_settlement');
 x=await fixture({state:'Verified',can_credit:true},{dirty:true});x.buttons[0].fn();assert.equal(x.calls.length,1);
 x=await fixture({state:'Needs Review',can_review:true,manual_review_allowed:true});x.buttons.find(b=>b.label==='Revisar evidencia corregida').fn();assert.equal(x.reviews[0][1],false);
 x.buttons.find(b=>b.label==='Declarar jornada de RR. HH.').fn();assert.equal(x.reviews[1][1],true);
 x.buttons.find(b=>b.label==='Historial de conciliación').fn();assert.equal(x.routes[0][2].retroactive_adjustment,'AJUSTE');
 x=await fixture({can_review:true,audit:'DRAFT-AUDIT'},{doc:{docstatus:0}});
 assert.equal(x.calls[0].method,'powerpro.controllers.retroactive_draft_review.get_status');
 x.buttons.find(b=>b.label==='Declarar jornada inicial de RR. HH.').fn();assert.equal(x.reviews[0][1],true);
 x.buttons.find(b=>b.label==='Evidencia declarada').fn();assert.equal(x.routes[0][2],'DRAFT-AUDIT');
 x=await fixture({can_review:false},{doc:{docstatus:0}});assert.equal(x.buttons.length,0);
 x=await fixture({can_review:true},{doc:{docstatus:0},is_new:true});assert.equal(x.calls.length,0);
 console.log('Retroactive UI: current evidence alert, scoped night creation/link, permission/dirty guards and explicit cash POST passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
