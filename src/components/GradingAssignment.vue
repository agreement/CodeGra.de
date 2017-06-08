<template>
    <div class="GradingAssignment">
        <div class="row">
            <div class="col-lg-6">
                <div class="input-group">
                    <div class="input-group-btn">
                        <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" v-on:click="submitGradeAndGenFeedback($event)">Submit All</button>
                    </div>
                    <input type="number" step="any" min="0" max="10"  class="form-control" aria-label="Grade" placeholder="Grade">
                </div>
            </div>
            <div class="col-lg-6">
                <div class="input-group">
                    <textarea type="text" class="form-control" aria-label="General feedback" placeholder="General feedback" rows="3"></textarea>
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
            id: this.$route.params.id,
            grade: this.$route.params.grade,
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
            this.$http.get('/api/v1/general-feedback/${this.id}').then((data) => {
                Object.assign(this, data.body);
            });
        },

        submitGradeAndGenFeedback(event) {
            console.log(event);
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
