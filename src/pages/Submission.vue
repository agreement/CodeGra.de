<template>
    <div class="page submission">
        <h1>{{ title }}</h1>

        <div class="row">
            <div class="col-lg-10 justify-content-end">
                <code-viewer class="" v-bind:editable="true"
                    v-bind:id="fileId" v-if="fileId"></code-viewer>
                <grade-viewer v-bind:id="submissionId"></grade-viewer>
            </div>

            <file-tree class="col-lg-2" v-bind:collapsed="false"
                v-bind:tree="fileTree" v-if="fileTree"></file-tree>
        </div>
    </div>
</template>

<script>
import { CodeViewer, FileTree, GradeViewer } from '@/components';

export default {
    name: 'assignment-page',

    data() {
        return {
            submissionId: this.$route.params.submissionId,
            fileId: this.$route.params.fileId,
            title: '',
            fileTree: null,
            grade: 0,
            feedback: '',
        };
    },

    mounted() {
        this.getSubmission();
    },

    watch: {
        $route() {
            this.submissionId = this.$route.params.submissionId;
            this.fileId = this.$route.params.fileId;
        },
    },

    methods: {
        getSubmission() {
            this.$http.get(`/api/v1/submission/${this.submissionId}`).then((data) => {
                this.title = data.body.title;
                this.fileTree = data.body.fileTree;
                this.grade = data.body.grade;
                this.feedback = data.body.feedback;
            });
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
.code-viewer {
    margin-bottom: 30px;
}
</style>
