<template>
    <nav class="row">
        <div class="col-12">
            <h4>Grading: {{ this.submission.user.name }}</h4>
            <div class="input-group">
                <span class="input-group-btn">
                    <b-button v-if="next" :to="{
                            name: 'submission',
                            params: {
                                assignmentId: this.assignmentId,
                                submissionId: prev,
                            },
                        }" class="arrow-btn">
                        <icon name="arrow-left"></icon>
                    </b-button>
                    <b-button v-else class="arrow-btn disabled">
                        <icon name="arrow-left"></icon>
                    </b-button>
                </span>
                <b-form-select v-model="selected"
                               :options="options"
                               calss="mb-3"></b-form-select>
                <span class="input-group-btn">
                    <b-button v-if="next" :to="{
                            name: 'submission',
                            params: {
                                assignmentId: this.assignmentId,
                                submissionId: next,
                            },
                        }" class="arrow-btn">
                        <icon name="arrow-right"></icon>
                    </b-button>
                    <b-button v-else class="arrow-btn disabled">
                        <icon name="arrow-right"></icon>
                    </b-button>
                </span>
            </div>
        </div>
    </nav>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/arrow-left';
import 'vue-awesome/icons/arrow-right';
import 'vue-awesome/icons/list';

import { mapGetters } from 'vuex';

export default {
    name: 'submission-nav-bar',

    data() {
        return {
            selected: this.submission.id,
            options: {},
            next: null,
            prev: null,
        };
    },

    mounted() {
        this.options = this.filterLatestSubmissions(this.submissions);
    },

    methods: {
        filterLatestSubmissions(submissions) {
            // filter submissions on latest only
            // and if assignee is set only
            // the submissions assigned to this user
            const latestSubmissions = [];
            const seen = {};
            const len = submissions.length;
            let curSubPassed = false;
            for (let i = 0; i < len; i += 1) {
                const sub = submissions[i];
                if (seen[sub.user.id] !== true) {
                    if (this.submission.assignee === '' ||
                        sub.assignee.id === this.userid) {
                        // find next and prev
                        if (curSubPassed) {
                            this.next = sub.id;
                        } else if (this.submission.id === sub.id) {
                            curSubPassed = true;
                        }
                        this.prev = sub.id;

                        const grade = sub.grade ? sub.grade : '-';
                        latestSubmissions.push({
                            text: `name: ${sub.user.name}, grade: ${grade}`,
                            value: sub.id,
                        });
                        seen[sub.user.id] = true;
                    }
                }
            }
            return latestSubmissions;
        },
    },

    watch: {
        selected(val) {
            this.$router.push({
                name: 'submission',
                params: {
                    assignmentId: this.assignmentId,
                    submissionId: val,
                },
            });
            this.$emit('subChange');
        },
    },

    computed: {
        ...mapGetters('user', {
            loggedIn: 'loggedIn',
            userid: 'id',
            username: 'name',
        }),
    },

    props: {
        submission: {
            type: Object,
            default: {},
        },

        submissions: {
            type: Array,
            default: [],
        },

        courseId: {
            type: Number,
            default: 0,
        },

        assignmentId: {
            type: Number,
            default: 0,
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>

.row {
    padding-bottom: 1em;
}

</style>
