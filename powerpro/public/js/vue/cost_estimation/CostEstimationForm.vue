// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

<script>
import props from "./options/props.js";
import computed from "./options/computed.js";
import methods from "./options/methods.js";
import components from "./options/components.js";
import watch from "./options/watch.js";
import data from "./options/data.js";
import life_cycle_hooks from "./options/life_cycle_hooks.js";

export default {
    name: "CostEstimation",
    props,
    data,
    watch,
    computed,
    methods,
    components,
    ...life_cycle_hooks,
};
</script>

<template>
    <div
        class="frappe-control"
        data-fieldtype="HTML"
        data-fieldname="cost_estimation_app"
    >
        <div data-component="cost-estimation">
            <section>
                <div class="row">
                    <div ref="tipo_de_producto" class="col-sm-6">
                        <!-- <div
                            class="form-group" 
                        >
                            <label for="">Tipo de Producto</label>
                            <div class="input-group mb-3">
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="form_data.tipo_de_producto"
                                    @change="value => form_data.tipo_de_producto = value"
                                    :readonly="readonly"
                                />

                                <button
                                    class="btn btn-secondary"
                                    style="border-radius: 0; height: 28px"
                                    v-if="form_data.tipo_de_producto"
                                    @click="fetch_product_type_details(form_data.tipo_de_producto)"
                                    :disabled="readonly"
                                >
                                    {{ "Refrescar" }}
                                </button>

                                <button
                                    class="btn btn-primary"
                                    style="border-top-left-radius: 0; border-bottom-left-radius: 0; height: 28px"
                                    @click="select_product_type()"
                                    :disabled="readonly"
                                >
                                    {{ !form_data.tipo_de_producto? "Seleccionar": "Cambiar" }}
                                </button>
                            </div>
                        </div> -->
                    </div>
                    <div ref="material" class="col-sm-6">
                        
                    </div>
                </div>
            </section>

            <section>
                <hr />
                <div class="row">
                    <div class="px-3" style="width: 100%">
                        <h3>Cantidad</h3>
                    </div>
                    <div class="form-column col-sm-4">
                        <qty-field
                            label="Cantidad"
                            :initial_value="form_data.cantidad_de_producto"
                            :enforce_positive="true"
                            :enforce_integer="true"
                            :format_with_comma="true"
                            @after_select="
                                (value) => (form_data.cantidad_de_producto = value)
                            "
                            :read_only="readonly"
                        />

                        <qty-field
                            label="Unidades en Montaje"
                            :initial_value="form_data.cantidad_montaje"
                            :enforce_positive="true"
                            :enforce_integer="true"
                            :format_with_comma="true"
                            @after_select="
                                (value) => (form_data.cantidad_montaje = value)
                            "
                            :read_only="readonly"
                        />
                    </div>

                    <div class="form-column col-sm-4">
                        <select-field
                            label="Porcentaje Adicional"
                            :selected="form_data.porcentaje_adicional"
                            @after_select="
                                (value) => (form_data.porcentaje_adicional = value)
                            "
                            :options="[
                                { value: 0, label: '0%' },
                                { value: 5, label: '5%' },
                                { value: 10, label: '10%' },
                                { value: 15, label: '15%' },
                            ]"
                            help_text="Este porcentaje se le sumará a la cantidad total."
                            :read_only="readonly"
                        />
                    </div>

                    <div class="form-column col-sm-4">
                       <div class="form-group">
                        <label for="cantidad_de_producto_con_adicional" class="for">
                            Cantidad con Adicional
                        </label>
                        <span
                            class="form-control"
                        >{{ cantidad_de_producto_con_adicional }}</span>
                       </div>
                    </div>
                </div>
            </section>


            <section>
                <hr>
                <div class="row">
                    <div class="px-3" style="width: 100%">
                        <h3>Dimensiones</h3>
                    </div>
                    <div class="form-column col-sm-4">
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
                            :read_only="readonly"
                        />
                    </div>
                    <div class="form-column col-sm-4">
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
                            :read_only="readonly"
                        />
                    </div>
                    <div class="form-column col-sm-4">
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
                            :read_only="readonly"
                        />
                    </div>
                </div>
            </section>


            <section v-if="false">
                <hr />
                <div class="row">
                    <div class="form-column col-sm-6">
                        <checkbox-field
                            label="Incluye Pre-corte?"
                            :initial_value="form_data.incluye_precorte"
                            @after_select="
                                (value) => (form_data.incluye_precorte = value)
                            "
                            :read_only="readonly"
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
                            :read_only="readonly"
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
                            :read_only="readonly"
                            @after_select="
                                (value) => (form_data.tecnologia = value)
                            "
                        />
                    </div>
                </div>
            </section>

            <section>
                <!-- <hr v-if="['Digital', 'Offset'].includes(form_data.tecnologia)" /> -->
                <div class="row">
                    <div class="px-3" style="width: 100%">
                        <h3>Colores</h3>
                    </div>
                    <div class="form-column col-sm-4">
                        <select-field
                            label="Cantidad de Tintas Tiro"
                            :options="[
                                { value: 0, label: '0' },
                                { value: 1, label: '1' },
                                { value: 2, label: '2' },
                                { value: 3, label: '3' },
                                { value: 4, label: '4' },
                                { value: 5, label: '5' },
                                { value: 6, label: '6' },
                                { value: 7, label: '7' },
                                { value: 8, label: '8' },
                            ]"
                            :selected="form_data.cantidad_de_tintas_tiro"
                            @after_select="
                                (value) => (form_data.cantidad_de_tintas_tiro = parseFloat(value))
                            "
                            :read_only="readonly"
                        />

                        <button
                            class="btn btn-primary btn-xs"
                            @click="load_full_color('frontside')"
                            :disabled="readonly"
                            v-if="form_data.cantidad_de_tintas_tiro >= 4"
                        >
                            Cargar Cuatricomía
                        </button>
                    </div>
                    <div class="form-column col-sm-8">
                        <!-- :field_id="`tinta_seleccionada_${index}`"
                        :list_id="`listado_de_tintas_${index}`" -->
                        
                        <div
                            class="form-group" 
                            v-for="index in form_data.cantidad_de_tintas_tiro"
                        >
                            <label for="">Tinta {{ index }}</label>
                            <div class="input-group mb-3">
                                <span
                                    class="input-group-text color" id=""
                                    :style="{ background: form_data[`hex_tinta_seleccionada_tiro_${index}`] || '#56565656'}"
                                ></span>
                                <input
                                    type="text"
                                    class="form-control"
                                    :list="`listado_de_tintas_tiro_${index}`"
                                    v-model="form_data[`tinta_seleccionada_tiro_${index}`]"
                                    @change="form_data[`hex_tinta_seleccionada_tiro_${index}`] = ''"
                                    @input="form_data[`tinta_seleccionada_tiro_${index}`] = ''"
                                    :readonly="readonly"
                                />

                                <button
                                    class="btn btn-primary"
                                    style="border-top-left-radius: 0; border-bottom-left-radius: 0; height: 28px"
                                    @click="select_ink_color('Tiro', `tinta_seleccionada_tiro_${index}`)"
                                    :disabled="readonly"
                                >
                                    Seleccionar
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="form-column col-sm-12">
                    <hr>
                    </div>
                    <div class="form-column col-sm-4">
                        <select-field
                            label="Cantidad de Tintas Retiro"
                            :options="[
                                { value: 0, label: '0' },
                                { value: 1, label: '1' },
                                { value: 2, label: '2' },
                                { value: 3, label: '3' },
                                { value: 4, label: '4' },
                                { value: 5, label: '5' },
                                { value: 6, label: '6' },
                                { value: 7, label: '7' },
                                { value: 8, label: '8' },
                            ]"
                            :selected="form_data.cantidad_de_tintas_retiro"
                            @after_select="
                                (value) => (form_data.cantidad_de_tintas_retiro = parseFloat(value))
                            "
                            :read_only="readonly"
                        />
                        <button
                            class="btn btn-primary btn-xs"
                            @click="load_full_color('backside')"
                            :disabled="readonly"
                            v-if="form_data.cantidad_de_tintas_retiro >= 4"
                        >
                            Cargar Cuatricomía
                        </button>
                    </div>
                    <div class="form-column col-sm-8">
                        <!-- :field_id="`tinta_seleccionada_${index}`"
                        :list_id="`listado_de_tintas_${index}`" -->
                        
                        <div
                            class="form-group" 
                            v-for="index in form_data.cantidad_de_tintas_retiro"
                        >
                            <label for="">Tinta {{ index }}</label>
                            <div class="input-group mb-3">
                                <span
                                    class="input-group-text color" id=""
                                    :style="{ background: form_data[`hex_tinta_seleccionada_retiro_${index}`] || '#56565656'}"
                                ></span>
                                <input
                                    type="text"
                                    class="form-control"
                                    :list="`listado_de_tintas_retiro${index}`"
                                    v-model="form_data[`tinta_seleccionada_retiro_${index}`]"
                                    @change="form_data[`hex_tinta_seleccionada_retiro_${index}`] = ''"
                                    @input="form_data[`tinta_seleccionada_retiro_${index}`] = ''"
                                    :readonly="readonly"
                                />

                                <button
                                    class="btn btn-primary"
                                    style="border-top-left-radius: 0; border-bottom-left-radius: 0; height: 28px"
                                    @click="select_ink_color('Retiro', `tinta_seleccionada_retiro_${index}`)"
                                    :disabled="readonly"
                                >
                                    Seleccionar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row" v-if="form_data.tecnologia === 'Digital'">
                    <div class="form-column col-sm-6">
                        <p class="full-color-text" style="color: greenyellow">
                            Full Color
                        </p>
                    </div>
                </div>
            </section>

            <section>
                <hr />
                <div class="row">
                    <div class="form-column col-sm-6">
                        <checkbox-field
                            label="Incluye Barnizado?"
                            :initial_value="form_data.incluye_barnizado"
                            @after_select="
                                (value) => (form_data.incluye_barnizado = value)
                            "
                            :read_only="readonly"
                        />

                        <!-- Calculated in Inches Square -->
                        <select-field
                            label="Tipo de Barnizado"
                            :options="select_options['tipo_barnizado']"
                            :selected="form_data.tipo_barnizado"
                            @after_select="
                                (value) => (form_data.tipo_barnizado = value)
                            "
                            v-if="form_data.incluye_barnizado"
                            :read_only="readonly"
                        />
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
                            :read_only="readonly"
                        />

                        <select-field
                            label="Tipo de Laminado"
                            :options="select_options['tipo_laminado']"
                            :selected="form_data.tipo_laminado"
                            @after_select="
                                (value) => (form_data.tipo_laminado = value)
                            "
                            v-if="form_data.incluye_laminado"
                            :read_only="readonly"
                        />
                    </div>
                </div>
            </section>

            <section>
                <hr />
                <div class="row">
                    <div class="form-column col-sm-6">
                        <checkbox-field
                            label="Incluye Relieve?"
                            :initial_value="form_data.incluye_relieve"
                            @after_select="
                                (value) => (form_data.incluye_relieve = value)
                            "
                            :read_only="readonly"
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
                            :read_only="readonly"
                        />

                        <select-field
                            label="Color de Lamina"
                            :options="select_options['color_lamina']"
                            :selected="form_data.tipo_de_material_relieve"
                            @after_select="
                                (value) => (form_data.tipo_de_material_relieve = value)
                            "
                            v-if="form_data.incluye_relieve"
                            :read_only="readonly"
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
                            :read_only="readonly"
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
                            :read_only="readonly"
                        />
                    </div>
                </div>
            </section>

            <section>
                <hr />
                <div class="row">
                    <div class="form-column col-sm-6">
                        <checkbox-field
                            label="Incluye Troquelado?"
                            :initial_value="form_data.incluye_troquelado"
                            @after_select="
                                (value) => (form_data.incluye_troquelado = value)
                            "
                            :read_only="readonly"
                        />
                    </div>
                    <div class="form-column col-sm-6">
                        <checkbox-field
                            v-if="form_data.incluye_troquelado"
                            label="Troquel en Inventario?"
                            :conventional_checkbox="true"
                            :initial_value="form_data.troquel_en_inventario"
                            @after_select="
                                (value) => (form_data.troquel_en_inventario = value)
                            "
                            :read_only="readonly"
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
                            label="Incluye Utilidad?"
                            :initial_value="form_data.incluye_utilidad"
                            @after_select="
                                (value) => (form_data.incluye_utilidad = value)
                            "
                            :read_only="readonly"
                        />

                        <select-field
                            label="Tipo de Utilidad"
                            :options="[
                                { value: '' },
                                { value: 'Cinta Doble Cara' },
                            ]"
                            :selected="form_data.tipo_utilidad"
                            @after_select="handle_utility_type_change"
                            v-if="form_data.incluye_utilidad"
                            :read_only="readonly"
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
                            v-if="form_data.incluye_utilidad && form_data.tipo_utilidad === 'Cinta Doble Cara'"
                            :read_only="readonly"
                        />

                        <dimension
                            label="Tamaño de los Puntos"
                            :width="form_data.cinta_doble_cara_ancho_punto"
                            :height="form_data.cinta_doble_cara_alto_punto"
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
                            v-if="form_data.incluye_utilidad && form_data.tipo_utilidad === 'Cinta Doble Cara'"
                            :read_only="readonly"
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
                            :read_only="readonly"
                        />

                        <select-field
                            label="Tipo de Pegado"
                            :options="select_options.tipo_pegado"
                            :selected="form_data.tipo_pegado"
                            @after_select="
                                (value) => (form_data.tipo_pegado = value)
                            "
                            v-if="form_data.incluye_pegado"
                            :read_only="readonly"
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
                                { value: '' },
                                { value: 'Corrugado' },
                                { value: 'Papel' },
                                { value: 'Plástico' },
                            ]"
                            :selected="form_data.tipo_de_empaque"
                            @after_select="
                                (value) => (form_data.tipo_de_empaque = value)
                            "
                            :read_only="readonly"
                        />
                    </div>
                </div>
            </section>

            <section>
                <hr />
                <div class="row">
                    <div class="px-3" style="width: 100%">
                        <h3>Costo Unitario</h3>
                    </div>
                    <div class="col-sm-6">
                        <percent-field
                            label="Margen de Utilidad"
                            :value="form_data.margen_de_utilidad"
                            @after_select="validate_and_set_margin_of_utility"
                            :read_only="readonly"
                        />
                    </div>
                    <div class="col-sm-6 px-3">
                        <h2 class="text-right" v-if="!is_new()">
                            C/U <br>
                            <small
                                class="text-muted"
                                style="color: var(--success) !important; font-weight: bold" >
                                $ {{ parseFloat(form_data.unit_cost || 0.000).toLocaleString() }}
                            </small>
                        </h2>
                    </div>
                </div>
            </section>
        </div>
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

.input-group > span.color {
    width: 90px;
    height: 28px;
    border: none;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
}
</style>