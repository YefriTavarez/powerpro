/* IGCARIBE: one coordinator, native shifts / authorizations / settlements. */
(() => {
  'use strict';
  const DT='Registro de Jornada';
  const esc=v=>frappe.utils.escape_html(String(v??''));
  const num=v=>Number(v||0).toLocaleString('es-DO',{maximumFractionDigits:2});
  const money=(v,c='DOP')=>new Intl.NumberFormat('es-DO',{style:'currency',currency:c||'DOP'}).format(Number(v||0));
  const names={'Shift Assignment':'Turno','Retroactive Overtime Adjustment':'Ajuste Retroactivo','Ordinary Night Settlement':'Nocturnidad','Overtime Work Call':'Convocatoria'};
  const link=(dt,name,label)=>`<a href="/app/${frappe.router.slug(dt)}/${encodeURIComponent(name)}" target="_blank" rel="noopener">${esc(label||name)}</a>`;
  const api=async(frm,action,args={})=>(await frappe.call({method:'igc_journey_register_v1',args:{name:frm.doc.name,modified:frm.doc.modified,action,...args},freeze:['prepare','apply_shift','review_apply'].includes(action),freeze_message:'Actualizando la jornada…'})).message;
  const errorText=e=>{
    try{return JSON.parse(e._server_messages||'[]').map(v=>JSON.parse(v).message).join(' · ')||e.message||'No se pudo completar la acción.';}catch(_){return e.message||'No se pudo completar la acción.';}
  };
  const clean=frm=>{if(frm.is_dirty()){frappe.msgprint('Guarde los cambios antes de continuar.');return false;}return true;};
  function header(frm){
    frm.fields_dict.intro.$wrapper.html(`<div style="border:1px solid #dce4ed;border-left:4px solid #087f5b;border-radius:10px;padding:15px 18px;margin-bottom:14px;background:var(--card-bg,#fff)"><strong style="color:#021e42;font-size:17px">Registro de Jornada</strong><p style="margin:6px 0 0;color:#64748b">Seleccione los empleados, identifique si hubo un cambio de turno o trabajo adicional y elija la fecha de pago. Las jornadas pasadas conservan su fecha original.</p>${frm.doc.source_work_call?`<p style="margin:6px 0 0">Convocatoria de Origen: ${link('Overtime Work Call',frm.doc.source_work_call)}</p>`:''}</div>`);
  }
  function configure(frm){
    frm.set_query('payroll_entry',()=>({filters:{company:frm.doc.company,docstatus:0}}));
    frm.set_query('employee','employees',()=>({filters:{company:frm.doc.company}}));
    frm.set_query('work_order','employees',()=>({filters:{company:frm.doc.company,docstatus:['<',2]}}));
    frm.set_query('job_card','employees',(_doc,cdt,cdn)=>({filters:{work_order:locals[cdt][cdn].work_order||'__none__',docstatus:['<',2]}}));
    const frozen=!!frm.doc.source_snapshot;
    for(const f of ['company','journey_type','starts_at','ends_at','replacement_shift','reason','payroll_entry','payroll_date'])frm.set_df_property(f,'read_only',frozen?1:0);
    const grid=frm.fields_dict.employees.grid;
    grid.cannot_add_rows=frozen;grid.cannot_delete_rows=frozen;
    for(const f of ['employee','work_order','job_card'])grid.update_docfield_property(f,'read_only',frozen?1:0);
    if(!frozen)frm.add_custom_button('Agregar Empleados',()=>addEmployees(frm));
    frm.add_custom_button('Ver Registros',()=>frappe.set_route('List',DT));
    if(!frm.is_new())frm.add_custom_button('Actualizar Revisión',()=>refreshReview(frm));
  }
  function addEmployees(frm){
    const selector=new frappe.ui.form.MultiSelectDialog({doctype:'Employee',target:frm,setters:{company:frm.doc.company},get_query:()=>({filters:{company:frm.doc.company}}),action:selections=>{
      const existing=new Set((frm.doc.employees||[]).map(r=>r.employee));
      selections.forEach(employee=>{if(!existing.has(employee)){frm.add_child('employees',{employee,break_mode:'Marcaciones'});existing.add(employee);}});
      frm.refresh_field('employees');frm.dirty();selector.dialog.hide();
    }});
  }
  async function refreshReview(frm){
    const box=frm.fields_dict.review.$wrapper;
    if(frm.is_new()){box.html('<p class="text-muted">Guarde la jornada para revisar los turnos y preparar sus documentos.</p>');return;}
    const generation=(frm.__journeyGeneration||0)+1;frm.__journeyGeneration=generation;
    box.html('<p class="text-muted" role="status">Consultando la jornada y sus documentos…</p>');
    try{
      const data=await api(frm,'details');if(frm.__journeyGeneration!==generation)return;
      frm.__journeyData=data;
      box.html(`<style>
      .igc-journey-table{width:100%;min-width:1120px;table-layout:fixed;font-size:12px;border-collapse:collapse}
      .igc-journey-table th{background:#092746;color:#fff;padding:11px 12px;white-space:nowrap}
      .igc-journey-table td{padding:12px;border-bottom:1px solid #dce4ed;vertical-align:middle;overflow-wrap:anywhere}
      .igc-journey-table tbody tr:nth-child(even){background:var(--subtle-fg,#f7f9fc)}
      .igc-journey-actions{display:flex;align-items:center;gap:7px;flex-wrap:nowrap}
      .igc-journey-actions .btn{margin:0;white-space:nowrap;min-height:29px;flex:0 0 auto}
      .igc-journey-doc{margin:4px 0}.igc-journey-muted{color:#64748b;font-size:11px;margin-top:5px}
      </style><div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px"><strong>${data.rows.length} empleados · Documentos y Cálculo</strong><button class="btn btn-default btn-sm" data-journey-batch>Preparar Pendientes</button></div><div style="overflow:auto;border:1px solid #dce4ed;border-radius:10px"><table class="igc-journey-table"><colgroup><col style="width:21%"><col style="width:17%"><col style="width:15%"><col style="width:23%"><col style="width:270px"></colgroup><thead><tr><th>Empleado</th><th>Turno</th><th>Descanso</th><th>Documentos</th><th>Acciones</th></tr></thead><tbody>${data.rows.map(r=>{
        const shiftDraft=r.links.find(x=>x.field==='shift_assignment'&&x.docstatus===0);
        const financial=r.links.some(x=>['retroactive_adjustment','night_settlement'].includes(x.field));
        return `<tr><td><strong>${esc(r.employee_name)}</strong>${r.approver?`<div class="igc-journey-muted">Aprobador: ${esc(r.approver)}</div>`:''}${r.warnings.length?`<details style="margin-top:6px"><summary class="text-warning">${r.warnings.length} puntos por revisar</summary><ul style="margin:7px 0;padding-left:15px">${r.warnings.map(w=>`<li style="margin-bottom:5px">${esc(w)}</li>`).join('')}</ul></details>`:''}</td><td>${esc(r.target_shift||'Sin Turno')}${r.current_shift!==r.target_shift?`<div class="igc-journey-muted">Actual: ${esc(r.current_shift||'Sin Turno')}</div>`:''}</td><td>${esc(r.break_mode)}<div class="igc-journey-muted">Regla del turno: ${num(r.break_minutes)} min</div></td><td>${r.links.map(x=>`<div class="igc-journey-doc">${link(x.doctype,x.name,names[x.doctype]+': '+x.name)}<div class="igc-journey-muted">${x.docstatus===0?'Borrador':x.docstatus===2?'Cancelado':'Validado'}${x.settlement_status?' · '+esc(({Pending:'Pendiente',Created:'Salario Adicional Creado','Payroll Submitted':'En Nómina',Paid:'Pagado',Cancelled:'Cancelado'})[x.settlement_status]||x.settlement_status):''}</div></div>`).join('')||'<span class="text-muted">Pendiente de Preparar</span>'}</td><td><div class="igc-journey-actions"><button class="btn btn-default btn-xs" data-journey-action="${shiftDraft?'apply_shift':'prepare'}" data-row="${esc(r.row)}">${shiftDraft?'Aplicar Turno':'Preparar'}</button>${financial?`<button class="btn btn-default btn-xs" data-journey-action="preview" data-row="${esc(r.row)}">Ver Cálculo</button>`:''}<button class="btn btn-default btn-xs" data-journey-action="evidence" data-row="${esc(r.row)}">Detalle</button></div></td></tr>`;
      }).join('')}</tbody></table></div><p class="text-muted" style="font-size:12px;margin-top:10px">Preparar crea los documentos para revisión. El cálculo muestra por separado los conceptos de pago y utiliza las aprobaciones correspondientes. Una liquidación creada todavía no confirma el pago.</p>`);
      box.off('.igcJourney').on('click.igcJourney','[data-journey-action]',async function(){
        const action=this.dataset.journeyAction,row=this.dataset.row;
        if(action==='evidence')return evidenceDialog(frm,row);
        if(action==='preview')return calculation(frm,row);
        if(!clean(frm))return;
        const run=async()=>{try{const result=await api(frm,action,{row});await frm.reload_doc();frappe.show_alert({message:result.notice,indicator:'green'},8);}catch(e){await refreshReview(frm);}};
        if(action==='apply_shift')frappe.confirm('¿Confirmar este cambio temporal de turno para la fecha registrada? Se validará la asignación vinculada.',run);else await run();
      }).on('click.igcJourney','[data-journey-batch]',()=>prepareBatch(frm));
    }catch(e){box.html('<p class="text-warning">No se pudo consultar la revisión. Use Actualizar Revisión para reintentar.</p>');}
  }
  async function prepareBatch(frm){
    if(!clean(frm))return;
    const rows=(frm.doc.employees||[]).map(r=>({name:r.name,label:r.employee_name||r.employee}));
    const outcomes=[];
    for(const row of rows){
      try{const result=await api(frm,'prepare',{row:row.name});outcomes.push({employee:row.label,message:result.notice,ok:true});}
      catch(e){outcomes.push({employee:row.label,message:errorText(e),ok:false});}
      await frm.reload_doc();
    }
    frappe.msgprint({title:'Documentos de la Jornada',message:outcomes.map(x=>`<p><strong>${esc(x.employee)}</strong><br><span class="${x.ok?'text-muted':'text-warning'}">${esc(x.message)}</span></p>`).join('')});
  }
  async function calculation(frm,row){
    if(!clean(frm))return;
    const d=new frappe.ui.Dialog({title:'Cálculo de la Jornada',size:'large',fields:[{fieldname:'result',fieldtype:'HTML'}],primary_action_label:'Cerrar',primary_action:()=>d.hide()});
    d.show();const box=d.fields_dict.result.$wrapper;box.html('<p>Consultando el cálculo…</p>');
    try{
      const p=await api(frm,'preview',{row});const parts=[];
      if(p.retroactive){const r=p.retroactive;const s=r.reconciliation||(r.snapshot&&typeof r.snapshot==='object'?r.snapshot:r);parts.push(`<h5>Horas Adicionales</h5><table class="table table-bordered"><tr><th>Horas Verificadas</th><td>${num(s.verified_hours)}</td></tr><tr><th>Extras con Recargo Regular</th><td>${num(s.regular_35_hours)}</td></tr><tr><th>Extras con Recargo Extraordinario</th><td>${num(s.regular_100_hours)}</td></tr><tr><th>Horas Nocturnas Adicionales</th><td>${num(s.night_hours)}</td></tr></table>`);const w=[...(r.warnings||s.warnings||[]),...(r.settlement_blockers||[])];if(w.length)parts.push(`<div class="text-warning">${w.map(x=>`<p>${esc(x)}</p>`).join('')}</div>`);const payment=r.cash_settlement||r.settlement;if(payment?.total_amount!=null)parts.push(`<p><strong>Importe: ${money(payment.total_amount,payment.currency)}</strong></p>`);}
      if(p.night){const n=p.night;parts.push(`<h5>Nocturnidad Ordinaria</h5><p>${num(n.hours)} horas × ${money(n.rate,n.currency)} × ${num(n.percent)} %</p><p><strong>Recargo: ${money(n.amount,n.currency)}</strong></p><p>Estado de Evidencia: ${esc(({Verified:'Verificada',Waiting:'Pendiente', 'Needs Review':'Requiere Revisión'})[n.state]||n.state)}</p>${n.additional_salary?`<p>Salario Adicional: ${link('Additional Salary',n.additional_salary)}</p>`:''}`);}
      if(!parts.length)parts.push('<p>Prepare primero los documentos correspondientes. Las horas sin evidencia suficiente quedan pendientes de revisión.</p>');
      box.html(parts.join('')+'<p class="text-muted">Revise y apruebe los documentos vinculados para liquidar los conceptos correspondientes.</p>');
    }catch(e){box.html('<p class="text-warning">El cálculo requiere revisión. Consulte el documento vinculado y los puntos pendientes de la jornada.</p>');}
  }
  function evidenceDialog(frm,rowName){
    if(!clean(frm))return;
    const row=frm.doc.employees.find(r=>r.name===rowName);
    const info=frm.__journeyData?.rows.find(r=>r.row===rowName);
    const d=new frappe.ui.Dialog({title:'Detalle de '+(row.employee_name||row.employee),size:'large',fields:[
      {fieldtype:'HTML',fieldname:'hint',options:`<p>El empleado puede decidir cuándo toma su descanso. Registre la evidencia disponible para esta jornada.</p><p class="text-muted">Duración configurada en el turno: ${num(info?.break_minutes)} minutos. La opción flexible conserva el dato pendiente de aplicación; no inventa una ubicación de la pausa.</p>`},
      {fieldtype:'Datetime',fieldname:'actual_start',label:'Inicio Real',default:row.actual_start},
      {fieldtype:'Datetime',fieldname:'actual_end',label:'Fin Real',default:row.actual_end},
      {fieldtype:'Select',fieldname:'break_mode',label:'Descanso',options:['Marcaciones','Descanso Flexible del Turno','Descanso Declarado'],default:row.break_mode||'Marcaciones',reqd:1},
      {fieldtype:'Column Break',fieldname:'col'},
      {fieldtype:'Datetime',fieldname:'break_start',label:'Inicio del Descanso',default:row.break_start,depends_on:'eval:doc.break_mode==="Descanso Declarado"'},
      {fieldtype:'Datetime',fieldname:'break_end',label:'Fin del Descanso',default:row.break_end,depends_on:'eval:doc.break_mode==="Descanso Declarado"'},
      {fieldtype:'Small Text',fieldname:'evidence_reference',label:'Referencia de la Declaración',default:row.evidence_reference},
      {fieldtype:'Section Break',fieldname:'native'},
      {fieldtype:'HTML',fieldname:'links',options:`<p>${(info?.links||[]).map(x=>link(x.doctype,x.name,names[x.doctype])).join(' · ')}</p>`}
    ],primary_action_label:'Guardar Detalle',primary_action:async values=>{
      for(const field of ['actual_start','actual_end','break_mode','break_start','break_end','evidence_reference'])await frappe.model.set_value(row.doctype,row.name,field,values[field]||null);
      await frm.save();d.hide();
      if(values.break_mode==='Descanso Declarado'&&row.retroactive_adjustment)await reviewDeclaration(frm,rowName);
    }});d.show();
  }
  async function reviewDeclaration(frm,row){
    if(!clean(frm))return;
    const p=await api(frm,'review_preview',{row});
    const d=new frappe.ui.Dialog({title:'Revisar Declaración de Jornada',size:'large',fields:[{fieldname:'preview',fieldtype:'HTML',options:`<p>Horas adicionales verificadas: <strong>${num(p.after?.verified_hours)}</strong></p><p>${esc(p.manual_declaration?.reference||'')}</p><ul>${(p.manual_declaration?.intervals||[]).map(i=>`<li>${esc(i.start)} — ${esc(i.end)}</li>`).join('')}</ul>${(p.settlement_blockers||[]).map(w=>`<p class="text-warning">${esc(w)}</p>`).join('')}<p class="text-muted">La declaración queda registrada para la aprobación del ajuste.</p>`},{fieldname:'confirmed',fieldtype:'Check',label:'Confirmo que incluye toda la jornada y excluye el descanso declarado',reqd:1}],primary_action_label:'Aceptar Evidencia',primary_action:async values=>{if(!values.confirmed)return;await api(frm,'review_apply',{row,token:p.token,confirmed:'1'});d.hide();await frm.reload_doc();frappe.show_alert({message:'Evidencia registrada para revisión del ajuste.',indicator:'green'});}});d.show();
  }
  frappe.ui.form.on(DT,{
    refresh(frm){header(frm);configure(frm);refreshReview(frm);},
    onload(frm){if(frm.is_new()&&!frm.doc.payroll_date)frm.set_value('payroll_date',frappe.datetime.get_today());},
    async payroll_entry(frm){if(!frm.doc.payroll_entry)return;const p=(await frappe.db.get_value('Payroll Entry',frm.doc.payroll_entry,['end_date','company'])).message;if(p){await frm.set_value('payroll_date',p.end_date);}},
    journey_type(frm){frm.toggle_reqd('replacement_shift',frm.doc.journey_type!=='Horas Adicionales');},
    after_save:refreshReview
  });
})();
