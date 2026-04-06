// Source Client Script: Esconder Barra Lateral en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
	setup(frm) {
		 jQuery(`
            <style>
                div[id="page-Product Generator"] div.layout-side-section,
                div[id="page-Product Generator"] button.btn-reset.sidebar-toggle-btn {
                    display: none !important;
                }
            </style>
        `).appendTo(document.head);
	}
})
