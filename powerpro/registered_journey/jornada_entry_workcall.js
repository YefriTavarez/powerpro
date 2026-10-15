/* IGC: access the journey coordinator without altering the work-call controller. */
frappe.ui.form.on('Overtime Work Call',{
  refresh(frm){
    frm.add_custom_button('Registrar Jornada',async()=>{
      if(frm.is_new())return frappe.new_doc('Registro de Jornada',{company:frm.doc.company});
      if(frm.is_dirty()){frappe.msgprint('Guarde la convocatoria para tomar sus datos actuales.');return;}
      if(frm.doc.docstatus!==0)return frappe.new_doc('Registro de Jornada',{company:frm.doc.company});
      const data=(await frappe.call({method:'igc_journey_register_v1',args:{action:'import_call',source_work_call:frm.doc.name},freeze:true,freeze_message:'Preparando la jornada…'})).message;
      await frappe.model.with_doctype('Registro de Jornada');
      const doc=frappe.model.get_new_doc('Registro de Jornada');
      for(const key of ['company','starts_at','ends_at','reason','payroll_date','source_work_call'])doc[key]=data[key];
      doc.journey_type='Horas Adicionales';
      for(const item of data.employees||[])Object.assign(frappe.model.add_child(doc,'Registro de Jornada Empleado','employees'),item);
      frappe.set_route('Form','Registro de Jornada',doc.name);
    });
  }
});
