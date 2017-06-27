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
        <submissions-exporter v-if="canDownload && submissions.length"
          :table="getTable"
          :filename="exportFilename">
            Export feedback
        </submissions-exporter>

        <b-table striped hover
            ref="table"
            v-on:row-clicked='gotoSubmission'
            :items="submissions"
            :fields="fields"
            :current-page="currentPage"
            :filter="filterItems"
            :show-empty="true">
            <template slot="user" scope="item">
                {{item.value.name ? item.value.name : '-'}}
            </template>
            <template slot="grade" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="created_at" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="assignee" scope="item">
                {{item.value ? item.value.name : '-'}}
            </template>
        </b-table>
    </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import SubmissionsExporter from './SubmissionsExporter';

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
    },

    data() {
        return {
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
        };
    },

    computed: {
        ...mapGetters('user', {
            userId: 'id',
            userName: 'name',
        }),

        exportFilename() {
            return this.assignment ? `${this.assignment.course_name}-${this.assignment.name}.csv` : null;
        },
    },

    watch: {
        submissions(submissions) {
            this.latest = this.getLatest(submissions);
        },
    },

    mounted() {
        this.hasPermission('can_submit_own_work').then((perm) => {
            this.assigneeFilter = !perm && this.submissions.some(s => s.assignee);
        });
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

        hasPermission(perm) {
            return this.u_hasPermission({ name: perm, course_id: this.assignment.course_id });
        },

        ...mapActions({
            u_hasPermission: 'user/hasPermission',
        }),
    },

    components: {
        SubmissionsExporter,
    },
};
</script>
