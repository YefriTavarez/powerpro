<template>
	<div class="form-group">
		<label :for="id">{{  label }}</label>
		<input
			type="text"
			class="form-control"
			v-model="value"
			@change="on_change"
			:id="id"
			:readonly="read_only"
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
		enforce_integer: {
			type: Boolean,
			default: false,
		},
		format_with_comma: {
			type: Boolean,
			default: false,
		},
		read_only: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			id: this.getRandomId(),
			value: flt(this.initial_value).toLocaleString(),
		}
	},
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
		on_change() {
			// this.value = parseFloat(this.value);
			// this.$emit("after_select", this.value);

			let _value = flt(this.value);

			if (this.enforce_positive && _value < 0) {
				_value = 0;
			}

			if (this.enforce_integer) {
				_value = parseInt(_value);
			}

			if (this.format_with_comma) {
				_value = _value.toLocaleString();
			}

			this.value = _value;

			this.$emit("after_select", _value);
		},
	},
}
</script>