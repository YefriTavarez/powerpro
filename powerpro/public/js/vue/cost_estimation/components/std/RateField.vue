<template>
	<div class="form-group">
		<label for="rate">{{  label }}</label>
		<input type="text" class="form-control" id="rate" v-model="rate">
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
			default: "Rate",
		},
	},
	data() {
		return {
			rate: this.value,
		}
	},
	watch: {
		rate(newVal, oldVal) {
			this.$emit('update:rate', this.rate);
		},
	},
}
</script>