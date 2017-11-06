<template>
    <div class="exporter">
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
                description="When <i>All</i> is selected all submissions of this
                             assignment will be exported.<br>The <i>Current</i> option only
                             exports the submissions that are shown by the current filter that
                             is applied to the list.">
                <b-form-radio v-model="exportSetting" :options="['All', 'Current']"/>
            </b-form-fieldset>
        </b-collapse>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/cog';

import Baby from 'babyparse';

export default {
    name: 'submissions-exporter',

    components: {
        Baby,
        Icon,
    },

    props: {
        getSubmissions: {
            type: Function,
            required: true,
        },
        filename: {
            type: String,
            default: 'export.csv',
        },
        assignmentId: {
            type: Number,
            default: 0,
            required: true,
        },
        columns: {
            type: Array,
            default() {
                return [
                    {
                        name: 'Id',
                        enabled: false,
                        getter: submission => submission.user.id,
                    },
                    {
                        name: 'Username',
                        enabled: true,
                        getter: submission => submission.user.username,
                    },
                    {
                        name: 'Name',
                        enabled: true,
                        getter: submission => submission.user.name,
                    },
                    {
                        name: 'Grade',
                        enabled: true,
                        getter: submission => submission.grade,
                    },
                    {
                        name: 'Created at',
                        enabled: true,
                        getter: submission => submission.created_at,
                    },
                    {
                        name: 'Assigned to',
                        enabled: true,
                        getter: submission => (submission.assignee ? submission.assignee.name : ''),
                    },
                    {
                        name: 'General feedback',
                        enabled: false,
                        getter: (submission) => {
                            if (submission.feedback && submission.feedback.general !== '') {
                                return submission.feedback.general;
                            }
                            return '';
                        },
                    },
                    {
                        name: 'Line feedback',
                        enabled: false,
                        getter: (submission) => {
                            if (submission.feedback && submission.feedback.user) {
                                return submission.feedback.user.join('\n');
                            }
                            return '';
                        },
                    },
                    {
                        name: 'Linter feedback',
                        enabled: false,
                        getter: (submission) => {
                            if (submission.feedback && submission.feedback.linter) {
                                return submission.feedback.user.join('\n');
                            }
                            return '';
                        },
                    },
                ];
            },
        },
    },

    computed: {
        items() {
            // eslint-disable-next-line no-underscore-dangle
            return this.exportSetting === 'All' ? this.getSubmissions(false) : this.getSubmissions(true);
        },

        enabledColumns() {
            return this.columns.filter(col => col.enabled);
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
        createCSV() {
            const data = [];
            const idx = Object.keys(this.enabledColumns);
            let cont;

            if (this.enabledColumns.find(item => item.name.endsWith('feedback')) === undefined) {
                cont = Promise.resolve({ data: {} });
            } else {
                cont = this.$http.get(`/api/v1/assignments/${this.assignmentId}/feedbacks/`).catch(() => ({
                    data: {},
                }));
            }

            cont.then(({ data: feedback }) => {
                for (let i = 0; i < this.items.length; i += 1) {
                    const item = Object.assign({
                        feedback: feedback[this.items[i].id],
                    }, this.items[i]);
                    const row = {};
                    for (let j = 0; j < idx.length; j += 1) {
                        const col = this.enabledColumns[idx[j]];
                        row[col.name] = col.getter(item);
                    }
                    data.push(row);
                }
                const csv = Baby.unparse({
                    fields: this.enabledColumns.map(obj => obj.name),
                    data,
                });
                this.$http.post('/api/v1/files/', csv).then((response) => {
                    window.open(`/api/v1/files/${response.data}/${this.currentFilename}`);
                });
            });
        },
    },
};
</script>
