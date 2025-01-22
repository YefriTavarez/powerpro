// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.listview_settings["PrintCard"] = {
	onload(listview) {
		console.log("loading...");
	},
	get_indicator(doc) {
		return [__(doc.estado), {
			"Borrador": "red",
			"Pendiente": "orange",
			"Aprobado": "green",
			"Rechazado": "red",
		}[doc.estado], "estado,=," + doc.estado];
	},
};