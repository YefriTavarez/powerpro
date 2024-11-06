// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

export default {
	form_data: {
		handler(newVal, oldVal) {
			if (this.loading) {
				return this;
			}

			this.update_data();
		},
		deep: true,
	},
};