frappe.ui.form.on('Working Time Review',{
    refresh(frm){
        if(frm.is_new())return;
        frm.add_custom_button(__('Abrir documento de origen'),()=>frappe.set_route('Form',frm.doc.source_type,frm.doc.source_name));
        frm.add_custom_button(__('Ver incidencias'),()=>frappe.set_route('List','Working Time Incident',{working_time_review:frm.doc.name}));
        frm.add_custom_button(__('Configurar vigilancia'),()=>{
            const states={'Activa':'Active','Pausada':'Paused'};
            frappe.prompt([
                {fieldname:'status',label:__('Vigilancia de esta evaluación'),fieldtype:'Select',options:Object.keys(states).join('\n'),default:frm.doc.status==='Paused'?'Pausada':'Activa',reqd:1},
                {fieldname:'responsible',label:__('Responsable de detectar incidencias nuevas'),fieldtype:'Link',options:'User',default:frm.doc.responsible,reqd:1},
                {fieldname:'reason',label:__('Motivo'),fieldtype:'Small Text',reqd:1}
            ],v=>{
                if(frm.is_dirty())return frappe.msgprint(__('Recargue la evaluación antes de continuar.'));
                frappe.call({method:'powerpro.controllers.working_time_reviews.configure',type:'POST',freeze:true,
                    args:{name:frm.doc.name,...v,status:states[v.status]}}).then(()=>frm.reload_doc());
            },__('Pausar, reanudar o reasignar la evaluación'),__('Guardar'));
        });
    }
});
