<template>
    <div class="grade-viewer row" v-if="show">
        <div class="col-6">
            <b-input-group>
                <b-input-group-button>
                    <b-button :variant="submitted ? 'success' : 'primary'" v-on:click="putFeedback()" v-if="editable">
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
                            v-model:value="feedback"
                            :disabled="!editable">
              </b-form-input>
            </b-input-group>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { bButton, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';

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
            this.$http.get(`/api/v1/submissions/${this.submissionId}`).then((data) => {
                this.grade = data.data.grade;
                this.feedback = data.data.comment;
                this.show = true;
                console.log(data.data);
            });
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
            });
        },
    },

    components: {
        bButton,
        bInputGroup,
        bInputGroupButton,
        Icon,
    },
};
</script>

<style lang="less" scoped>
input.grade {
    text-align: right;
    &::-webkit-inner-spin-button {
        -webkit-appearance: none;
    }
    -moz-appearance: textfield;
    appearance: textfield;
    padding-right: 1em;
}
input:disabled, textarea:disabled {
    background: white;
    cursor: text;
}
</style>
