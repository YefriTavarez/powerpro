frappe.ui.form.on('Overtime Rest Watch',{
    refresh(frm){
        if(frm.is_new())return;
        const call=(method,args)=>{
            if(frm.is_dirty())return frappe.msgprint(__('Recargue el seguimiento antes de continuar.'));
            return frappe.call({method:'powerpro.controllers.overtime_rest_monitor.'+method,type:'POST',freeze:true,
                args:{name:frm.doc.name,...args}}).then(()=>frm.reload_doc());
        };
        frm.add_custom_button(__('Abrir elección del empleado'),()=>frappe.set_route('Form','Overtime Settlement Election',frm.doc.election));
        frm.add_custom_button(__('Comprobar nuevamente'),()=>call('recheck',{}));
        frm.add_custom_button(__('Asignar responsable'),()=>frappe.prompt([
            {fieldname:'responsible',label:__('Responsable'),fieldtype:'Link',options:'User',default:frm.doc.responsible,reqd:1},
            {fieldname:'reason',label:__('Motivo'),fieldtype:'Small Text',reqd:1}
        ],v=>call('assign',v),__('Asignar seguimiento de descanso'),__('Guardar')));
    }
});
