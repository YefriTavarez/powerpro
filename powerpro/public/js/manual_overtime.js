// Explicit manager verification; all permissions and calculations are enforced server-side.
frappe.provide("powerpro.manual_overtime");

(() => {
    const api = "powerpro.controllers.manual_overtime.";
    const esc = value => frappe.utils.escape_html(String(value ?? ""));
    const source_args = frm => frm.doctype === "Overtime Work Call"
        ? {work_call: frm.doc.name} : {authorization: frm.doc.name};
    const call = async (method, args) => (await frappe.call({method: api + method, args})).message;

    powerpro.manual_overtime.add_button = async frm => {
        const doc = frm.doc;
        const options = await call("get_manual_verification_options", source_args(frm));
        if (frm.doc !== doc || doc.docstatus !== 1 || !options?.allowed || !options.rows?.length) return;
        frm.add_custom_button(__("Manually Verify Attendance"), () => open_dialog(frm), __("Overtime"));
    };

    async function open_dialog(frm) {
        const options = await call("get_manual_verification_options", source_args(frm));
        const rows = (options?.rows || []).filter(row => row.completed_window);
        if (!options?.allowed || !rows.length) {
            frappe.msgprint(__("No completed, unsettled authorizations are available for manual verification."));
            return;
        }
        let busy = false;
        let dialog;
        dialog = new frappe.ui.Dialog({
            title: __("Manual Attendance Verification"),
            size: "extra-large",
            fields: [
                {fieldname: "authorization", fieldtype: "Select", label: __("Employee / Work Date"), reqd: 1,
                    options: rows.map(row => ({value: row.name, label: `${row.employee_name} · ${row.work_date} · ${row.name}`})),
                    default: rows[0].name, onchange: () => show_window()},
                {fieldname: "window", fieldtype: "HTML"},
                {fieldname: "intervals", fieldtype: "Table", label: __("Actual Worked Intervals"), reqd: 1,
                    in_place_edit: true, data: [],
                    description: __("Enter actual start and end times. Add separate rows around breaks. Use the site's timezone."),
                    fields: [
                        {fieldname: "start", fieldtype: "Datetime", label: __("Actual Start"), reqd: 1, in_list_view: 1},
                        {fieldname: "end", fieldtype: "Datetime", label: __("Actual End"), reqd: 1, in_list_view: 1},
                    ]},
                {fieldname: "reason", fieldtype: "Small Text", label: __("Verification Reason"), reqd: 1,
                    description: __("Explain the evidence used and any missing or incorrect check-ins. Supporting documents may be attached to the authorization or Work Call.")},
            ],
            primary_action_label: __("Preview Verified Hours"),
            async primary_action(values) {
                if (busy) return;
                busy = true;
                dialog.get_primary_btn().prop("disabled", true);
                // Freeze input for this preview; edits require another calculation.
                const args = {authorization: values.authorization,
                    intervals: JSON.stringify((values.intervals || []).map(row => ({start: row.start, end: row.end}))),
                    reason: values.reason};
                try {
                    const result = await call("preview_manual_verification", args);
                    dialog.hide();
                    show_preview(frm, dialog, args, result);
                } finally {
                    busy = false;
                    dialog.get_primary_btn().prop("disabled", false);
                }
            },
        });
        function show_window() {
            if (!dialog) return;
            const row = rows.find(item => item.name === dialog.get_value("authorization"));
            if (!row) return;
            dialog.fields_dict.window.$wrapper.html(`<p><strong>${esc(row.employee_name)}</strong><br>
                ${esc(__("Authorized Window"))}: ${esc(row.authorization_start)} – ${esc(row.authorization_end)}<br>
                ${esc(__("Maximum Authorized Hours"))}: ${esc(row.maximum_hours)} · ${esc(__(row.reconciliation_status))}</p>
                <p class="text-muted">${esc(__("Only verified overtime within the authorized window and maximum can be settled."))}</p>`);
            // Never carry another employee's attendance across a selection change.
            dialog.fields_dict.intervals.df.data = [];
            dialog.fields_dict.intervals.grid.refresh();
            dialog.set_value("reason", "");
        }
        dialog.show();
        show_window();
    }

    function show_preview(frm, editor, args, result) {
        const s = result.snapshot;
        const facts = [
            [__("Verified Hours"), s.verified_hours],
            [__("Check-in Verified Hours"), result.checkin_comparison.verified_hours],
            [__("Difference from Check-ins"), result.hours_difference],
            [__("Reconciliation Status"), __(s.reconciliation_status)],
            [__("Regular Overtime 35% Hours"), s.regular_35_hours],
            [__("Extraordinary Overtime 100% Hours"), s.regular_100_hours],
            [__("Holiday 100% Hours"), s.holiday_100_hours],
            [__("Weekly Rest Hours"), s.weekly_rest_hours],
            [__("Night Hours"), s.night_hours],
            [__("Hours Outside Authorized Window"), s.unapproved_hours],
        ];
        const warnings = result.checkin_comparison.warnings || [];
        const worked = result.intervals.map(row => `<li>${esc(row.start)} – ${esc(row.end)}</li>`).join("");
        let saving = false;
        const preview = new frappe.ui.Dialog({
            title: __("Approve Verified Attendance"), size: "large",
            fields: [{fieldname: "summary", fieldtype: "HTML"}],
            primary_action_label: __("Approve Attendance"),
            async primary_action() {
                if (saving) return;
                saving = true;
                preview.get_primary_btn().prop("disabled", true);
                try {
                    await call("approve_manual_verification", {...args, preview_token: result.preview_token});
                    preview.hide();
                    await frm.reload_doc();
                    frappe.show_alert({message: __("Attendance verified. Use Settlement to preview the next step."), indicator: "green"});
                } catch (error) {
                    // A failed or stale approval must go through a fresh preview.
                    preview.hide();
                    editor.show();
                }
            },
            secondary_action_label: __("Back to Attendance"),
            secondary_action() { preview.hide(); editor.show(); },
        });
        preview.fields_dict.summary.$wrapper.html(`<p><strong>${esc(result.employee_name)}</strong> · ${esc(result.authorization)}</p>
            <ul>${worked}</ul><p>${esc(result.reason)}</p>
            <table class="table table-bordered"><tbody>${facts.map(([label, value]) => `<tr><td>${esc(label)}</td><td>${esc(value)}</td></tr>`).join("")}</tbody></table>
            ${warnings.length ? `<p>${esc(__("Check-in Warnings"))}</p><ul>${warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul>` : ""}
            <p class="text-muted">${esc(__("Approval records verified attendance only. Payment or compensatory leave requires the separate settlement confirmation."))}</p>`);
        preview.show();
    }
})();
