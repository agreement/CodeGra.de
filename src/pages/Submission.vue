<template>
    <div class="page submission">
        <h1>{{ title }}</h1>

        <div class="row">
            <div class="col-10 justify-content-end">
                <code-viewer class="" v-bind:editable="true"
                    v-bind:id="fileId" v-if="fileId" ref="codeViewer"></code-viewer>
                <grade-viewer v-bind:id="submissionId"
                    v-on:submit="submitAllFeedback($event)"></grade-viewer>
            </div>

            <file-tree class="col-2" v-bind:collapsed="false"
                v-bind:tree="fileTree" v-if="fileTree"></file-tree>
        </div>
    </div>
</template>

<script>
import { CodeViewer, FileTree, GradeViewer } from '@/components';

export default {
    name: 'submission-page',

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
            submissionId: this.$route.params.submissionId,
            fileId: this.$route.params.fileId,
            title: '',
            description: '',
            course_name: '',
            course_id: '',
            fileTree: null,
            grade: 0,
            feedback: '',
        };
    },

    mounted() {
        this.getAssignment();
        // this.getSubmission();
    },

    watch: {
        $route() {
            this.submissionId = this.$route.params.submissionId;
            this.fileId = this.$route.params.fileId;
        },
    },

    methods: {
        getAssignment() {
            this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
                this.title = data.data.name;
                this.description = data.data.description;
                this.course_name = data.data.course_name;
                this.course_id = data.data.course_id;
            });
        },

        getSubmission() {
            this.$http.get(`/api/v1/submission/${this.submissionId}`).then((data) => {
                this.title = data.data.title;
                this.fileTree = data.data.fileTree;
                this.grade = data.data.grade;
                this.feedback = data.data.feedback;
            });
        },

        submitAllFeedback(event) {
            this.$refs.codeViewer.submitAllFeedback(event);
        },
    },

    components: {
        CodeViewer,
        FileTree,
        GradeViewer,
    },
};
</script>

<style scoped>
h1,
.code-viewer,
.grade-viewer {
    margin-bottom: 30px;
}
</style>
