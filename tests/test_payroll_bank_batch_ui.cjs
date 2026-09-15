// Isolated form-event contracts; no browser, network or database writes.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const folder = "powerpro/power_pro/doctype/payroll_bank_batch";
const source = fs.readFileSync(path.join(root, folder, "payroll_bank_batch.js"), "utf8");

function form({ rows = [], isNew = true, docstatus = 0 } = {}) {
    let events;
    const locals = Object.fromEntries(rows.map((row) => [row.name, row]));
    const calls = [];
    const buttons = [];
    const intros = [];
    const requests = [];
    const frm = {
        doc: { details: rows, docstatus, status: "Draft" },
        is_new: () => isNew,
        refresh_field: (field) => calls.push(["refresh_field", field]),
        set_intro: (message) => intros.push(message),
        add_custom_button: (label, callback) => buttons.push({ label, callback }),
        call: async (options) => {
            requests.push(options);
            calls.push(["call", options.method]);
            return { message: { file_name: "TEST.txt" } };
        },
        reload_doc: () => calls.push(["reload_doc"]),
    };
    vm.runInNewContext(source, {
        __: (message) => message,
        frappe: {
            confirm: (message, callback) => callback(),
            show_alert: () => {},
            ui: { form: { on: (doctype, handlers) => { events = handlers; } } },
            model: {
                clear_doc: (doctype, name) => {
                    delete locals[name];
                    frm.doc.details = frm.doc.details.filter((row) => row.name !== name);
                    frm.doc.details.forEach((row, index) => { row.idx = index + 1; });
                },
            },
        },
    });
    return { frm, events, locals, calls, buttons, intros, requests };
}

function placeholder(name = "empty") {
    return {
        doctype: "Payroll Bank Batch Detail", name, amount: 0,
        currency: "DOP", identification_type: "Cédula", validation_status: "Pending",
    };
}

test("metadata allows an empty read-only table but keeps source links required", () => {
    const parent = JSON.parse(fs.readFileSync(path.join(root, folder, "payroll_bank_batch.json")));
    const details = parent.fields.find((field) => field.fieldname === "details");
    assert.equal(details.read_only, 1);
    assert.ok(!details.reqd, "Desk must not create a mandatory blank child");
    const child = JSON.parse(fs.readFileSync(path.join(root,
        "powerpro/power_pro/doctype/payroll_bank_batch_detail/payroll_bank_batch_detail.json")));
    for (const field of child.fields) {
        if (["salary_slip", "employee", "currency", "validation_status"].includes(field.fieldname)) {
            assert.equal(field.reqd, 1, field.fieldname);
        } else {
            assert.ok(!field.reqd, field.fieldname);
        }
        assert.equal(field.read_only, 1, field.fieldname);
    }
});

for (const event of ["onload", "validate"]) {
    test(`${event} removes only legacy placeholders, including their local documents`, () => {
        const empty = placeholder();
        const partial = { ...placeholder("partial"), employee_name: "KEEP THIS ROW" };
        const actual = { ...placeholder("actual"), salary_slip: "SLIP-001", employee: "EMP-001" };
        const { frm, events, locals } = form({ rows: [empty, partial, actual] });
        events[event](frm);
        assert.deepEqual(frm.doc.details.map((row) => row.name), ["partial", "actual"]);
        assert.equal(locals.empty, undefined);
        assert.equal(locals.partial, partial);
        assert.equal(actual.idx, 2);
    });
}

test("nondefault values and validation observations are not silently discarded", () => {
    const rows = [
        { ...placeholder("currency"), currency: "USD" },
        { ...placeholder("identity"), identification_type: "Pasaporte" },
        { ...placeholder("message"), validation_message: "REVIEW" },
        { ...placeholder("blocked"), validation_status: "Blocked" },
    ];
    const { frm, events } = form({ rows });
    events.validate(frm);
    assert.equal(frm.doc.details.length, 4);
});

test("submitted and cancelled snapshots are never cleaned up", () => {
    for (const docstatus of [1, 2]) {
        const { frm, events } = form({ rows: [placeholder()], docstatus, isNew: false });
        events.onload(frm);
        events.validate(frm);
        assert.equal(frm.doc.details.length, 1);
    }
});

test("new draft explains save-first; saved draft exposes explicit load action", async () => {
    const fresh = form();
    fresh.events.refresh(fresh.frm);
    assert.ok(fresh.intros.at(-1).includes("Guarde el borrador"));
    assert.equal(fresh.buttons.length, 0);
    assert.equal(fresh.calls.length, 0);

    const saved = form({ isNew: false });
    saved.events.refresh(saved.frm);
    const load = saved.buttons.find((button) => button.label === "Cargar pagos sometidos");
    assert.ok(load);
    assert.equal(saved.calls.length, 0, "refresh must not automatically load or save payroll");
    load.callback();
    await Promise.resolve();
    assert.deepEqual(saved.calls, [["call", "load_payments"], ["reload_doc"]]);
    assert.equal(saved.requests[0].doc, saved.frm.doc,
        "Frappe v15 requires doc to route the object-form call to run_doc_method");
});

test("approved persisted state routes generation to the batch document", async () => {
    const state = form({ isNew: false, docstatus: 1 });
    state.frm.doc.status = "Approved";
    state.events.refresh(state.frm);
    assert.deepEqual(state.buttons.map((button) => button.label), ["Generar TXT privado"]);
    assert.equal(state.calls.length, 0);
    state.buttons[0].callback();
    await Promise.resolve();
    assert.equal(state.requests[0].method, "generate_file");
    assert.equal(state.requests[0].doc, state.frm.doc);
    assert.deepEqual(state.calls, [["call", "generate_file"], ["reload_doc"]]);
});
