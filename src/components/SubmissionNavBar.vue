<template>
    <b-form-fieldset class="submission-nav-bar">
        <b-input-group>
            <b-input-group-prepend>
                <b-button class="angle-btn"
                          @click="backToSubmissions">
                    <icon name="angle-double-left"/>
                </b-button>
            </b-input-group-prepend>
            <b-input-group-prepend>
                <b-button :disabled="!hasPrev"
                          @click="selectPrev">
                    <icon name="angle-left"/>
                </b-button>
            </b-input-group-prepend>
            <b-input-group-prepend style="flex-grow: 1;">
                <b-form-select :options="options"
                               v-model="selected"
                               id="student-selector"/>
            </b-input-group-prepend>
            <b-input-group-append>
                <b-button :disabled="!hasNext"
                          @click="selectNext">
                    <icon name="angle-right"/>
                </b-button>
            </b-input-group-append>
        </b-input-group>
    </b-form-fieldset>
</template>

<script>
import moment from 'moment';
import { formatGrade, sortSubmissions, parseBool } from '@/utils';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-double-left';
import 'vue-awesome/icons/angle-left';
import 'vue-awesome/icons/angle-right';

export default {
    name: 'submission-nav-bar',

    props: {
        value: {
            type: Object,
            default: null,
        },
        submissions: {
            type: Array,
            default: [],
        },
        filter: {
            type: Function,
            default: x => x,
        },
    },

    data() {
        return {
            selected: this.value,
        };
    },

    computed: {
        options() {
            const res = this.filter(this.submissions);

            res.sort((a, b) => sortSubmissions(a, b, this.$route.query.sortBy || 'user'));

            if (!parseBool(this.$route.query.sortAsc)) {
                res.reverse();
            }

            return res.map(sub => ({
                text: this.getItemText(sub),
                value: sub,
            }));
        },

        optionIndex() {
            return this.options.findIndex(opt => opt.value === this.value);
        },

        hasPrev() {
            return this.optionIndex > 0 && this.optionIndex < this.options.length;
        },

        hasNext() {
            return this.optionIndex >= 0 && this.optionIndex < this.options.length - 1;
        },
    },

    watch: {
        selected(submission) {
            this.$emit('input', submission);
        },
    },

    mounted() {
        this.$root.$on('shown::dropdown', () => {
            this.$nextTick(this.scrollToItem);
        });
    },

    methods: {
        backToSubmissions() {
            this.$router.push({
                name: 'assignment_submissions',
                params: {
                    courseId: this.$route.params.courseId,
                    assignmentId: this.$route.params.assignmentId,
                },
                query: {
                    q: this.$route.query.search || undefined,
                    mine: this.$route.query.mine || false,
                    latest: this.$route.query.latest || false,
                    sortBy: this.$route.query.sortBy,
                    sortAsc: this.$route.query.sortAsc,
                },
            });
        },

        selectPrev() {
            if (this.hasPrev) {
                this.selected = this.options[this.optionIndex - 1].value;
            }
        },

        selectNext() {
            if (this.hasNext) {
                this.selected = this.options[this.optionIndex + 1].value;
            }
        },

        getItemText(submission) {
            const date = moment.utc(submission.created_at, moment.ISO_8601)
                .local().format('DD-MM-YYYY HH:mm');
            const grade = formatGrade(submission.grade);
            let text = `${submission.user.name} - ${date}`;

            if (grade != null) {
                text += ` [${grade}]`;
            }
            if (submission.assignee) {
                text += ` (${submission.assignee.name})`;
            }

            return text;
        },

        scrollToItem() {
            let el = document.getElementById('selectedItem').parentNode;
            for (let i = 0, end = 6; i < end; i += 1) {
                el = el.previousSibling || el;
            }
            el.scrollIntoView(true);
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
    padding-top: .625rem;
}
</style>
