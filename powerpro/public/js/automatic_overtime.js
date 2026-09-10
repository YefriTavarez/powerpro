frappe.provide("powerpro.automatic_overtime");
(() => {
    const api = "powerpro.controllers.automatic_overtime.";
    const esc = (v) => frappe.utils.escape_html(String(v ?? ""));
    const rpc = async (method, args) => (await frappe.call({ method: api + method, args })).message;
    powerpro.automatic_overtime.add_button = (frm) => {
        frm.add_custom_button(__("Attendance and Automatic Settlement"), () => open(frm), __("Overtime"));
    };
    async function open(frm) {
        const state = await rpc("get_work_call_status", { work_call: frm.doc.name });
        const d = new frappe.ui.Dialog({ title: __("Attendance and Automatic Settlement"), size: "extra-large", fields: [
            {fieldname:"notice", fieldtype:"HTML"},
            {fieldname:"records", fieldtype:"HTML"},
            {fieldname:"authorization", label:__("Employee / Date"), fieldtype:"Select", onchange: () => { d.set_value("reason", ""); d.fields_dict.intervals.df.data = []; d.fields_dict.intervals.grid.refresh(); }, options: state.rows.filter(r => r.can_correct).map(r => ({value:r.name,label:`${r.employee_name} · ${r.work_date} · ${r.name}`}))},
            {fieldname:"action", label:__("Action"), fieldtype:"Select", options:["Mark Absent","Correct Worked Hours","Cancel Participation"], reqd:1},
            {fieldname:"reason", label:__("Reason"), fieldtype:"Small Text", reqd:1},
            {fieldname:"intervals", label:__("Worked Intervals (excluding breaks)"), fieldtype:"Table", depends_on:"eval:doc.action === 'Correct Worked Hours'", in_place_edit:true, fields:[
                {fieldname:"start", label:__("Start"), fieldtype:"Datetime", in_list_view:1, reqd:1},
                {fieldname:"end", label:__("End"), fieldtype:"Datetime", in_list_view:1, reqd:1}
            ]}
        ], primary_action_label:__("Review Exception"), primary_action: async () => {
            const v = d.get_values(); if (!v || !v.authorization) return;
            const args = {authorization:v.authorization, action:v.action, reason:v.reason, intervals:(v.intervals || []).map(r => ({start:r.start,end:r.end}))};
            const preview = await rpc("preview_attendance_exception", args);
            frappe.confirm(`${esc(__("Apply this attendance exception to the selected employee/date?"))}<br><b>${esc(v.action)}</b><br>${esc(v.authorization)}<br>${esc(v.reason)}<br>${esc(__("Existing settlement outputs will be reversed or replaced if safe. Submitted payroll or used leave will remain unchanged and require correction."))}`, async () => {
                const result = await rpc("record_attendance_exception", {...args, token:preview.token});
                show_result(result); d.hide(); await frm.reload_doc();
            });
        }});
        d.fields_dict.notice.$wrapper.html(`<p>${esc(__(state.enrolled ? "Attendance is presumed unless an authorized person records an exception. Each employee/date settles after its window ends." : "This Work Call is not enrolled. Enabling the setting does not process existing Work Calls."))}</p>`);
        d.fields_dict.records.$wrapper.html(`<div style="overflow:auto"><table class="table table-bordered"><thead><tr>${["Employee / Date","Attendance","Verified Hours","Presumed Hours","Processing","Settlement","Details"].map(x=>`<th>${esc(__(x))}</th>`).join("")}</tr></thead><tbody>${state.rows.map(r=>`<tr><td>${esc(r.employee_name)}<br>${esc(r.work_date)}</td><td>${esc(__(r.attendance_state || "Pending"))}</td><td>${esc(r.verified_hours)}</td><td>${esc(r.presumed_hours)}</td><td>${esc(__(r.auto_status || "Not enrolled"))}</td><td>${esc(__(r.settlement_status))}</td><td>${esc(r.auto_error)}${r.attendance_exception ? `<br><a href="#" data-overtime-audit="${esc(r.name)}">${esc(__("View Exception"))}</a>` : ""}</td></tr>`).join("")}</tbody></table></div>`);
        d.fields_dict.records.$wrapper.on("click", "[data-overtime-audit]", async (event) => {
            event.preventDefault();
            const item = await rpc("get_attendance_exception", {authorization:event.currentTarget.dataset.overtimeAudit});
            if (!item) return;
            const b = item.blockers ? JSON.parse(item.blockers) : null;
            frappe.msgprint({title:__(item.status),message:`<p><b>${esc(__(item.action))}</b><br>${esc(item.reason)}</p><p>${esc(item.recorded_by)} · ${esc(item.recorded_on)}</p>${b ? `<p>${esc(b.reason)}</p>` + (b.documents || []).map(r=>`<a href="/app/${frappe.router.slug(r.doctype)}/${encodeURIComponent(r.name)}">${esc(r.doctype)}: ${esc(r.name)}</a>`).join("<br>") : ""}<details><summary>${esc(__("Original Evidence"))}</summary><pre>${esc(item.before_snapshot)}</pre></details><details><summary>${esc(__("Resulting Evidence"))}</summary><pre>${esc(item.after_snapshot)}</pre></details>`});
        });
        if (!state.enrolled || !state.rows.some(r=>r.can_correct)) d.get_primary_btn().hide();
        if (!state.enrolled && state.enabled && state.can_enroll) {
            d.set_secondary_action_label(__("Enroll This Work Call"));
            d.set_secondary_action(() => frappe.confirm(__("Enroll this Work Call only? Already-ended windows will be processed on the next scheduler run using presumed attendance and the configured cash payroll date policy."), async () => {
                await rpc("enroll_work_call", {work_call:frm.doc.name, modified:frm.doc.modified});
                d.hide(); await frm.reload_doc(); open(frm);
            }));
        } else if (state.rows.some(r=>r.can_correct && r.auto_status === "Correction Pending")) {
            d.set_secondary_action_label(__("Retry Selected Pending Correction"));
            d.set_secondary_action(async () => {
                const authorization = d.get_value("authorization");
                const r = state.rows.find(r=>r.name===authorization);
                if (!r || r.auto_status !== "Correction Pending") return frappe.msgprint(__("Select a record with a pending correction."));
                const result = await rpc("retry_attendance_exception", {authorization});
                show_result(result); d.hide(); await frm.reload_doc();
            });
        }
        d.show();
    }
    function show_result(result) {
        let detail = "";
        if (result.blockers) {
            const b = JSON.parse(result.blockers);
            detail = `<p>${esc(b.reason)}</p>` + (b.documents || []).map(r=>`<a href="/app/${frappe.router.slug(r.doctype)}/${encodeURIComponent(r.name)}">${esc(r.doctype)}: ${esc(r.name)}</a>`).join("<br>");
        }
        frappe.msgprint({title:__(result.status),message:`${esc(__("Attendance exception recorded."))}${detail}`,indicator:result.status==="Applied"?"green":"orange"});
    }
})();
