<template>
    <div>
        <b-button-group>
            <b-button variant="primary" @click="createCSV">
                <span>Export as CSV</span>
            </b-button>
            <b-button v-b-toggle.settings>
                <icon name='cog'></icon>
            </b-button>
        </b-button-group>
        <b-collapse id="settings">
        <!-- TODO: fix html format -->
            Select Columns:<br>
            <b-button-group>
                <b-button v-for="col in cols" :key="col.name"
                  :variant="col.enabled ?  'success' : 'danger'"
                  @click="toggleColumn(col)">
                    {{ col.name }}
                </b-button>
            </b-button-group><br>
            Export setting:
            <b-form-radio v-model="exportSetting" :options="['All', 'Current']">
            </b-form-radio>
        </b-collapse>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bCollapse, bFormRadio, bFormFieldset } from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/cog';

import * as Papa from 'papaparse';

export default {
    name: 'submissions-exporter',

    components: {
        bButton,
        bButtonGroup,
        bCollapse,
        bFormRadio,
        bFormFieldset,
        Papa,
        Icon,
    },

    props: {
        table: {
            type: Function,
        },
        filename: {
            type: String,
            default: 'export.csv',
        },
        columns: {
            type: Array,
            default: function defaultColumns() {
                return [
                    { name: 'User', getter: submission => submission.user.name },
                    { name: 'Grade', getter: submission => submission.grade },
                    { name: 'Created at', getter: submission => submission.created_at },
                    { name: 'Assigned to', getter: submission => submission.assignee },
                ];
            },
        },
    },

    computed: {
        items() {
            // eslint-disable-next-line no-underscore-dangle
            return this.exportSetting === 'All' ? this.table().items : this.table()._items;
        },
    },

    mounted() {
        this.updateColumns();
    },

    data() {
        return {
            cols: null,
            exportSetting: 'Current',
        };
    },


    methods: {
        updateColumns() {
            const keys = Object.keys(this.columns);
            for (let i = 0; i < keys.length; i += 1) {
                const col = this.columns[i];
                if (!('enabled' in col)) {
                    col.enabled = true;
                }
            }
            this.cols = this.columns;
        },

        toggleColumn(column) {
            this.$set(column, 'enabled', !column.enabled);
        },

        createCSV: function createCSV() {
            const data = [];
            const columns = Object.keys(this.columns);
            for (let i = 0; i < this.items.length; i += 1) {
                const item = this.items[i];
                const row = {};
                for (let j = 0; j < columns.length; j += 1) {
                    const col = this.columns[j];
                    row[col.name] = col.getter(item);
                }
                data.push(row);
            }
            const csv = Papa.unparse(data);
            this.$http.post('/api/v1/files/', csv).then((response) => {
                window.open(`/api/v1/files/${response.data}?name=${this.filename}`);
            });
        },
    },
};

</script>
