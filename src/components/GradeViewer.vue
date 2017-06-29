<template>
    <div class="grade-viewer">
        <b-collapse
            id="rubric-collapse"
            v-if="rubric">
            <rubric-viewer
                v-model="rubricScore"
                :editable="editable"
                :submission="submission"
                :rubric="rubric"
                ref="rubricViewer">
            </rubric-viewer>
        </b-collapse>
        <div class="row">
            <div class="col-6">
                <b-input-group>
                    <b-input-group-button v-if="editable">
                        <b-button
                            :variant="submitted ? 'success' : 'primary'"
                            @click="putFeedback">
                            <icon name="refresh" spin v-if="submitting"></icon>
                            <span v-else>Submit all</span>
                        </b-button>
                    </b-input-group-button>

                    <b-form-input
                        type="number"
                        step="any"
                        min="0"
                        max="10"
                        :disabled="!editable"
                        placeholder="Grade"
                        v-model="grade"
                        v-if="!rubric">
                    </b-form-input>
                    <b-form-input
                        class="text-right"
                        :disabled="true"
                        :value="`${this.grade.toFixed(2)} ( ${this.rubricScore.total} / ${this.rubricScore.max} )`"
                        v-else>
                    </b-form-input>

                    <b-input-group-button v-if="rubric">
                        <b-popover
                            placement="top"
                            triggers="hover"
                            content="Rubric">
                            <b-button
                                variant="secondary"
                                v-b-toggle.rubric-collapse>
                                <icon name="bars"></icon>
                            </b-button>
                        </b-popover>
                    </b-input-group-button>
                </b-input-group>
            </div>
            <div class="col-6">
                <b-input-group>
                    <b-form-input
                        :textarea="true"
                        :placeholder="editable ? 'Feedback' : 'No feedback given :('"
                        :rows="3"
                        ref="field"
                        v-model="feedback"
                        @keydown.native.tab.capture="expandSnippet"
                        :disabled="!editable">
                    </b-form-input>
                </b-input-group>
            </div>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/bars';
import 'vue-awesome/icons/refresh';
import { mapActions, mapGetters } from 'vuex';
import RubricViewer from './RubricViewer';

export default {
    name: 'grade-viewer',

    props: {
        editable: {
            type: Boolean,
            default: false,
        },
        assignment: {
            type: Object,
            default: {},
        },
        submission: {
            type: Object,
            default: {},
        },
        rubric: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            submitting: false,
            submitted: false,
            feedback: '',
            grade: 0,
            rubricScore: {},
        };
    },

    watch: {
        rubricScore({ total, max }) {
            this.grade = 10 * (total / max);
        },
    },

    mounted() {
        this.feedback = this.submission.feedback || '';
        this.grade = this.submission.grade || 0;
    },

    methods: {
        expandSnippet(event) {
            const field = this.$refs.field;
            const end = field.$el.selectionEnd;
            if (field.$el.selectionStart === end) {
                event.preventDefault();
                const val = this.feedback.slice(0, end);
                const start = Math.max(val.lastIndexOf(' '), val.lastIndexOf('\n')) + 1;
                const res = this.snippets()[val.slice(start, end)];
                if (res !== undefined) {
                    this.feedback = val.slice(0, start) + res.value + this.feedback.slice(end);
                }
                if (Math.random() < 0.25) {
                    this.refreshSnippets();
                }
            }
        },

        putFeedback() {
            this.submitting = true;
            this.$http.patch(`/api/v1/submissions/${this.submission.id}`,
                {
                    grade: this.grade,
                    feedback: this.feedback,
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                this.submitting = false;
                this.submitted = true;
                this.$emit('submit');
                this.$nextTick(() => setTimeout(() => {
                    this.submitted = false;
                }, 1000));
                this.$emit('gradeChange', this.grade);
            });
        },

        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
        }),

        ...mapGetters({
            snippets: 'user/snippets',
        }),
    },

    components: {
        Icon,
        RubricViewer,
    },
};
</script>
