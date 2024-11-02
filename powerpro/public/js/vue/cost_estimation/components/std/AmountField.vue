<template>
	<div class="form-group">
		<label for="amount">
			{{  label }}
		</label>
		<input
			type="text"
			class="form-control"
			v-model="amount"
		/>
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
			default: "Amount",
		},
	},
	data() {
		return {
			amount: 0,
		}
	},
	mounted() {
		this.amount = this.value;
	},
	watch: {
		amount(newVal, oldVal) {
			this.$emit(
				'update:amount', this.value
			);
		},
	},
	methods: {
		set_amount(value) {
			this.amount = value;
		}
	}
}
</script>