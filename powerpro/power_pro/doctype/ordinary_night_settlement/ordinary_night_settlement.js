frappe.ui.form.on('Ordinary Night Settlement', {
 refresh(frm) {
  frm.set_intro(__('El envío crea únicamente el recargo nocturno ordinario como salario adicional. Revise las marcaciones y la política antes de enviar.'));
  if (frm.doc.docstatus !== 1) return;
  frappe.call({method: 'powerpro.controllers.ordinary_night.get_status', args: {name: frm.doc.name}, callback(r) {
   if (r.message && r.message.state !== 'Verified') frm.dashboard.set_headline_alert(__('La evidencia actual requiere revisión; se conserva la liquidación original.'), 'orange');
  }});
 }
});
