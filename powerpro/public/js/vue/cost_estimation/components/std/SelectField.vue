<template>
	<div class="form-group">
		<label>{{ label }}</label>
		<div class="inner-form-group">
			<select :disabled="read_only" class="form-control" v-model="value">
				<option
					v-for="option in options"
					:value="option.value"
					:disabled="option.disabled"
				>
					{{ option.label || option.value }}
				</option>
			</select>
			<p v-if="help_text" class="text-muted">{{ help_text }}</p>
		</div>
	</div>
</template>

<script>
export default {
	props: {
		label: {
			type: String,
			default: __("Select"),
		},
		options: {
			type: Array,
			default: () => [],
		},
		selected: {
			type: String,
			default: "",
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
			value: this.selected,
		}
	},
	watch: {
		value(newVal, oldVal) {
			if (newVal === oldVal) return;

			// this is being watched by the parent component via v-model and watchers
			this.$emit("after_select", this.value);
		},
	},
}