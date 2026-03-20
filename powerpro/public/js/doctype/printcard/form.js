frappe.ui.form.on("PrintCard", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("Download Remote PDF"), async () => {
			await requestRemotePdf(frm);
		}, __("Actions"));
	},
});

async function requestRemotePdf(frm) {
	frappe.dom.freeze(__("Requesting remote PDF..."));

	try {
		const response = await frappe.call({
			method: "powerpro.controllers.printcard.client.request_remote_printcard_pdf",
			args: {
				printcard_name: frm.doc.name,
			},
		});

		const data = response.message || {};
		if (!data.ok || !data.pdf_base64) {
			throw new Error(__("Remote service did not return a valid PDF."));
		}

		downloadBase64Pdf(data.pdf_base64, data.filename || `${frm.doc.name}.pdf`);
		frappe.show_alert({
			message: __("Remote PDF downloaded."),
			indicator: "green",
		});
	} catch (error) {
		frappe.msgprint({
			title: __("Remote PDF Error"),
			message: error.message || __("Failed to download remote PDF."),
			indicator: "red",
		});
	} finally {
		frappe.dom.unfreeze();
	}
}

function downloadBase64Pdf(base64Content, filename) {
	const binary = atob(base64Content);
	const length = binary.length;
	const bytes = new Uint8Array(length);

	for (let i = 0; i < length; i++) {
		bytes[i] = binary.charCodeAt(i);
	}

	const blob = new Blob([bytes], { type: "application/pdf" });
	const link = document.createElement("a");
	const objectUrl = URL.createObjectURL(blob);

	link.href = objectUrl;
	link.download = filename.endsWith(".pdf") ? filename : `${filename}.pdf`;
	document.body.appendChild(link);
	link.click();
	link.remove();
	URL.revokeObjectURL(objectUrl);
}
