frappe.provide('powerpro.ordinary_night_history');
powerpro.ordinary_night_history.add_button=(frm,status)=>{
    if(frm.doc.docstatus!==2 || !status.can_review)return;
    frm.add_custom_button(__('Revisar evidencia histórica'),()=>{
        if(frm.is_dirty())return frappe.msgprint(__('Guarde los cambios antes de revisar.'));
        const fields=[{fieldname:'reason',label:__('Motivo de la revisión'),fieldtype:'Small Text',reqd:1}];
        if(status.manual_review_allowed)fields.push(
            {fieldname:'manual',label:__('Declarar toda la jornada con respaldo documental'),fieldtype:'Check'},
            {fieldname:'reference',label:__('Referencia de la jornada completa'),fieldtype:'Small Text',depends_on:'eval:doc.manual'},
            {fieldname:'intervals',label:__('Intervalos trabajados, excluyendo pausas'),fieldtype:'Table',depends_on:'eval:doc.manual',
                fields:[{fieldname:'start',label:__('Entrada'),fieldtype:'Datetime',reqd:1,in_list_view:1},
                        {fieldname:'end',label:__('Salida'),fieldtype:'Datetime',reqd:1,in_list_view:1}]});
        frappe.prompt(fields,values=>{
            if(frm.is_dirty())return frappe.msgprint(__('Guarde los cambios antes de revisar.'));
            const args={name:frm.doc.name,reason:values.reason};
            if(values.manual)args.manual_declaration=JSON.stringify({full_session:true,reference:values.reference,
                intervals:(values.intervals||[]).map(r=>({start:r.start,end:r.end}))});
            frappe.call({method:'powerpro.controllers.ordinary_night_history.preview_review',args,freeze:true}).then(({message:r})=>{
                const e=v=>frappe.utils.escape_html(String(v??''));
                const dialog=new frappe.ui.Dialog({title:__('Revisión histórica nocturna'),fields:[{fieldname:'preview',fieldtype:'HTML',options:
                    `<p>${e(r.note)}</p><p>${__('Horas trabajadas antes')}: ${e(r.worked_hours_before)} · ${__('Después')}: ${e(r.worked_hours_after)}</p>`+
                    `<ul>${r.worked_intervals.map(x=>`<li>${e(x.start)} — ${e(x.end)}</li>`).join('')}</ul>`}],
                    primary_action_label:__('Aceptar revisión histórica'),primary_action:()=>{
                        if(frm.is_dirty())return frappe.msgprint(__('Guarde los cambios antes de aceptar.'));
                        frappe.call({method:'powerpro.controllers.ordinary_night_history.apply_review',type:'POST',freeze:true,
                            args:{...args,token:r.token}}).then(()=>{dialog.hide();frm.reload_doc();});
                    }});dialog.show();
            });
        },__('Revisar trabajo conservado'),__('Consultar'));
    },__('Overtime'));
};
