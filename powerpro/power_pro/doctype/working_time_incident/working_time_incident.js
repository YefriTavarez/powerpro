frappe.ui.form.on('Working Time Incident', {
    refresh(frm) {
        if (frm.is_new()) return;
        const call=(action,args)=> {
            if (frm.is_dirty()) return frappe.msgprint(__('Recargue el documento antes de continuar.'));
            return frappe.call({method:'powerpro.controllers.working_time_incidents.'+action,type:'POST',
                args:{name:frm.doc.name,...args},freeze:true}).then(()=>frm.reload_doc());
        };
        frm.add_custom_button(__('Abrir documento de origen'),()=>frappe.set_route('Form',frm.doc.source_type,frm.doc.source_name));
        frm.add_custom_button(__('Comprobar nuevamente'),()=>call('recheck',{}));
        frm.add_custom_button(__('Asignar responsable'),()=>frappe.prompt([
            {fieldname:'responsible',label:__('Responsable'),fieldtype:'Link',options:'User',reqd:1,default:frm.doc.responsible},
            {fieldname:'reason',label:__('Motivo de asignación'),fieldtype:'Small Text',reqd:1}
        ],v=>call('assign',v),__('Asignar responsable'),__('Guardar')));
        if (frm.doc.status!=='Open') return;
        frm.add_custom_button(__('Registrar resolución'),()=>{
            const resolutions={'Corregido y comprobado':'Resolved','Excepción documentada':'Documented Exception'};
            const hash=frm.doc.evidence_hash;
            frappe.prompt([
                {fieldname:'resolution',label:__('Resultado'),fieldtype:'Select',options:Object.keys(resolutions).join('\n'),reqd:1},
                {fieldname:'reason',label:__('Justificación'),fieldtype:'Small Text',reqd:1},
                {fieldname:'reference',label:__('Referencia de respaldo'),fieldtype:'Small Text',reqd:1}
            ],v=>call('resolve',{...v,resolution:resolutions[v.resolution],expected_hash:hash}),__('Resolver conservando horas y pagos'),__('Registrar'));
        });
    }
});
