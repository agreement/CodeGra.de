<template>
    <div class="GradingAssignment">
        <div class="row">
            <div class="col-lg-6">
                <div class="input-group">
                    <div class="input-group-btn">
                        <button type="button" class="btn btn-primary dropdown-toggle input-lg" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" v-on:click="submitGradeAndGenFeedback()">Submit All</button>
                    </div>
                    <input type="number" step="any" min="0" max="10"  class="form-control input-lg" aria-label="Grade" placeholder="Grade" v-model:value="grade">
                </div>
            </div>
            <div class="col-lg-6">
                <div class="input-group">
                    <textarea type="text" class="form-control" aria-label="General feedback" placeholder="General feedback" rows="3" v-model="general_feedback"></textarea>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'grade-viewer',

    props: ['editable'],

    data() {
        return {
            work_id: this.$route.params.id,
            grade: null,
            general_feedback: '',
        };
    },

    mounted() {
        if (!this.grade) {
            this.getGradeAndGenFeedback();
        }
    },

    methods: {
        getGradeAndGenFeedback() {
            this.$http.get(`/api/v1/work/${this.work_id}/general-feedback/`).then((data) => {
                Object.assign(this, data.body);
            });
        },

        submitGradeAndGenFeedback() {
            this.$http.put(`/api/v1/work/${this.work_id}/general-feedback/`,
                {
                    id: this.id,
                    grade: this.grade,
                    general_feedback: this.general_feedback,
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                console.log('submitted grade and feedback!');
            });
        },
    },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.input-group {
    width: 100%;
    margin: 5px;
}
</style>
