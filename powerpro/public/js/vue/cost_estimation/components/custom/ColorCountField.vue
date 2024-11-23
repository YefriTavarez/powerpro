<template>
	<select-field
		:label="label"
		:options="options"
		@after_select="after_select"
		:selected="value"
		:read_only="read_only"	
	/>
</template>

<script>
import SelectField from "../std/SelectField.vue";
export default {
	name: "ColorCountField",
	props: {
		label: {
			type: String,
			default: __("Color Count"),
		},
		selected: {
			type: Number,
			default: 0,
		},
		only_numbers: {
			type: Boolean,
			default: true,
		},
		read_only: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			options: [
				{ label: "N/A", value: 0 },
				{ label: "1", value: 1 },
				{ label: "2", value: 2 },
				{ label: "3", value: 3 },
				{ label: this.only_numbers? "4": "Full Color", value: 4 },
			],
			value: this.selected,
		}
	},
	methods: {
		after_select(newVal) {
			this.value = newVal;
			this.$emit('after_select', this.value);
		},
	},
	components: {
		SelectField,
	},
}