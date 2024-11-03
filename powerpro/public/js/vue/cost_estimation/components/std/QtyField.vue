<template>
	<div class="form-group">
		<label :for="id">{{  label }}</label>
		<input
			type="text"
			class="form-control"
			v-model="value"
			@change="on_change"
			:id="id"
		/>
	</div>
</template>

<script>
export default {
	props: {
		initial_value: {
			type: Number,
			default: 0,
		},
		label: {
			type: String,
			default: "Quantity",
		},
	},
	data() {
		return {
			id: this.getRandomId(),
			value: this.initial_value,
		}
	},
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
		on_change() {
			this.value = parseFloat(this.value);
			this.$emit("after_select", this.value);
		},
	},
}
</script>