<template>
    <div class="page submission-list">
        <div class="row">
          <div class="text-center loader col-md-6" v-if="loading">
            <icon name="refresh" scale="4" spin></icon>
          </div>
            <div :class="`col-md-${canUpload ? 6 : 11}`" v-else>
                <h1>Submissions</h1>
                <submission-list :submissions="submissions" v-on:goto="gotoSubmission"></submission-list>
            </div>

            <div class="col-md-6" v-if="canUpload">
                <h1>Submit work for assignment {{ assignmentId }}</h1>
                <code-uploader :assignmentId="assignmentId"></code-uploader>
            </div>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { mapActions } from 'vuex';
import { SubmissionList, CodeUploader } from '@/components';

export default {
    name: 'submission-list-page',

    data() {
        return {
            loading: true,
            assignmentId: this.$route.params.assignmentId,
            courseId: this.$route.params.courseId,
            submissions: [],
            canUpload: false,
        };
    },

    mounted() {
        this.hasPermission({ name: 'can_submit_own_work', course_id: this.courseId }).then((val) => {
            this.canUpload = val;
        });
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then((data) => {
            this.loading = false;
            this.submissions = data.data;
        });
    },

    methods: {
        gotoSubmission(submission) {
            this.$router.push({
                name: 'submission',
                params: { submissionId: submission.id },
            });
        },
        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
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
    padding-top: 3.5em;
}
</style>
