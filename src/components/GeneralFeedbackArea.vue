<template>
<div class="general-feedback-area">
    <textarea :placeholder="editable ? 'Feedback' : 'No feedback given :('"
              class="form-control"
              :rows="10"
              ref="field"
              v-model="feedback"
              @keydown.ctrl.enter="putFeedback"
              @keydown.native.tab.capture="expandSnippet"
              v-if="editable"/>
    <pre class="feedback-field"
         v-else>{{ feedback || 'No feedback given :(' }}</pre>
    <submit-button ref="submitButton"
                   @click="putFeedback"
                   v-if="editable"
                   style="margin: 15px 0; float: right;"/>
</div>
</template>

<script>
import SubmitButton from './SubmitButton';

export default {
    name: 'general-feedback-area',

    props: {
        editable: {
            type: Boolean,
            default: false,
        },
        submission: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            feedback: this.submission.comment,
        };
    },

    watch: {
        submission() {
            this.feedback = this.submission.comment || '';
        },
    },

    methods: {
        putFeedback() {
            const data = { feedback: this.feedback || '' };

            const req = this.$http.patch(
                `/api/v1/submissions/${this.submission.id}`,
                data,
            ).then(() => {
                this.$emit('updated', data.feedback);
            }, (err) => {
                throw err.response.data.message;
            });
            this.$refs.submitButton.submit(req);
        },

        expandSnippet(event) {
            const { field } = this.$refs;
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

    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.feedback-field {
    max-height: 80vh;
    margin-bottom: 0;
    padding: 0.375rem 0.75rem;
    white-space: pre-wrap;
    text-align: left;
    .default-text-colors;
}
</style>
