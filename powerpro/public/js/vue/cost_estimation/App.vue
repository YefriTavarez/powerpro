<template>
	<div class="app-wrapper">
		<cost-estimation-form
			:frm="frm"
			:document="document"
			ref="calculator"
			:readonly="readonly"
		/>
	</div>
</template>

<script>
import CostEstimationForm from "./CostEstimationForm.vue";
export default {
	name: 'CostEstimationApp',
	props: {
		frm: {
			type: Object,
			required: true,
		},
		doc: {
			type: Object,
			required: true,
		},
	},
	data() {
		return {
			document: this.doc,
		}
	},
	components: {
		CostEstimationForm,
	},
	computed: {
		readonly() {
			return this.frm.doc.docstatus === 1;
		},
	},
	update_data(doc) {
		this.document = doc;
		console.log("update_data", doc);
	},
}
</script>