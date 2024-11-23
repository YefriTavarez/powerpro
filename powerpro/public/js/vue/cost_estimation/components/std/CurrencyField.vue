<template>
	<div class="form-group">
		<label>{{ label }}</label>
		<div class="inner-form">
			<input type="text" :readonly="read_only" class="form-control" v-model="value" @input="onInput" />
			<p v-if="help_text" class="text-muted">{{ help_text }}</p>
		</div>
	</div>
</template>

<script>
export default {
	props: {
		label: {
			type: String,
			default: __("Currency"),
		},
		value: {
			type: Number,
			default: 0,
		},
		help_text: {
			type: String,
			default: null,
		},
		read_only: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			value: this.value,
		}
	},
	watch: {
		value(newVal, oldVal) {
			this.value = newVal;
			this.$emit('update:value', this.value);
		},
	},
	methods: {
		onInput(event) {
			const value = parseFloat(event.target.value);
			if (!isNaN(value)) {
				this.value = value;
			}
		}
	}
}
</script>
