/* Site-free UI interaction tests; run with node --test. No browser/site mutations. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../powerpro/public/js/manual_overtime.js'), 'utf8');
function harness({allowed=true, future=false}={}) {
    const dialogs=[], buttons=[], requests=[], messages=[], alerts=[];
    let failSave=false, pendingSave=null;
    const rows=[{name:'AUTH-1',employee_name:'Employee <One>',work_date:'2026-09-13',authorization_start:'2026-09-13 07:00',authorization_end:'2026-09-13 12:00',maximum_hours:5,reconciliation_status:'Scheduled',completed_window:!future},
        {name:'AUTH-2',employee_name:'Employee Two',work_date:'2026-09-13',authorization_start:'2026-09-13 07:00',authorization_end:'2026-09-13 12:00',maximum_hours:5,reconciliation_status:'Scheduled',completed_window:true}];
    if(future) rows.pop();
    const result={employee_name:'Employee <One>',authorization:'AUTH-1',intervals:[{start:'2026-09-13 07:00',end:'2026-09-13 12:00'}],reason:'Supervisor <verified>',snapshot:{verified_hours:5,reconciliation_status:'Completed',weekly_rest_hours:5},checkin_comparison:{verified_hours:0,warnings:['Missing <punch>']},hours_difference:5,preview_token:'TOKEN'};
    class Dialog {
        constructor(options) {
            Object.assign(this,options);this.fields_dict={};this.values={};this.visible=false;this.disabled=false;
            for(const field of options.fields) {
                const holder={df:{...field},$wrapper:{html(value){holder.html=value;}}};
                holder.grid={refresh:()=>{this.values[field.fieldname]=holder.df.data;}};
                this.fields_dict[field.fieldname]=holder;
                this.values[field.fieldname]=field.default ?? field.data;
            }
            // Frappe can initialize fields while the caller's dialog variable is unset.
            for(const field of options.fields) if(field.onchange) field.onchange();
            dialogs.push(this);
        }
        get_value(key){return this.values[key];}
        set_value(key,value){this.values[key]=value;const field=this.fields_dict[key].df;if(field.onchange)field.onchange();}
        get_primary_btn(){return {prop:(key,value)=>{this.disabled=value;}};}
        show(){this.visible=true;}
        hide(){this.visible=false;}
    }
    const context={console, __:s=>s, powerpro:{}, frappe:{
        provide:()=>{}, ui:{Dialog},utils:{escape_html:value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')},
        async call({method,args}){
            requests.push({method,args});
            if(method.endsWith('get_manual_verification_options'))return {message:{allowed,rows}};
            if(method.endsWith('preview_manual_verification'))return {message:result};
            if(method.endsWith('approve_manual_verification')){
                if(pendingSave)await pendingSave;
                if(failSave)throw Error('Stale preview');
                return {message:{verified_hours:5}};
            }
            throw Error(method);
        }, msgprint:s=>messages.push(s),show_alert:s=>alerts.push(s),
    }};
    context.powerpro.manual_overtime={};vm.runInNewContext(source,context);
    const frm={doctype:'Overtime Work Call',doc:{name:'CALL',docstatus:1},add_custom_button:(label,action,group)=>buttons.push({label,action,group}),reloads:0,async reload_doc(){this.reloads++;}};
    return {context,frm,dialogs,buttons,requests,messages,alerts,
        set failSave(value){failSave=value;},set pendingSave(value){pendingSave=value;},
        async open(){await context.powerpro.manual_overtime.add_button(frm);await buttons[0].action();return dialogs[0];}};
}
const values=()=>({authorization:'AUTH-1',intervals:[{start:'2026-09-13 07:00',end:'2026-09-13 12:00'}],reason:'Supervisor confirmed'});

test('button uses server permission response, not hardcoded roles',async()=>{
    const h=harness({allowed:false});await h.context.powerpro.manual_overtime.add_button(h.frm);assert.equal(h.buttons.length,0);
});
test('future-only records display an explanation without opening approval',async()=>{
    const h=harness({future:true});await h.open();assert.equal(h.dialogs.length,0);assert.match(h.messages[0],/No completed/);
});
test('employee selection clears attendance from previous employee',async()=>{
    const h=harness();const d=await h.open();d.values.intervals=values().intervals;d.values.reason='previous';d.set_value('authorization','AUTH-2');
    assert.equal(d.values.intervals.length,0);assert.equal(d.values.reason,'');assert.match(d.fields_dict.window.html,/Employee Two/);
});
test('preview is separate from approval and sends only explicit intervals',async()=>{
    const h=harness();const d=await h.open();await d.primary_action(values());
    assert.equal(h.dialogs.length,2);assert.equal(h.requests.filter(r=>r.method.endsWith('approve_manual_verification')).length,0);
    assert.equal(h.dialogs[1].visible,true);assert.equal(d.visible,false);
    const request=h.requests.find(r=>r.method.endsWith('preview_manual_verification'));
    assert.equal(JSON.parse(request.args.intervals)[0].start,'2026-09-13 07:00');
});
test('preview escapes names, reasons and warnings',async()=>{
    const h=harness();const d=await h.open();await d.primary_action(values());const html=h.dialogs[1].fields_dict.summary.html;
    assert.ok(!html.includes('Employee <One>'));assert.match(html,/Employee &lt;One&gt;/);assert.match(html,/Missing &lt;punch&gt;/);
});
test('back action returns to editing without writing',async()=>{
    const h=harness();const d=await h.open();await d.primary_action(values());h.dialogs[1].secondary_action();assert.equal(d.visible,true);
    assert.equal(h.requests.filter(r=>r.method.endsWith('approve_manual_verification')).length,0);
});
test('approval sends frozen input and token, then reloads source',async()=>{
    const h=harness();const d=await h.open();const input=values();await d.primary_action(input);input.reason='changed after preview';await h.dialogs[1].primary_action();
    const request=h.requests.find(r=>r.method.endsWith('approve_manual_verification'));
    assert.equal(request.args.reason,'Supervisor confirmed');assert.equal(request.args.preview_token,'TOKEN');assert.equal(h.frm.reloads,1);
});
test('stale approval returns to editor and requires a new preview',async()=>{
    const h=harness();const d=await h.open();await d.primary_action(values());h.failSave=true;await h.dialogs[1].primary_action();
    assert.equal(d.visible,true);assert.equal(h.frm.reloads,0);assert.equal(h.alerts.length,0);
});
test('double click cannot send duplicate approval requests',async()=>{
    const h=harness();const d=await h.open();await d.primary_action(values());let release;h.pendingSave=new Promise(resolve=>{release=resolve;});
    const first=h.dialogs[1].primary_action();await h.dialogs[1].primary_action();release();await first;
    assert.equal(h.requests.filter(r=>r.method.endsWith('approve_manual_verification')).length,1);
});
