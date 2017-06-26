<template>
    <div class="grade-viewer" v-if="show">
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
                                v-model:value="grade">
                    </b-form-input>
                </b-input-group>
            </div>
            <div class="col-6">
                <b-input-group>
                    <b-form-input :textarea="true"
                        :placeholder="editable ? 'Feedback' : 'No feedback given :('"
                        :rows="3"
                        ref="field"
                        v-model:value="feedback"
                        v-on:keydown.native.tab.capture="expandSnippet"
                        :disabled="!editable">
                    </b-form-input>
                </b-input-group>
            </div>
        </div>
        <feedback-exporter :id="submissionId"></feedback-exporter>
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

    props: ['editable', 'id'],

    data() {
        return {
            submissionId: this.id,
            grade: 0,
            feedback: '',
            submitting: false,
            submitted: false,
            show: false,
        };
    },

    mounted() {
        this.getFeedback();
    },

    methods: {
        getFeedback() {
            this.$http.get(`/api/v1/submissions/${this.submissionId}`).then(({ data }) => {
                this.grade = data.grade ? data.grade : '';
                this.feedback = data.comment ? data.comment : '';
                this.show = true;
            });
        },

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
            this.$http.patch(`/api/v1/submissions/${this.submissionId}`,
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
