// Source Client Script: Generador de Descripción en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh: function(frm) {
        actualizar_html_descripcion(frm);
        registrar_cambios(frm);
    },
    validate: function(frm) {
        actualizar_html_descripcion(frm);
    },
    material: function(frm) {
        if (frm.doc.material) {
            frappe.db.get_value('Raw Material', frm.doc.material, 'description')
                .then(r => {
                    const descripcion = r.message.description || "";
                    frm.set_value('descripcion_material', descripcion);
                    actualizar_html_descripcion(frm);
                });
        } else {
            frm.set_value('descripcion_material', '');
            actualizar_html_descripcion(frm);
        }
    },

    requiere_troquelado: function(frm) {
        actualizar_html_descripcion(frm);
    },
    requiere_laminado: function(frm) {
        actualizar_html_descripcion(frm);
    },
    requiere_barnizado: function(frm) {
        actualizar_html_descripcion(frm);
    },
    requiere_pegado: function(frm) {
        actualizar_html_descripcion(frm);
    }
});


// Registra eventos de cambio para actualizar on the fly
function registrar_cambios(frm) {
    const campos_relevantes = [
        "ancho_producto",
        "alto_producto",
        "requiere_troquelado",
        "requiere_laminado",
        "tipo_de_laminado",
        "requiere_barnizado",
        "tipo_de_barnizado",
        "requiere_pegado",
        "tipo_producto",
        "material",
        "tipo_de_pegado"
    ];

    campos_relevantes.forEach(campo => {
        if (!frm.fields_dict[campo] || frm.fields_dict[campo].onchange_hooked) return;

        frappe.ui.form.on(frm.doctype, campo, function(frm) {
            actualizar_html_descripcion(frm);
        });

        frm.fields_dict[campo].onchange_hooked = true;
    });
}

// Función principal para generar y mostrar descripción
async function actualizar_html_descripcion(frm) {
    console.log("⏳ Ejecutando actualización de descripción desde el servidor...");

    try {
        const r = await frappe.call({
            method: "igcaribe.api.get_analisis_descripcion",
            args: { ...frm.doc }
        });

        const resultado = r.message || {};
        const descripcion = resultado.codigo || "";
        const titulo = resultado.product_title || "";

        console.log("✅ Descripción:", descripcion);
        console.log("✅ Título:", titulo);

        frm.set_value("description", descripcion);
        frm.set_value("item_name", titulo);

        if (!descripcion || descripcion.trim() === "") {
            frm.set_df_property("html_descripcion", "options", `
                <div style="color: orange;">
                    (No se generó ninguna descripción. Verifica si faltan campos clave).
                </div>
            `);
            return;
        }

        const html = `
            <div style="
                border-left: 6px solid #ff7300;
                background: #fff8f2;
                padding: 12px 16px;
                margin: 10px 0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.5;
                color: #4a2e00;
                border-radius: 6px;
                box-shadow: 0 0 3px rgba(0,0,0,0.05);
            ">
                <div style="font-weight: 600; margin-bottom: 6px; color: #d35400;">
                    Descripción del Producto
                </div>
                <div>${frappe.utils.escape_html(descripcion).replace(/\n/g, "<br>")}</div>
            </div>
        `;

        frm.set_df_property("html_descripcion", "options", html);
    } catch (error) {
        console.error("❌ Error generando HTML de descripción:", error);
        frm.set_df_property("html_descripcion", "options", `<span style="color:red;">${error}</span>`);
    }
}
