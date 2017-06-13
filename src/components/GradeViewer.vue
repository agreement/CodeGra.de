<template>
    <div class="grade-viewer row">
        <div class="col-6">
            <b-input-group>
                <b-input-group-button>
                    <b-button variant="primary" v-on:click="putFeedback()">
                        Submit all
                    </b-button>
                </b-input-group-button>

                <b-form-input type="number" step="any" min="0" max="10"
                    placeholder="Grade" v-model:value="grade"></b-form-input>
            </b-input-group>
        </div>
        <div class="col-6">
            <b-input-group>
                <b-form-input :textarea="true" placeholder="Feedback" :rows="3"
                    v-model:value="feedback"></b-form-input>
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
            this.$http.get(`/api/v1/submissions/${this.submissionId}/general-feedback`).then((data) => {
                this.grade = data.data.grade;
                this.feedback = data.data.feedback;
            });
        },

        putFeedback() {
            this.$http.put(`/api/v1/submissions/${this.submissionId}/general-feedback`,
                {
                    grade: this.grade,
                    feedback: this.feedback,
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                // eslint-disable-next-line
                console.log('submitted grade and feedback!');
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
