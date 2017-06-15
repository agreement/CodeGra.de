<template>
    <div class="grade-viewer row">
        <div class="col-6">
            <b-input-group>
                <b-input-group-button>
                    <b-button variant="primary" v-on:click="putFeedback()" v-if="editable">
                        Submit all
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
                            v-model:value="feedback"
                            :disabled="!editable">
              </b-form-input>
            </b-input-group>
        </div>
    </div>
</template>

<script>
import { bButton, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';

export default {
    name: 'grade-viewer',

    props: ['editable', 'id'],

    data() {
        return {
            submissionId: this.id,
            grade: 0,
            feedback: '',
        };
    },

    mounted() {
        this.getFeedback();
    },

    methods: {
        getFeedback() {
            this.$http.get(`/api/v1/submissions/${this.submissionId}`).then((data) => {
                this.grade = data.data.grade;
                this.feedback = data.data.comment;
            });
        },

        putFeedback() {
            this.$http.patch(`/api/v1/submissions/${this.submissionId}`,
                {
                    grade: this.grade,
                    feedback: this.feedback,
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
            });
            this.$emit('submit');
        },
    },

    components: {
        bButton,
        bInputGroup,
        bInputGroupButton,
    },
};
</script>

<style lang="less" scoped>
  input:disabled, textarea:disabled {
    background: white;
    cursor: text;
  }
</style>
