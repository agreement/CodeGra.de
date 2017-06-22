<template>
  <div class="page submission-list">
      <div class="row">
        <loader :class="`col-md-${canUpload ? 6 : 12} text-center`" v-if="loading < 3"></loader>
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
import moment from 'moment';

import * as assignmentState from '../store/assignment-states';

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
            showAssignedFilter: false,
        };
    },

    mounted() {
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then(({ data }) => {
            this.partDone();
            for (let i = 0, len = data.length; i < len; i += 1) {
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
            }
            this.submissions = data;
        });

        this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
            this.assignment = data.data;
            this.assignment.id = this.assignmentId;

            this.hasPermission('can_submit_own_work').then((val) => {
                this.canUpload = val && this.assignment.open;
                this.partDone();
            });

            const checkDownload = () => {
                if (this.assignment.state === assignmentState.DONE) {
                    this.canDownload = true;
                    this.partDone();
                } else {
                    this.hasPermission('can_see_grade_before_open').then((res) => {
                        this.canDownload = res;
                        this.partDone();
                    });
                }
            };

            this.hasPermission('can_see_others_work').then((res) => {
                if (res) {
                    checkDownload();
                } else {
                    this.partDone();
                }
            });
        });
    },

    methods: {
        hasPermission(perm) {
            return this.u_hasPermission({ name: perm, course_id: this.courseId });
        },

        partDone() {
            this.loading += 1;
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

<style lang="less" scoped>
.loader {
    padding-top: 3.5em;
}
</style>
