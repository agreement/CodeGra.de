<template>
    <div v-if="loading">
        <loader style="text-align: center; margin-top: 30px;"/>
    </div>
    <div class="page submission" v-else>
        <h2>
            <i><router-link :to="{ name: 'assignment_submissions', }">"
                    {{ assignment.name }}"
            </router-link></i>
            by {{ submission.user.name }}
        </h2>
        <div class="row submission-nav-bar">
            <div class="col-12">
                <submission-nav-bar v-if="submissions && submission"
                                    v-on:subChange="reloadSubmission"
                                    :submission="submission"
                                    :submissions="submissions"
                                    :courseId="courseId"
                                    :assignmentId="assignmentId"></submission-nav-bar>
            </div>
        </div>
        <div class="row">
            <div class="col-9 code-and-grade">
                <pdf-viewer v-if="fileExtension === 'pdf'" :id="fileId"></pdf-viewer>
                <code-viewer class="" :editable="editable"
                    :tree="fileTree" v-else-if="fileId" ref="codeViewer"></code-viewer>
                <grade-viewer :submission="submission"
                              :editable="editable"
                              v-on:gradeChange="gradeChange"
                              @submit="submitAllFeedback($event)"></grade-viewer>
            </div>

            <file-tree-container class="col-3" :fileTree="fileTree"></file-tree-container>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import { CodeViewer, FileTreeContainer, GradeViewer, Loader, PdfViewer, SubmissionNavBar } from '@/components';

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
            submission: null,
            fileTree: null,
            editable: false,
            fileExtension: '',
            title: '',
            grade: 0,
            showGrade: false,
            feedback: '',
            submissions: null,
            loading: true,
        };
    },

    computed: {
        courseId() { return Number(this.$route.params.courseId); },
        assignmentId() { return Number(this.$route.params.assignmentId); },
        submissionId() { return Number(this.$route.params.submissionId); },
        fileId() { return Number(this.$route.params.fileId); },
    },

    watch: {
        fileId() {
            this.getFileMetadata();
        },
    },

    mounted() {
        this.hasPermission({
            name: 'can_grade_work',
            course_id: this.courseId,
        }).then((val) => {
            this.editable = val;
        }, (err) => {
            // eslint-disable-next-line
            console.dir(err);
        });
        Promise.all([
            this.getSubmission(),
            this.getSubmissionFiles(),
            this.getAllSubmissions(),
            this.getAssignment(),
        ]).then(() => {
            this.loading = false;
        }, (err) => {
            // eslint-disable-next-line
            console.dir(err);
        });

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

    methods: {
        getSubmissionFiles() {
            return this.$http.get(`/api/v1/submissions/${this.submissionId}/files/`).then((data) => {
                this.fileTree = data.data;
                this.$router.replace({
                    name: 'submission_file',
                    params: {
                        fileId: this.fileId ? this.fileId : getFirstFile(this.fileTree).id,
                    },
                });
            });
        },

        gradeChange(grade) {
            this.$set(this.submission, 'grade', Number(grade));
            let i = 0;
            for (const len = this.submissions.length; i < len; i += 1) {
                if (this.submissions[i].id === this.submission.id) {
                    break;
                }
            }
            const sub = this.submissions[i];
            this.$set(sub, 'grade', Number(grade));
            this.$set(this.submissions, i, sub);
        },

        getSubmission() {
            return new Promise((resolve) => {
                this.$http.get(`/api/v1/submissions/${this.submissionId}`).then((data) => {
                    this.submission = data.data;
                    resolve();
                }).catch(() => {
                    resolve();
                });
            });
        },

        getAssignment() {
            return this.$http.get(`/api/v1/assignments/${this.assignmentId}`).then(({ data }) => {
                this.assignment = data;
            });
        },

        getFileMetadata() {
            if (this.fileId === undefined) {
                return null;
            }

            this.fileExtension = '';
            return this.$http.get(`/api/v1/code/${this.fileId}?type=metadata`).then((response) => {
                this.fileExtension = response.data.extension;
            });
        },

        getAllSubmissions() {
            return this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/`).then(({ data }) => {
                this.submissions = data;
            });
        },

        submitAllFeedback(event) {
            this.$refs.codeViewer.submitAllFeedback(event);
        },

        reloadSubmission() {
            this.getSubmission();
            this.getSubmissionFiles();
            this.getFileMetadata();
        },

        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    components: {
        CodeViewer,
        FileTreeContainer,
        GradeViewer,
        Loader,
        PdfViewer,
        SubmissionNavBar,
    },
};
</script>

<style lang="less" scoped>
h2 {
    text-align: center;
    margin-bottom: 15px;
    a {
        cursor: pointer;
        color: black;
    }
}

.page.submission {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    flex-shrink: 1;
}

.row {
    flex-grow: 1;
    flex-shrink: 1;
}

h1 {
    flex-grow: 0;
    flex-shrink: 0;
}

.code-and-grade {
    display: flex;
    flex-direction: column;
}

.pdfobject-container {
    flex-grow: 1;
    flex-shrink: 1;
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

.submission-nav-bar {
    flex-shrink: 0;
    flex-grow: 0;
}
</style>
