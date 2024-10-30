<template>
  <div id="cost-estimation">
    <h4>{{ title }}</h4>
    <h5>Material</h5>
    <Material :raw_material_specs="raw_material_specs" />
    <p class="text-muted">{{ doc.raw_material }}</p>

    <form class="col col-sm-6">
      
      <h5>{{ amount }}</h5>
      <div class="form-group">
        <label for="quantity">Quantity</label>
        <input type="text" class="form-control" id="quantity" v-model="quantity">
      </div>
      <div class="form-group">
        <label for="rate">Rate</label>
        <input type="text" class="form-control" id="rate" v-model="rate">
      </div>
      <div class="form-group">
        <label for="amount">Amount (USD)</label>
        <input type="text" class="form-control" id="amount" v-model="amount">
      </div>
      <div class="form-group text-right">
        <button type="button" class="btn btn-primary" @click="calculate_cost">Calculate</button>
      </div>
    </form>
  </div>
</template>

<script>
import Material from "./Material.vue";
import RawMaterialController from "../../controllers/material_controller.js";
export default {
  name: 'CostEstimation',
  props: {
    frm: {
      type: Object,
      required: true,
    }
  },
  mounted() {
    this.material_controller = new RawMaterialController({ vm: this });

    if (this.frm.doc.raw_material) {
      this.fetch_raw_material_specs();
    }

    this.calculate_cost();
  },
  computed: {
    // amount_display() {
    //   return flt(this.quantity) * flt(this.rate);
    // },
    title() {
      return __("Cost Estimation Calculator");
    }
  },
  data() {
    return {
      quantity: 5,
      rate: 3,
      amount: 0,
      doc: { ...this.frm.doc },
      raw_material_specs: {},
    }
  },
  watch: {
    quantity(newVal, oldVal) {
      this.calculate_cost();
    },
    rate(newVal, oldVal) {
      this.calculate_cost();
    },
    amount(newVal, oldVal) {
      this.rate = flt(newVal) / flt(this.quantity);
    },
  },
  methods: {
    refresh() {
      // copy doc to prevent reactivity
      this.doc = { ...this.frm.doc };
    },
    fetch_raw_material_specs() {
      this.material_controller.fetch_raw_material_specs(this.frm.doc.raw_material);
    },
    calculate_cost() {
      this.amount = flt(this.quantity) * flt(this.rate);
      console.log(`Amount: ${this.amount}`);
    }
  },
  components: {
    Material,
  }
}
</script>
