<template>
    <div>
        <h3>Material Specification</h3>
        <table class="table table-bordered">
            <thead>
                <tr>
                <th>GSM</th>
                <th v-if="raw_material_specs.base_material=='Paperboard'">Caliper</th>
                <th v-if="raw_material_specs.base_material=='Paper'">Paper Weight</th>
                <th v-if="raw_material_specs.material_format=='Roll'">Width</th>
                <th v-if="raw_material_specs.material_format=='Sheet'">Dimension</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <td>{{ raw_material_specs.gsm }}</td>
                <td v-if="raw_material_specs.base_material=='Paperboard'">{{  raw_material_specs.paperboard_caliper }}</td>
                <td v-if="raw_material_specs.base_material=='Paper'">{{ raw_material_specs.paper_weight }}</td>
                <td v-if="raw_material_specs.material_format=='Roll'">{{ raw_material_specs.roll_width }} in</td>
                <td v-if="raw_material_specs.material_format=='Sheet'">{{ raw_material_specs.sheet_width }} x {{ raw_material_specs.sheet_height }} in</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
export default {
    name: 'Material',
    props: {
        raw_material_specs: {
            type: Object,
            required: true,
        }
    },
}
</script>