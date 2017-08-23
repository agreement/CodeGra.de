<template>
    <b-form-fieldset class="submission-nav-bar">
        <b-input-group>
            <b-input-group-button>
                <b-button class="angle-btn" @click="backToSubmissions">
                    <icon name="angle-double-left"></icon>
                </b-button>
            </b-input-group-button>
            <b-input-group-button>
                <b-button :disabled="!prev" @click="gotoSubmission(prev)" class="angle-btn">
                    <icon name="angle-left"></icon>
                </b-button>
            </b-input-group-button>
            <b-input-group-button style="flex-grow: 1;">
                <b-form-select :options="options.map(item => item.item)"
                               v-model="selectedOption"
                               id="student-selector">
                </b-form-select>
            </b-input-group-button>
            <b-input-group-button>
                <b-button :disabled="!next" @click="gotoSubmission(next)" class="angle-btn">
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
            selectedOption: 0,
            options: [],
            next: null,
            prev: null,
        };
    },

    mounted() {
        this.options = this.filterAll();
        this.findNextPrev();
        this.selectedOption = this.submission.user.id;
        this.$root.$on('shown::dropdown', () => {
            this.$nextTick(this.scrollToItem);
        });
    },

    methods: {
        gotoSubmission(next) {
            this.selectedOption = next;
        },
        scrollToItem() {
            let el = document.getElementById('selectedItem').parentNode;
            for (let i = 0, end = 6; i < end; i += 1) {
                el = el.previousSibling || el;
            }
            el.scrollIntoView(true);
        },

        getItemText(submission) {
            let text = submission.user.name;
            if (submission.grade) {
                text += ` [${submission.grade}]`;
            }
            if (submission.assignee) {
                text += ` (${submission.assignee.name})`;
            }
            return {
                text,
                value: submission.user.id,
            };
        },

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
                    latestSubs.push({
                        item: this.getItemText(sub),
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
                this.prev = this.options[index - 1].item.value;
            }
            if (index < this.options.length - 1) {
                this.next = this.options[index + 1].item.value;
            }
        },

        backToSubmissions() {
            this.$router.push({
                name: 'assignment_submissions',
            });
        },

        clicked(val) {
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
    },

    watch: {
        selectedOption() {
            for (let i = 0, len = this.options.length; i < len; i += 1) {
                if (this.options[i].item.value === this.selectedOption) {
                    this.clicked(this.options[i].value);
                }
            }
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
            name: 'name',
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
.btn-group {
    width: 100%;
}

.dropdown {
    width: 100%;
}
</style>

<style lang="less">
.submission-nav-bar {
    .dropdown button {
        width: 100%;
        font-size: 1rem;
        padding: 0.5rem;
    }
}
.dropdown-header .dropdown-item:active {
    background-color: inherit;
}

#student-selector {
    border-radius: 0;
    width: 100%;
}
</style>
