<template>
  <div class="page submission-list">
      <div class="row">
        <loader :class="`col-md-${canUpload ? 6 : 12} text-center`" v-if="loading < 2"></loader>
        <div :class="`col-md-${canUpload ? 6 : 12}`" v-else>
            <h1>Submissions</h1>
            <submission-list :submissions="submissions"></submission-list>
            <submissions-exporter :assignment="assignment" v-if="canDownload"></submissions-exporter>
        </div>

        <div class="col-md-6" v-if="canUpload">
            <h1>Submit work for assignment {{ assignmentId }}</h1>
            <code-uploader :assignmentId="assignmentId"></code-uploader>
        </div>
      </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import { SubmissionList, CodeUploader, Loader, SubmissionsExporter }
    from '@/components';

export default {
    name: 'submission-list-page',

    data() {
        return {
            loading: 0,
            assignmentId: this.$route.params.assignmentId,
            courseId: this.$route.params.courseId,
            submissions: [],
            canUpload: false,
            assignment: null,
            canDownload: false,
        };
    },

    mounted() {
        this.hasPermission('can_submit_own_work').then((val) => {
            this.canUpload = val;
        });
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then((data) => {
            this.loading += 1;
            this.submissions = data.data;
        });
        this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
            this.loading += 1;
            this.assignment = data.data;
            this.assignment.id = this.assignmentId;
            const checkDownload = () => {
                if (this.assignment.state === 3) {
                    this.canDownload = true;
                } else {
                    this.hasPermission('can_see_grade_before_open').then((res) => {
                        this.canDownload = res;
                    });
                }
            };
            checkDownload();
            this.hasPermission('can_see_others_work').then((res) => {
                if (res) {
                    this.checkDownload();
                }
            });
        });
    },

    methods: {
        hasPermission(perm) {
            return this.u_hasPermission({ name: perm, course_id: this.courseId });
        },
        gotoSubmission(submission) {
            this.$router.push({
                name: 'submission',
                params: { submissionId: submission.id },
            });
        },
        ...mapActions({
            u_hasPermission: 'user/hasPermission',
        }),
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
