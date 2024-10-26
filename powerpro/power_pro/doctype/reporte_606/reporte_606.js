frappe.ui.form.on("Reporte 606", {
	onload: function(frm) {
		frm.set_value("from_date", frappe.datetime.month_start());
		frm.set_value("to_date", frappe.datetime.month_end());
		frm.disable_save();
	},

	refresh: function(frm) {
		frm.trigger("render_summary");
	},

	from_date: function(frm) {
		frm.trigger("render_summary");
	},

	to_date: function(frm) {
		frm.trigger("render_summary");
	},

	render_summary: function(frm) {
		const { doc } = frm;
		const wrapper = frm.fields_dict.summary.$wrapper;
		let summary_data = {};
	
		const method = "powerpro.power_pro.doctype.reporte_606.reporte_606.get_summary_data";
		const args = {
			from_date: doc.from_date,
			to_date: doc.to_date
		};
	
		if (!doc.from_date || !doc.to_date) {
			wrapper.find("#summary").remove();
			return; // No data to show
		}
	
		const callback = function(response) {
			if (response.message) {
				summary_data = response.message;
				const fieldtype = "Currency";
				const subtotal = frappe.format(summary_data.subtotal, { fieldtype: fieldtype });
				const itbis = frappe.format(summary_data.itbis, { fieldtype: fieldtype });
	
				let summary_div = wrapper.find("#summary");
				if (summary_div.length > 0) {
					// Update the values
					summary_div.find("td").eq(0).html(subtotal);
					summary_div.find("td").eq(1).html(itbis);
	
					// Center the values
					summary_div.find("td").eq(0).find("div").css("text-align", "center");
					summary_div.find("td").eq(1).find("div").css("text-align", "center");
				} else {
					const summary_html = `
						<div id="summary" class="row" style="padding: 10px">
							<style>
								#summary table.table-condensed th,
								#summary table.table-condensed td {
									text-align: center !important;
								}
								#summary h4 {
									text-align: center;
								}
							</style>
							<h2>${__("Summary")}</h2>
							<table class="table table-condensed">
								<thead>
									<tr>
										<th>${__("SUBTOTAL")}</th>
										<th>${__("ITBIS")}</th>
									</tr>
								</thead>
								<tbody>
									<tr>
										<td>${subtotal}</td>
										<td>${itbis}</td>
									</tr>
								</tbody>
							</table>
						</div>
					`;
	
					wrapper.append(summary_html);

					wrapper.find("#summary td").eq(0).find("div").css("text-align", "center");
					wrapper.find("#summary td").eq(1).find("div").css("text-align", "center");
				}
			}
		}
		frappe.call({ method, args, callback });
	},
		

	descargar_reporte: function(frm){
		var file_url = __("/api/method/powerpro.power_pro.doctype.reporte_606.reporte_606.get_file_address?from_date={0}&to_date={1}&file_type=csv", 
			[frm.doc.from_date, frm.doc.to_date]);

		window.open(file_url);
	},

	descargar_reporte_txt: function(frm) {
        var file_url = __("/api/method/powerpro.power_pro.doctype.reporte_606.reporte_606.get_file_address?from_date={0}&to_date={1}&file_type=txt", 
            [frm.doc.from_date, frm.doc.to_date]);

        window.open(file_url);
    }
});

