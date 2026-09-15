// Isolated Desk form contracts. No browser, network, database, or invoice writes.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const folder = path.join(root, "powerpro/power_pro/doctype");
const read = (slug, suffix) => fs.readFileSync(path.join(folder, slug, `${slug}.${suffix}`), "utf8");

function form({ kind = "batch", docstatus = 0, isNew = false, dirty = false,
    roles = ["Accounts User"], rows = [], saveError = null } = {}) {
    const events = {};
    const buttons = [];
    const calls = [];
    const requests = [];
    const confirmations = [];
    const properties = {};
    const queries = {};
    const grid = {};
    const frm = {
        doc: {
            docstatus, company: "Test Company", currency: "DOP", frequency: "Monthly",
            supplier: "Test Supplier", details: rows,
            total_amount: rows.reduce((sum, row) => sum + Number(row.gross_amount || 0), 0),
        },
        is_new: () => isNew,
        is_dirty: () => dirty,
        get_field: (field) => { assert.equal(field, "details"); return { grid }; },
        set_intro: (message) => calls.push(["intro", message]),
        add_custom_button: (label, callback, group) => buttons.push({ label, callback, group }),
        set_df_property: (field, prop, value) => { properties[`${field}.${prop}`] = value; },
        set_query: (...args) => { queries[args.slice(0, -1).join(".")] = args.at(-1); },
        clear_table: (field) => { calls.push(["clear_table", field]); frm.doc[field] = []; },
        refresh_field: (field) => calls.push(["refresh_field", field]),
        set_value: (field, value) => { frm.doc[field] = value; return Promise.resolve(); },
        save: async () => {
            calls.push(["save"]);
            if (saveError) throw saveError;
        },
        call: async (options) => {
            calls.push(["call", options.method]);
            requests.push(options);
            return { message: {} };
        },
        reload_doc: async () => calls.push(["reload_doc"]),
    };
    vm.runInNewContext(read(`supplier_retainer_${kind}`, "js"), {
        __: (message) => message,
        flt: (value) => Number(value || 0),
        frappe: {
            user_roles: roles,
            ui: { form: { on: (doctype, handlers) => { events[doctype] = handlers; } } },
            confirm: (message, callback) => confirmations.push({ message, callback }),
            set_route: (...args) => calls.push(["route", ...args]),
            new_doc: (doctype, defaults) => calls.push(["new_doc", doctype, defaults]),
        },
    });
    const handlers = events[kind === "batch" ? "Supplier Retainer Batch" : "Supplier Retainer Agreement"];
    return { frm, handlers, events, buttons, calls, requests, confirmations, properties, queries, grid };
}

const actionCalls = (state) => state.calls.filter(([name]) => ["save", "call", "reload_doc"].includes(name));
const loadButton = (state) => state.buttons.find((button) => button.label === "Cargar acuerdos");

test("load saves new or changed drafts, routes to document method, then reloads", async () => {
    for (const options of [{ isNew: true }, { dirty: true }, {}]) {
        const state = form(options);
        state.handlers.refresh(state.frm);
        assert.deepEqual(actionCalls(state), [], "refresh must not save or load implicitly");
        await loadButton(state).callback();
        const expected = options.isNew || options.dirty ? [["save"]] : [];
        expected.push(["call", "load_agreements"], ["reload_doc"]);
        assert.deepEqual(actionCalls(state), expected);
        assert.equal(state.requests[0].doc, state.frm.doc,
            "Frappe v15 object-form calls need doc to invoke the controller method");
        assert.equal(state.requests[0].freeze, true);
    }
});

test("a failed draft save prevents loading and discarding current form state", async () => {
    const state = form({ dirty: true, saveError: new Error("Draft validation failed") });
    state.handlers.refresh(state.frm);
    await assert.rejects(loadButton(state).callback(), /Draft validation failed/);
    assert.deepEqual(actionCalls(state), [["save"]]);
    assert.equal(state.requests.length, 0);
});

test("reloading a selection requires confirmation before any write", async () => {
    const state = form({ rows: [{ agreement: "Agreement A", gross_amount: 100 }] });
    state.handlers.refresh(state.frm);
    loadButton(state).callback();
    assert.equal(state.confirmations.length, 1);
    assert.deepEqual(actionCalls(state), []);
    assert.equal(state.frm.doc.details.length, 1, "dismissed confirmation preserves selection");
    await state.confirmations[0].callback();
    assert.deepEqual(actionCalls(state), [["call", "load_agreements"], ["reload_doc"]]);
});

test("each source filter clears draft selection but preserves submitted and cancelled rows", () => {
    for (const event of ["company", "currency", "frequency", "period_date", "supplier"]) {
        const state = form({ rows: [{ agreement: "Agreement A", gross_amount: 100 }] });
        state.handlers[event](state.frm);
        assert.deepEqual(state.frm.doc.details, []);
        assert.equal(state.frm.doc.total_amount, 0);
        assert.ok(state.calls.some(([name, field]) => name === "refresh_field" && field === "details"));
        assert.deepEqual(actionCalls(state), [], "filter changes must not save implicitly");
        for (const docstatus of [1, 2]) {
            const saved = form({ docstatus, rows: [{ agreement: "Agreement A", gross_amount: 100 }] });
            saved.handlers[event](saved.frm);
            assert.equal(saved.frm.doc.details.length, 1);
            assert.equal(saved.frm.doc.total_amount, 100);
            assert.deepEqual(saved.calls, []);
        }
    }
});

test("loaded draft grid permits removal but never manual addition; completed grids are locked", () => {
    for (const docstatus of [0, 1, 2]) {
        const state = form({ docstatus });
        state.handlers.refresh(state.frm);
        assert.equal(state.grid.cannot_add_rows, true);
        assert.equal(state.grid.cannot_delete_rows, docstatus !== 0);
        assert.equal(Boolean(loadButton(state)), docstatus === 0);
    }
    const state = form({ rows: [{ gross_amount: 100 }, { gross_amount: "25.50" }] });
    state.events["Supplier Retainer Batch Detail"].details_remove(state.frm);
    assert.equal(state.frm.doc.total_amount, 125.5);
});

test("agreement template stays editable in drafts and only managers can edit it after submit", () => {
    for (const roles of [["Accounts User"], ["Accounts Manager"], ["System Manager"]]) {
        for (const docstatus of [0, 1]) {
            const state = form({ kind: "agreement", roles, docstatus });
            state.handlers.refresh(state.frm);
            assert.equal(state.properties["taxes_and_charges.read_only"],
                docstatus === 1 && roles[0] === "Accounts User");
        }
    }
});

test("navigation opens agreement lists and carries agreement filters to a new batch", () => {
    const batch = form();
    batch.handlers.refresh(batch.frm);
    batch.buttons.find((button) => button.label === "Ver acuerdos").callback();
    assert.ok(batch.calls.some(([name, view, doctype]) => name === "route"
        && view === "List" && doctype === "Supplier Retainer Agreement"));
    const agreement = form({ kind: "agreement", docstatus: 1 });
    agreement.handlers.refresh(agreement.frm);
    agreement.buttons.find((button) => button.label === "Preparar liquidación").callback();
    const creation = agreement.calls.find(([name]) => name === "new_doc");
    assert.equal(creation[1], "Supplier Retainer Batch");
    for (const field of ["supplier", "company", "currency", "frequency"]) {
        assert.equal(creation[2][field], agreement.frm.doc[field]);
    }
    assert.deepEqual(actionCalls(agreement), [], "navigation must not create invoices");
});

test("metadata preserves removable rows, source snapshots and explicitly editable replacement", () => {
    const batch = JSON.parse(read("supplier_retainer_batch", "json"));
    assert.ok(!batch.fields.find((field) => field.fieldname === "details").read_only);
    const child = JSON.parse(read("supplier_retainer_batch_detail", "json"));
    assert.equal(child.fields.find((field) => field.fieldname === "replaces_invoice").fieldtype, "Data",
        "Frappe rejects cancelled targets in Link fields; the server validates this explicit reference");
    for (const field of child.fields.filter((field) => field.fieldtype !== "Section Break")) {
        assert.equal(Boolean(field.read_only), field.fieldname !== "replaces_invoice", field.fieldname);
    }
    const agreement = JSON.parse(read("supplier_retainer_agreement", "json"));
    const template = agreement.fields.find((field) => field.fieldname === "taxes_and_charges");
    assert.equal(template.options, "Purchase Taxes and Charges Template");
    assert.equal(template.allow_on_submit, 1);
    assert.equal(template.permlevel, 1);
    assert.equal(agreement.track_changes, 1);
});

test("Igualas workspace exposes the workflow to accounting roles with valid shortcut blocks", () => {
    const workspace = JSON.parse(fs.readFileSync(path.join(root,
        "powerpro/power_pro/workspace/igualas/igualas.json"), "utf8"));
    assert.equal(workspace.doctype, "Workspace");
    assert.equal(workspace.name, "Igualas");
    assert.equal(workspace.module, "Power Pro");
    assert.equal(workspace.public, 1);
    assert.equal(workspace.is_hidden, 0);
    assert.deepEqual(workspace.roles.map((entry) => entry.role).sort(),
        ["Accounts Manager", "Accounts User", "System Manager"]);
    assert.deepEqual(workspace.shortcuts.map((shortcut) => shortcut.link_to),
        ["Supplier Retainer Agreement", "Supplier Retainer Batch", "Power-Pro Settings"]);
    for (const shortcut of workspace.shortcuts) {
        assert.equal(shortcut.type, "DocType");
        assert.ok(!shortcut.url, "shortcuts must respect document permissions and site routing");
    }
    const blocks = JSON.parse(workspace.content);
    assert.equal(new Set(blocks.map((block) => block.id)).size, blocks.length);
    assert.deepEqual(blocks.filter((block) => block.type === "shortcut")
        .map((block) => block.data.shortcut_name), workspace.shortcuts.map((shortcut) => shortcut.label));
});
