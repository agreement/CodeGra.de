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
            <b-form-fieldset label="Filename:">
                <b-form-input v-model="userFilename" type="text"
                  :placeholder="filename"></b-form-input>
            </b-form-fieldset>
            <b-form-fieldset
              label="Columns:"
              description="Checked columns will be included in the exported file.">
                <b-form-checkbox
                  v-for="(col, key) in columns"
                  :key="key"
                  v-model="col.enabled">
                    {{ col.name }}
                </b-form-checkbox>
            </b-form-fieldset>
            <b-form-fieldset
              label="Rows:"
              description="When <i>All</i> is selected all submissions of this assignment will be exported.<br>The <i>Current</i> option only exports the submissions that are shown by the current filter that is applied to the list.">
                <b-form-radio v-model="exportSetting" :options="['All', 'Current']">
                </b-form-radio>
            </b-form-fieldset>
        </b-collapse>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/cog';

import * as Papa from 'papaparse';

export default {
    name: 'submissions-exporter',

    components: {
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
                    {
                        name: 'User',
                        enabled: [true],
                        getter: submission => submission.user.name,
                    },
                    {
                        name: 'Grade',
                        enabled: [true],
                        getter: submission => submission.grade,
                    },
                    {
                        name: 'Created at',
                        enabled: [true],
                        getter: submission => submission.created_at,
                    },
                    {
                        name: 'Assigned to',
                        enabled: [true],
                        getter: submission => submission.assignee,
                    },
                ];
            },
        },
    },

    computed: {
        items() {
            // eslint-disable-next-line no-underscore-dangle
            return this.exportSetting === 'All' ? this.table().items : this.table()._items;
        },

        enabledColumns() {
            return this.columns.filter(col => col.enabled[0]);
        },

        currentFilename() {
            return encodeURIComponent((this.userFilename) ? this.userFilename : this.filename);
        },
    },

    data() {
        return {
            exportSetting: 'Current',
            userFilename: null,
        };
    },


    methods: {
        createCSV: function createCSV() {
            const data = [];
            const idx = Object.keys(this.enabledColumns);
            for (let i = 0; i < this.items.length; i += 1) {
                const item = this.items[i];
                const row = {};
                for (let j = 0; j < idx.length; j += 1) {
                    const col = this.enabledColumns[idx[j]];
                    row[col.name] = col.getter(item);
                }
                data.push(row);
            }
            const csv = Papa.unparse(data);
            this.$http.post('/api/v1/files/', csv).then((response) => {
                window.open(`/api/v1/files/${response.data}?name=${this.currentFilename}`);
            });
        },
    },
};

</script>
