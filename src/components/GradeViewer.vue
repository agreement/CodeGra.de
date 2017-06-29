<template>
    <div class="grade-viewer">
        <b-collapse
            id="rubric-collapse"
            v-if="showRubric">
            <rubric-viewer
                v-model="rubricPoints"
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
                        v-if="!showRubric">
                    </b-form-input>
                    <b-form-input
                        class="text-right"
                        :disabled="!editable"
                        v-model="gradeAndRubricPoints"
                        v-else>
                    </b-form-input>

                    <b-input-group-button v-if="showRubric">
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
            default: {},
        },
    },

    data() {
        return {
            submitting: false,
            submitted: false,
            feedback: '',
            grade: 0,
            rubricPoints: {},
            gradeAndRubricPoints: '',
        };
    },

    computed: {
        showRubric() {
            return this.rubric.rubrics.length;
        },
    },

    watch: {
        grade(grade) {
            this.$emit('gradeChange', grade);
        },

        rubricPoints({ selected, max, grade }) {
            if (grade) this.grade = grade;
            this.gradeAndRubricPoints = `${this.grade} ( ${selected} / ${max} )`;
        },

        gradeAndRubricPoints(value) {
            console.log(value, parseFloat(value));
            this.grade = parseFloat(value);
        },
    },

    mounted() {
        this.feedback = this.submission.feedback || '';
        this.grade = this.submission.grade || 0;

        if (this.showRubric) {
            this.rubric.points.grade = this.grade;
        }
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
            console.log(this.grade);

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
