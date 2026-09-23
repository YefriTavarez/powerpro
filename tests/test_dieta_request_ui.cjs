const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../powerpro/custom_hr/client_scripts/solicitud_de_dieta.js'), 'utf8');

function harness(overrides = {}) {
    const state = { calls: [], dialogs: [], buttons: {}, readonly: {}, reloads: 0 };
    let context = { request: 'REQ', modified: 'v1', amount: 300, notes: 'Original', currency: 'DOP',
        can_edit: true, expense_approver: 'approver@example.com', work_call: null,
        approval_status: 'Pending', payment_status: 'Unpaid', ...overrides };
    const frappe = {
        utils: { escape_html: value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;') },
        ui: { form: { on: (_, handlers) => { state.handlers = handlers; } }, Dialog: class {
            constructor(options) { Object.assign(this, options); state.dialogs.push(this); }
            get_primary_btn() { return { prop: (_, value) => { this.disabled = value; } }; }
            show() { this.visible = true; }
            hide() { this.visible = false; }
        } },
        async call(payload) {
            state.calls.push(payload);
            if (payload.method.endsWith('get_context')) return { message: { ...context } };
            if (state.fail) throw Error('stale or forbidden');
            if (state.pending) await state.pending;
            return { message: { request: 'REQ', modified: 'v2' } };
        },
        msgprint: value => { state.message = value; },
        set_route: (...args) => { state.route = args; },
    };
    const frm = {
        doc: { name: 'REQ', amount: 123, notes: 'Stale form text' },
        is_new: () => !!state.is_new,
        set_df_property: (field, _, value) => { state.readonly[field] = value; },
        enable_save: () => { state.save = true; }, disable_save: () => { state.save = false; },
        add_custom_button: (label, callback) => { state.buttons[label] = callback; },
        remove_custom_button: label => { delete state.buttons[label]; },
        set_intro: (text, color) => { state.intro = text; state.color = color; },
        reload_doc: async () => { state.reloads++; },
    };
    vm.runInNewContext(source, { frappe, __: value => value });
    return { state, frm, frappe, context, refresh: () => state.handlers.refresh(frm) };
}

test('new requests keep native creation; saved requests disable generic Save', async () => {
    const h = harness();
    h.state.is_new = true;
    await h.refresh();
    assert.equal(h.state.save, true);
    assert.equal(h.state.readonly.notes, 0);
    assert.equal(h.state.calls.length, 0);
    h.state.is_new = false;
    await h.refresh();
    assert.equal(h.state.save, false);
    for (const v of Object.values(h.state.readonly)) assert.equal(v, 1);
    assert.ok(h.state.buttons['Editar solicitud']);
    assert.match(h.state.intro, /sin convocatoria todavía no están disponibles/);
});

test('dialog reloads current server values and sends only amount, notes and version', async () => {
    const h = harness();
    await h.refresh();
    h.context.modified = 'v2'; h.context.notes = 'Fresh';
    await h.state.buttons['Editar solicitud']();
    const d = h.state.dialogs[0];
    assert.equal(d.fields.find(f => f.fieldname === 'notes').default, 'Fresh');
    await d.primary_action({ amount: 350, notes: 'Motivo', approval_status: 'Approved', employee: 'E2' });
    const args = JSON.parse(JSON.stringify(h.state.calls.at(-1).args));
    assert.deepEqual(args, { request: 'REQ', modified: 'v2', amount: 350, notes: 'Motivo' });
    assert.equal(d.visible, false);
    assert.equal(h.state.reloads, 1);
});

test('failure keeps dialog values available and permits retry without silently reloading', async () => {
    const h = harness();
    await h.refresh(); await h.state.buttons['Editar solicitud']();
    const d = h.state.dialogs[0]; h.state.fail = true;
    await assert.rejects(d.primary_action({ amount: 350, notes: 'Motivo' }));
    assert.equal(d.visible, true); assert.equal(d.disabled, false); assert.equal(h.state.reloads, 0);
});

test('double clicks send one update while the first request is pending', async () => {
    const h = harness();
    await h.refresh(); await h.state.buttons['Editar solicitud']();
    let finish; h.state.pending = new Promise(resolve => { finish = resolve; });
    const d = h.state.dialogs[0];
    const first = d.primary_action({ amount: 350, notes: 'Motivo' });
    await d.primary_action({ amount: 350, notes: 'Motivo' });
    assert.equal(h.state.calls.filter(c => c.method.endsWith('update_request')).length, 1);
    assert.equal(d.disabled, true); finish(); await first;
});

test('lost permission or changed status removes edit and is rechecked on dialog open', async () => {
    const h = harness();
    await h.refresh();
    h.context.can_edit = false;
    await h.state.buttons['Editar solicitud']();
    assert.equal(h.state.dialogs.length, 0); assert.match(h.state.message, /ya no/);
    await h.refresh(); assert.equal(h.state.buttons['Editar solicitud'], undefined);
});

test('linked request routes to Work Call and escapes the approver in its guidance', async () => {
    const h = harness({ work_call: 'CALL', expense_approver: '<img src=x>' });
    await h.refresh();
    assert.match(h.state.intro, /&lt;img/); assert.doesNotMatch(h.state.intro, /<img/);
    h.state.buttons['Abrir convocatoria']();
    assert.deepEqual(h.state.route, ['Form', 'Overtime Work Call', 'CALL']);
});

test('slow response from an older refresh cannot reintroduce stale edit permissions', async () => {
    const h = harness(); let resolve;
    const normalCall = h.frappe.call;
    h.frappe.call = () => new Promise(r => { resolve = r; });
    const first = h.refresh();
    h.frappe.call = normalCall; h.context.can_edit = false;
    await h.refresh();
    resolve({ message: { ...h.context, can_edit: true } }); await first;
    assert.equal(h.state.buttons['Editar solicitud'], undefined);
});

test('navigation during save does not reload the unrelated document', async () => {
    const h = harness();
    await h.refresh(); await h.state.buttons['Editar solicitud']();
    let finish; h.state.pending = new Promise(r => { finish = r; });
    const save = h.state.dialogs[0].primary_action({ amount: 300, notes: 'Updated' });
    h.frm.doc.name = 'OTHER'; finish(); await save;
    assert.equal(h.state.reloads, 0);
});
