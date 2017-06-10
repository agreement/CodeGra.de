<template>
    <div class="grade-viewer row">
        <div class="col-6">
            <b-input-group>
                <b-input-group-button>
                    <b-dropdown variant="primary" text="Submit All"
                        v-on:click="putFeedback()"></b-dropdown>
                </b-input-group-button>

                <b-form-input type="number" step="any" min="0" max="10"
                    placeholder="Grade" v-model:value="grade"></b-form-input>
            </b-input-group>
        </div>
        <div class="col-6">
            <b-input-group>
                <b-form-input textarea="true" placeholder="Feedback" rows="3"
                    v-model="feedback"></b-form-input>
            </b-input-group>
        </div>
    </div>
</template>

<script>
import { bDropdown, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';

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
            this.$http.get(`/api/v1/submission/${this.submissionId}/general-feedback`).then((data) => {
                this.grade = data.body.grade;
                this.feedback = data.body.feedback;
            });
        },

        putFeedback() {
            this.$http.put(`/api/v1/submission/${this.submissionId}/general-feedback`,
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
        },
    },

    components: {
        bDropdown,
        bInputGroup,
        bInputGroupButton,
    },
};
</script>
