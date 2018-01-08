<template>
    <div class="submission-list">
        <b-form-fieldset>
            <b-input-group>
                <input v-model="filter"
                       class="form-control"
                       placeholder="Type to Search"
                       @keyup.enter="submit"/>

                <b-form-checkbox class="input-group-addon" v-model="latestOnly" @change="submit"
                    v-if="latest.length !== submissions.length">
                    Latest only
                </b-form-checkbox>

                <b-form-checkbox class="input-group-addon" v-model="mineOnly" @change="submit"
                    v-if="assigneeFilter">
                    Assigned to me
                </b-form-checkbox>
            </b-input-group>
        </b-form-fieldset>

        <div style="margin-bottom: 1em; overflow: hidden;">
            <submit-button label="Show Rubric"
                           @click="showRubricModal = !showRubricModal"
                           style="float: right;"
                           v-if="rubric"/>
            <submissions-exporter v-if="canDownload && submissions.length"
                                  :get-submissions="filter => filter ? filteredSubmissions : submissions"
                                  :assignment-id="assignment.id"
                                  :filename="exportFilename">
                Export feedback
            </submissions-exporter>
        </div>

        <b-modal v-if="rubric"
                 v-model="showRubricModal"
                 :ok-only="true"
                 ok-title="Close"
                 :hide-header="true">
            <rubric-editor :editable="false"
                           :defaultRubric="rubric"
                           :assignmentId="assignment.id"/>
        </b-modal>


        <b-table striped hover
                 ref="table"
                 @row-clicked='gotoSubmission'
                 @sort-changed="sortChanged"
                 :items="filteredSubmissions"
                 :fields="fields"
                 :current-page="currentPage"
                 :sort-compare="sortSubmissions"
                 :show-empty="true"
                 class="submissions-table">
            <template slot="user" scope="item">
                <a class="invisible-link"
                   href="#"
                   @click.prevent>
                   {{item.value.name ? item.value.name : '-'}}
                </a>
            </template>
            <template slot="grade" scope="item">
                {{formatGrade(item.value) || '-'}}
            </template>
            <template slot="created_at" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="assignee" scope="item">
                <span v-if="!canChangeAssignee">
                    {{ item.value ? item.value.name : '-' }}
                </span>
                <loader :scale="1" v-else-if="assigneeUpdating[item.item.id]"/>
                <b-form-select
                    :options="assignees"
                    :value="item.value ? item.value.id : null"
                    @input="updateAssignee($event, item)"
                    @click.native.stop
                    style="max-width: 20em;"
                    v-else/>
            </template>
        </b-table>

        <b-alert variant="warning"
                 :dismissable="true"
                 :show="error !== ''">
            {{ error }}
        </b-alert>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { formatGrade, filterSubmissions, sortSubmissions, parseBool } from '@/utils';
import SubmissionsExporter from './SubmissionsExporter';
import Loader from './Loader';
import SubmitButton from './SubmitButton';
import RubricEditor from './RubricEditor';

export default {
    name: 'submission-list',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
        submissions: {
            type: Array,
            default: [],
        },
        canDownload: {
            type: Boolean,
            default: false,
        },
        rubric: {
            default: null,
        },
    },

    data() {
        return {
            showRubricModal: false,
            latestOnly: parseBool(this.$route.query.latest, true),
            mineOnly: parseBool(this.$route.query.mine, true),
            currentPage: 1,
            filter: this.$route.query.q || '',
            latest: this.getLatest(this.submissions),
            fields: {
                user: {
                    label: 'User',
                    sortable: true,
                },
                grade: {
                    label: 'Grade',
                    sortable: true,
                },
                created_at: {
                    label: 'Created at',
                    sortable: true,
                },
                assignee: {
                    label: 'Assigned to',
                    sortable: true,
                },
            },
            assigneeFilter: false,
            canChangeAssignee: false,
            assignees: [],
            assigneeUpdating: [],
            error: '',
        };
    },

    computed: {
        ...mapGetters('user', {
            userId: 'id',
            userName: 'name',
        }),

        exportFilename() {
            return this.assignment ? `${this.assignment.course.name}-${this.assignment.name}.csv` : null;
        },

        filteredSubmissions() {
            // WARNING: We need to access all, do not change!
            if ([
                this.submissions,
                this.latestOnly,
                this.mineOnly,
                this.userId,
                this.filter,
            ].indexOf(undefined) !== -1) {
                return [];
            }

            return filterSubmissions(
                this.submissions,
                this.latestOnly,
                this.mineOnly,
                this.userId,
                this.filter,
            );
        },
    },

    watch: {
        submissions(submissions) {
            this.latest = this.getLatest(submissions);
        },
    },

    mounted() {
        this.$hasPermission(
            'can_assign_graders',
            this.assignment.course.id,
        ).then((canChangeAssignee) => {
            if (canChangeAssignee) {
                this.$http.get(`/api/v1/assignments/${this.assignment.id}/graders/`).then((res) => {
                    const assignees = res.data.map(ass =>
                        ({ value: ass.id, text: ass.name, data: ass }));
                    assignees.unshift({ value: null, text: '-', data: null });
                    this.assignees = assignees;
                    this.canChangeAssignee = canChangeAssignee;
                }, ({ response }) => {
                    this.error = `There was an issue loading the graders from the server: ${response.data.message}`;
                });
            }
        });

        this.assigneeFilter = this.submissions.some(s => s.assignee &&
                                                    s.assignee.id === this.userId);
        this.$refs.table.sortBy = this.$route.query.sortBy || 'user';
        // Fuck you bootstrapVue (sortDesc should've been sortAsc).
        this.$refs.table.sortDesc = parseBool(this.$route.query.sortAsc, true);
    },

    methods: {
        getLatest(submissions) {
            const latest = {};
            submissions.forEach((item) => {
                if (!latest[item.user.id]) {
                    latest[item.user.id] = item.id;
                }
            });
            return latest;
        },

        sortChanged(context) {
            this.$router.replace({
                query: Object.assign(
                    // Fuck you bootstrapVue (sortDesc should've been sortAsc)
                    {}, this.$route.query, { sortBy: context.sortBy, sortAsc: context.sortDesc },
                ),
            });
        },

        getTable() {
            return this.$refs ? this.$refs.table : null;
        },

        gotoSubmission(submission) {
            this.submit();

            this.$router.push({
                name: 'submission',
                params: { submissionId: submission.id },
                query: {
                    mine: this.mineOnly == null ? undefined : this.mineOnly,
                    latest: this.latestOnly == null ? undefined : this.latestOnly,
                    search: this.filter || undefined,
                    // Fuck you bootstrapVue (sortDesc should've been sortAsc)
                    sortBy: this.$refs.table.sortBy,
                    sortAsc: this.$refs.table.sortDesc,
                },
            });
        },

        submit() {
            const query = {
                latest: this.latestOnly,
                mine: this.mineOnly,
            };
            query.q = this.filter || undefined;
            this.$router.replace({
                query: Object.assign(
                    {}, this.$route.query, query,
                ),
            });
        },

        isEmptyObject(obj) {
            return Object.keys(obj).length === 0 && obj.constructor === Object;
        },

        filterItems(item) {
            if ((this.latestOnly && this.latest[item.user.id] !== item.id) ||
                (this.assigneeFilter && this.mineOnly &&
                 (item.assignee == null || item.assignee.id !== this.userId))) {
                return false;
            } else if (!this.filter) {
                return true;
            }

            const terms = {
                user_name: item.user.name.toLowerCase(),
                grade: (item.grade || 0).toString(),
                created_at: item.created_at,
                assignee: item.assignee ? item.assignee.name.toLowerCase() : '-',
            };
            return this.filter.toLowerCase().split(' ').every(word =>
                Object.keys(terms).some(key =>
                    terms[key].indexOf(word) >= 0));
        },

        updateAssignee(newId, { item: submission }) {
            const oldId = submission.assignee ? submission.assignee.id : null;
            if (oldId === newId) {
                return;
            }

            this.$set(this.assigneeUpdating, submission.id, true);

            let res;
            if (newId != null) {
                res = this.$http.patch(`/api/v1/submissions/${submission.id}/grader`, {
                    user_id: newId,
                });
            } else {
                res = this.$http.delete(`/api/v1/submissions/${submission.id}/grader`);
            }

            res.then(() => {
                this.$set(this.assigneeUpdating, submission.id, false);
                let newAssignee;
                for (let i = 0; i < this.assignees.length; i += 1) {
                    if (this.assignees[i].data && this.assignees[i].data.id === newId) {
                        newAssignee = this.assignees[i].data;
                        break;
                    }
                }
                this.$emit('assigneeUpdated', submission, newAssignee);
            }, ({ response }) => {
                // eslint-disable-next-line
                console.log(response);
            });
        },

        formatGrade,
        sortSubmissions,
    },

    components: {
        Loader,
        SubmitButton,
        RubricEditor,
        SubmissionsExporter,
    },
};
</script>

<style lang="less">
.submissions-table {
    td, th {
        // grade
        &:nth-child(2) {
            width: 10em;
        }

        // student
        // created at
        // assignee
        &:nth-child(1),
        &:nth-child(3),
        &:nth-child(4) {
            width: 20em;
        }
    }
}

.submissions-table td:last-child {
    padding-top: 0.3rem;
    padding-bottom: 0.3rem;
}

.submissions-table td .loader {
    padding: 0.7rem;
}

.submission-list .modal-dialog.modal-md {
    max-width: 1550px;
    width: 100%;
}
</style>
