<template>
    <div class="grade-viewer">
        <b-collapse id="rubric-collapse"
                    v-if="showRubric">
            <rubric-viewer
                v-model="rubricPoints"
                :editable="editable"
                :submission="submission"
                :rubric="rubric"
                @gradeUpdated="gradeUpdated"
                ref="rubricViewer">
            </rubric-viewer>
        </b-collapse>
        <div class="row">
            <div class="col-6">
                <b-input-group>
                    <b-input-group-button v-if="editable">
                        <submit-button @click="putFeedback" ref="submitButton"/>
                    </b-input-group-button>

                    <b-form-input type="number"
                                  step="any"
                                  min="0"
                                  max="10"
                                  :disabled="!editable"
                                  placeholder="Grade"
                                  @keyup.enter="putFeedback"
                                  v-model="grade"
                                  v-if="!showRubric"/>
                    <b-form-input class="text-right"
                                  :disabled="!editable"
                                  v-model="gradeAndRubricPoints"
                                  v-else/>
                    <b-input-group-button v-if="editable && grade">
                        <b-popover triggers="hover" placement="top" :content="showRubric ?
                                                                              'Reset the grade to the grade from the rubric' :
                                                                              'Delete grade'">
                            <submit-button @click="deleteGrade"
                                           ref="deleteButton"
                                           default="danger"
                                           label='✖'/>
                        </b-popover>
                    </b-input-group-button>

                    <b-input-group-button v-if="showRubric">
                        <b-popover placement="top"
                                   triggers="hover"
                                   content="Rubric">
                            <b-button variant="secondary"
                                      v-b-toggle.rubric-collapse>
                                <icon name="bars"/>
                            </b-button>
                        </b-popover>
                    </b-input-group-button>
                </b-input-group>
                <grade-history v-if="gradeHistory"
                               style="margin-top: 0.5em; width: 100%;"
                               ref="gradeHistory"
                               :submissionId="submission.id"
                               :isLTI="assignment.course.is_lti"/>
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
import SubmitButton from './SubmitButton';
import GradeHistory from './GradeHistory';

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
            default: null,
        },
        rubric: {
            type: Object,
            default: {},
        },
    },

    data() {
        return {
            feedback: this.submission.comment,
            grade: this.submission.grade,
            rubricPoints: {},
            gradeAndRubricPoints: '',
            gradeHistory: false,
        };
    },

    computed: {
        showRubric() {
            return this.rubric && this.rubric.rubrics.length;
        },
    },

    watch: {
        submission() {
            this.feedback = this.submission.comment || '';
            this.grade = this.submission.grade || 0;
        },

        rubric() {
            if (this.showRubric) {
                this.rubric.points.grade = this.grade;
            }
        },

        rubricPoints({ selected, max, grade }) {
            if (grade) this.grade = Number(grade.toFixed(2));
            this.gradeAndRubricPoints = `${this.grade} ( ${selected} / ${max} )`;
        },

        gradeAndRubricPoints(value) {
            this.grade = parseFloat(value);
        },
    },

    mounted() {
        if (this.showRubric) {
            this.rubric.points.grade = this.grade;
        }
        this.hasPermission({ name: 'can_see_grade_history', course_id: this.assignment.course.id }).then((val) => {
            this.gradeHistory = val;
        });
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

        gradeUpdated() {
            if (this.$refs.gradeHistory) {
                this.$refs.gradeHistory.updateHistory();
            }
            this.$emit('gradeUpdated', this.grade);
        },

        deleteGrade() {
            const req = this.$http.patch(`/api/v1/submissions/${this.submission.id}`, { grade: null });
            req.then(({ data }) => {
                this.grade = data.grade;
                this.gradeUpdated(data.grade);
            });
            this.$refs.deleteButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        putFeedback() {
            const grade = parseFloat(this.grade);
            if (!(grade >= 0 && grade <= 10)) {
                this.$refs.submitButton.fail(`Grade '${this.grade}' must be between 0 and 10`);
                return;
            }

            const req = this.$http.patch(`/api/v1/submissions/${this.submission.id}`, {
                grade,
                feedback: this.feedback || '',
            });
            req.then(() => {
                this.grade = grade;
                this.gradeUpdated(grade);
            });
            this.$refs.submitButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
            hasPermission: 'user/hasPermission',
        }),

        ...mapGetters({
            snippets: 'user/snippets',
        }),
    },

    components: {
        Icon,
        SubmitButton,
        GradeHistory,
        RubricViewer,
    },
};
</script>

<style lang="less" scoped>
input,
textarea {
    &:disabled {
        color: black;
        background-color: white;
        cursor: text;
    }
}
</style>

<style lang="less">
.grade-viewer .grade-submit .loader {
    height: 1.25rem;
}
</style>
