// Source Client Script: Redondear Ancho y Alto de Producto 1/8 Hacia Arriba - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    onload(frm) {
        redondear_al_octavo(frm, 'ancho_producto');
        redondear_al_octavo(frm, 'alto_producto');
    },
    validate(frm) {
        redondear_al_octavo(frm, 'ancho_producto');
        redondear_al_octavo(frm, 'alto_producto');
    },
    ancho_producto(frm) {
        redondear_al_octavo(frm, 'ancho_producto');
    },
    alto_producto(frm) {
        redondear_al_octavo(frm, 'alto_producto');
    }
});

function redondear_al_octavo(frm, campo) {
    let valor = frm.doc[campo];
    if (valor && typeof valor === 'number') {
        let redondeado = Math.ceil(valor * 8) / 8;
        if (redondeado !== valor) {
            frm.set_value(campo, redondeado);
        }
    }
}
