<template>
    <loader style="text-align: center; margin-top: 30px;" v-if="loading"/>
    <div class="page submission outer-container"
         v-else>
        <div class="row justify-content-center inner-container">
            <div class="col-lg-9 code-and-grade">
                <submission-nav-bar v-if="submissions"
                                    v-model="submission"
                                    :submissions="submissions"
                                    :filter="filterSubmissions"/>

                <div v-if="!fileTree" class="no-file">
                    <loader/>
                </div>
                <b-alert show
                         class="error no-file"
                         variant="danger"
                         v-else-if="fileTree.entries.length === 0">
                    No files found!
                </b-alert>
                <pdf-viewer :id="currentFile.id"
                            v-else-if="currentFile.extension === 'pdf'"/>
                <code-viewer :assignment="assignment"
                             :submission="submission"
                             :file="currentFile"
                             :editable="editable"
                             :tree="fileTree"
                             v-else/>

                <grade-viewer :assignment="assignment"
                              :submission="submission"
                              :rubric="rubric"
                              :editable="editable"
                              v-if="editable || assignment.state === assignmentState.DONE"
                              @gradeUpdated="gradeUpdated"/>
            </div>

            <div class="col-lg-3 file-tree-container">
                <b-form-fieldset class="submission-button-bar">
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
                    <div v-if="canDeleteSubmission">
                        <b-btn class="text-center"
                                variant="danger"
                                @click="$root.$emit('show::modal',`modal_delete`)">
                            <icon name="times"/> Delete
                        </b-btn>
                        <b-modal :id="`modal_delete`" title="Are you sure?" :hide-footer="true">
                            <p style="text-align: center;">
                                By deleting all information about this submissions,
                                including files, will be lost forever! So are you
                                really sure?
                            </p>
                            <b-button-toolbar justify>
                                <submit-button class="text-center delete-confirm"
                                                ref="deleteButton"
                                                default="outline-danger"
                                                @click="deleteSubmission"
                                                label="Yes"/>
                                <b-btn class="text-center"
                                        variant="success"
                                        @click="$root.$emit('hide::modal', `modal_delete`)">
                                    No!
                                </b-btn>
                            </b-button-toolbar>
                        </b-modal>
                    </div>
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
import 'vue-awesome/icons/times';

import { CodeViewer, FileTree, GradeViewer, Loader, PdfViewer, SubmissionNavBar, SubmitButton } from '@/components';

import * as assignmentState from '@/store/assignment-states';

import { setPageTitle, pageTitleSep } from '@/pages/title';

export default {
    name: 'submission-page',

    data() {
        return {
            courseId: Number(this.$route.params.courseId),
            assignmentId: Number(this.$route.params.assignmentId),
            assignment: null,
            submissionId: Number(this.$route.params.submissionId),
            submission: null,
            fileTree: null,
            currentFile: null,
            submissions: null,
            rubric: null,
            loading: true,
            canDeleteSubmission: false,
            initialLoad: true,
            assignmentState,
            canSeeFeedback: false,
        };
    },

    watch: {
        assignment() {
            if (this.submission) {
                let title = this.assignment.name;
                if (this.submission.grade) {
                    title += ` (${parseFloat(this.submission.grade).toFixed(2)})`;
                }
                setPageTitle(`${title} ${pageTitleSep} ${this.submission.created_at}`);
            }
        },

        submission(submission) {
            this.submissionId = submission.id;

            if (this.assignment) {
                let title = this.assignment.name;
                if (submission.grade) {
                    title += ` (${parseFloat(submission.grade).toFixed(2)})`;
                }
                setPageTitle(`${title} ${pageTitleSep} ${submission.created_at}`);
            }

            this.loading = true;
            this.getSubmissionData().then(() => {
                this.loading = false;
            });

            if (!this.initialLoad) {
                this.$router.push({
                    name: 'submission',
                    params: {
                        courseId: this.courseId,
                        assignmentId: this.assignmentId,
                        submissionId: submission.id,
                    },
                });
            }

            this.initialLoad = false;
        },

        $route(to) {
            this.currentFile = this.searchTree(this.fileTree, Number(to.params.fileId));
        },

        fileTree(tree) {
            const fileId = Number(this.$route.params.fileId);

            let file;
            if (!Number.isNaN(fileId)) {
                file = this.searchTree(tree, fileId);
            } else {
                file = this.getFirstFile(tree);
                if (file != null) {
                    this.$router.replace({
                        name: 'submission_file',
                        params: { fileId: file.id },
                    });
                }
            }

            this.currentFile = file;
        },

        currentFile(file) {
            if (file != null) {
                file.extension = '';
                const nameparts = file.name.split('.');
                if (nameparts.length > 1) {
                    file.extension = nameparts[nameparts.length - 1];
                }
            }
        },
    },

    mounted() {
        this.hasPermission({
            name: ['can_grade_work', 'can_see_grade_before_open', 'can_delete_submission'],
            course_id: this.courseId,
        }).then(([canGrade, canSeeGrade, canDeleteSubmission]) => {
            this.editable = canGrade;
            this.canSeeFeedback = canSeeGrade;
            this.canDeleteSubmission = canDeleteSubmission;
        });

        this.loading = true;
        Promise.all([
            this.getAssignment(),
            this.getAllSubmissions(),
        ]).then(() => {
            this.setPageCSS();
            this.loading = false;
        });
    },

    destroyed() {
        this.restorePageCSS();
    },

    methods: {
        getAssignment() {
            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}`,
            ).then(({ data: assignment }) => {
                this.assignment = assignment;
                this.canSeeFeedback = this.canSeeFeedback ||
                    (assignment.state === assignmentState.DONE);
            });
        },

        getAllSubmissions() {
            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}/submissions/`,
            ).then(({ data: submissions }) => {
                this.submissions = submissions;
                this.submission = submissions.find(sub =>
                    sub.id === this.submissionId);
            });
        },

        deleteSubmission() {
            const req = this.$http.delete(`/api/v1/submissions/${this.submissionId}`);

            this.$refs.deleteButton.submit(req.catch((err) => {
                throw err.response.data.message;
            })).then(() => {
                this.$router.push({
                    name: 'assignment_submissions',
                    params: {
                        courseId: this.assignment.course.id,
                        assignmentId: this.assignment.id,
                    },
                });
            });
        },

        getSubmissionData() {
            return Promise.all([
                this.getFileTree(),
                this.getRubric(),
            ]);
        },

        getFileTree() {
            return this.$http.get(
                `/api/v1/submissions/${this.submissionId}/files/`,
            ).then(({ data: fileTree }) => {
                this.fileTree = fileTree;
            });
        },

        getRubric() {
            if (!UserConfig.features.rubrics) {
                return Promise.resolve(null);
            }
            return this.$http.get(
                `/api/v1/submissions/${this.submissionId}/rubrics/`,
            ).then(({ data: rubric }) => {
                this.rubric = rubric;
            }, () => null);
        },

        getFirstFile(fileTree) {
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

            return null;
        },

        searchTree(tree, id) {
            for (let i = 0; i < tree.entries.length; i += 1) {
                const child = tree.entries[i];
                if (child.id === id) {
                    return child;
                } else if (child.entries != null) {
                    const match = this.searchTree(child, id);
                    if (match != null) {
                        return match;
                    }
                }
            }
            return null;
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
        SubmitButton,
        Icon,
    },
};
</script>

<style lang="less" scoped>
.outer-container {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    flex-shrink: 1;
    max-height: 100%;
    margin-bottom: 0;
}

.inner-container {
    min-height: 0;
}

.row {
    flex-grow: 1;
    flex-shrink: 1;
}

.code-and-grade {
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.pdf-viewer {
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

.no-file,
.code-viewer,
.pdf-viewer,
.grade-viewer,
.file-tree {
    margin-bottom: 1rem;
}

.file-tree-container {
    display: flex;
    flex-direction: column;
}

@media (max-width: 992px) {
    .file-tree-container {
        margin-bottom: 1em;
    }
}

@media (min-width: 992px) {
    .file-tree-container {
        height: 100%;
    }
}

.submission-button-bar {
    flex-grow: 0;
    flex-shrink: 0;
    button {
        margin-bottom: 0.2em;
    }
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

<style lang="less">
@media (max-width: 992px) {
    #app, html {
        height: inherit !important;
    }
}
</style>
