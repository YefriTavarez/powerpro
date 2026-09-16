// Copyright (c) 2026, PowerPro contributors

function configure_retainer_grid(frm) {
    const grid = frm.get_field("details").grid;
    // Load source snapshots through the server; users may remove unselected rows.
    grid.cannot_add_rows = true;
    grid.cannot_delete_rows = frm.doc.docstatus !== 0;
}

function invalidate_retainer_selection(frm) {
    if (frm.doc.docstatus !== 0 || !(frm.doc.details || []).length) return;
    frm.clear_table("details");
    frm.refresh_field("details");
    frm.set_value("total_amount", 0);
    frm.set_intro(__("Los filtros cambiaron. Use Acciones > Cargar acuerdos para revisar la selección del nuevo período."), "blue");
}

async function load_retainer_agreements(frm) {
    if (frm.is_new() || frm.is_dirty()) await frm.save();
    await frm.call({
        doc: frm.doc,
        method: "load_agreements",
        freeze: true,
        freeze_message: __("Cargando acuerdos vigentes..."),
    });
    await frm.reload_doc();
}

frappe.ui.form.on("Supplier Retainer Batch", {
    setup(frm) {
        frm.set_query("supplier", () => ({ filters: { disabled: 0 } }));
    },

    refresh(frm) {
        configure_retainer_grid(frm);
        frm.set_intro("");
        frm.add_custom_button(__("Ver acuerdos"), () => {
            frappe.set_route("List", "Supplier Retainer Agreement");
        }, __("Ir a"));

        if (frm.doc.docstatus === 0) {
            frm.set_intro(__("Cargue los acuerdos y quite los que no desea procesar. Al validar se crearán facturas de compra en borrador para revisión."), "blue");
            frm.add_custom_button(__("Cargar acuerdos"), () => {
                if ((frm.doc.details || []).length) {
                    frappe.confirm(
                        __("Se reemplazará la selección actual con los acuerdos que cumplan los filtros. Deberá volver a quitar las filas que no correspondan."),
                        () => load_retainer_agreements(frm)
                    );
                } else {
                    return load_retainer_agreements(frm);
                }
            }, __("Acciones"));
        } else if (frm.doc.docstatus === 1) {
            frm.set_intro(__("Abra las facturas desde la tabla para revisarlas. Al cancelar esta liquidación se eliminan sus borradores sin procesamiento fiscal y se conserva el historial. Las facturas sometidas requieren cancelación individual."), "green");
        }
    },

    company: invalidate_retainer_selection,
    currency: invalidate_retainer_selection,
    frequency: invalidate_retainer_selection,
    period_date: invalidate_retainer_selection,
    supplier: invalidate_retainer_selection,
});

frappe.ui.form.on("Supplier Retainer Batch Detail", {
    details_remove(frm) {
        const total = (frm.doc.details || []).reduce((sum, row) => sum + flt(row.gross_amount), 0);
        frm.set_value("total_amount", total);
    },
});
