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
			const { doc } = this.frm;
			// readonly if docstatus is not draft
			// or if edit_mode is not set and edition_requested is set
			// return doc.docstatus !== 0 || !Boolean(doc.edit_mode) && Boolean(doc.edition_requested);
			return !Boolean(doc.edit_mode);
		},
	},
	update_data(doc) {
		this.document = doc;
		console.log("update_data", doc);
	},
}
</script>