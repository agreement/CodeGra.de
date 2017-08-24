<template>
    <b-form-fieldset class="submission-nav-bar">
        <b-input-group>
            <b-input-group-button>
                <b-button class="angle-btn"
                          @click="backToSubmissions">
                    <icon name="angle-double-left"/>
                </b-button>
            </b-input-group-button>
            <b-input-group-button>
                <b-button :disabled="!hasPrev"
                          @click="selectPrev">
                    <icon name="angle-left"/>
                </b-button>
            </b-input-group-button>
            <b-input-group-button style="flex-grow: 1;">
                <b-form-select :options="options"
                               v-model="selected"
                               id="student-selector"/>
            </b-input-group-button>
            <b-input-group-button>
                <b-button :disabled="!hasNext"
                          @click="selectNext">
                    <icon name="angle-right"/>
                </b-button>
            </b-input-group-button>
        </b-input-group>
    </b-form-fieldset>
</template>

<script>
import moment from 'moment';
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
            index: this.submissions.indexOf(this.value),
        };
    },

    computed: {
        options() {
            return this.filter(this.submissions).map(sub => ({
                text: this.getItemText(sub),
                value: sub,
            }));
        },

        hasPrev() {
            return this.index > 0 && this.index < this.submissions.length;
        },

        hasNext() {
            return this.index >= 0 && this.index < this.submissions.length - 1;
        },
    },

    watch: {
        selected(submission) {
            this.index = this.submissions.indexOf(submission);
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
            });
        },

        selectPrev() {
            if (this.hasPrev) {
                this.selected = this.submissions[this.index - 1];
            }
        },

        selectNext() {
            if (this.hasNext) {
                this.selected = this.submissions[this.index + 1];
            }
        },

        getItemText(submission) {
            const date = moment.utc(submission.created_at, moment.ISO_8601)
                .local().format('DD-MM-YYYY HH:mm');
            let text = `${submission.user.name} - ${date}`;
            if (submission.grade) {
                text += ` [${submission.grade}]`;
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
