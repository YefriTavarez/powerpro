<template>
	<div class="form-group">
		<label for="quantity">{{  label }}</label>
		<input type="text" class="form-control" id="quantity" v-model="quantity">
	</div>
</template>

<script>
export default {
	props: {
		value: {
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
			quantity: this.value,
		}
	},
	watch: {
		quantity(newVal, oldVal) {
			this.$emit('update:quantity', this.quantity);
		},
	},
}
</script>