<template>
    <loader :class="`col-md-12 text-center`" v-if="loading < 2"></loader>
    <div class="page submission-list" v-else>
        <h1>Submissions for {{ assignment.name }}</h1>

        <submission-list :submissions="submissions"></submission-list>
        <code-uploader :assignment="assignment" v-if="canUpload"></code-uploader>
        <submissions-exporter :assignment="assignment" v-if="canDownload"></submissions-exporter>
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
        const partDone = () => {
            this.loading += 1;
        };

        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then(({ data }) => {
            partDone();
            this.submissions = data;
            for (let i = 0, len = data.length; i < len; i += 1) {
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
            }
        });

        this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
            this.assignment = data.data;
            this.assignment.id = this.assignmentId;

            this.hasPermission(['can_submit_own_work', 'can_see_others_work', 'can_see_grade_before_open']).then(([submit, others, before]) => {
                this.canUpload = submit && this.assignment.open;

                if (others && this.assignment.state === assignmentState.DONE) {
                    this.canDownload = true;
                } else if (others) {
                    this.canDownload = before;
                }
                partDone();
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

<style lang="less" scoped>
.loader {
    padding-top: 3.5em;
}
</style>
