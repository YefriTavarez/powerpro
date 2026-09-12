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

const weeklyHtml = api.render({name:"AUTH", evidence_source:"snapshot", baseline:{}, difference:{},
 proposed:{segments:[]}, warnings:[], assumptions:[], weekly_evidence:{notes:[xss], weeks:[
 {week_start:"2026-09-21", paired_hours:16, hours_before_cutoff:8, configured_threshold:68,
 provisional_hours_to_threshold:60, legacy_regular_overtime_before:3, offshift_punches:1,
 days:[{date:"2026-09-21",paired_hours:8,punch_count:2,status:"paired_evidence"}],
 issues:[{code:"consecutive_in",checkins:[xss]}]}, {week_start:"2026-09-28",truncated:true}]}});
assert(weeklyHtml.includes("Evidencia semanal provisional"));
assert(weeklyHtml.includes("Demasiadas marcaciones"));
assert(weeklyHtml.includes("Entradas consecutivas"));
assert(weeklyHtml.includes("cobertura no certificada"));
assert(!weeklyHtml.includes("<img"));
assert(!weeklyHtml.includes("<button"));
console.log("Weekly UI: evidence, coverage, truncation and issue escaping passed.");
const shiftedHtml = api.render({name:"AUTH", evidence_source:"snapshot", baseline:{}, difference:{},proposed:{segments:[]},
 warnings:[],assumptions:[],weekly_evidence:{notes:[],weeks:[{week_start:"2026-09-21",days:[],issues:[],
 shift_comparison:{configured:{paired_hours:10,hours_before_cutoff:8},with_corrections:{paired_hours:9,hours_before_cutoff:8},
 sessions:[{shift:xss,shift_start:"2026-09-21",hours:10,direction_rule:xss,hours_rule:xss}],
 applied_corrections:[{name:xss,kind:"Manual Verification",start:"2026-09-21",end:"2026-09-22"}],
 issues:[{code:"overlapping_corrections",source:xss}],notes:[xss]}}]}});
assert(shiftedHtml.includes("Turno con correcciones aplicadas"));
assert(shiftedHtml.includes("Correcciones superpuestas"));
assert(shiftedHtml.includes("<details>"));
assert(!shiftedHtml.includes("<img"));
console.log("Shift/correction UI: separate totals, review issues and escaping passed.");
