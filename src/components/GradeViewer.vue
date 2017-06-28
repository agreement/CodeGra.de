<template>
    <div class="grade-viewer">
        <div class="row">
            <div class="col-6">
                <b-input-group>
                    <b-input-group-button v-if="editable">
                        <b-popover :show="grade < 0 || grade > 10"
                                   content="Grade have to be between 0 and 10">
                            <b-button :variant="submitted ? 'success' : 'primary'"
                                      v-on:click="putFeedback"
                                      class="grade-submit"
                                      :disabled="grade < 0 || grade > 10">
                                <loader :scale="1" v-if="submitting"/>
                                <span v-else>Submit all</span>
                            </b-button>
                        </b-popover>
                    </b-input-group-button>

                    <b-form-input type="number"
                                  step="any"
                                  min="0"
                                  max="10"
                                  :disabled="!editable"
                                  placeholder="Grade"
                                  v-model="grade">
                    </b-form-input>
                </b-input-group>
            </div>
            <div class="col-6">
                <b-input-group>
                    <b-form-input :textarea="true"
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
import 'vue-awesome/icons/refresh';
import { mapActions, mapGetters } from 'vuex';

import Loader from './Loader';

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
            submission: null,
            submitting: false,
            submitted: false,
            feedback: '',
            grade: '',
        };
    },

    mounted() {
        this.grade = this.submission.grade ? this.submission.grade : '';
        this.feedback = this.submission.comment ? this.submission.comment : '';
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
        Loader,
    },
};
</script>

<style lang="less">
.grade-viewer .grade-submit .loader {
    height: 1.25rem;
}
</style>
