const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const messages = [], calls = [];
const ctx = {
	__: (x) => x, powerpro: {overtime_calendar: {}},
	frappe: {provide() {}, utils: {escape_html(value) {
		return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
			.replaceAll('"', "&quot;").replaceAll("'", "&#39;");
	}}, msgprint(x) {messages.push(x);}, call(x) {calls.push(x); return Promise.resolve({message: {}});}},
};
vm.runInNewContext(fs.readFileSync(path.join(root, "powerpro/public/js/overtime_calendar.js"), "utf8"), ctx);
const api = ctx.powerpro.overtime_calendar;
const xss = '<img src=x onerror="alert(1)">';
const html = api.render({name:xss, evidence_source:xss, baseline:{}, difference:{},
	proposed:{segments:[{date:"2026-09-24", start:"2026-09-24T00:00:00", end:"2026-09-24T02:00:00",
		classification:xss, verified_hours:2, night_hours:2}], excluded_by_maximum_hours:1},
	warnings:[xss], assumptions:[xss], pricing_note:xss});
assert(!html.includes("<img"));
assert(html.includes("&lt;img"));
assert(html.includes("Vista previa de solo lectura"));
assert(!html.includes("<button"));
let button;
const frm = {doc:{doctype:"Overtime Authorization",name:"AUTH",docstatus:1},
	is_new:()=>false, is_dirty:()=>true, add_custom_button(label, action) {button={label,action};}};
api.add_button(frm);
assert.equal(button.label, "Comparar cálculo por fecha");
button.action();
assert.equal(calls.length, 0);
assert(messages[0].includes("Guarde los cambios"));
for (const status of [0,1]) {
	button = undefined;
	api.add_button({...frm,doc:{...frm.doc,docstatus:status}});
	assert(button);
}
button = undefined;
api.add_button({...frm,doc:{...frm.doc,docstatus:2}});
assert.equal(button, undefined);
api.add_button({...frm,is_new:()=>true});
assert.equal(button, undefined);
for (const dt of ["overtime_authorization", "overtime_work_call", "retroactive_overtime_adjustment"]) {
	const code = fs.readFileSync(path.join(root, `powerpro/power_pro/doctype/${dt}/${dt}.js`), "utf8");
	assert(code.includes('/assets/powerpro/js/overtime_calendar.js'));
}
console.log("Calendar UI: escaping, read-only actions, dirty/new/cancelled guards and three entry points passed.");
