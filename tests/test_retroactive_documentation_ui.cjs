const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const handlers={},calls=[],buttons=[],display=[],headlines=[];
const ctx={__:(s)=>s,frappe:{ui:{form:{on:(dt,h)=>Object.assign(handlers,h)}},call:q=>{calls.push(q);throw Error('Documentary form must not calculate payroll');}}};
vm.runInNewContext(fs.readFileSync('powerpro/power_pro/doctype/retroactive_overtime_adjustment/retroactive_overtime_adjustment.js','utf8'),ctx);
const frm={doc:{doctype:'Retroactive Overtime Adjustment',docstatus:0,historical_documentation:1,reconciliation_engine:'Verified Checkins'},
 toggle_display:(...a)=>display.push(a),set_df_property(){},clear_custom_buttons(){buttons.length=0;},
 dashboard:{set_headline_alert:(...a)=>headlines.push(a)},add_custom_button:(...a)=>buttons.push(a),
 is_new:()=>false,is_dirty:()=>false};
handlers.refresh(frm);
assert.equal(calls.length,0); assert.equal(buttons.length,0);
assert(headlines[0][0].includes('no verifica ponches'));
assert(display.some(a=>a[0]==='reconciliation_section' && a[1]===false));
frm.doc.docstatus=1;frm.doc.planned_settlement='Cash';
ctx.add_cash_settlement_actions(frm);ctx.add_evidence_actions(frm);handlers.refresh(frm);
assert.equal(calls.length,0);assert.equal(buttons.length,0);
frm.doc.historical_documentation=0;
assert.equal(ctx.configure_documentary_display(frm),false);
assert(display.some(a=>a[0]==='reconciliation_section' && a[1]===true));
console.log('Documentary UI: draft/submitted forms make no payroll/evidence request and offer no settlement actions.');
