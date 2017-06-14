<template>
    <div class="page submission-list">
        <div class="row">
            <div class="col-md-6">
                <h1>Submissions</h1>
                <submission-list :submissions="submissions" v-on:goto="gotoSubmission"></submission-list>
                <div class="text-center loader" v-if="loading">
                  <icon name="refresh" scale="4" spin></icon>
                </div>
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
import { SubmissionList, CodeUploader } from '@/components';

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
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/works`).then((data) => {
            this.loading = false;
            this.submissions = data.data;
        });
    },

    methods: {
        gotoSubmission(submission) {
            this.$router.push(`/assignments/${this.assignmentId}/submissions/${submission.id}/`);
        },
    },

    components: {
        SubmissionList,
        CodeUploader,
        Icon,
    },
};
</script>

<style lang="less">
.loader {
    padding-top: 1em;
}
</style>
