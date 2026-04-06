// Source Client Script: Dinamica HTML de Cinta Doble Cara en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh(frm) {
        render_cinta_doble_cara(frm);
    },

    requiere_cinta_doble_cara(frm) {
        render_cinta_doble_cara(frm);
    },

    puntos_cinta_doble_cara(frm) {
        render_cinta_doble_cara(frm);
    },

    validate(frm) {
        const errores = [];

        if (frm.doc.requiere_cinta_doble_cara && frm.doc.puntos_cinta_doble_cara) {
            if (!frm.doc.ancho_punto_cinta_doble_cara || !frm.doc.alto_punto_cinta_doble_cara) {
                errores.push("Debes completar ancho y alto del punto de cinta doble cara.");
            }
        } else {
            // Limpiar si no se requiere
            frm.set_value("puntos_cinta_doble_cara", null);
            frm.set_value("ancho_punto_cinta_doble_cara", null);
            frm.set_value("alto_punto_cinta_doble_cara", null);
        }

        if (errores.length > 0) {
            frappe.throw(errores.join("<br>"));
        }
    }
});

function render_cinta_doble_cara(frm) {
    const wrapper = frm.fields_dict.html_cinta_doble_cara?.$wrapper;
    if (!wrapper) return;
    wrapper.empty();

    if (!frm.doc.requiere_cinta_doble_cara || !frm.doc.puntos_cinta_doble_cara) return;

    const style_cinta = `<style>
        .detalles-acabado:first-child { margin-top: 22px !important; }
        .detalles-acabado { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; font-family: "Segoe UI", sans-serif; font-size: 12px; }
        .detalle-container { display: flex; align-items: stretch; }
        .detalle-mini { flex-grow: 1; background: #f8f9fa; border: 1px solid #e0e0e0; border-left: 3px solid #0069d9; border-radius: 6px; padding: 6px 10px; }
        .detalle-mini .etiqueta { font-weight: 600; font-size: 11px; color: #333; margin-bottom: 4px; }
        .detalle-mini .campos { display: flex; gap: 6px; }
        .detalle-mini input { padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 4px; width: 100%; min-width: 80px; }
    </style>`;

    const html = `
        <div class="detalles-acabado">
            <div class="detalle-container">
                <div class="detalle-mini">
                    <div class="etiqueta">Punto de Cinta Doble Cara (in)</div>
                    <div class="campos">
                        <input type="number" step="0.5" min="0.5" max="2" placeholder="Ancho" value="${frm.doc.ancho_punto_cinta_doble_cara || ""}" data-field="ancho_punto_cinta_doble_cara" />
                        <input type="number" step="0.5" min="0.5" max="10" placeholder="Alto" value="${frm.doc.alto_punto_cinta_doble_cara || ""}" data-field="alto_punto_cinta_doble_cara" />
                    </div>
                </div>
            </div>
        </div>
        ${style_cinta}
    `;

    wrapper.html(html);

    wrapper.find("input").on("change", function () {
        const field = $(this).data("field");
        let value = Math.ceil(parseFloat(this.value || 0) * 2) / 2;

        if (field === "ancho_punto_cinta_doble_cara") {
            value = Math.min(2, Math.max(0.5, value));
        } else {
            value = Math.min(10, Math.max(0.5, value));
        }

        frm.set_value(field, value);
        $(this).val(value);
    });
}
