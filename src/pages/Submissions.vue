<template>
    <loader :class="`col-md-12 text-center`" v-if="loading"/>
    <div class="page submission-list" v-else>
        <h4>
            Submissions for {{ assignment.name }} in
            <router-link :to="courseRoute"
                         v-if="canManage || !inLTI">
                {{ course.name }}
            </router-link>
            <span v-else>{{ course.name }}</span>
        </h4>

        <submission-list
            :assignment="assignment"
            :submissions="submissions"
            :canDownload="canDownload"
            :rubric="rubric"
            :graders="graders"
            @assigneeUpdated="updateAssignee"/>

        <b-modal id="wrong-files-modal" hide-footer>
            <p>The following files should not be in your archive according to the <code style="margin: 0 0.25rem;">.cgignore</code> file:</p>
            <ul style="list-style-type: none">
                <li style="margin-right: 2px; padding: 0.5em;" v-for="file in wrongFiles">
                    <code style="margin-right: 0.25rem">{{ file[0] }}</code> is ignored by <code>{{ file[1] }}</code>
                </li>
            </ul>
            <b-button-toolbar justify>
                <submit-button ref="submitDelete"
                               label="Delete files" default="danger"
                               @click="overrideSubmit('delete', $refs.submitDelete)"/>
                <submit-button ref="submitKeep"
                               label="Keep files" default="warning"
                               @click="overrideSubmit('keep', $refs.submitKeep)"/>
                <submit-button label="Cancel submission"
                               @click="$root.$emit('hide::modal', 'wrong-files-modal');"/>
            </b-button-toolbar>
        </b-modal>

        <b-popover
            placement="top"
            :triggers="assignment.is_lti && !inLTI ? ['hover'] : []"
            content="You can only submit this assignment from within your LMS">
            <file-uploader
                ref="uploader"
                :url="`/api/v1/assignments/${this.assignmentId}/submission?ignored_files=error`"
                :show-empty="true"
                @error="uploadError"
                @response="goToSubmission"
                v-if="canUpload"/>
        </b-popover>
    </div>
</template>

<script>
import { SubmissionList, Loader, SubmitButton } from '@/components';
import { MANAGE_COURSE_PERMISSIONS } from '@/constants';
import moment from 'moment';

import FileUploader from '@/components/FileUploader';
import * as assignmentState from '../store/assignment-states';

import { setPageTitle, pageTitleSep } from './title';

export default {
    name: 'submissions-page',

    data() {
        return {
            loading: true,
            submissions: [],
            canUpload: false,
            assignment: null,
            course: null,
            canDownload: false,
            canManage: false,
            rubric: null,
            graders: null,
            inLTI: window.inLTI,
            wrongFiles: [],
        };
    },

    computed: {
        assignmentId() {
            return this.$route.params.assignmentId;
        },

        courseId() {
            return this.$route.params.courseId;
        },

        courseRoute() {
            if (this.canManage) {
                return { name: 'assignment_manage', params: { courseId: this.course.id } };
            }
            return { name: 'assignments', query: { q: this.course.name } };
        },
    },

    mounted() {
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
                    'can_see_others_work',
                    'can_see_grade_before_open',
                    'can_upload_after_deadline',
                    ...MANAGE_COURSE_PERMISSIONS,
                ],
                this.courseId,
            ).then(([submit, others, before, afterDeadline, ...manage]) => {
                this.canUpload = (
                    submit &&
                        (this.assignment.state === assignmentState.SUBMITTING ||
                         (afterDeadline && this.assignment.state !== assignmentState.HIDDEN))
                );
                this.canManage = manage.some(x => x);

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

    methods: {
        uploadError(err) {
            if (err.data.code !== 'INVALID_FILE_IN_ARCHIVE') return;

            // We need the double next ticks as next ticks are executed before
            // data updates of the next tick.
            this.$nextTick(() => {
                this.$nextTick(() => {
                    this.$refs.uploader.$refs.submitButton.reset();
                });
            });

            this.wrongFiles = err.data.invalid_files;
            this.$root.$emit('show::modal', 'wrong-files-modal');
        },

        overrideSubmit(type, btn) {
            const requestData = this.$refs.uploader.requestData;
            const url = `/api/v1/assignments/${this.assignmentId}/submission?ignored_files=${type}`;
            btn.submit(this.$http.post(url, requestData).then((res) => {
                this.goToSubmission(res);
            }, ({ response }) => {
                this.$emit('error', response);
                throw response.data.message;
            }));
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
        FileUploader,
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
