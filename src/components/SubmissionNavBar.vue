<template>
    <nav class="row">
        <div class="col-9">
            <h4>Grading: {{ this.submission.user.name }}</h4>
            <div class="input-group">
                <span class="input-group-btn">
                    <b-button :disabled="!prev" @click="selected = prev" class="arrow-btn">
                        <icon name="arrow-left"></icon>
                    </b-button>
                </span>
                <b-form-select v-model="selected"
                               :options="options"
                               calss="mb-3"
                               size="lg"></b-form-select>
                <span class="input-group-btn">
                    <b-button :disabled="!next" @click="selected = next" class="arrow-btn">
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
        const options = this.filterLatestSubmissions(this.submissions);
        this.options = this.filterMineOnly(options);
        this.findNextPrev();
    },

    methods: {
        filterLatestSubmissions(submissions) {
            // filter submissions on latest only
            const latestSubs = [];
            const seen = {};
            const len = submissions.length;
            for (let i = 0; i < len; i += 1) {
                const sub = submissions[i];
                if (seen[sub.user.id] !== true) {
                    const grade = sub.grade ? sub.grade : '';
                    const assignee = sub.assignee ? sub.assignee.name : '-';
                    latestSubs.push({
                        text: `${sub.user.name} - ${grade} - assigned to ${assignee}`,
                        value: sub.id,
                        assignee: sub.assignee,
                    });
                    seen[sub.user.id] = true;
                }
            }

            return latestSubs;
        },

        filterMineOnly(options) {
            // and filter submissions on mine only
            let mineOnlyOptions;
            if (this.submission.assignee !== null &&
                this.submission.assignee.id === this.userid) {
                mineOnlyOptions = options.filter(sub => sub.assignee !== null &&
                                         sub.assignee.id === this.userid);
                return mineOnlyOptions;
            }
            return options;
        },

        findNextPrev() {
            // find next and prev submissions
            this.next = null;
            this.prev = null;
            const index = this.options.findIndex(x => x.value === this.submission.id);
            if (index >= 1) {
                this.prev = this.options[index - 1].value;
            }
            if (index < this.options.length - 1) {
                this.next = this.options[index + 1].value;
            }
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
            this.options = this.filterMineOnly(this.options);
        },

        submission() {
            this.findNextPrev();
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
