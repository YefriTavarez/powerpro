// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */


import { createApp } from 'vue';
import App from './cost_estimation/App.vue';

frappe.provide("power.ui");

power.ui.CostEstimationApp = class {
	constructor(frm, parent, dont_mount = false) {
		this.frm = frm;
		this.parent = parent;

		if (!dont_mount) {
			this.mount();
		}
	}

	mount() {
		const vm = createApp(App, {
			frm: this.frm,
			doc: this.frm.doc,
		});

		vm.mount(this.parent);
		this.vm = vm;
	}

	fetch_raw_material_specs() {
		// this.vm.fetch_raw_material_specs();
	}

	update(opts) {
		Object.assign(this, opts);
	}
}