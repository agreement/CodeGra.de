<template>
    <div class="page assignment">
        <h2>{{ title }}</h2>

        <div class="assignment-container">
            <code-viewer v-bind:editable="false" v-bind:id="currentFileId"
                v-if="currentFileId"></code-viewer>
            <file-tree v-bind:collapsed="false" v-bind:tree="fileTree"
                v-if="fileTree"></file-tree>
        </div>
    </div>
</template>

<script>
import { CodeViewer, FileTree } from '@/components';

export default {
    name: 'assignment-page',

    data() {
        return {
            studentId: this.$route.params.sid,
            assignmentId: this.$route.params.aid,
            currentFileId: this.$route.params.fid,
            title: '',
            fileTree: null,
            currentFile: null,
        };
    },

    mounted() {
        if (!this.assignment) {
            this.getStudentAssignment();
        }
    },

    watch: {
        $route() {
            this.studentId = this.$route.params.sid;
            this.assignmentId = this.$route.params.aid;
            this.currentFileId = this.$route.params.fid;
        },
    },

    methods: {
        getStudentAssignment() {
            this.$http.get(`/api/v1/students/${this.studentId}/assignments/${this.assignmentId}`).then((data) => {
                this.title = data.body.title;
                this.fileTree = data.body.fileTree;
            });
        },
    },

    components: {
        CodeViewer,
        FileTree,
    },
};
</script>

<style lang="less">
.page.assignment {
    @file-tree-width: 10em;

    .assignment-container {
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
}
</style>
