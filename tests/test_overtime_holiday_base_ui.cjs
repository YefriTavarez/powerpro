const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
async function fixture(allowed=true){
 const calls=[],buttons=[],dialogs=[],messages=[];let submit,dirty=false,reloaded=false;
 const ctx={__:x=>x,powerpro:{checkin_overtime:{}},frappe:{provide(){},
  call(q){calls.push(q);return Promise.resolve({message:q.method.endsWith('get_status')?{can_declare:allowed}:q.method.endsWith('preview')?
   {token:'TOKEN',declaration:{covered_hours:1,holiday_hours:1,reference:'<script>bad</script>'},estimate:{total_amount:115,holiday_base_already_in_salary:100}}:{audit:'AUDIT'}})},
  utils:{escape_html:x=>x.replaceAll('<','&lt;').replaceAll('>','&gt;')},msgprint:x=>messages.push(x),
  prompt(){throw new Error('Auto-closing prompt used')},ui:{Dialog:function(config){this.config=config;this.show=()=>{};this.hide=()=>{};this.get_primary_btn=()=>({prop(){}});if(config.fields[0].fieldname==='covered_hours')submit=config.primary_action;else dialogs.push(this)}}}};
 vm.runInNewContext(fs.readFileSync('powerpro/public/js/checkin_overtime.js','utf8'),ctx);
 const frm={doc:{doctype:'Overtime Authorization',name:'AUTH',docstatus:1,planned_settlement:'Cash'},
  is_new:()=>false,is_dirty:()=>dirty,add_custom_button(label,fn){buttons.push(fn)},reload_doc(){reloaded=true}};
 ctx.powerpro.checkin_overtime.add_holiday_action(frm);await Promise.resolve();
 return {calls,buttons,dialogs,messages,setDirty:x=>dirty=x,submit:x=>submit(x),reloaded:()=>reloaded};
}
(async()=>{
 const denied=await fixture(false);assert.equal(denied.buttons.length,0);
 const x=await fixture();x.setDirty(true);x.buttons[0]();assert.equal(x.messages.length,1);x.setDirty(false);x.buttons[0]();
 await x.submit({covered_hours:1,reference:'ref'});await Promise.resolve();
 assert.equal(x.dialogs.length,1);const d=x.dialogs[0].config;
 assert(d.fields[0].options.includes('&lt;script&gt;'));assert(!d.fields[0].options.includes('<script>'));
 x.setDirty(true);await d.primary_action();assert.equal(x.calls.length,2);x.setDirty(false);await d.primary_action();await Promise.resolve();
 assert.equal(x.calls[2].type,'POST');assert.equal(x.calls[2].args.token,'TOKEN');
 assert.equal(x.calls[2].args.covered_hours,1);assert.equal(x.calls[2].args.reference,'<script>bad</script>');assert(x.reloaded());
 console.log('Holiday base UI: permissions, dirty guards, escaped preview and captured POST passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
