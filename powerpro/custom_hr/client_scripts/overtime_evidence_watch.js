frappe.ui.form.on('Overtime Evidence Watch', {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__('Abrir documento de origen'), () => frappe.set_route('Form', frm.doc.source_type, frm.doc.source_name));
        frm.add_custom_button(__('Comprobar nuevamente'), () => frappe.call({
            method: 'powerpro.controllers.overtime_evidence_monitor.recheck', type: 'POST',
            args: {name: frm.doc.name}, freeze: true
        }).then(() => frm.reload_doc()));
    }
});
