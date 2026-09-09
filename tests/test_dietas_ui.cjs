/* Run with NODE_PATH pointing at test-only jsdom/jquery dependencies. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname,'../powerpro/public/js/dietas.js'),'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));

function harness(accounting=false) {
    const dom = new JSDOM('<div id="dashboard"></div>', {url:'https://example.test/app/overtime-work-call/CALL',runScripts:'outside-only'});
    const w=dom.window;const $=require('jquery')(w);w.$=$;
    let paid=false,failConfirm=false;const dialogs=[],calls=[],buttons=[],alerts=[],handlers={},messages=[],controls=[];
    const rows=[{employee:'E1',employee_name:'Employee One',amount:300,version:'v1',approval_status:'None',payment_status:'Unpaid',source_work_call:'CALL',cost_center:accounting?'Pegado':null,audit:[]},
        {employee:'E2',employee_name:'Employee Two',amount:300,version:'v2',approval_status:'Approved',payment_status:'Paid',source_work_call:'CALL',cost_center:accounting?'Pegado':null,audit:[]}];
    class Dialog {
        constructor(opts) {
            Object.assign(this,opts);this.fields_dict={};this.values={};dialogs.push(this);
            for (const f of opts.fields||[]) {
                this.fields_dict[f.fieldname]={df:f,$wrapper:$('<div>')};
                this.values[f.fieldname]=f.default||'';
            }
            // Frappe controls may invoke onchange while initial values are loaded.
            for(const f of opts.fields||[]) if(f.onchange)f.onchange();
        }
        get_value(name){return this.values[name];}
        set_value(name,value){this.values[name]=value;this.fields_dict[name].df.onchange?.();}
        show(){this.shown=true;} hide(){this.shown=false;this.onhide?.();}
        get_primary_btn(){return $('<button>');}
        disable_primary_action(){this.disabled=true;} enable_primary_action(){this.disabled=false;}
        add_custom_action(label,fn){this.custom=fn;}
    }
    w.frappe={provide:()=>{w.powerpro={dietas:{}};},utils:{escape_html:x=>$('<span>').text(x).html()},
        datetime:{get_today:()=> '2026-09-09'},user:{has_role:()=>true},ui:{Dialog,form:{on:(dt,events)=>{handlers[dt]=events;},make_control:opts=>{
            const input=$('<input>').addClass('mock-link').appendTo(opts.parent);
            const control={df:opts.df,get_value:()=>input.val(),set_value:value=>{input.val(value);opts.df.onchange?.();}};
            input.on('change',()=>opts.df.onchange?.());controls.push(control);return control;
        }}},
        msgprint:value=>messages.push(value),show_alert:value=>alerts.push(value),prompt:()=>{},
        call:async ({method,args})=>{
            calls.push({method,args:structuredClone(args)});
            if(method.endsWith('work_call_context'))return {message:{enabled:true,active:true,company:'IGC',generate_journal_entry:accounting?1:0,work_call:'CALL',dates:['2026-09-09'],currency:'DOP',methods:['Cash'],
                summary:{pending:paid?0:1,approved_unpaid:0,paid:paid?300:0,accounting_attention:0},rows:rows.map((r,i)=>({...r,payment_status:i===0&&paid?'Paid':r.payment_status}))}};
            if(method.endsWith('preview_payout'))return {message:{token:'preview-token',generate_journal_entry:accounting?1:0,rows:args.rows.map(r=>({...r,employee_name:'Employee One'})),total:args.rows.reduce((s,r)=>s+r.amount,0),currency:'DOP',payment:{payment_date:args.payment_date,mode_of_payment:args.mode_of_payment}}};
            if(method.endsWith('confirm_payout')){if(failConfirm){failConfirm=false;throw Error('network');}paid=true;return {message:{batch:'BATCH-1',status:'Confirmed',accounting_status:'Pending'}};}
            if(method.endsWith('payment_history'))return {message:[{name:'BATCH-1',status:'Confirmed',payment_date:'2026-09-09',work_date:'2026-09-09',total:300,accounting_status:'Error',rows:[{employee_name:'Employee One',amount:300,cost_center:accounting?'Pegado':null}],audit:[]}]};
            return {message:{updated:1}};
        }};
    w.format_currency=(value,currency)=>currency+' '+value;
    w.eval(source);
    // Frappe v15 exposes parent/add_section/show; it has no dashboard.wrapper.
    const dashboard={parent:$('#dashboard'),
        add_section(html,label=null,cssClass='custom') {
            return $('<div>').addClass(cssClass).html(html).appendTo(this.parent);
        },
        show(){this.parent.addClass('visible-section');},
    };
    const frm={doc:{name:'CALL',docstatus:1},dashboard,add_custom_button:(label,fn)=>buttons.push({label,fn})};
    return {w,dialogs,calls,buttons,alerts,messages,controls,handlers,frm,failNext:()=>{failConfirm=true;},close:()=>w.close()};
}

test('registered refresh renders menu and one summary with Frappe v15 dashboard API',async()=>{
    const h=harness();
    assert.equal(h.frm.dashboard.wrapper,undefined);
    await h.handlers['Overtime Work Call'].refresh(h.frm);
    assert.deepEqual(h.buttons.map(b=>b.label),['Pagar dietas','Gestionar solicitudes','Ver pagos']);
    assert.match(h.frm.dashboard.parent.text(),/Dietas.*1 pendientes/);
    assert.ok(h.frm.dashboard.parent.hasClass('visible-section'));
    await h.handlers['Overtime Work Call'].refresh(h.frm);
    assert.equal(h.frm.dashboard.parent.find('.dieta-summary').length,1);
    assert.equal(h.alerts.length,0);
    h.close();
});

test('registered refresh reports failures instead of silently hiding Dietas',async()=>{
    const h=harness();const errors=[];h.w.console.error=(...args)=>errors.push(args);
    h.w.frappe.call=async()=>{throw Error('Service unavailable');};
    await h.handlers['Overtime Work Call'].refresh(h.frm);
    assert.equal(h.alerts.length,1);assert.match(h.alerts[0].message,/No se pudo cargar Dietas/);
    assert.equal(errors.length,1);h.close();
});

test('Work Call buttons open modals without route changes',async()=>{
    const h=harness();await h.w.powerpro.dietas.refresh(h.frm);
    assert.deepEqual(h.buttons.map(b=>b.label),['Pagar dietas','Gestionar solicitudes','Ver pagos']);
    h.buttons[0].fn();await flush();
    assert.equal(h.dialogs[0].title,'Pagar dietas');assert.equal(h.dialogs[0].get_value('work_date'),'2026-09-09');
    assert.equal(h.w.location.pathname,'/app/overtime-work-call/CALL');h.close();
});

test('select workers, bulk amount, review and confirm; paid rows cannot be selected',async()=>{
    const h=harness();await h.w.powerpro.dietas.refresh(h.frm);h.buttons[0].fn();await flush();
    const d=h.dialogs[0];const wrapper=d.fields_dict.workers.$wrapper;
    assert.equal(wrapper.find('.pick:disabled').length,1);
    wrapper.find('.select-all').prop('checked',true).trigger('change');
    d.values.bulk_amount=450;d.values.reason='Extra meal';d.fields_dict.apply_amount.df.click();
    assert.match(wrapper.find('.dieta-total').text(),/1 seleccionados/);
    d.values.mode_of_payment='Cash';const pending=d.primary_action(d.values);await flush();
    const preview=h.dialogs[1];assert.equal(preview.title,'Confirmar pagos realizados');
    assert.match(preview.fields_dict.preview.$wrapper.text(),/450/);
    await preview.primary_action();await pending;await flush();
    assert.equal(d.shown,false);
    const confirmed=h.calls.find(c=>c.method.endsWith('confirm_payout'));
    assert.equal(confirmed.args.rows.length,1);assert.equal(confirmed.args.rows[0].amount,450);
    assert.ok(h.messages.some(m=>m.message?.includes('BATCH-1')));assert.equal(h.w.location.pathname,'/app/overtime-work-call/CALL');h.close();
});

test('transport retry preserves exact payment idempotency key',async()=>{
    const h=harness();await h.w.powerpro.dietas.refresh(h.frm);h.buttons[0].fn();await flush();const d=h.dialogs[0];
    d.fields_dict.workers.$wrapper.find('.pick').first().prop('checked',true).trigger('change');d.values.mode_of_payment='Cash';
    const pending=d.primary_action(d.values);await flush();const confirm=h.dialogs[1];h.failNext();
    await confirm.primary_action();assert.match(confirm.fields_dict.feedback.$wrapper.text(),/No se pudo confirmar/);assert.equal(confirm.shown,true);assert.equal(confirm.disabled,false);
    await confirm.primary_action();const calls=h.calls.filter(c=>c.method.endsWith('confirm_payout'));
    assert.equal(calls.length,2);assert.deepEqual(calls[0].args,calls[1].args);await pending;h.close();
});

test('history expands and accounting retry never routes to a Journal Entry',async()=>{
    const h=harness();await h.w.powerpro.dietas.openHistory(h.frm);const d=h.dialogs[0];
    assert.equal(d.fields_dict.history.$wrapper.find('details').length,1);
    d.fields_dict.history.$wrapper.find('.retry').trigger('click');await flush();
    assert.ok(h.calls.some(c=>c.method.endsWith('retry_accounting')));
    assert.equal(h.w.location.pathname,'/app/overtime-work-call/CALL');h.close();
});

test('employee names and audit content are escaped',async()=>{
    const h=harness();const original=h.w.frappe.call;
    h.w.frappe.call=async args=>{const r=await original(args);if(r.message.rows)r.message.rows[0].employee_name='<img src=x onerror=alert(1)>';return r;};
    await h.w.powerpro.dietas.refresh(h.frm);h.buttons[0].fn();await flush();
    assert.equal(h.dialogs[0].fields_dict.workers.$wrapper.find('img').length,0);h.close();
});

test('Dieta settings selectors exclude groups and respect each row company', () => {
    const vm = require('node:vm');
    const queries = {};
    let handlers;
    const row = {company: 'IGC'};
    const context = {
        locals: {Row: {one: row}},
        frappe: {ui: {form: {on: (doctype, events) => { handlers = events; }}}},
    };
    vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,
        '../powerpro/power_pro/doctype/igc_settings/igc_settings.js'), 'utf8'), context);
    handlers.setup({set_query: (field, table, query) => { queries[table + '.' + field] = query; }});
    const candidates = [
        {name: 'Expense group', company: 'IGC', is_group: 1, disabled: 0, root_type: 'Expense'},
        {name: 'Meals', company: 'IGC', is_group: 0, disabled: 0, root_type: 'Expense', account_type: 'Indirect Expense'},
        {name: 'Disabled', company: 'IGC', is_group: 0, disabled: 1, root_type: 'Expense'},
        {name: 'Other company', company: 'OTHER', is_group: 0, disabled: 0, root_type: 'Expense'},
        {name: 'Cash group', company: 'IGC', is_group: 1, disabled: 0, account_type: 'Cash'},
        {name: 'Cash', company: 'IGC', is_group: 0, disabled: 0, account_type: 'Cash'},
        {name: 'Bank', company: 'IGC', is_group: 0, disabled: 0, account_type: 'Bank'},
    ];
    const matches = (items, query) => {
        const filters = query({}, 'Row', 'one').filters;
        return items.filter(item => Object.entries(filters).every(([key, value]) =>
            Array.isArray(value) ? value[1].includes(item[key]) : item[key] === value)).map(item => item.name);
    };
    assert.deepEqual(matches(candidates, queries['dieta_companies.expense_account']), ['Meals']);
    assert.deepEqual(matches(candidates, queries['dieta_payment_methods.payment_account']), ['Cash', 'Bank']);
    assert.equal(queries['dieta_companies.cost_center'],undefined);
    row.company = 'OTHER';
    assert.deepEqual(matches(candidates, queries['dieta_companies.expense_account']), ['Other company']);
    row.company = '';
    assert.deepEqual(matches(candidates, queries['dieta_companies.expense_account']), []);
});


test('centers are editable, filtered, retained across renders and visible in preview/history',async()=>{
    const h=harness(true);await h.w.powerpro.dietas.refresh(h.frm);h.buttons[0].fn();await flush();
    const d=h.dialogs[0],wrapper=d.fields_dict.workers.$wrapper;
    assert.equal(wrapper.find('.mock-link').first().val(),'Pegado');
    assert.deepEqual(JSON.parse(JSON.stringify(h.controls[0].df.get_query().filters)),{company:'IGC',is_group:0,disabled:0});
    wrapper.find('.mock-link').first().val('Impresión').trigger('change');
    wrapper.find('.select-all').prop('checked',true).trigger('change');
    assert.equal(wrapper.find('.mock-link').first().val(),'Impresión');
    d.values.bulk_amount=350;d.fields_dict.apply_amount.df.click();
    assert.equal(wrapper.find('.mock-link').first().val(),'Impresión');
    d.values.mode_of_payment='Cash';const pending=d.primary_action(d.values);await flush();
    const preview=h.dialogs[1];assert.match(preview.fields_dict.preview.$wrapper.text(),/Impresión.*Distribución por centro de costo.*Impresión/s);
    assert.equal(h.calls.find(c=>c.method.endsWith('preview_payout')).args.rows[0].cost_center,'Impresión');
    preview.secondary_action();await pending;
    assert.equal(d.shown,true);assert.equal(wrapper.find('.mock-link').first().val(),'Impresión');
    await h.w.powerpro.dietas.openHistory(h.frm);assert.match(h.dialogs[2].fields_dict.history.$wrapper.text(),/Pegado/);
    d.set_value('work_date','2026-09-09');await flush();
    assert.equal(wrapper.find('.mock-link').first().val(),'Pegado');h.close();
});

test('missing selected center prevents preview; no selector when accounting is disabled',async()=>{
    const h=harness(true);await h.w.powerpro.dietas.refresh(h.frm);h.buttons[0].fn();await flush();
    const d=h.dialogs[0],wrapper=d.fields_dict.workers.$wrapper;
    wrapper.find('.pick').first().prop('checked',true).trigger('change');
    wrapper.find('.mock-link').first().val('').trigger('change');
    await d.primary_action(d.values);assert.match(h.messages.at(-1),/Employee One/);
    assert.ok(!h.calls.some(c=>c.method.endsWith('preview_payout')));h.close();
    const other=harness(false);await other.w.powerpro.dietas.refresh(other.frm);other.buttons[0].fn();await flush();
    assert.equal(other.controls.length,0);other.close();
});
