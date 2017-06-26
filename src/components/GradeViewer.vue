<template>
    <div class="grade-viewer">
        <div class="row">
            <div class="col-6">
                <b-input-group>
                    <b-input-group-button v-if="editable">
                        <b-button :variant="submitted ? 'success' : 'primary'" v-on:click="putFeedback()">
                            <icon name="refresh" spin v-if="submitting"></icon>
                            <span v-else>Submit all</span>
                        </b-button>
                    </b-input-group-button>

                    <b-form-input type="number"
                                step="any"
                                min="0"
                                max="10"
                                :disabled="!editable"
                                placeholder="Grade"
                                v-model="submission.grade">
                    </b-form-input>
                </b-input-group>
            </div>
            <div class="col-6">
                <b-input-group>
                    <b-form-input :textarea="true"
                        :placeholder="editable ? 'Feedback' : 'No feedback given :('"
                        :rows="3"
                        ref="field"
                        v-model="submission.feedback"
                        v-on:keydown.native.tab.capture="expandSnippet"
                        :disabled="!editable">
                    </b-form-input>
                </b-input-group>
            </div>
        </div>
        <feedback-exporter :id="submission.id"></feedback-exporter>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { bButton, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';

import { mapActions, mapGetters } from 'vuex';

import FeedbackExporter from './FeedbackExporter';

export default {
    name: 'grade-viewer',

    props: {
        editable: {
            type: Boolean,
            default: false,
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
        };
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
        bButton,
        bInputGroup,
        bInputGroupButton,
        Icon,
        FeedbackExporter,
    },
};
</script>
