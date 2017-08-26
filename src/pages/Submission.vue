<template>
    <loader style="text-align: center; margin-top: 30px;" v-if="loading"/>
    <div class="page submission" v-else>
        <div class="row justify-content-center">
            <div class="col-lg-9 code-and-grade">
                <submission-nav-bar v-if="submissions"
                                    v-model="submission"
                                    :submissions="submissions"
                                    :filter="filterSubmissions"/>

                <pdf-viewer :id="fileId"
                            v-if="fileExtension === 'pdf'"/>
                <code-viewer :assignment="assignment"
                             :submission="submission"
                             :fileId="+fileId"
                             :editable="editable"
                             :tree="fileTree"
                             v-else-if="fileId"/>

                <grade-viewer :assignment="assignment"
                              :submission="submission"
                              :rubric="rubric"
                              :editable="editable"
                              v-if="editable || assignment.state === assignmentState.DONE"
                              @gradeUpdated="gradeUpdated"/>
            </div>

            <div class="col-lg-3 file-tree-container">
                <b-form-fieldset class="button-bar">
                    <b-button @click="downloadType('zip')"
                              variant="primary">
                        <icon name="download"/>
                        Archive
                    </b-button>
                    <b-button @click="downloadType('feedback')"
                              v-if="assignment.state === assignmentState.DONE"
                              variant="primary">
                        <icon name="download"/>
                        Feedback
                    </b-button>
                </b-form-fieldset>

                <loader class="text-center"
                        :scale="3"
                        v-if="!fileTree"/>
                <file-tree class="form-control"
                           :collapsed="false"
                           :tree="fileTree"
                           v-else/>
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';

import { CodeViewer, FileTree, GradeViewer, Loader, PdfViewer, SubmissionNavBar } from '@/components';

import * as assignmentState from '@/store/assignment-states';

import { setPageTitle, pageTitleSep } from '@/pages/title';

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
            courseId: Number(this.$route.params.courseId),
            assignmentId: Number(this.$route.params.assignmentId),
            assignment: null,
            submissionId: Number(this.$route.params.submissionId),
            submission: null,
            fileId: Number(this.$route.params.fileId) || null,
            fileTree: null,
            submissions: null,
            rubric: null,
            fileExtension: '',
            loading: true,
            initialLoad: true,
            assignmentState,
            canSeeFeedback: false,
        };
    },

    watch: {
        $route(to) {
            if (to.params.fileId) {
                this.fileId = to.params.fileId;
                this.getFileMetadata();
            }
        },

        submission(submission) {
            this.submissionId = submission.id;
            this.fileId = this.$route.params.fileId;

            let title = this.assignment.name;
            if (submission.grade) {
                title += ` (${submission.grade})`;
            }
            setPageTitle(`${title} ${pageTitleSep} ${submission.created_at}`);

            if (this.initialLoad) {
                this.initialLoad = false;
                return;
            }

            this.fileId = undefined;
            this.$router.push({
                name: 'submission',
                params: {
                    courseId: this.courseId,
                    assignmentId: this.assignmentId,
                    submissionId: submission.id,
                },
            });

            this.loading = true;
            this.getSubmissionData().then(() => {
                this.loading = false;
            });
        },
    },

    mounted() {
        this.hasPermission({
            name: ['can_grade_work', 'can_see_grade_before_open'],
            course_id: this.courseId,
        }).then(([canGrade, canSeeGrade]) => {
            this.editable = canGrade;
            this.canSeeFeedback = canSeeGrade;
        });

        this.loading = true;
        Promise.all([
            this.getAssignment(),
            this.getAllSubmissions(),
            this.getSubmissionData(),
        ]).then(([assignment, submissions]) => {
            this.assignment = assignment;
            this.canSeeFeedback = this.canSeeFeedback ||
                (assignment.state === assignmentState.DONE);

            this.submissions = submissions;
            this.submission = submissions.find(sub =>
                sub.id === this.submissionId);

            this.setPageCSS();

            this.getFileMetadata().then(() => {
                this.loading = false;
            });
        });
    },

    destroyed() {
        this.restorePageCSS();
    },

    methods: {
        getAssignment() {
            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}`,
            ).then(({ data }) => data);
        },

        getAllSubmissions() {
            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}/submissions/`,
            ).then(({ data }) => data);
        },

        getSubmissionData() {
            return Promise.all([
                this.getFileTree(),
                this.getRubric(),
            ]).then(([fileTree, rubric]) => {
                this.fileTree = fileTree;

                this.rubric = rubric;

                if (!this.fileId) {
                    const firstFile = getFirstFile(fileTree);
                    if (firstFile) {
                        this.$router.replace({
                            name: 'submission_file',
                            params: { fileId: firstFile.id },
                        });
                    }
                }
            }, (err) => {
                // eslint-disable-next-line
                console.dir(err);
            });
        },

        getFileTree() {
            return this.$http.get(
                `/api/v1/submissions/${this.submissionId}/files/`,
            ).then(({ data }) => data);
        },

        getRubric() {
            return this.$http.get(
                `/api/v1/submissions/${this.submissionId}/rubrics/`,
            ).then(({ data }) => data);
        },

        getFileMetadata() {
            if (this.fileId == null || Number.isNaN(this.fileId)) {
                return Promise.resolve(null);
            }

            this.fileExtension = '';
            return this.$http.get(
                `/api/v1/code/${this.fileId}?type=metadata`,
            ).then((response) => {
                this.fileExtension = response.data.extension;
            }, (err) => {
                // eslint-disable-next-line
                console.dir(err);
            });
        },

        filterSubmissions(submissions) {
            const userId = this.$store.state.user.id;

            const filterLatest = this.submission.user.id !== userId;
            const filterAssignee = this.submission.assignee &&
                this.submission.assignee.id === userId;

            const seen = [];
            return submissions.filter((sub) => {
                if (filterLatest && seen[sub.user.id]) {
                    return false;
                }
                seen[sub.user.id] = true;

                if (filterAssignee) {
                    return sub.assignee && sub.assignee.id === userId;
                }
                return true;
            });
        },

        downloadType(type) {
            this.$http.get(`/api/v1/submissions/${this.submissionId}?type=${type}`).then(({ data }) => {
                const params = new URLSearchParams();
                params.append('name', data.output_name);
                window.open(`/api/v1/files/${data.name}?${params.toString()}`);
            });
        },

        gradeUpdated(grade) {
            this.$set(this.submission, 'grade', grade);

            if (this.submissions) {
                this.$set(this.submissions, this.submissions.indexOf(this.submission),
                    this.submission);
            }
        },

        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),

        setPageCSS() {
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

        restorePageCSS() {
            const els = Array.from(document.querySelectorAll('html, body, #app, nav, footer'));
            const [html, body, app, nav, footer] = els;

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
    },

    components: {
        CodeViewer,
        FileTree,
        GradeViewer,
        Loader,
        PdfViewer,
        SubmissionNavBar,
        Icon,
    },
};
</script>

<style lang="less" scoped>
.page.submission {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    flex-shrink: 1;
    margin-bottom: 0;
}

.row {
    flex-grow: 1;
    flex-shrink: 1;
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

.grade-viewer,
.submission-nav-bar {
    flex-grow: 0;
    flex-shrink: 0;
}

.code-viewer,
.pdfobject-container,
.grade-viewer {
    margin-bottom: 1rem;
}

.file-tree-container {
    display: flex;
    flex-direction: column;
}

.button-bar {
    flex-grow: 0;
    flex-shrink: 0;
}

.file-tree {
    flex-grow: 0;
    flex-shrink: 1;
    overflow: auto;
}

.loader {
    margin-top: 1em;
}
</style>

<style>
@media (max-width: 992px) {
    #app, html {
        height: inherit !important;
    }
}
</style>
