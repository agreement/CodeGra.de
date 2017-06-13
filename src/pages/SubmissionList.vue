<template>
    <div class="page submission-list">
        <div class="row">
            <div class="col-md-6">
                <h1>Submissions</h1>
                <submission-list :submissions="submissions"></submission-list>
            </div>

            <div class="col-md-6">
                <h1>Submit work for assignment {{ assignmentId }}</h1>
                <code-uploader :assignmentId="assignmentId"></code-uploader>
            </div>
        </div>
    </div>
</template>

<script>
import { SubmissionList, CodeUploader } from '@/components';

export default {
    name: 'submission-list-page',

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
            submissions: [],
        };
    },

    mounted() {
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/works`).then((data) => {
            this.submissions = data.data;
        });
    },

    components: {
        SubmissionList,
        CodeUploader,
    },
};
</script>
