// Source Client Script: Dinamica HTML Acabado Especial en Generador de Producto
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh(frm) {
        render_acabado_bloques(frm);
    },

    acabado_especial(frm) {
        render_acabado_bloques(frm);
    },

    elementos_acabado_especial(frm) {
        render_acabado_bloques(frm);
    },

    foil_color(frm) {
        render_acabado_bloques(frm);
    },

    requiere_acabado_especial(frm) {
        render_acabado_bloques(frm);
    },

  validate(frm) {
    const errores = [];
    const requiere = frm.doc.requiere_acabado_especial;
    const cantidad = cint(frm.doc.elementos_acabado_especial || 0);

    // Si no requiere acabado especial, limpiar todos los campos relacionados
    if (!requiere) {
        frm.set_value("acabado_especial", null);
        frm.set_value("elementos_acabado_especial", null);
        frm.set_value("foil_color", null);

        for (let i = 1; i <= 6; i++) {
            frm.set_value(`ancho_elemento_${i}`, null);
            frm.set_value(`alto_elemento_${i}`, null);
        }

        return; // no validar nada más si no requiere
    }

    // Validaciones si sí requiere acabado especial
    for (let i = 1; i <= cantidad; i++) {
        const ancho = cint(frm.doc[`ancho_elemento_${i}`]);
        const alto = cint(frm.doc[`alto_elemento_${i}`]);

        if (!ancho) {
            errores.push(`Debes completar el ancho del Elemento ${i}.`);
        } else if (ancho < 1 || ancho > 20) {
            errores.push(`El ancho del Elemento ${i} debe estar entre 1 y 20.`);
        }

        if (!alto) {
            errores.push(`Debes completar el alto del Elemento ${i}.`);
        } else if (alto < 1 || alto > 20) {
            errores.push(`El alto del Elemento ${i} debe estar entre 1 y 20.`);
        }
    }

    if (errores.length > 0) {
        frappe.throw(errores.join("<br>"));
    }
}

});

function render_acabado_bloques(frm) {
    const requiere = frm.doc.requiere_acabado_especial;
    const acabado = (frm.doc.acabado_especial || "").toLowerCase();
    const cantidad = cint(frm.doc.elementos_acabado_especial || 0);

    const campos_html = [
        "html_acabado_especial_1",
        "html_acabado_especial_2",
        "html_acabado_especial_3"
    ];

    frm.toggle_display("acabado_especial", !!requiere);
    frm.toggle_display("elementos_acabado_especial", !!requiere);
    frm.toggle_display("foil_color", !!requiere);

    if (!requiere || cantidad === 0 || !acabado) {
        campos_html.forEach(campo => {
            if (frm.fields_dict[campo]) {
                frm.fields_dict[campo].$wrapper.empty();
            }
        });
        return;
    }

    if (acabado.includes("estampado") && frm.doc.foil_color) {
        frappe.db.get_value("Foil Color", frm.doc.foil_color, "hex_color").then(res => {
            const foil_hex = res.message.hex_color || null;
            render_bloque_acabado(frm, 1, 2, "html_acabado_especial_1", foil_hex);
            render_bloque_acabado(frm, 3, 4, "html_acabado_especial_2", foil_hex);
            render_bloque_acabado(frm, 5, 6, "html_acabado_especial_3", foil_hex);
        });
    } else {
        render_bloque_acabado(frm, 1, 2, "html_acabado_especial_1", null);
        render_bloque_acabado(frm, 3, 4, "html_acabado_especial_2", null);
        render_bloque_acabado(frm, 5, 6, "html_acabado_especial_3", null);
    }
}

function render_bloque_acabado(frm, desde, hasta, fieldname_html, foil_hex_color) {
    const field = frm.fields_dict[fieldname_html];
    if (!field) return;

    const wrapper = field.$wrapper;
    wrapper.empty();

    const cantidad = cint(frm.doc.elementos_acabado_especial || 0);
    if (cantidad < desde) return;

    let td_class = "";
    let td_style = "";

    const acabado = (frm.doc.acabado_especial || "").toLowerCase();

    if (acabado.includes("estampado") && foil_hex_color) {
        td_class = "shimmer-td";
        td_style = `--foil-color: ${foil_hex_color};`;
    } else if (acabado.includes("embosado")) {
        td_class = "emboss-td";
        td_style = "";
    } else if (acabado.includes("debosado")) {
        td_class = "deboss-td";
        td_style = "";
    }

    let html = `<div class="detalles-acabado">`;

    for (let i = desde; i <= hasta; i++) {
        if (i > cantidad) break;

        html += `
            <div class="detalle-container">
                <div class="detalle-mini">
                    <div class="etiqueta">Elemento ${i} (in)</div>
                    <div class="campos">
                        <input type="number" placeholder="Ancho" min="1" max="20" step="1" data-field="ancho_elemento_${i}" value="${frm.doc[`ancho_elemento_${i}`] || ""}" />
                        <input type="number" placeholder="Alto" min="1" max="20" step="1" data-field="alto_elemento_${i}" value="${frm.doc[`alto_elemento_${i}`] || ""}" />
                    </div>
                </div>
                <div class="td-color ${td_class}" style="${td_style}"></div>
            </div>
        `;
    }

    html += `</div>${style_acabado}`;

    wrapper.html(html);

    wrapper.find("input").on("change", function () {
        const field = $(this).data("field");
        let value = Math.ceil(parseFloat(this.value || 0));
        value = Math.max(1, Math.min(20, value));
        frm.set_value(field, value);
        $(this).val(value);
    });
}

const style_acabado = `<style>
    .detalles-acabado:first-child { margin-top: 22px !important; }
    .detalles-acabado { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; font-family: "Segoe UI", sans-serif; font-size: 12px; }
    .detalle-container { display: flex; align-items: stretch; }
    .detalle-mini { flex-grow: 1; background: #f8f9fa; border: 1px solid #e0e0e0; border-left: 3px solid #0069d9; border-radius: 6px 0 0 6px; padding: 6px 10px; }
    .td-color { width: 25px; border-radius: 0 6px 6px 0; }
    .shimmer-td { background-color: var(--foil-color); position: relative; overflow: hidden; }
    .shimmer-td::after { content: ""; position: absolute; top: -100%; left: 0; width: 100%; height: 200%; background: linear-gradient(to bottom, rgba(255,255,255,0.05) 0%, rgba(230,230,230,0.25) 40%, rgba(240,240,240,0.4) 50%, rgba(230,230,230,0.25) 60%, rgba(255,255,255,0.05) 100%); animation: shimmer-slide 4s infinite ease-in-out; }
    .emboss-td { background: #e3e6ea; animation: emboss-pulse 2.5s ease-in-out infinite; }
    @keyframes emboss-pulse { 0%, 100% { box-shadow: inset -1px -1px 1px rgba(255,255,255,0.8), inset 2px 2px 3px rgba(0,0,0,0.05); } 50% { box-shadow: inset -2px -2px 2px rgba(255,255,255,0.9), inset 3px 3px 5px rgba(0,0,0,0.08); } }
    .deboss-td { background: #dde1e5; animation: deboss-pulse 2.5s ease-in-out infinite; }
    @keyframes deboss-pulse { 0%, 100% { box-shadow: inset 2px 2px 3px rgba(0,0,0,0.15), inset -1px -1px 1px rgba(255,255,255,0.4); } 50% { box-shadow: inset 3px 3px 5px rgba(0,0,0,0.2), inset -2px -2px 2px rgba(255,255,255,0.6); } }
    @keyframes shimmer-slide { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
    .detalle-mini .etiqueta { font-weight: 600; font-size: 11px; color: #333; margin-bottom: 4px; }
    .detalle-mini .campos { display: flex; gap: 6px; }
    .detalle-mini input { padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 4px; width: 100%; min-width: 80px; }
</style>`;
