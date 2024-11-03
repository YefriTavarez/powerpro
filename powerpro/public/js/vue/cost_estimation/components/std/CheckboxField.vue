<script>
export default {
	props: {
		label: {
			type: String,
			default: __("Checkbox"),
		},
		initial_value: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			id: this.getRandomId(),
			value: this.initial_value,
		}
	},
	watch: {
		value(newVal, oldVal) {
			if (newVal === oldVal) return;
			this.$emit("after_select", this.value);
		},
	},
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
	},
}
</script>

<template>
	<div class="form-group">
		<h3>
			<input
				type="checkbox"
				autocomplete="off"
				class="input-with-feedback"
				:data-fieldname="id"
				:id="id"
				v-model="value"
			/>
			<label :for="id">{{ label }}</label>
		</h3>
	</div>
</template>

<style scoped>
label {
	cursor: pointer;
	/* font-weight: bold; */
	/* text-transform: uppercase; */
	/* font-size: 1.2em; */
}

h3 {
	margin-top: 10px;
	margin-bottom: -10px;
}
</style>