const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');

function harness() {
    const dialogs = [], calls = [], buttons = [];
    let response, reloads = 0;
    class Dialog {
        constructor(options) {
            Object.assign(this, options);
            this.values = {};
            this.visible = false;
            this.disabled = false;
            dialogs.push(this);
        }
        show() { this.visible = true; }
        hide() { this.visible = false; }
        get_primary_btn() { return {prop: (key, value) => { this.disabled = value; }}; }
        click() {
            // Match Frappe Dialog's required-field validation before primary_action.
            if (this.fields.some(f => f.reqd && !this.values[f.fieldname])) return;
            return this.primary_action(this.values);
        }
    }
    const ctx = {__: value => value, powerpro: {checkin_overtime: {}}, frappe: {
        provide() {}, ui: {Dialog},
        utils: {escape_html: value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')},
        prompt() { throw new Error('Auto-closing prompt used'); },
        msgprint() {}, call(args) { calls.push(args); return response(args); }
    }};
    vm.runInNewContext(fs.readFileSync('powerpro/public/js/checkin_overtime.js', 'utf8'), ctx);
    const frm = {doc: {doctype: 'Retroactive Overtime Adjustment', name: 'TEST-ADJUSTMENT', docstatus: 0},
        is_new: () => false, is_dirty: () => false, reload_doc() { reloads++; },
        add_custom_button(label, callback) { buttons.push(callback); }};
    return {dialogs, calls, buttons, frm, api: ctx.powerpro.checkin_overtime,
        respond(fn) { response = fn; }, get reloads() { return reloads; }};
}
function fill(input) {
    input.values = {reason: 'Documented correction', reference: 'Reference retained', full_session: 1,
        authorized_interval_only: 1, observation_start: '2026-08-16 18:00:00', observation_end: '2026-08-17 06:00:00',
        intervals: [{start: '2026-08-16 18:00:00', end: '2026-08-16 17:00:00'},
            {start: '2026-08-17 00:00:00', end: '2026-08-17 06:00:00'}]};
}
function preview(args, token = 'TOKEN') {
    return {message: {token, reason: args.reason, before: {}, after: {verified_hours: 11}, financial_before: {},
        manual_declaration: args.manual_declaration && JSON.parse(args.manual_declaration),
        settlement_blockers: [], dependencies: [], draft_only: true}};
}

test('failed interval preview keeps the same input and all rows; corrected retry gets a fresh preview', async () => {
    const h = harness();
    h.respond(() => Promise.reject(new Error('Los intervalos deben ser positivos')));
    const input = h.api.review(h.frm, true);
    fill(input);
    const originalValues = structuredClone(input.values);
    await input.click();
    assert.equal(h.dialogs.length, 1);
    assert.equal(input.visible, true);
    assert.equal(input.disabled, false);
    assert.deepEqual(input.values, originalValues);
    assert.equal(h.reloads, 0);
    input.values.intervals[0].end = '2026-08-17 00:00:00';
    h.respond(args => Promise.resolve(preview(args.args, 'CORRECTED')));
    await input.click();
    assert.equal(h.dialogs.length, 2);
    assert.equal(input.visible, false);
    assert.equal(h.dialogs[1].visible, true);
    const sent = JSON.parse(h.calls[1].args.manual_declaration);
    assert.equal(sent.intervals.length, 2);
    assert.equal(sent.intervals[0].end, input.values.intervals[0].end);
    assert.equal(sent.reference, originalValues.reference);
    assert.equal(sent.observation_window.start, originalValues.observation_start);
    assert.equal(h.calls.filter(c => c.method.endsWith('apply_review')).length, 0);
});

test('apply error retains preview; Edit entries reopens original form and acceptance uses new token', async () => {
    const h = harness();
    h.respond(args => Promise.resolve(preview(args.args, 'OLD')));
    const input = h.api.review(h.frm, true);
    fill(input);
    await input.click();
    const first = h.dialogs[1];
    h.respond(() => Promise.reject(new Error('Preview expired')));
    await first.click();
    assert.equal(first.visible, true);
    assert.equal(first.disabled, false);
    assert.equal(h.reloads, 0);
    first.secondary_action();
    assert.equal(first.visible, false);
    assert.equal(input.visible, true);
    assert.equal(input.values.reference, 'Reference retained');
    input.values.reason = 'Corrected reference';
    h.respond(args => Promise.resolve(preview(args.args, 'NEW')));
    await input.click();
    const revised = h.dialogs[2];
    h.respond(() => Promise.resolve({message: {ok: true}}));
    await revised.click();
    assert.equal(h.calls.at(-1).args.token, 'NEW');
    assert.equal(h.calls.at(-1).args.reason, 'Corrected reference');
    assert.equal(revised.visible, false);
    assert.equal(h.reloads, 1);
});

test('in-flight clicks do not duplicate preview or apply requests; retry is enabled afterwards', async () => {
    const h = harness();
    let resolve;
    h.respond(() => new Promise(done => { resolve = done; }));
    const input = h.api.review(h.frm, true);
    fill(input);
    const pending = input.click();
    await input.click();
    assert.equal(h.calls.length, 1);
    assert.equal(input.visible, true);
    assert.equal(input.disabled, true);
    resolve(preview(h.calls[0].args));
    await pending;
    const confirmation = h.dialogs[1];
    const saving = confirmation.click();
    await confirmation.click();
    confirmation.secondary_action();
    assert.equal(confirmation.visible, true);
    assert.equal(input.visible, false);
    assert.equal(h.calls.length, 2);
    resolve({message: {ok: true}});
    await saving;
    assert.equal(h.reloads, 1);
});

test('required-field failures and resolved server exceptions do not discard input', async () => {
    const h = harness();
    h.respond(() => Promise.resolve({exc: 'ValidationError'}));
    const input = h.api.review(h.frm, true);
    await input.click();
    assert.equal(h.calls.length, 0);
    fill(input);
    await input.click();
    assert.equal(h.dialogs.length, 1);
    assert.equal(input.visible, true);
    assert.equal(input.values.intervals.length, 2);
    assert.equal(h.reloads, 0);
});

test('holiday coverage uses the same retained-form behavior and supports editing after apply failure', async () => {
    const h = harness();
    h.respond(() => Promise.resolve({message: {can_declare: true}}));
    h.api.add_holiday_action(h.frm);
    await Promise.resolve();
    h.buttons[0]();
    const input = h.dialogs[0];
    input.values = {covered_hours: 2, reference: 'Existing salary coverage'};
    h.respond(() => Promise.reject(new Error('Coverage outside reviewed hours')));
    await input.click();
    assert.equal(input.visible, true);
    assert.equal(input.values.covered_hours, 2);
    h.respond(() => Promise.resolve({message: {declaration: {holiday_hours: 6, ...input.values}, token: 'COVERAGE'}}));
    await input.click();
    const confirmation = h.dialogs[1];
    h.respond(() => Promise.resolve({exc: 'ValidationError'}));
    await confirmation.click();
    assert.equal(confirmation.visible, true);
    assert.equal(h.reloads, 0);
    confirmation.secondary_action();
    assert.equal(input.visible, true);
    assert.equal(input.values.reference, 'Existing salary coverage');
});
