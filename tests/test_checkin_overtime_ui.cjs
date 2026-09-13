const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
async function fixture(reply,doc={docstatus:1,name:'AUTH',evidence_enrolled:1},dirty=false){
 const calls=[],buttons=[],messages=[],routes=[],drafts=[];
 const ctx={__:x=>x,powerpro:{checkin_overtime:{}},frappe:{provide(){},call(q){calls.push(q);return Promise.resolve({message:q.method==='powerpro.controllers.checkin_overtime.get_status'?reply:q.method==='powerpro.controllers.overtime_holiday_base.get_status'?{can_declare:false}:{status:'Verified'}})},msgprint(x){messages.push(x)},show_alert(){},set_route(...args){routes.push(args)},new_doc(...args){drafts.push(args)}}};
 vm.runInNewContext(fs.readFileSync('powerpro/public/js/checkin_overtime.js','utf8'),ctx);
 const frm={doc,is_new:()=>false,is_dirty:()=>dirty,add_custom_button(label,fn){buttons.push({label,fn})},reload_doc(){messages.push('reloaded')}};
 ctx.powerpro.checkin_overtime.add_actions(frm);await Promise.resolve();return {calls,buttons,messages,routes,drafts};
}
(async()=>{
 let x=await fixture({enabled:true,can_process:false});assert.equal(x.buttons.length,0);
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:1});await x.buttons[0].fn();await Promise.resolve();
 assert.equal(x.calls[2].type,'POST');assert.equal(x.calls[2].method,'powerpro.controllers.checkin_overtime.process_now');assert(x.messages.includes('reloaded'));
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:1},undefined,true);x.buttons[0].fn();assert.equal(x.calls.length,2);
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:0},{docstatus:1,name:'AUTH'});x.buttons[0].fn();assert.equal(x.calls[2].method,'powerpro.controllers.checkin_overtime.enroll');
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:0},{docstatus:1,name:'AUTH',overtime_work_call:'CALL'});assert.equal(x.buttons.length,0);
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:1,can_night:true},{docstatus:1,name:'AUTH',employee:'EMP',work_date:'2026-09-14',auto_payroll_date:'2026-09-15'});
 x.buttons.find(b=>b.label==='Nocturnidad ordinaria').fn();assert.equal(x.drafts[0][0],'Ordinary Night Settlement');assert.equal(x.drafts[0][1].settlement_payroll_date,'2026-09-15');
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:1,can_night:true,ordinary_night:'NIGHT'});x.buttons.find(b=>b.label==='Nocturnidad ordinaria').fn();assert.equal(x.routes[0][2],'NIGHT');
 x=await fixture({enabled:true,can_process:true,evidence_enrolled:1,can_night:true},undefined,true);x.buttons.find(b=>b.label==='Nocturnidad ordinaria').fn();assert.equal(x.drafts.length,0);
 console.log('Checkin evidence UI: permission, explicit POST, dirty guard and standalone enrollment passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
