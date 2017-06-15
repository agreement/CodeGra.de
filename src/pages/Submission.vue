<template>
    <div class="page submission">
        <h1>{{ title }}</h1>

        <div class="row code-browser">
            <div class="col-10 code-and-grade">
                <code-viewer class="" v-bind:editable="editable"
                    v-bind:id="fileId" v-if="fileId" ref="codeViewer"></code-viewer>
                <grade-viewer v-bind:id="submissionId" :editable="editable"
                    v-on:submit="submitAllFeedback($event)"></grade-viewer>
            </div>

            <loader class="col-2 text-center" :scale="3" v-if="!fileTree"></loader>
            <file-tree class="col-2" v-bind:collapsed="false" v-bind:submissionId="submissionId"
                v-bind:tree="fileTree" v-else></file-tree>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import { CodeViewer, FileTree, GradeViewer, Loader } from '@/components';

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
            assignmentId: this.$route.params.assignmentId,
            submissionId: this.$route.params.submissionId,
            fileId: this.$route.params.fileId,
            editable: false,
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
    },

    methods: {
        getSubmission() {
            this.$http.get(`/api/v1/submissions/${this.submissionId}/files/`).then((data) => {
                this.fileTree = data.data;
                this.$router.push({
                    name: 'submission_file',
                    params: {
                        submissionId: this.submissionId,
                        fileId: getFirstFile(this.fileTree).id } });
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

.loader {
    margin-top: 1em;
}
</style>
