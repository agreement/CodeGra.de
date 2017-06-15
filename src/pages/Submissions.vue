<template>
    <div class="page submission-list">
        <div class="row">
            <loader class="col-md-6 text-center" v-if="loading"></loader>
            <div class="col-md-6" v-else>
                <h1>Submissions</h1>
                <submission-list :submissions="submissions"></submission-list>
                <submissions-exporter :id="assignmentId"></submissions-exporter>
            </div>

            <div class="col-md-6">
                <h1>Submit work for assignment {{ assignmentId }}</h1>
                <code-uploader :assignmentId="assignmentId"></code-uploader>
            </div>
        </div>
    </div>
</template>

<script>
import { SubmissionList, CodeUploader, Loader, SubmissionsExporter }
    from '@/components';

export default {
    name: 'submission-list-page',

    data() {
        return {
            loading: true,
            assignmentId: this.$route.params.assignmentId,
            submissions: [],
        };
    },

    mounted() {
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then((data) => {
            this.loading = false;
            this.submissions = data.data;
        });
    },

    components: {
        SubmissionList,
        CodeUploader,
        Loader,
        SubmissionsExporter,
    },
};
</script>

<style lang="less">
.loader {
    padding-top: 3.5em;
}
</style>
