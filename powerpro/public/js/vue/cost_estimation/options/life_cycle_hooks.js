// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */


export default {
	mounted() {
        this.load_power_pro_settings();
        
        this.load_coating_type_options();
        this.load_lamination_type_options();
        this.load_gluing_type_options();
        this.load_foil_color_options();

		this.mount_product_type_field();
		this.mount_raw_material_field();
    },
}