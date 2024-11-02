// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

<script>

// Standard Fields
import QtyField from "./components/std/QtyField.vue";
import RateField from "./components/std/RateField.vue";
import AmountField from "./components/std/AmountField.vue";
import SelectField from "./components/std/SelectField.vue";

// Custom Fields
import Dimension from "./components/custom/DimensionField.vue";
import PrintingTecnique from "./components/custom/PrintingTecniqueField.vue";
import ColorCount from "./components/custom/ColorCountField.vue";
// import RawMaterialController from "../../controllers/material_controller.js";

// import computed from "./options/computed.js";

export default {
  name: "CostEstimation",
  props: {
    frm: {
      type: Object,
      required: true,
    },
  },
  data() {
    const { doc } = this.frm;

    let form_data = {};
    try {
      form_data = JSON.parse(doc.data || "{}");
    } catch (e) {
      console.error(e);
    }

    return {
      quantity: 5,
      rate: 3,
      amount: 0,
      doc: { ...this.frm.doc },
      raw_material_specs: {},

      // Cost Estimation Fields
      form_data, // let this one be dynamic
      // form_data: {
      //   ancho_montaje: 0,
      //   alto_montaje: 0,
      //   ancho_material: 0,
      //   alto_material: 0,
      //   ancho_producto: 0,
      //   alto_producto: 0,
      //   tecnologia: "",

      //   // colors
      //   colores_procesos_tiro: 0,
      //   colores_pantones_tiro: 0,
      //   colores_especiales_tiro: 0,
      //   colores_procesos_retiro: 0,
      //   colores_pantones_retiro: 0,
      //   colores_especiales_retiro: 0,
      // },
    }
  },
  // computed,
  watch: {
    form_data: {
      handler(newVal, oldVal) {
        if (this.loading) {
          return this;
        }
        
        this.update_data();
      },
      deep: true,
    },
  },
  methods: {
    fetch_raw_material_specs() {
      this.material_controller.fetch_raw_material_specs(this.frm.doc.raw_material);
    },
    calculate_cost() {
      // this.amount = flt(this.quantity) * flt(this.rate);
      // // this.$emit("update:amount", this.amount);
      // // this.$refs.amt.set_amount(this.amount);
      // const { $refs: refs } = this;
      // refs.amt.set_amount(this.amount);
    },
    update_data() {
      const data = JSON.stringify(this.form_data, null, 4);
      this.frm.set_value("data", data);
    },
    after_color_select(fieldname, value) {
      this.form_data[fieldname] = value;
      this.update_data();
    }
  },
  components: {
    QtyField,
    RateField,
    AmountField,
    SelectField,
    Dimension,
    PrintingTecnique,
    ColorCount,
  }
}
</script>

<template>
  <div data-component="cost-estimation">
    <!-- Tamaño Montaje:
    Tamaño Material:
    Tamaño Producto Final:

    Tecnologia Impresión:
        Digital (Pendiente a desarrollar)
        Offset -->

    <div class="row">
      <div class="form-column col-sm-6">
        <h3>Dimensiones</h3>
        <dimension
          label="Tamaño Montaje"
          :width="form_data.ancho_montaje"
          :height="form_data.alto_montaje"
          @on_change="({ width: ancho_montaje, height: alto_montaje }) => form_data = { ...form_data, ancho_montaje, alto_montaje }"
        />
        <dimension
          label="Tamaño Material"
          :width="form_data.ancho_material"
          :height="form_data.alto_material"
          @on_change="({ width: ancho_material, height: alto_material }) => form_data = { ...form_data, ancho_material, alto_material }"
        />
      </div>
      <div class="form-column col-sm-6">
        <dimension
          label="Tamaño Producto"
          :width="form_data.ancho_producto"
          :height="form_data.alto_producto"
          @on_change="({ width: ancho_producto, height: alto_producto }) => form_data = { ...form_data, ancho_producto, alto_producto }"
        />
      </div>
    </div>

    <div class="row">
      <div class="form-column col-sm-6">
        <h3>Tecnología de Impresión</h3>
        <printing-tecnique
          label="Tecnología"
          :selected="form_data.tecnologia"
          @after_select="value => form_data.tecnologia = value"
        />
      </div>
    </div>

    <hr>
    <div class="row">
      <div class="form-column col-sm-6"></div>
    </div>

    <section>
      <h4>Colores</h4>
      <hr />
      <div class="row">
        <div class="form-column col-sm-6">
          <color-count
            label="Colores Procesos Tiro"
            :selected="form_data.colores_procesos_tiro" :only_numbers="false"
            @after_select="value => form_data.colores_procesos_tiro = value"
          />
          <color-count
            label="Colores Pantones Tiro"
            :selected="form_data.colores_pantones_tiro"
            @after_select="value => form_data.colores_pantones_tiro = value"
          />
          <color-count
            label="Colores Especiales Tiro"
            :selected="form_data.colores_especiales_tiro"
            @after_select="value => form_data.colores_especiales_tiro = value"
          />
        </div>
        <div class="form-column col-sm-6">
          <color-count
            label="Colores Procesos Retiro"
            :selected="form_data.colores_procesos_retiro" :only_numbers="false"
            @after_select="value => form_data.colores_procesos_retiro = value"
          />
          <color-count
            label="Colores Pantones Retiro"
            :selected="form_data.colores_pantones_retiro"
            @after_select="value => form_data.colores_pantones_retiro = value"
          />
          <color-count
            label="Colores Especiales Retiro"
            :selected="form_data.colores_especiales_retiro"
            @after_select="value => form_data.colores_especiales_retiro = value"
          />
        </div>
      </div>
    </section>
    
  </div>
</template>