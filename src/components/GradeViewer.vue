<template>
    <div class="grade-viewer">
        <b-collapse
            id="rubric-collapse"
            v-if="rubrics">
            <rubric-viewer
                v-model="rubricSelected"
                :editable="editable"
                :rubrics="rubrics"
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
                        :disabled="!!rubrics || !editable"
                        placeholder="Grade"
                        v-model="grade">
                    </b-form-input>
                    <b-input-group-button v-if="rubrics">
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
                        v-on:keydown.native.tab.capture="expandSnippet"
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
    },

    data() {
        return {
            submitting: false,
            submitted: false,
            feedback: this.submission.feedaback || '',
            grade: this.submission.grade || 0,
            rubricSelected: this.submission.rubric || [2, 5, 8],
            rubrics: this.assignment.rubrics || [
                {
                    id: 0,
                    header: 'Header 1',
                    description: 'Description for header 1',
                    items: [
                        {
                            id: 0,
                            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed fringilla, purus vitae vulputate vulputate, libero nunc tincidunt massa, at iaculis orci felis a risus. Nunc varius velit at ipsum tempor consequat. Etiam commodo lacus quis ante rhoncus blandit. Nam sed nisi congue, tempus est eu, ullamcorper ipsum.',
                            points: 0,
                        },
                        {
                            id: 1,
                            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed fringilla, purus vitae vulputate vulputate, libero nunc tincidunt massa, at iaculis orci felis a risus. Nunc varius velit at ipsum tempor consequat. ',
                            points: 1,
                        },
                        {
                            id: 2,
                            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed fringilla, purus vitae vulputate vulputate, libero nunc tincidunt massa, at iaculis orci felis a risus. Nunc varius velit at ipsum tempor consequat. Etiam commodo lacus quis ante rhoncus blandit.',
                            points: 2,
                        },
                        {
                            id: 3,
                            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed fringilla, purus vitae vulputate vulputate, libero nunc tincidunt massa, at iaculis orci felis a risus. ',
                            points: 3,
                        },
                    ],
                },
                {
                    id: 1,
                    header: 'Header 2',
                    description: 'Description for header 2',
                    items: [
                        {
                            id: 4,
                            description: 'Description 1',
                            points: 0,
                        },
                        {
                            id: 5,
                            description: 'Description 1',
                            points: 1,
                        },
                        {
                            id: 6,
                            description: 'Description 1',
                            points: 2,
                        },
                        {
                            id: 7,
                            description: 'Description 1',
                            points: 3,
                        },
                    ],
                },
                {
                    id: 1,
                    header: 'Header 2',
                    description: 'Description for header 2',
                    items: [
                        {
                            id: 8,
                            description: 'Description 1',
                            points: 0,
                        },
                        {
                            id: 9,
                            description: 'Description 1',
                            points: 1,
                        },
                        {
                            id: 10,
                            description: 'Description 1',
                            points: 2,
                        },
                        {
                            id: 11,
                            description: 'Description 1',
                            points: 3,
                        },
                    ],
                },
            ],
        };
    },

    watch: {
        rubricSelected() {
            const total = this.$refs.rubricViewer.totalPoints();
            const max = this.$refs.rubricViewer.maxPoints();
            this.grade = 10 * (total / max);
        },
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
                    rubric: this.rubricResult.selected,
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
