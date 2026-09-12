frappe.ui.form.on('Ordinary Night Settlement', {
 refresh(frm) {
        frappe.require("/assets/powerpro/js/working_time_controls.js", () => powerpro.working_time_controls.add_button(frm));
  frm.set_intro(__('El envío crea únicamente el recargo nocturno ordinario como salario adicional. Revise las marcaciones o la declaración validada de Gestión Humana y la política antes de enviar.'));
  let snapshot;
  try { snapshot = JSON.parse(frm.doc.evidence_snapshot || '{}'); } catch (_) { snapshot = {}; }
  const certified = snapshot.input && snapshot.input.certified_session;
  if (certified) frm.set_intro(__('Se utiliza la jornada completa validada por Gestión Humana en {0}. Consulte la referencia y los intervalos en Evidencia y cálculo.', [certified.authorization]));
  if (frm.doc.docstatus !== 1) return;
  frappe.call({method: 'powerpro.controllers.ordinary_night.get_status', args: {name: frm.doc.name}, callback(r) {
   if (r.message && r.message.state !== 'Verified') frm.dashboard.set_headline_alert(__('La evidencia actual requiere revisión; se conserva la liquidación original.'), 'orange');
  }});
 }
});
