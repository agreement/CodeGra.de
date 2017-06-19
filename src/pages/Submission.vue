<template>
    <div class="page submission container">
        <div class="row justify-content-center code-browser">
            <h1>{{ title }}</h1>
            <div class="col-10 code-and-grade">
                <pdf-viewer v-if="fileExtension === 'pdf'" :id="fileId"></pdf-viewer>
                <code-viewer class="" v-bind:editable="editable" v-bind:id="fileId" v-else-if="fileExtension != ''" ref="codeViewer"></code-viewer>
                <grade-viewer v-bind:id="submissionId" :editable="editable" v-on:submit="submitAllFeedback($event)"></grade-viewer>
            </div>

            <loader class="col-2 text-center" :scale="3" v-if="!fileTree"></loader>
            <file-tree class="col-2" v-bind:collapsed="false" v-bind:submissionId="submissionId" v-bind:tree="fileTree" v-else></file-tree>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import { CodeViewer, FileTree, GradeViewer, Loader, PdfViewer } from '@/components';

function getFirstFile(fileTree) {
    // Returns the first file in the file tree that is not a folder
    // The file tree is searched with BFS
    const queue = [fileTree];
    let candidate = null;

    while (queue.length > 0) {
        candidate = queue.shift();

        if (candidate.entries) {
            queue.push(...candidate.entries);
        } else {
            return candidate;
        }
    }

    return false;
}

export default {
    name: 'submission-page',

    data() {
        return {
            assignmentId: Number(this.$route.params.assignmentId),
            submissionId: Number(this.$route.params.submissionId),
            fileId: Number(this.$route.params.fileId),
            editable: false,
            fileExtension: '',
            title: '',
            description: '',
            course_name: '',
            courseId: this.$route.params.courseId,
            fileTree: null,
            grade: 0,
            showGrade: false,
            feedback: '',
        };
    },

    mounted() {
        this.hasPermission({ name: 'can_grade_work', course_id: this.courseId }).then((val) => {
            this.editable = val;
        });
        this.getSubmission();
        this.getFileMetadata();

        const elements = Array.from(document.querySelectorAll('html, body, #app, nav, footer'));
        const [html, body, app, nav, footer] = elements;

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
            nav: {
                flexGrow: nav.style.flexGrow,
                flexShrink: nav.style.flexShrink,
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
        nav.style.flexGrow = 0;
        nav.style.flexShrink = 0;
        footer.style.flexGrow = 0;
        footer.style.flexShrink = 0;
    },

    destroyed() {
        const elements = Array.from(document.querySelectorAll('html, body, #app, nav, footer'));
        const [html, body, app, nav, footer] = elements;

        html.style.height = this.oldCSS.html.height;
        body.style.height = this.oldCSS.body.height;
        app.style.height = this.oldCSS.app.height;
        app.style.display = this.oldCSS.app.display;
        app.style.flexDirection = this.oldCSS.app.flexDirection;
        nav.style.flexGrow = this.oldCSS.nav.flexGrow;
        nav.style.flexShrink = this.oldCSS.nav.flexShrink;
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
        getSubmission() {
            this.$http.get(`/api/v1/submissions/${this.submissionId}/files/`).then((data) => {
                this.fileTree = data.data;
                this.$router.replace({
                    name: 'submission_file',
                    params: {
                        submissionId: this.submissionId,
                        fileId: getFirstFile(this.fileTree).id,
                    },
                });
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
        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    components: {
        CodeViewer,
        FileTree,
        GradeViewer,
        Loader,
        PdfViewer,
    },
};
</script>

<style scoped>
.page.submission {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    flex-shrink: 1;
}

h1 {
    flex-grow: 0;
    flex-shrink: 0;
}

.code-browser {
    flex-grow: 1;
    flex-shrink: 1;
}

.code-and-grade {
    display: flex;
    flex-direction: column;
}

.pdfobject-container {
    flex-grow: 1;
}

.code-viewer {
    overflow: auto;
}

.grade-viewer {
    flex-grow: 0;
    flex-shrink: 0;
}

h1,
.code-viewer,
.pdfobject-container,
.grade-viewer {
    margin-bottom: 30px;
}

.loader {
    margin-top: 1em;
}
</style>
