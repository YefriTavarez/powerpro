<template>
	<div class="form-group">
		<label for="rate">{{  label }}</label>
		<input type="text" :readonly="read_only" class="form-control" id="rate" v-model="rate">
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
		read_only: {
			type: Boolean,
			default: false,
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


<!--
<div class="form-group">
	<label>Rate</label>
	<div class="form-input-group">
		<span>$</span>
		<input type="text" />
		<span>&times;</span>
	</div>
</div>
-->
