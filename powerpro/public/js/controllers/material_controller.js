// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

export default RawMaterialController = class {
	constructor({ vm }) {
		const { frm } = vm;
		const { doc } = frm;

		this.frm = frm;
		this.doc = doc;
		this.vm = vm;
	}

	fetch_raw_material_specs(material_id) {
		fetch(`/api/resource/Raw Material/${material_id}`)
			.then(response => response.json())
			.then(response => {
				this.vm.raw_material_specs = response.data;
			});
	}
}