<template>
	<div class="form-group">
		<label for="">{{ label }}</label>
		<div class="inner-form-group">
			<input
				type="text"
				data-fieldname="width"
				class="form-control"
				v-model="_width"
				@input="on_width_change"
			/>
			<span>&times;</span> 
			<input
				type="text"
				data-fieldname="height"
				class="form-control"
				v-model="_height"
				@input="on_height_change"
			/>
			<span>{{ uom }}</span>
		</div>
		<p class="text-muted">Ejemplo: 8.5 x 11 pulgadas</p>
	</div>
</template>

<script>
export default {
	props: {
		label: {
			type: String,
			default: __("Dimension"),
		},
		width: {
			type: String,
			default: "",
		},
		height: {
			type: String,
			default: "",
		},
		uom: {
			type: String,
			default: "in",
		},
	},
	data() {
		return {
			_width: this.width,
			_height: this.height,
		}
	},
	methods: {
		on_width_change(event) {
			const { value } = event.target;
			this._width = parseFloat(value);

			this.$emit("on_change", {
				width: this._width,
				height: this._height,
			});
		},
		on_height_change(event) {
			const { value } = event.target;
			this._height = parseFloat(value);

			this.$emit("on_change", {
				width: this._width,
				height: this._height,
			});
		}
	}
}
</script>

<style scoped>
.inner-form-group {
	display: flex;
}

.inner-form-group input {
	margin-right: 5px;
}
.inner-form-group input:nth-child(3) {
	margin-left: 5px;
}

.inner-form-group span {
	width: 20px;
	font-weight: bold;
	display: inline-block
}

.inner-form-group span:nth-child(2) {
	text-align: center;
}

.inner-form-group span:nth-child(3) {
	text-align: right;
}

.text-muted {
	font-size: 12px;
}

.text-muted::before {
	content: "Nota: ";
	font-weight: bold;
}

.text-muted::after {
	content: " (pulgadas)";
}



</style>
