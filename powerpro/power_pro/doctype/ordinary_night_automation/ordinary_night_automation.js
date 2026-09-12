frappe.ui.form.on('Ordinary Night Automation', {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) return;
        frm.add_custom_button(__('Comprobar fechas inscritas'), () => {
            if (frm.is_dirty()) return frappe.msgprint(__('Guarde la programación antes de procesar.'));
            frappe.call({method: 'powerpro.controllers.ordinary_night_automation.process_now',type:'POST',
                args:{schedule:frm.doc.name},freeze:true}).then(() => frm.reload_doc());
        });
        const names = [...new Set((frm.doc.days || []).map(row => row.settlement).filter(Boolean))];
        names.forEach(name => frm.add_custom_button(name, () => frappe.set_route('Form','Ordinary Night Settlement',name),__('Liquidaciones')));
        frm.dashboard.set_headline_alert(__('Pausar o cancelar esta programación detiene nuevos procesamientos; las liquidaciones existentes conservan su propio flujo de revisión y cancelación.'),'blue');
    }
});
