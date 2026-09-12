frappe.provide('powerpro.working_time_controls');
powerpro.working_time_controls.add_button = frm => {
    const dt=frm.doc.doctype;
    if (frm.doc.docstatus!==1 || (dt==='Overtime Authorization' && !frm.doc.evidence_enrolled)
        || (dt==='Retroactive Overtime Adjustment' && frm.doc.reconciliation_engine!=='Verified Checkins')) return;
    frm.add_custom_button(__('Controles de jornada'), () => {
        if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios antes de consultar los controles.'));
        const profiles={'General':'General','Jornada corrida industrial acordada':'Agreed industrial continuous day',
            'Jornada corrida comercial acordada':'Agreed commercial continuous day','Funcionamiento continuo':'Continuous operation','Trabajo declarado peligroso o insalubre':'Declared hazardous work'};
        const breaks={'Una hora después de cuatro':'One hour after four','Hora y media después de cinco':'Ninety minutes after five'};
        const causes={'Pendiente de clasificar':'Unclassified','Aumento extraordinario de trabajo':'Extraordinary workload','Otro supuesto documentado':'Other documented cause'};
        frappe.prompt([
            {fieldname:'profile',label:__('Régimen a evaluar'),fieldtype:'Select',options:Object.keys(profiles).join('\n'),default:'General',reqd:1},
            {fieldname:'reference',label:__('Referencia que sustenta el régimen especial'),fieldtype:'Small Text'},
            {fieldname:'break_rule',label:__('Pausa acordada a evaluar'),fieldtype:'Select',options:Object.keys(breaks).join('\n'),default:Object.keys(breaks)[0],reqd:1},
            {fieldname:'quarterly_basis',label:__('Causa de las prolongaciones del trimestre'),fieldtype:'Select',options:Object.keys(causes).join('\n'),default:Object.keys(causes)[0],reqd:1},
            {fieldname:'rest_start',label:__('Inicio del descanso semanal previsto'),fieldtype:'Datetime'},
            {fieldname:'rest_end',label:__('Fin del descanso semanal previsto'),fieldtype:'Datetime'}
        ], values => {
            if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios antes de consultar los controles.'));
            const options={...values,profile:profiles[values.profile],break_rule:breaks[values.break_rule],quarterly_basis:causes[values.quarterly_basis]};
            frappe.call({method:'powerpro.controllers.working_time_controls.preview',args:{source_type:dt,source_name:frm.doc.name,...options},freeze:true}).then(({message:r})=>{
                const e=v=>frappe.utils.escape_html(String(v??''));
                const labels={daily_work:'Jornada completa',weekly_work:'Acumulado semanal',work_break:'Pausas',session_evidence:'Evidencia de jornada',quarterly_extension:'Prolongación trimestral',weekly_continuous_rest:'Descanso semanal'};
                const states={'Review':'Requiere revisión','Within evaluated limit':'Dentro del límite evaluado','Incomplete':'Evidencia incompleta','Applicability review':'Revisar aplicabilidad','Documented regime required':'Verificar régimen documentado','Enjoyment unverified':'Disfrute no verificado'};
                const html=`<p>${__('Evaluación de controles; conserva las horas y los pagos. El régimen seleccionado requiere confirmar su aplicabilidad.')}</p>
                    <p>${e(values.profile)} · ${e(r.reference)}</p><p>${e(values.break_rule)} · ${e(values.quarterly_basis)}</p><div style="overflow-x:auto"><table class="table table-bordered"><thead><tr><th>${__('Control')}</th><th>${__('Resultado')}</th><th>${__('Observado')}</th><th>${__('Límite')}</th><th>${__('Detalle')}</th></tr></thead><tbody>
                    ${r.controls.map(x=>`<tr><td>${e(labels[x.code]||x.code)}</td><td>${e(states[x.status]||x.status)}</td><td>${e(x.observed)}</td><td>${e(x.limit)} ${e(x.unit==='hours'?'h':x.unit)}</td><td>${x.article ? `Art. ${e(x.article)}. ` : ""}${e(x.message)} ${e(x.start||'')} ${e(x.end||'')}</td></tr>`).join('')}</tbody></table></div>
                    <ul>${r.notes.map(x=>`<li>${e(x)}</li>`).join('')}</ul><p>${__('Problemas de evidencia')}: ${e(r.evidence_issues.length)}</p>`;
                const dialog=new frappe.ui.Dialog({title:__('Controles de jornada'),size:'extra-large',fields:[{fieldtype:'HTML',fieldname:'result',options:html}],
                    primary_action_label:__('Guardar evaluación e incidencias'),primary_action:()=>{
                        if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios antes de registrar incidencias.'));
                        frappe.prompt([{fieldname:'responsible',label:__('Responsable de revisión'),fieldtype:'Link',options:'User',reqd:1}],v=>{
                            if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios antes de registrar incidencias.'));
                            frappe.call({method:'powerpro.controllers.working_time_incidents.record',type:'POST',freeze:true,
                                args:{source_type:dt,source_name:frm.doc.name,options:JSON.stringify(options),responsible:v.responsible,expected_hash:r.input_hash}
                            }).then(({message:rows})=>{
                                dialog.hide();
                                if (!rows.length) {
                                    frappe.msgprint(__('Evaluación inscrita; actualmente no tiene controles pendientes.'));
                                    return frappe.set_route('List','Working Time Review',{source_type:dt,source_name:frm.doc.name});
                                }
                                frappe.set_route('List','Working Time Incident',{source_type:dt,source_name:frm.doc.name});
                            });
                        },__('Registrar incidencias'),__('Guardar'));
                    }});
                dialog.show();
            });
        },__('Condiciones de evaluación'),__('Consultar'));
    },__('Overtime'));
};
