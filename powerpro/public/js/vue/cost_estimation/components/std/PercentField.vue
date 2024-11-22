<script>
let notified = true;
export default {
	props: {
		value: {
			type: Number,
			default: 0,
		},
		label: {
			type: String,
			default: "Percentage",
		},
	},
	data() {
		return {
			percentage: flt(this.value !== null? this.value: 30),
		}
	},
	watch: {
		percentage(newVal, oldVal) {
			const self = this;

			const value = flt(newVal);
			// validate percentage
			if (value < 0) {
				self.percentage = 0;
			} else if (value > 100) {
				self.percentage = 100;
			}

			// let timeoutId;
			// timeoutId = setTimeout(function() {
			// 	clearTimeout(timeoutId);

			// 	self.$emit("after_select", flt(self.percentage));
			// }, 1000);

			notified = false;
		},
	},
	methods: {
		clearValue() {
			this.percentage = 0;
		},
		_setValue(newVal) {
			this.percentage = newVal;
		},
		notifyUpdate() {
			if (notified) return;
			this.$emit("after_select", flt(this.percentage), this._setValue);
			notified = true;
		},
	},
}
</script>

<template>
	<div class="form-group">
		<label>{{ label }}</label>
		<div class="form-input-group">
			<span>%</span>
			<input @blur="notifyUpdate" v-model="percentage" type="text" />
			<span @click="clearValue">&times;</span>
		</div>
	</div>
</template>

<style scoped>
	div.form-group div.form-input-group {
		width: 100%;
		background-color: var(--control-bg);
		padding: 5px;
		margin: 5px auto;
		/* border: 1px solid #344; */
		border-radius: var(--border-radius-sm);
		display: flex;
		justify-content: space-between;
	}

	div.form-group div.form-input-group span:first-child {
		float: left;
		margin-left: 5px;
		margin-right: 5px;
		color: var(--text-color);
	}
		
	div.form-group div.form-input-group input {
		border: none;
		outline: none;
		background-color: transparent;
		color: var(--text-color);
		width: 90%;
	}
	
	div.form-group div.form-input-group span:last-child {
		cursor: pointer;
		color: var(--text-color);
		margin-left: 5px;
		margin-right: 5px;
	}
</style>
