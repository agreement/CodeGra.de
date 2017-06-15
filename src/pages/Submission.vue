<template>
    <div class="page submission">
        <h1>{{ title }}</h1>

        <div class="row code-browser">
            <div class="col-10 code-and-grade">
                <pdf-viewer v-if="fileExtension === 'pdf'" :id="fileId"></pdf-viewer>
                <code-viewer class="" v-bind:editable="true" v-bind:id="fileId" v-else-if="fileExtension != '' && fileId" ref="codeViewer"></code-viewer>
                <grade-viewer v-bind:id="submissionId" v-on:submit="submitAllFeedback($event)"></grade-viewer>
            </div>

            <file-tree class="col-2" v-bind:collapsed="false" v-bind:submissionId="submissionId" v-bind:tree="fileTree" v-if="fileTree"></file-tree>
        </div>
    </div>
</template>

<script>
import { CodeViewer, FileTree, GradeViewer } from '@/components';
import PdfViewer from '@/components/PdfViewer';

export default {
    name: 'submission-page',

    data() {
        return {
            assignmentId: Number(this.$route.params.assignmentId),
            submissionId: Number(this.$route.params.submissionId),
            fileId: this.$route.params.fileId,
            fileExtension: '',
            title: '',
            description: '',
            course_name: '',
            course_id: 0,
            fileTree: null,
            grade: 0,
            feedback: '',
        };
    },

    mounted() {
        this.getSubmission();
        this.getFileMetadata();

        const elements = Array.from(document.querySelectorAll('html, body, #app, header, footer'));
        const [html, body, app, header, footer] = elements;

        this.oldCSS = {
            html: {
                height: html.style.height,
            },
            body: {
                height: body.style.height,
            },
            app: {
                height: app.style.height,
                display: app.style.display,
                flexDirection: app.style.flexDirection,
            },
            header: {
                flexGrow: header.style.flexGrow,
                flexShrink: header.style.flexShrink,
            },
            footer: {
                flexGrow: footer.style.flexGrow,
                flexShrink: footer.style.flexShrink,
            },
        };

        html.style.height = '100%';
        body.style.height = '100%';
        app.style.height = '100%';
        app.style.display = 'flex';
        app.style.flexDirection = 'column';
        header.style.flexGrow = 0;
        header.style.flexShrink = 0;
        footer.style.flexGrow = 0;
        footer.style.flexShrink = 0;
    },

    destroyed() {
        const elements = Array.from(document.querySelectorAll('html, body, #app, header, footer'));
        const [html, body, app, header, footer] = elements;

        html.style.height = this.oldCSS.html.height;
        body.style.height = this.oldCSS.body.height;
        app.style.height = this.oldCSS.app.height;
        app.style.display = this.oldCSS.app.display;
        app.style.flexDirection = this.oldCSS.app.flexDirection;
        header.style.flexGrow = this.oldCSS.header.flexGrow;
        header.style.flexShrink = this.oldCSS.header.flexShrink;
        footer.style.flexGrow = this.oldCSS.footer.flexGrow;
        footer.style.flexShrink = this.oldCSS.footer.flexShrink;
    },

    watch: {
        $route() {
            this.submissionId = this.$route.params.submissionId;
            this.fileId = this.$route.params.fileId;
        },

        fileId() {
            this.getFileMetadata();
        },
    },

    methods: {
        getAssignment() {
            // this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then((data) => {
            //     this.title = data.data.name;
            //     this.description = data.data.description;
            //     this.course_name = data.data.course_name;
            //     this.course_id = data.data.course_id;
            //     this.getSubmission();
            // });
        },

        getSubmission() {
            this.$http.get(`/api/v1/submissions/${this.submissionId}/files/`).then((data) => {
                this.fileTree = data.data;
            });
        },

        getFileMetadata() {
            if (this.fileId === undefined) {
                return;
            }

            this.fileExtension = '';
            this.$http.get(`/api/v1/file/metadata/${this.fileId}`).then((response) => {
                this.fileExtension = response.data.extension;
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
        PdfViewer,
    },
};
</script>

<style scoped>
.page.submission {
    display: flex;
    flex-direction: column;
}

h1 {
    flex-grow: 0;
    flex-shrink: 0;
}

.code-and-grade {
    display: flex;
    flex-direction: column;
}

.code-viewer {
    flex-grow: 1;
    flex-shrink: 1;
    overflow: auto;
}

.grade-viewer {
    flex-grow: 0;
    flex-shrink: 0;
}

h1,
.code-viewer,
.grade-viewer {
    margin-bottom: 30px;
}
</style>
