<template>
    <div class="page submission">
        <h2>{{ title }}</h2>

        <div class="code-browser">
            <code-viewer v-bind:editable="false" v-bind:id="fileId"
                v-if="fileId"></code-viewer>
            <file-tree v-bind:collapsed="false" v-bind:tree="fileTree"
                v-if="fileTree"></file-tree>
        </div>

        <grade-viewer v-bind:id="submissionId"></grade-viewer>
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

<style lang="less" scoped>
@file-tree-width: 10em;

.code-browser {
    display: flex;
    justify-content: flex-end;
}

.code-viewer {
    flex-grow: 1;
    flex-shrink: 1;
}

.file-tree {
    flex: 0 0 @file-tree-width;
}
</style>
