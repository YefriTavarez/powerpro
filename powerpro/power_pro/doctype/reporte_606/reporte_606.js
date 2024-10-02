frappe.ui.form.on("Reporte 606", {
	onload: function(frm) {
		frm.set_value("from_date", frappe.datetime.month_start());
		frm.set_value("to_date", frappe.datetime.month_end());
		frm.disable_save();
	},
	descargar_reporte: function(frm){
		var file_url = __("/api/method/powerpro.power_pro.doctype.reporte_606.reporte_606.get_file_address?from_date={0}&to_date={1}", 
			[frm.doc.from_date, frm.doc.to_date]);

		window.open(file_url);
	}
});

