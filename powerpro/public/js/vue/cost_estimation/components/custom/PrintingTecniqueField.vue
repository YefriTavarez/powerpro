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
	props: {
		label: {
			type: String,
			default: __("Printing Tecnique"),
		},
		selected: {
			type: String,
			default: "",
		},
		read_only: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			options: [
				{ label: "Digital", value: "Digital" },
				{ label: "Offset", value: "Offset" },
				{ label: "N/A", value: "No Print" },
			],
			value: this.selected,
		}
	},
	methods: {
		after_select(newVal) {
			this.value = newVal;

			// this is being watched by the parent component via v-model and watchers
			this.$emit('update:selected', this.value);
		},
	},
	components: {
		SelectField,
	},
}
</script>