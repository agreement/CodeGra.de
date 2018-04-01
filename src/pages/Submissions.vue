<template>
<loader center v-if="loading"/>
<div class="submission-list" v-else>
    <submission-list
        :assignment="assignment"
        :submissions="submissions"
        :canDownload="canDownload"
        :rubric="rubric"
        :graders="graders"
        @assigneeUpdated="updateAssignee"/>

    <div v-if="canUpload">
        <b-popover target="submission-file-uploader-wrapper"
                   placement="top"
                   v-if="fileUploaderDisabled"
                   triggers="hover">
            <span>
                {{ fileUploaderDisabledMessage }}
            </span>
        </b-popover>
        <span id="submission-file-uploader-wrapper">
            <submission-uploader :assignment="assignment"
                                 :for-others="canUploadForOthers"
                                 :disabled="fileUploaderDisabled"
                                 @created="goToSubmission"/>
        </span>
    </div>
</div>
</template>

<script>
import { SubmissionList, Loader, SubmitButton, SubmissionUploader } from '@/components';
import moment from 'moment';

import * as assignmentState from '../store/assignment-states';

import { setPageTitle, pageTitleSep } from './title';

export default {
    name: 'submissions-page',

    data() {
        return {
            loading: true,
            submissions: [],
            canUpload: false,
            canUploadForOthers: false,
            assignment: null,
            course: null,
            canDownload: false,
            rubric: null,
            graders: null,
            wrongFiles: [],
        };
    },

    computed: {
        assignmentId() {
            return Number(this.$route.params.assignmentId);
        },

        courseId() {
            return this.$route.params.courseId;
        },

        fileUploaderDisabledMessage() {
            if (this.assignment.is_lti && !this.$inLTI) {
                return 'You can only submit this assignment from within your LMS';
            } else if (this.$inLTI && this.$LTIAssignmentId == null) {
                return "You didn't launch the assignment using LTI, please navigate to the 'Assignments' page and submit your work there.";
            } else if (this.$inLTI &&
                       this.assignmentId !== this.$LTIAssignmentId) {
                return 'You launched CodeGra.de for a different assignment. Please retry opening the correct assignment.';
            } else {
                return undefined;
            }
        },

        fileUploaderDisabled() {
            if (this.assignment.is_lti && !this.$inLTI) {
                return true;
            } else if (this.$inLTI && this.$LTIAssignmentId == null) {
                return true;
            } else if (this.$inLTI &&
                       this.assignmentId !== this.$LTIAssignmentId) {
                return true;
            } else {
                return false;
            }
        },
    },

    watch: {
        assignmentId(newVal, oldVal) {
            // If the assignmentId has not changed we do not need to reload the data.
            if (newVal.toString() === oldVal.toString()) {
                return;
            }
            this.loadData();
        },
    },

    mounted() {
        this.loadData();
    },

    methods: {
        loadData() {
            this.loading = true;
            Promise.all([
                this.$http.get(`/api/v1/assignments/${this.assignmentId}`),
                this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`),
                this.$http.get(`/api/v1/assignments/${this.assignmentId}/rubrics/`).catch(() => ({ data: null })),
            ]).then(([
                { data: assignment },
                { data: submissions },
                { data: rubric },
            ]) => {
                let done = false;
                this.course = assignment.course;
                this.assignment = assignment;
                this.submissions = submissions;
                this.rubric = rubric;

                setPageTitle(`${assignment.name} ${pageTitleSep} Submissions`);

                this.$hasPermission(
                    [
                        'can_submit_own_work',
                        'can_submit_others_work',
                        'can_see_others_work',
                        'can_see_grade_before_open',
                        'can_upload_after_deadline',
                    ],
                    this.courseId,
                ).then(([submitOwn, submitOthers, others, before, afterDeadline]) => {
                    this.canUploadForOthers = submitOthers;
                    this.canUpload = (
                        (submitOwn || submitOthers) &&
                            (this.assignment.state === assignmentState.SUBMITTING ||
                             (afterDeadline && this.assignment.state !== assignmentState.HIDDEN))
                    );

                    if (others) {
                        if (this.assignment.state === assignmentState.DONE) {
                            this.canDownload = true;
                        } else {
                            this.canDownload = before;
                        }
                    }

                    if (done) this.loading = false;
                    done = true;
                });

                submissions.forEach((sub) => {
                    sub.created_at = moment.utc(sub.created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
                });

                if (done) this.loading = false;
                done = true;
            }, (err) => {
                // eslint-disable-next-line
                console.dir(err);
            });

            this.$hasPermission([
                'can_assign_graders',
                'can_see_assignee',
            ], this.courseId).then(([assign, see]) => {
                if (assign && see) {
                    this.$http.get(`/api/v1/assignments/${this.assignmentId}/graders/`).then(({ data }) => {
                        this.graders = data;
                    }).catch(() => {
                        this.graders = null;
                    });
                }
            });
        },

        goToSubmission({ data: submission }) {
            this.$router.push({
                name: 'submission',
                params: { submissionId: submission.id },
            });
        },

        updateAssignee(submission, assignee) {
            this.submissions = this.submissions.map((sub) => {
                if (sub.id === submission.id) {
                    sub.assignee = assignee;
                }
                return sub;
            });
        },
    },

    components: {
        SubmissionUploader,
        SubmissionList,
        Loader,
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
.loader {
    padding-top: 3.5em;
}

#wrong-files-modal ul {
    max-height: 50vh;
    overflow-y: auto;

}
</style>
