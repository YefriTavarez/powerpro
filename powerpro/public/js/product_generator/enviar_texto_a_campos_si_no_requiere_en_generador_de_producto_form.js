// Source Client Script: Enviar Texto a Campos si no Requiere en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    requiere_troquelado: function (frm) {
        if (frm.doc.requiere_troquelado) {
            frm.set_value("corte", "Troquelado");
        } else {
            frm.set_value("corte", "Refilado");
        }
    },

    requiere_laminado: function (frm) {
        if (frm.doc.requiere_laminado) {
            frm.set_value("texto_laminado", "");
        } else {
            frm.set_value("texto_laminado", "No requiere Laminado");
        }
    },

    requiere_barnizado: function (frm) {
        if (frm.doc.requiere_barnizado) {
            frm.set_value("texto_barnizado", "");
        } else {
            frm.set_value("texto_barnizado", "No requiere Barnizado");
        }
    },

    requiere_pegado: function (frm) {
        if (frm.doc.requiere_pegado) {
            frm.set_value("texto_pegado", "");
        } else {
            frm.set_value("texto_pegado", "No requiere Pegado");
        }
    },

    refresh(frm) {
        // Aplicar lógicas también al cargar
        frm.trigger('requiere_troquelado');
        frm.trigger('requiere_laminado');
        frm.trigger('requiere_barnizado');
        frm.trigger('requiere_pegado');
    }
});
