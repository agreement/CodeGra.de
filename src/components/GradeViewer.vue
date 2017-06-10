<template>
    <div class="grade-viewer row">
        <div class="col-lg-5">
            <div class="input-group">
                <div class="input-group-btn">
                    <button type="button" class="btn btn-primary dropdown-toggle input-lg"
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"
                        v-on:click="putFeedback()">Submit All</button>
                </div>
                <input type="number" step="any" min="0" max="10" class="form-control input-lg"
                    aria-label="Grade" placeholder="Grade" v-model:value="grade">
            </div>
        </div>
        <div class="col-lg-5">
            <div class="input-group">
                <textarea type="text" class="form-control" aria-label="Feedback"
                    placeholder="Feedback" rows="3" v-model="feedback">
                    {{ feedback }}
                </textarea>
            </div>
        </div>
    </div>
</template>

<script>
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
};
</script>
