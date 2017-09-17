<template>
    <div class="grade-viewer">
        <b-collapse id="rubric-collapse"
                    v-if="showRubric">
            <rubric-viewer
                v-model="rubricPoints"
                :editable="editable"
                :submission="submission"
                :rubric="rubric"
                ref="rubricViewer">
            </rubric-viewer>
        </b-collapse>
        <b-alert :class="{closed: Object.keys($refs.rubricViewer.outOfSync).length === 0,
                         'out-of-sync-alert': true,}"
                 show
                 v-if="showRubric && $refs.rubricViewer"
                 variant="warning">
            <b>The rubric is not yet saved!</b>
        </b-alert>
        <div class="row">
            <div class="col-6">
                <b-input-group>
                    <b-input-group-button v-if="editable">
                        <submit-button @click="putFeedback" ref="submitButton"/>
                    </b-input-group-button>

                    <input type="number"
                           class="form-control"
                           step="any"
                           min="0"
                           max="10"
                           :disabled="!editable"
                           placeholder="Grade"
                           @keydown.enter="putFeedback"
                           v-model="grade"/>

                    <div :class="`text-right input-group-addon
                                 ${rubricOverridden ? 'rubric-overridden' : ''}`"
                         style="text-align: center !important; display: inline;"
                         v-if="showRubric">
                        <b-popover triggers="click"
                                   placement="top"
                                   content="Rubric grade was overridden."
                                   v-if="rubricOverridden">
                            {{ rubricScore }}
                        </b-popover>
                        <span v-else>{{ rubricScore }}</span>
                    </div>
                    <b-input-group-button class="delete-button-group">
                        <b-popover :triggers="showDeleteButton ? 'hover' : ''" placement="top" :content="deleteButtonText">
                            <submit-button @click="deleteGrade"
                                           ref="deleteButton"
                                           default="danger"
                                           :disabled="!showDeleteButton"
                                           class="delete-button"
                                           style="height: 100%;"
                                           :label="rubricOverridden ? '↩' : '✖'"/>
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
                        @keydown.native.ctrl.enter="putFeedback"
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
import 'vue-awesome/icons/info';
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
            rubricHasSelectedItems: false,
            gradeHistory: false,
        };
    },

    computed: {
        deleteButtonText() {
            if (this.showRubric) {
                if (this.rubricOverridden) {
                    return 'Reset the grade to the grade from the rubric';
                }
                return 'Clear the rubric';
            }
            return 'Delete grade';
        },
        showDeleteButton() {
            if (!this.editable) {
                return false;
            }
            if (this.showRubric) {
                return this.rubricHasSelectedItems || this.rubricOverridden;
            }
            return this.grade !== null;
        },
        showRubric() {
            return this.rubric && this.rubric.rubrics.length;
        },

        rubricOverridden() {
            if (!this.showRubric || this.grade === null) {
                return false;
            }
            const rubricGrade = ((this.rubricPoints.selected / this.rubricPoints.max)
                                 * 10)
                  .toFixed(2);
            return this.grade !== rubricGrade;
        },

        rubricScore() {
            return `${this.rubricPoints.selected} / ${this.rubricPoints.max}`;
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
            this.grade = grade ? parseFloat(grade).toFixed(2) : grade;
            this.rubricHasSelectedItems = this.$refs.rubricViewer.hasSelectedItems;
            this.rubricSelected = selected;
            this.rubricTotal = max;
            if (UserConfig.features.incremental_rubric_submission) {
                this.gradeUpdated();
            }
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
            let req;
            if (this.showRubric && !this.rubricOverridden) {
                req = this.$refs.rubricViewer.clearSelected();
            } else {
                req = this.$http.patch(`/api/v1/submissions/${this.submission.id}`, { grade: null });
            }
            req.then(({ data }) => {
                if (data.grade !== undefined) {
                    this.grade = data.grade ? parseFloat(data.grade).toFixed(2) : data.grade;
                    this.gradeUpdated(data.grade);
                }
            });
            this.$refs.deleteButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        putFeedback() {
            const grade = parseFloat(this.grade);
            const overrideGrade = this.rubricOverridden || !this.showRubric;

            if (!(grade >= 0 && grade <= 10) && overrideGrade) {
                this.$refs.submitButton.fail(`Grade '${this.grade}' must be between 0 and 10`);
                return;
            }

            const viewer = this.$refs.rubricViewer;
            const viewerReq = viewer ? viewer.submitAllItems() : Promise.resolve();
            const data = { feedback: this.feedback || '' };
            if (overrideGrade) {
                data.grade = grade;
            }

            const req = this.$http.patch(`/api/v1/submissions/${this.submission.id}`, data);
            req.then(() => {
                if (overrideGrade) this.grade = grade;
                this.gradeUpdated(grade);
            });
            this.$refs.submitButton.submit(Promise.all([req, viewerReq]).catch((err) => {
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

.rubric-overridden {
    background: fade(#f0ad4e, 50%) !important;
    cursor: help;
}

.out-of-sync-alert {
    max-height: 3em;
    overflow-x: hidden;

    transition-property: all;
    transition-duration: .5s;
    margin-bottom: 1rem;
    transition-timing-function: cubic-bezier(0, 1, 0.5, 1);

    &.closed {
        max-height: 0;
        border-color: transparent;
        background: none;
        padding-top: 0;
        padding-bottom: 0;
        margin-bottom: 0;
    }
}
</style>

<style lang="less">
.grade-viewer .grade-submit .loader {
    height: 1.25rem;
}

.grade-viewer .delete-button-group > div {
    height: 100%;
    .delete-button button {
        height: 100%;
    }
}
</style>
