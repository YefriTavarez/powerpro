frappe.ui.form.on("Salary Slip", {
    refresh(frm) {
        const field = frm.fields_dict.monthly_settlement_view;
        if (!field) return;
        let snapshot;
        try { snapshot = JSON.parse(frm.doc.monthly_settlement_snapshot || "null"); }
        catch (_) { field.$wrapper.text(__("No se pudo leer la evidencia del acumulado.")); return; }
        if (!snapshot) { field.$wrapper.empty(); return; }
        const esc = value => frappe.utils.escape_html(String(value ?? ""));
        const amt = value => format_currency(Number(value || 0), frm.doc.currency);
        const rows = Object.keys(snapshot.totals).sort().map(code =>
            `<tr><td>${esc(code)}</td><td>${amt(snapshot.previous[code])}</td><td>${amt(snapshot.current[code])}</td><td>${amt(snapshot.totals[code])}</td></tr>`).join("");
        const deductions = Object.entries(snapshot.employee).map(([code, row]) =>
            `<tr><td>${esc(code)}</td><td>${amt(row.total)}</td><td>${amt(row.previous)}</td><td>${amt(snapshot.employee_applied[code])}</td></tr>`).join("");
        const contributions = snapshot.employer.map(row =>
            `<tr><td>${esc(row.name)}</td><td>${amt(row.total)}</td><td>${amt(row.previous)}</td><td>${amt(snapshot.close ? row.amount : 0)}</td></tr>`).join("");
        const sources = snapshot.sources.map(s =>
            `<li><a href="/app/salary-slip/${encodeURIComponent(s.name)}">${esc(s.name)}</a> (${esc(s.start_date)} — ${esc(s.end_date)})</li>`).join("");
        const table = (head, body) => `<table class="table table-bordered"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table>`;
        field.$wrapper.html(`
            <h4>${snapshot.close ? __("Cierre mensual") : __("Acumulado informativo; sin liquidación mensual")}</h4>
            <p>${esc(snapshot.period.from)} — ${esc(snapshot.period.to)}</p>
            ${snapshot.issues.length ? `<div class="alert alert-warning">${snapshot.issues.map(esc).join("<br>")}</div>` : ""}
            ${table(["Ingreso", "Anterior", "Actual", "Total del mes"], rows)}
            <p>Base cotizable: ${amt(snapshot.cotizable)} · Base ISR: ${amt(snapshot.income_tax_base)}</p>
            <h5>Deducciones del empleado</h5>${table(["Concepto", "Obligación mensual", "Retenido antes", "Aplicado ahora"], deductions)}
            <h5>Aportes del empleador</h5>${table(["Concepto", "Obligación mensual", "Registrado antes", "Aplicado ahora"], contributions)}
            <h5>Recibos anteriores utilizados</h5><ul>${sources || "<li>Ninguno</li>"}</ul>
        `);
    }
});
