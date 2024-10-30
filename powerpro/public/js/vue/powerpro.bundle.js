// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */


import { createApp } from 'vue';
import CostEstimation from './cost_estimation/CostEstimation.vue';

frappe.provide("power.ui");

power.ui.CostEstimation = class {
	constructor(frm, parent, dont_mount = false) {
		this.frm = frm;
		this.parent = parent;

		if (!dont_mount) {
			this.mount();
		}
	}

	mount() {
		this.vm = createApp(
			CostEstimation, 
			{
				frm: this.frm,
			}
		).mount(this.parent);
	}

	fetch_raw_material_specs() {
		this.vm.fetch_raw_material_specs();
	}
}