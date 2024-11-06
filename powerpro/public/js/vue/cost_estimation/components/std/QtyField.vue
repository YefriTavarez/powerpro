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
		enforce_positive: {
			type: Boolean,
			default: false,
		},
		enfore_integer: {
			type: Boolean,
			default: false,
		},
		format_with_comma: {
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
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
		on_change() {
			// this.value = parseFloat(this.value);
			// this.$emit("after_select", this.value);

			const _value = flt(this.value);

			if (this.enforce_positive && _value < 0) {
				this.value = 0;
			}

			if (this.enfore_integer) {
				this.value = parseInt(_value);
			}

			if (this.format_with_comma) {
				this.value = _value.toLocaleString();
			}

			this.$emit("after_select", _value);
		},
	},
}
</script>