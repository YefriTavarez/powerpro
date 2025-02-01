// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.ui.form.ControlSignature.prototype.make_pad = function() {
	let width = this.body.width();

	if (width > 0 && !this.$pad) {
		this.$pad = this.body
			.jSignature({
				height: 203,
				color: "#0039A6",
				decorColor: "#000000",
				"decor-color": "#000000",
				width: 500,
				lineWidth: 2,
				// signatureLine: false,
				backgroundColor: "var(--control-bg)",
			})
			.on("change", this.on_save_sign.bind(this));
		this.load_pad();
		this.$reset_button_wrapper = $(`
				<div class="signature-btn-row">
					<a href="#" type="button" class="signature-reset btn icon-btn">
						${frappe.utils.icon("es-line-reload", "sm")}
					</a>
				</div>
			`)
			.appendTo(this.$pad)
			.on("click", ".signature-reset", () => {
				this.on_reset_sign();
				return false;
			});
		this.refresh_input();
	}
};