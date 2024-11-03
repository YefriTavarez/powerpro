// Copyright (c) 2024, Yefri Tavarez and contributors // For license
information, please see license.txt /* eslint-disable */

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
import CheckboxField from "./components/std/CheckboxField.vue";
import DataListField from './DataListField.vue'
// import RawMaterialController from "../../controllers/material_controller.js";

// import computed from "./options/computed.js";

export default {
    name: "CostEstimation",
    props: {
        frm: {
            type: Object,
            required: true,
        },
        document: {
            type: Object,
            required: true,
        },
    },
    data() {
        const { document: doc } = this;

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
            doc: this.document,
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
        };
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
            this.material_controller.fetch_raw_material_specs(
                this.frm.doc.raw_material,
            );
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
        },
        handle_relieve_dimension_change(index, width, height) {
            this.form_data[`ancho_elemento_relieve_${index}`] = width;
            this.form_data[`alto_elemento_relieve_${index}`] = height;
            this.update_data();
        },
        fetch_assets() {
            // Fetch:
            // - Foil colors
            // - Ink colors
        },
    },
    mounted() {
        this.fetch_assets();
    },
    components: {
    QtyField,
    RateField,
    AmountField,
    SelectField,
    Dimension,
    PrintingTecnique,
    ColorCount,
    CheckboxField,
    DataListField,
},
};
</script>

<template>
    <div data-component="cost-estimation">
        <section>
            <div class="row">
                <div class="px-3" style="width: 100%">
                    <h3>Dimensiones</h3>
                </div>
                <div class="form-column col-sm-6">
                    <dimension
                        label="Tamaño Montaje"
                        :width="form_data.ancho_montaje"
                        :height="form_data.alto_montaje"
                        @on_change="
                            ({ width: ancho_montaje, height: alto_montaje }) =>
                                (form_data = {
                                    ...form_data,
                                    ancho_montaje,
                                    alto_montaje,
                                })
                        "
                    />
                    <dimension
                        label="Tamaño Material"
                        :width="form_data.ancho_material"
                        :height="form_data.alto_material"
                        @on_change="
                            ({
                                width: ancho_material,
                                height: alto_material,
                            }) =>
                                (form_data = {
                                    ...form_data,
                                    ancho_material,
                                    alto_material,
                                })
                        "
                    />
                </div>
                <div class="form-column col-sm-6">
                    <dimension
                        label="Tamaño Producto"
                        :width="form_data.ancho_producto"
                        :height="form_data.alto_producto"
                        @on_change="
                            ({
                                width: ancho_producto,
                                height: alto_producto,
                            }) =>
                                (form_data = {
                                    ...form_data,
                                    ancho_producto,
                                    alto_producto,
                                })
                        "
                    />
                </div>
            </div>
        </section>

        <section>
            <hr />
            <div class="row">
                <div class="px-3" style="width: 100%">
                    <h3>Tecnología de Impresión</h3>
                </div>
                <div class="form-column col-sm-6">
                    <printing-tecnique
                        label="Tecnología"
                        :selected="form_data.tecnologia"
                        @after_select="
                            (value) => (form_data.tecnologia = value)
                        "
                    />
                </div>
            </div>
            <div class="row">
                <div class="form-column col-sm-6">
                    <!-- empty column -->
                </div>
            </div>
        </section>


        <section v-if="false">
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Pre-corte??"
                        :initial_value="form_data.incluye_precorte"
                        @after_select="
                            (value) => (form_data.incluye_precorte = value)
                        "
                    />

                    <select-field
                        label="Tipo de Pre-corte"
                        :options="[
                            { value: 'Guillotina' },
                            { value: 'Convertidora de Material', disabled: form_data.tecnologia !== 'Offset' },
                        ]"
                        :selected="form_data.tipo_precorte"
                        @after_select="
                            (value) => (form_data.tipo_precorte = value)
                        "
                        v-if="form_data.incluye_precorte"
                    />
                </div>
            </div>
        </section> 

        <section>
            <hr />
            <div class="row" v-if="form_data.tecnologia ==='Offset'">
                <div class="px-3" style="width: 100%">
                    <h3>Colores</h3>
                </div>
                <div class="form-column col-sm-6">
                    <select-field
                        label="Cantidad de Tintas"
                        :options="[
                            { value: 1, label: '1' },
                            { value: 2, label: '2' },
                            { value: 3, label: '3' },
                            { value: 4, label: '4' },
                            { value: 5, label: '5' },
                            { value: 6, label: '6' },
                            { value: 7, label: '7' },
                            { value: 8, label: '8' },
                        ]"
                        :selected="form_data.cantidad_de_tintas"
                        @after_select="
                            (value) => (form_data.cantidad_de_tintas = parseFloat(value))
                        "
                    />


                    <!-- <color-count
                        label="Colores Procesos Tiro"
                        :selected="form_data.colores_procesos_tiro"
                        :only_numbers="false"
                        @after_select="
                            (value) =>
                                (form_data.colores_procesos_tiro = value)
                        "
                    />
                    <color-count
                        label="Colores Pantones Tiro"
                        :selected="form_data.colores_pantones_tiro"
                        @after_select="
                            (value) =>
                                (form_data.colores_pantones_tiro = value)
                        "
                    />
                    <color-count
                        label="Colores Especiales Tiro"
                        :selected="form_data.colores_especiales_tiro"
                        @after_select="
                            (value) =>
                                (form_data.colores_especiales_tiro = value)
                        "
                    /> -->
                </div>
                <div class="form-column col-sm-6">
                    <!-- :field_id="`tinta_selccionada_${index}`"
                    :list_id="`listado_de_tintas_${index}`" -->
                    
                    <div v-for="index in form_data.cantidad_de_tintas">
                        <label for="">Tinta {{ index }}</label>
                        <input
                            type="text"
                            class="form-control"
                            :list="`listado_de_tintas_${index}`"
                            v-model="form_data[`tinta_selccionada_${index}`]"
                        />

                        
                    </div>

                    <!-- <color-count
                        label="Colores Procesos Retiro"
                        :selected="form_data.colores_procesos_retiro"
                        :only_numbers="false"
                        @after_select="
                            (value) =>
                                (form_data.colores_procesos_retiro = value)
                        "
                    />
                    <color-count
                        label="Colores Pantones Retiro"
                        :selected="form_data.colores_pantones_retiro"
                        @after_select="
                            (value) =>
                                (form_data.colores_pantones_retiro = value)
                        "
                    />
                    <color-count
                        label="Colores Especiales Retiro"
                        :selected="form_data.colores_especiales_retiro"
                        @after_select="
                            (value) =>
                                (form_data.colores_especiales_retiro = value)
                        "
                    /> -->
                </div>
            </div>
            <div class="row" v-else>
                <div class="form-column col-sm-6">
                    <p class="full-color-text" style="color: greenyellow">
                        Full Color
                    </p>
                </div>
            </div>
        </section>

        <section v-if="form_data.tecnologia ==='Offset'">
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Barnizado?"
                        :initial_value="form_data.incluye_barnizado"
                        @after_select="
                            (value) => (form_data.incluye_barnizado = value)
                        "
                    />

                    <select-field
                        label="Tipo de Barnizado"
                        :options="[
                            { value: 'Barnizado Base en Agua Brillo (in2)' },
                            { value: 'Barnizado Base en Agua Mate' },
                            { value: 'Barnizado Base en Aceite Brillo' },
                            { value: 'Barnizado Base en Aceite Mate' },
                            { value: 'Barnizado Base en Aceite Combinado' },
                            { value: 'Barnizado UV Brillo' },
                            { value: 'Barnizado UV Mate' },
                            { value: 'Barnizado UV Combinado' },
                        ]"
                        :selected="form_data.tipo_barnizado"
                        @after_select="
                            (value) => (form_data.tipo_barnizado = value)
                        "
                        v-if="form_data.incluye_barnizado"
                    />
                </div>
            </div>
        </section>

        <section v-if="form_data.tecnologia ==='Offset'">
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Troquelado?"
                        :initial_value="form_data.incluye_troquelado"
                        @after_select="
                            (value) => (form_data.incluye_troquelado = value)
                        "
                    />

                    <p v-if="form_data.incluye_troquelado" class="text-muted">
                        Este producto es troquelado.
                    </p>

                    <p v-else class="text-muted">
                        Este producto es refilado.
                    </p>
                </div>
            </div>
        </section>

        <section>
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Laminado?"
                        :initial_value="form_data.incluye_laminado"
                        @after_select="
                            (value) => (form_data.incluye_laminado = value)
                        "
                    />
                </div>
            </div>
        </section>

        <section v-if="form_data.tecnologia ==='Offset'">
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Relieve?"
                        :initial_value="form_data.incluye_relieve"
                        @after_select="
                            (value) => (form_data.incluye_relieve = value)
                        "
                    />

                    <select-field
                        label="Tipo de Relieve"
                        :options="[
                            { value: 'Repujado' },
                            { value: 'Estampado' },
                        ]"
                        :selected="form_data.tipo_de_relieve"
                        @after_select="
                            (value) => (form_data.tipo_de_relieve = value)
                        "
                        v-if="form_data.incluye_relieve"
                    />

                    <select-field
                        label="Color de Lamina"
                        :options="[
                            { value: 'Dorado' },
                            { value: 'Papel' },
                            { value: 'Cartón' },
                            { value: 'Plástico' },
                        ]"
                        :selected="form_data.tipo_de_material_relieve"
                        @after_select="
                            (value) => (form_data.tipo_de_material_relieve = value)
                        "
                        v-if="form_data.incluye_relieve"
                    />

                    <select-field
                        label="Cantidad de Elementos"
                        :options="[
                            { value: 1, label: '1' },
                            { value: 2, label: '2' },
                            { value: 3, label: '3' },
                            { value: 4, label: '4' },
                            { value: 5, label: '5' },
                        ]"
                        :selected="form_data.cantidad_de_elementos_en_relieve"
                        @after_select="
                            (value) => (form_data.cantidad_de_elementos_en_relieve = value)
                        "
                        v-if="form_data.incluye_relieve"
                    />

                </div>
                    <div class="form-column col-sm-6">
                    <dimension
                        v-for="index in form_data.cantidad_de_elementos_en_relieve"
                        :label="`Tamaño del Elemento ${index}`"
                        :width="form_data[`ancho_elemento_relieve_${index}`]"
                        :height="form_data[`alto_elemento_relieve_${index}`]"
                        @on_change="({ width, height }) => handle_relieve_dimension_change(index, width, height)"
                        v-if="form_data.incluye_relieve"
                    />
                </div>
            </div>
        </section>

        <section>
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Utilidad?"
                        :initial_value="form_data.incluye_utilidad"
                        @after_select="
                            (value) => (form_data.incluye_utilidad = value)
                        "
                    />

                    <select-field
                        label="Tipo de Utilidad"
                        :options="[{ value: 'Cinta Doble Cara' }]"
                        :selected="form_data.tipo_de_utilidad"
                        @after_select="
                            (value) => (form_data.tipo_de_utilidad = value)
                        "
                        v-if="form_data.incluye_utilidad"
                    />
                    <!--
                    Cantidad de puntos
                    Tamaño de los puntos (ancho y alto) con valores fijos
                    Ancho: 0.5, 0.75, 1 in
                    Largo: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5 in
                    -->

                    <qty-field
                        label="Cantidad de Puntos"
                        :initial_value="form_data.cinta_doble_cara_cantidad_de_puntos"
                        @after_select="
                            (value) => (form_data.cinta_doble_cara_cantidad_de_puntos = value)
                        "
                        v-if="form_data.tipo_de_utilidad && form_data.tipo_de_utilidad === 'Cinta Doble Cara'"
                    />

                    <dimension
                        label="Tamaño de los Puntos"
                        :width="form_data.ancho_punto"
                        :height="form_data.alto_punto"
                        :using_options="true"
                        :options="{
                            width: [
                                { value: 0.5, label: '0.5' },
                                { value: 0.75, label: '0.75' },
                                { value: 1, label: '1' },
                            ],
                            height: [
                                { value: 0.5, label: '0.5' },
                                { value: 1, label: '1' },
                                { value: 1.5, label: '1.5' },
                                { value: 2, label: '2' },
                                { value: 2.5, label: '2.5' },
                                { value: 3, label: '3' },
                                { value: 3.5, label: '3.5' },
                                { value: 4, label: '4' },
                                { value: 4.5, label: '4.5' },
                                { value: 5, label: '5' },
                            ],
                        }"
                        @on_change="
                            ({ width: cinta_doble_cara_ancho_punto, height: cinta_doble_cara_alto_punto }) =>
                                (form_data = {
                                    ...form_data,
                                    cinta_doble_cara_ancho_punto,
                                    cinta_doble_cara_alto_punto,
                                })
                        "
                        v-if="form_data.tipo_de_utilidad && form_data.tipo_de_utilidad === 'Cinta Doble Cara'"
                    />
                    
                </div>
            </div>
        </section>

        <section>
            <hr />
            <div class="row">
                <div class="form-column col-sm-6">
                    <checkbox-field
                        label="Incluye Pegado?"
                        :initial_value="form_data.incluye_pegado"
                        @after_select="
                            (value) => (form_data.incluye_pegado = value)
                        "
                    />

                    <select-field
                        label="Tipo de Pegado"
                        :options="[
                            { value: 'Fondo Automático' },
                            { value: 'Fondo Recto' },
                            { value: 'Fondo Automático con Ventana' },
                            { value: 'Fondo Recto con Ventana' },
                        ]"
                        :selected="form_data.tipo_de_utilidad"
                        @after_select="
                            (value) => (form_data.tipo_de_utilidad = value)
                        "
                        v-if="form_data.incluye_pegado"
                    />
                </div>
            </div>
        </section>

        <section>
            <hr />
            <div class="row">
                <div class="px-3" style="width: 100%">
                    <h3>Empaque</h3>
                </div>
                <div class="form-column col-sm-6">
                    <select-field
                        label="Tipo de Empaque"
                        :options="[
                            { value: 'Corrugado' },
                            { value: 'Papel' },
                            { value: 'Plástico' },
                        ]"
                        :selected="form_data.tipo_de_empaque"
                        @after_select="
                            (value) => (form_data.tipo_de_empaque = value)
                        "
                    />
                </div>
            </div>
        </section>
    </div>
</template>

<style scoped>
.full-color-text {
  display: inline-block;
  font-size: 48px;
  line-height: 1;
  font-weight: black;
  background: linear-gradient(to top left,#df0781,#e45508,#ffe83f,#07d664,#70e2ff,#6f0ac7);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>