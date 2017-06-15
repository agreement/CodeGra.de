<template>
    <div class="page submission-list">
        <div class="row">
          <div class="text-center loader col-md-6" v-if="loading">
            <icon name="refresh" scale="4" spin></icon>
          </div>
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
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { SubmissionList, CodeUploader, SubmissionsExporter } from '@/components';

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
        Icon,
        SubmissionsExporter,
    },
};
</script>

<style lang="less">
.loader {
    padding-top: 3.5em;
}
</style>
