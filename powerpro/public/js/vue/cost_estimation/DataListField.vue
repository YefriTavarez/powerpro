<template>
	<label :for="field_id">
		{{ label }}
	</label>
	<input
		class="form-control"
		:list="list_id"
		:id="field_id"
		:name="name_id"
		type="text"
		@change="after_change"
		v-model="value"
	/>

	<datalist :id="list_id">
		<option
			v-for="option in options"
			:value="option.value"
		>{{ option.label }}</option>
	</datalist>
</template>

<script>
export default {
	props: {
		field_id: {
			type: String,
			required: true,
		},
		list_id: {
			type: String,
			required: true,
		},
		options: {
			type: Array,
			required: true,
		},
		name: {
			type: String,
			default: null,
		},
		label: {
			type: String,
			default: 'Select',
		},
		selected: {
			type: String,
			default: null,
		},
	},
	data() {
		return {
			value: this.selected,
			list_id: this.getRandomId(),
			field_id: this.getRandomId(),
			name_id: this.name || this.getRandomId(),
		}
	},
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
		after_change() {
			// validate the selected value
			if (this.options.find(option => option.value === this.value)) {
				this.value = null;
			}

			this.$emit('after_select', this.value);
		},
	},
};
</script>
