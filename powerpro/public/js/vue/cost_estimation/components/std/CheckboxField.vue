<script>
export default {
	props: {
		label: {
			type: String,
			default: __("Checkbox"),
		},
		initial_value: {
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
	watch: {
		value(newVal, oldVal) {
			if (newVal === oldVal) return;
			this.$emit("after_select", this.value);
		},
	},
	methods: {
		getRandomId() {
			return Math.random().toString(36).substring(7);
		},
	},
}
</script>

<template>
	<div class="form-group">
		<h3 :for="id">
		<label class="switch">
			<input
				type="checkbox"
				autocomplete="off"
				class="input-with-feedback"
				:data-fieldname="id"
				:id="id"
				v-model="value"
			/>
			<span class="slider round"></span>
		</label>
		{{ label }}</h3>
	</div>
</template>

<style scoped>
label {
	cursor: pointer;
	/* font-weight: bold; */
	/* text-transform: uppercase; */
	/* font-size: 1.2em; */
}

h3 {
	margin-top: 10px;
	margin-bottom: -10px;
}

/* ======== */
.switch {
  position: relative;
  display: inline-block;
  width: 42.35px;
  height: 24px;
}

.switch input { 
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  -webkit-transition: .4s;
  transition: .4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18.35px;
  width: 18.35px;
  left: 2.5px;
  bottom: 3px;
  background-color: white;
  -webkit-transition: .4s;
  transition: .4s;
}
/* 
[data-theme=dark] input:checked + .slider {
  background-color: crimson;
}

[data-theme=light] input:checked + .slider {
  background-color: var(--btn-primary);
} */

[data-theme=dark] input:checked + .slider {
	background-color: #1f5193;
}

[data-theme=light] input:checked + .slider {
	background-color: #383c46;
}

[data-theme=dark] input:focus + .slider {
  box-shadow: 0 0 1px #1f5193;
}

[data-theme=light] input:focus + .slider {
  box-shadow: 0 0 1px #383c46;
}

input:checked + .slider:before {
  -webkit-transform: translateX(18.35px);
  -ms-transform: translateX(18.35px);
  transform: translateX(18.35px);
}

/* Rounded sliders */
.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}
</style>