<template>
<div class="grade-viewer">
    <b-collapse id="rubric-collapse"
                v-if="showRubric">
        <rubric-viewer
            v-model="rubricPoints"
            style="margin-bottom: 15px;"
            :editable="editable"
            :submission="submission"
            :rubric="rubric"
            ref="rubricViewer"/>
    </b-collapse>
    <b-alert :class="{closed: Object.keys($refs.rubricViewer.outOfSync).length === 0,
                     'out-of-sync-alert': true,}"
             show
             v-if="showRubric && $refs.rubricViewer"
             variant="warning">
        <b>The rubric is not yet saved!</b>
    </b-alert>
    <b-form-fieldset>
        <b-input-group>
            <b-input-group-prepend v-if="editable">
                <submit-button @click="putGrade" ref="submitButton"/>
            </b-input-group-prepend>

            <input type="number"
                   class="form-control"
                   step="any"
                   min="0"
                   max="10"
                   :disabled="!editable"
                   placeholder="Grade"
                   @keydown.enter="putGrade"
                   v-model="grade"/>
            <b-input-group-append class="text-right rubric-score"
                                  :class="{'rubric-overridden': rubricOverridden}"
                                  variant="warning"
                                  style="text-align: center !important; display: inline;"
                                  v-if="showRubric"
                                  is-text>
                <span v-if="rubricOverridden"
                      v-b-popover.top.hover="'Rubric grade was overridden.'">
                    {{ rubricScore }}
                </span>
                <span v-else>{{ rubricScore }}</span>
            </b-input-group-append>

            <b-input-group-append class="delete-button-group">
                <b-popover :triggers="showDeleteButton ? 'hover' : ''"
                           placement="top"
                           target="delete-grade-button">
                    {{ deleteButtonText }}
                </b-popover>
                <submit-button @click="deleteGrade"
                               id="delete-grade-button"
                               ref="deleteButton"
                               default="danger"
                               :disabled="!showDeleteButton"
                               class="delete-button"
                               style="height: 100%;"
                               label="">
                    <icon :name="rubricOverridden ? 'reply' : 'times'"/>
                </submit-button>
            </b-input-group-append>

            <b-input-group-append v-if="showRubric">
                <b-button variant="secondary"
                          v-b-popover.top.hover="'Toggle rubric'"
                          v-b-toggle.rubric-collapse>
                    <icon name="th"/>
                </b-button>
            </b-input-group-append>
        </b-input-group>
    </b-form-fieldset>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/th';
import 'vue-awesome/icons/info';
import 'vue-awesome/icons/refresh';
import 'vue-awesome/icons/reply';
import 'vue-awesome/icons/times';
import { mapActions, mapGetters } from 'vuex';
import { formatGrade } from '@/utils';
import RubricViewer from './RubricViewer';
import SubmitButton from './SubmitButton';

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
            grade: formatGrade(this.submission.grade),
            rubricPoints: {},
            rubricHasSelectedItems: false,
            externalGrade: formatGrade(this.submission.grade),
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
            return this.grade != null;
        },

        showRubric() {
            return !!(this.rubric && this.rubric.rubrics.length);
        },

        rubricOverridden() {
            if (!this.showRubric || this.grade == null) {
                return false;
            }
            if (!this.rubricHasSelectedItems) {
                return true;
            }
            const rubricGrade = Math.max(
                0,
                (this.rubricPoints.selected / this.rubricPoints.max) * 10,
            );
            return this.grade !== formatGrade(rubricGrade);
        },

        rubricScore() {
            const toFixed = (val) => {
                const fval = parseFloat(val);
                return fval.toFixed(10).replace(/[.,]([1-9]*)0+$/, '.$1').replace(/\.$/, '');
            };
            const scored = toFixed(this.rubricPoints.selected);
            const max = toFixed(this.rubricPoints.max);
            return `${scored} / ${max}`;
        },
    },

    watch: {
        submission() {
            this.grade = formatGrade(this.submission.grade) || 0;
        },

        rubric() {
            if (this.showRubric) {
                this.rubric.points.grade = this.grade;
            }
        },

        rubricPoints({ selected, max, grade }) {
            this.grade = formatGrade(grade) || null;
            this.rubricHasSelectedItems = this.$refs.rubricViewer.hasSelectedItems;
            this.rubricSelected = selected;
            this.rubricTotal = max;
            if (UserConfig.features.incremental_rubric_submission) {
                this.gradeUpdated();
            }
        },
    },

    async mounted() {
        if (this.showRubric) {
            this.rubric.points.grade = this.grade;
        }
    },

    methods: {
        gradeUpdated() {
            this.externalGrade = this.grade;
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
                    this.grade = formatGrade(data.grade) || null;
                    this.gradeUpdated();
                }
            });
            this.$refs.deleteButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        putGrade() {
            const grade = parseFloat(this.grade);
            const overrideGrade = ((this.rubricOverridden || !this.showRubric) &&
                                   this.externalGrade !== this.grade);

            if (!(grade >= 0 && grade <= 10) && overrideGrade) {
                this.$refs.submitButton.fail(`Grade '${this.grade}' must be between 0 and 10`);
                return;
            }

            const viewer = this.$refs.rubricViewer;
            const viewerReq = viewer ? viewer.submitAllItems() : Promise.resolve();
            const data = { };
            if (overrideGrade) {
                data.grade = grade;
            }

            const req = this.$http.patch(
                `/api/v1/submissions/${this.submission.id}`,
                data,
            ).then(() => {
                if (overrideGrade) {
                    this.grade = grade;
                }
                this.gradeUpdated();
            });
            this.$refs.submitButton.submit(Promise.all([req, viewerReq]).catch((err) => {
                throw err.response.data.message;
            }));
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
        SubmitButton,
        RubricViewer,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

input,
textarea {
    &:disabled {
        color: black;
        background-color: white;
        cursor: text;
    }
}

.rubric-overridden .input-group-text {
    background: fade(#f0ad4e, 50%) !important;
    cursor: help;

    #app.dark & {
        color: @text-color;
    }
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
