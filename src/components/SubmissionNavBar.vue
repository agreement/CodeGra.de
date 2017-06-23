<template>
    <nav class="row">
        <div class="col-12">
            {{ this.submission }}
            <h4>Grading: {{ this.submission.user.name }}</h4>
            <div class="input-group">
                <span class="input-group-btn">
                    <b-button class="arrow-btn">
                        <icon name="arrow-left"></icon>
                    </b-button>
                </span>
                <b-form-select v-model="selected"
                               :options="options"
                               calss="mb-3"></b-form-select>
                <span class="input-group-btn">
                    <b-button class="arrow-btn">
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
            selected: this.submission.user.id,
            options: [],
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
            if (this.submission.assignee === '-') {
                for (let i = 0; i < len; i += 1) {
                    if (seen[submissions[i].user.id] !== true) {
                        const sub = submissions[i];
                        const grade = sub.grade ? sub.grade : '-';
                        latestSubmissions.push({
                            text: `name: ${sub.user.name}, grade: ${grade}`,
                            value: sub.user.id,
                        });
                        seen[sub.user.id] = true;
                    }
                }
            } else {
                for (let i = 0; i < len; i += 1) {
                    const sub = submissions[i];
                    if (seen[sub.user.id] !== true && sub.assignee.id === this.userid) {
                        const grade = sub.grade ? sub.grade : '-';
                        latestSubmissions.push({
                            text: `name: ${sub.user.name}, grade: ${grade}`,
                            value: sub.user.id,
                        });
                        seen[sub.user.id] = true;
                    }
                }
            }
            return latestSubmissions;
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
