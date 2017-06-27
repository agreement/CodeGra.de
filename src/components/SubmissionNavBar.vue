<template>
    <b-form-fieldset class="submission-nav-bar">
        <b-input-group>
            <b-input-group-button class="buttons">
                <b-popover placement="top" triggers="hover" content="Back to all submissions">
                    <b-button class="angle-btn" @click="backToSubmissions">
                        <icon name="angle-double-left"></icon>
                    </b-button>
                </b-popover>
            </b-input-group-button>
            <b-input-group-button class="buttons">
                <b-button :disabled="!prev" @click="selected = prev" class="angle-btn">
                    <icon name="angle-left"></icon>
                </b-button>
            </b-input-group-button>
            <b-form-select v-model="selected"
                           :options="options"
                           style="height: 2em; text-align: center;"
                           size="lg"></b-form-select>
            <b-input-group-button class="buttons">
                <b-button :disabled="!next" @click="selected = next" class="angle-btn">
                    <icon name="angle-right"></icon>
                </b-button>
            </b-input-group-button>
        </b-input-group>
    </b-form-fieldset>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-left';
import 'vue-awesome/icons/angle-right';
import 'vue-awesome/icons/angle-double-left';
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
        this.options = this.filterAll();
        this.findNextPrev();
    },

    methods: {
        filterAll() {
            const options = this.filterLatestSubmissions(this.submissions);
            return this.filterMineOnly(options);
        },

        filterLatestSubmissions(submissions) {
            // filter submissions on latest only
            const latestSubs = [];
            const seen = {};
            for (let i = 0, len = submissions.length; i < len; i += 1) {
                const sub = submissions[i];
                if (seen[sub.user.id] !== true) {
                    const grade = sub.grade ? `- ${sub.grade} -` : '';
                    const assignee = sub.assignee ? sub.assignee.name : 'nobody';
                    let assigneeText;
                    if (sub.assignee === false) { // no permission
                        assigneeText = '';
                    } else {
                        assigneeText = `- Assigned to ${assignee}`;
                    }
                    latestSubs.push({
                        text: `${sub.user.name} ${grade} ${assigneeText}`,
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

        backToSubmissions() {
            this.$router.push({
                name: 'assignment_submissions',
            });
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

        submissions() {
            this.options = this.filterAll();
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
.buttons div, button {
    height: 100%;
}

select {
    text-align-last: center; text-align: center;
    -ms-text-align-last: center;
    -moz-text-align-last: center; text-align-last: center;
    cursor: pointer;
}
</style>
