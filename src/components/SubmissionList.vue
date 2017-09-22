<template>
    <div class="submission-list">
        <b-form-fieldset>
            <b-input-group>
                <b-form-input v-model="filter" placeholder="Type to Search" @keyup.enter="submit"></b-form-input>

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
                                  :table="getTable"
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
                 v-on:row-clicked='gotoSubmission'
                 :items="submissions"
                 :fields="fields"
                 :current-page="currentPage"
                 :sort-compare="sortTable"
                 :filter="filterItems"
                 :show-empty="true"
                 class="submissions-table">
            <template slot="user" scope="item">
                {{item.value.name ? item.value.name : '-'}}
            </template>
            <template slot="grade" scope="item">
                {{item.value ? parseFloat(item.value).toFixed(2) : '-'}}
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
import { mapActions, mapGetters } from 'vuex';
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
            latestOnly: this.$route.query.latest !== 'false',
            mineOnly: this.$route.query.mine !== 'false',
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
    },

    watch: {
        submissions(submissions) {
            this.latest = this.getLatest(submissions);
        },
    },

    mounted() {
        this.hasPermission({
            name: 'can_manage_course',
            course_id: this.assignment.course.id,
        }).then((canChangeAssignee) => {
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
        this.$refs.table.sortBy = 'user';
    },

    methods: {
        sortTable(a, b, sortBy) {
            const oneNull = (first, second) => {
                if (!first && !second) {
                    return 0;
                } else if (!first) {
                    return 1;
                } else if (!second) {
                    return -1;
                }
                return null;
            };

            const comp = (first, second) => first.toLowerCase().localeCompare(second.toLowerCase());

            if (typeof a[sortBy] === 'number' && typeof b[sortBy] === 'number') {
                return a[sortBy] - b[sortBy];
            } else if (sortBy === 'user' || sortBy === 'assignee') {
                const first = a[sortBy];
                const second = b[sortBy];

                const ret = oneNull(first, second);
                if (ret !== null) return ret;

                return comp(first.name, second.name);
            } else if (sortBy === 'created_at' || sortBy === 'grade') {
                const first = a[sortBy];
                const second = b[sortBy];

                const ret = oneNull(first, second);
                if (ret !== null) return ret;

                return comp(first, second);
            }

            return 0;
        },
        getLatest(submissions) {
            const latest = {};
            submissions.forEach((item) => {
                if (!latest[item.user.id]) {
                    latest[item.user.id] = item.id;
                }
            });
            return latest;
        },

        getTable() {
            return this.$refs ? this.$refs.table : null;
        },

        gotoSubmission(submission) {
            this.submit();
            this.$router.push({
                name: 'submission',
                params: { submissionId: submission.id },
            });
        },

        submit() {
            const query = {
                latest: this.latestOnly,
                mine: this.mineOnly,
            };
            if (this.filter) {
                query.q = this.filter;
            }
            this.$router.replace({ query });
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

        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
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
