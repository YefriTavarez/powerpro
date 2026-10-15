/* IGC: select the payroll settlement period while preserving the actual work date. */
frappe.ui.form.on('Payroll Entry',{
  refresh(frm){
    if(frm.is_new()||frm.doc.docstatus!==0)return;
    frm.add_custom_button('Registrar Jornada',()=>{
      if(frm.is_dirty()){frappe.msgprint('Guarde los cambios de la nómina antes de registrar una jornada.');return;}
      frappe.new_doc('Registro de Jornada',{company:frm.doc.company,payroll_entry:frm.doc.name,payroll_date:frm.doc.end_date});
    });
  }
});
