// Source Client Script: Filtrar Material por Tipo de Producto Seleccionado en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    tipo_producto(frm) {
        if (!frm.doc.tipo_producto) return;

        frappe.db.get_doc('Product Type', frm.doc.tipo_producto).then(product_type => {
            // Extraer los materiales de la tabla hija "Raw Materials"
            const materiales = (product_type.raw_materials || [])
                .map(row => row.raw_materials)
                .filter(Boolean); // Elimina vacíos o nulos

            if (materiales.length === 0) {
                frm.set_query('material', () => ({})); // sin filtro
                frm.set_value('material', null);
                return;
            }

            // Aplicar filtro dinámico en el campo "material"
            frm.set_query('material', () => ({
                filters: [['name', 'in', materiales]]
            }));

            // Limpiar si el valor actual no es válido
            if (frm.doc.material && !materiales.includes(frm.doc.material)) {
                frm.set_value('material', null);
            }
        });
    }
});
