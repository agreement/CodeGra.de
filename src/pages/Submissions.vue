<template>
    <loader :class="`col-md-12 text-center`" v-if="loading"/>
    <div class="page submission-list" v-else>
        <h1>
            Submissions for {{ assignment.name }} in
            <router-link :to="{ name: canManage ? 'courses' : 'assignments',
                              query: { q: course.name }}">
                {{ course.name }}
            </router-link>
        </h1>
        <submission-list
            :assignment="assignment"
            :submissions="submissions"
            :canDownload="canDownload"/>
        <b-popover
            placement="top"
            :triggers="assignment.is_lti && !inLTI ? ['hover'] : []"
            content="You can only submit this assignment from within your LMS">
            <file-uploader
                :url="`/api/v1/assignments/${this.assignmentId}/submission`"
                @response="goToSubmission"
                v-if="canUpload"/>
        </b-popover>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import { SubmissionList, Loader } from '@/components';
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
            canManage: true,
            inLTI: window.inLTI,
        };
    },

    computed: {
        assignmentId() {
            return this.$route.params.assignmentId;
        },
        courseId() {
            return this.$route.params.courseId;
        },
        courseLink() {
            return `/assignments?q=${this.course.name}`;
        },
    },

    mounted() {
        this.loading = true;
        Promise.all([
            this.$http.get(`/api/v1/courses/${this.courseId}`),
            this.$http.get(`/api/v1/assignments/${this.assignmentId}`),
            this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`),
        ]).then(([{ data: course }, { data: assignment }, { data: submissions }]) => {
            this.loading = false;

            this.course = course;
            this.assignment = assignment;
            this.submissions = submissions;

            this.hasPermission([
                'can_submit_own_work',
                'can_see_others_work',
                'can_see_grade_before_open',
                'can_manage_course',
            ]).then(([submit, others, before, manage]) => {
                this.canUpload = submit && this.assignment.state === assignmentState.SUBMITTING;
                this.canManage = manage;

                if (others) {
                    if (this.assignment.state === assignmentState.DONE) {
                        this.canDownload = true;
                    } else {
                        this.canDownload = before;
                    }
                }
            });

            setPageTitle(`${assignment.name} ${pageTitleSep} Submissions`);

            submissions.forEach((sub) => {
                sub.created_at = moment.utc(sub.created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
            });
        }, (err) => {
            // eslint-disable-next-line
            console.dir(err);
        });
    },

    methods: {
        hasPermission(perm) {
            return this.u_hasPermission({ name: perm, course_id: this.courseId });
        },

        goToSubmission({ data: submission }) {
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
        FileUploader,
        SubmissionList,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.loader {
    padding-top: 3.5em;
}
</style>
