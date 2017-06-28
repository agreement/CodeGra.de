<template>
    <loader :class="`col-md-12 text-center`" v-if="loading < 3">
    </loader>
    <div class="page submission-list" v-else>
        <h1>Submissions for {{ assignment.name }} in
            <router-link :to="{ name: 'assignments', query: { q: course.name }}">{{ course.name }}</router-link>
        </h1>
        <submission-list :assignment="assignment" :submissions="submissions" :canDownload="canDownload"></submission-list>
        <code-uploader :assignment="assignment" v-if="canUpload"></code-uploader>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import { SubmissionList, CodeUploader, Loader }
    from '@/components';
import moment from 'moment';

import * as assignmentState from '../store/assignment-states';

import { setTitle, titleSep } from './title';

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
            course: null,
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

        this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then(({ data }) => {
            setTitle(`${data.name} ${titleSep} Submissions`);

            this.assignment = data;
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

        this.$http.get(`/api/v1/courses/${this.courseId}`).then(({ data }) => {
            this.course = data;
            partDone();
        });
    },

    computed: {
        courseLink() {
            return `/assignments?q=${this.course.name}`;
        },
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
    },
};
</script>

<style lang="less" scoped>
.loader {
    padding-top: 3.5em;
}
</style>
