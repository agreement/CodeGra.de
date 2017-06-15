<template>
    <div class="page submission-list">
        <div class="row">
          <div class="text-center loader col-md-6" v-if="loading < 2">
            <icon name="refresh" scale="4" spin></icon>
          </div>
            <div :class="`col-md-${canUpload ? 6 : 11}`" v-else>
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
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { SubmissionList, CodeUploader, SubmissionsExporter } from '@/components';
import { mapActions } from 'vuex';

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
        this.hasPermission({ name: 'can_submit_own_work', course_id: this.courseId }).then((val) => {
            this.canUpload = val;
        });
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then((data) => {
            this.loading += 1;
            this.submissions = data.data;
        });
        this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
            this.loading += 1;
            this.assignment = data.data;
            this.hasPermission({ name: 'can_see_own_work', course_id: this.courseId }).then((val) => {
                const checkDownload = () => {
                    if (this.assignment.state === 3) {
                        this.canDownload = true;
                    } else {
                        this.hasPermission({
                            name: 'can_see_grade_before_open',
                            course_id: this.courseId,
                        }).then((res) => { this.canDownload = res; });
                    }
                };
                if (val) {
                    checkDownload();
                    this.hasPermission({ name: 'can_see_others_work', course_id: this.courseId }).then((res) => {
                        if (res) {
                            this.checkDownload();
                        }
                    });
                }
            });
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
        SubmissionsExporter,
    },
};
</script>

<style lang="less">
.loader {
    padding-top: 3.5em;
}
</style>
