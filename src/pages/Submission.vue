<template>
    <loader style="text-align: center; margin-top: 30px;" v-if="loading"/>
    <div class="page submission outer-container"
         v-else>
        <div class="row justify-content-center inner-container">
            <div class="col-md-9 code-and-grade">
                <submission-nav-bar v-if="submissions"
                                    v-model="submission"
                                    :submissions="submissions"
                                    :filter="filterSubmissions"/>

                <b-popover v-if="showPreferences"
                           triggers="click"
                           class="settings-popover"
                           :popover-style="{'max-width': '80%', width: '35em'}"
                           placement="right">
                    <b-btn class="settings-toggle" id="codeviewer-settings-toggle">
                        <icon name="cog"/>
                    </b-btn>
                    <div slot="content">
                        <div class="settings-content"
                             id="codeviewer-settings-content"
                             ref="settingsContent">
                            <preference-manager :file-id="currentFile && currentFile.id"
                                                :show-revision="canSeeRevision"
                                                :show-language="!diffMode"
                                                @whitespace="whitespaceChanged"
                                                @language="languageChanged"
                                                @font-size="fontSizeChanged"
                                                @revision="revisionChanged"/>
                        </div>
                    </div>
                </b-popover>

                <div v-if="!fileTree || !currentFile" class="no-file">
                    <loader/>
                </div>
                <b-alert show
                         class="error no-file"
                         variant="danger"
                         v-else-if="fileTree.entries.length === 0">
                    No files found!
                </b-alert>
                <pdf-viewer :id="currentFile.id"
                            v-else-if="currentFile.extension === 'pdf'"
                            @load="showPreferences = true"/>
                <image-viewer :id="currentFile.id"
                              :name="currentFile.name"
                              v-else-if="/^(?:gif|jpe?g|png|svg)$/.test(currentFile.extension)"
                              @load="showPreferences = true"/>
                <diff-viewer v-else-if="selectedRevision === 'diff' && currentFile.ids[0] !== currentFile.ids[1]"
                             :file="currentFile"
                             :font-size="fontSize"
                             :show-whitespace="showWhitespace"
                             :language="selectedLanguage"
                             @load="showPreferences = true"/>
                <code-viewer v-else
                             :assignment="assignment"
                             :submission="submission"
                             :file="currentFile"
                             :editable="editable && studentMode"
                             :tree="fileTree"
                             :font-size="fontSize"
                             :show-whitespace="showWhitespace"
                             :language="selectedLanguage"
                             @load="showPreferences = true"/>

                <grade-viewer :assignment="assignment"
                              :submission="submission"
                              :rubric="rubric"
                              :editable="editable"
                              v-if="editable || assignment.state === assignmentState.DONE"
                              @gradeUpdated="gradeUpdated"/>
            </div>

            <div class="col-md-3 file-tree-container">
                <b-form-fieldset class="submission-button-bar">
                    <b-button @click="downloadType('zip')"
                              variant="primary">
                        <icon name="download"/>
                        Archive
                    </b-button>

                    <b-button @click="downloadType('feedback')"
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
                <file-tree v-else
                            class="form-control"
                            :collapsed="false"
                            :tree="fileTree"/>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';
import 'vue-awesome/icons/times';
import { filterSubmissions, cmpNoCase, formatGrade, parseBool } from '@/utils';

import {
    CodeViewer,
    DiffViewer,
    FileTree,
    GradeViewer,
    ImageViewer,
    Loader,
    PdfViewer,
    PreferenceManager,
    SubmissionNavBar,
    SubmitButton,
    Toggle,
} from '@/components';

import * as assignmentState from '@/store/assignment-states';

import { setPageTitle, pageTitleSep } from '@/pages/title';

export default {
    name: 'submission-page',

    data() {
        let forceInclude = new Set();
        try {
            forceInclude = new Set(JSON.parse(this.$route.query.forceInclude));
        } catch (e) {
            // NOT EMPTY
        }

        return {
            courseId: Number(this.$route.params.courseId),
            assignmentId: Number(this.$route.params.assignmentId),
            assignment: null,
            submissionId: Number(this.$route.params.submissionId),
            submission: null,
            fileTree: null,
            studentTree: null,
            teacherTree: null,
            currentFile: null,
            submissions: null,
            rubric: null,
            loading: true,
            canDeleteSubmission: false,
            initialLoad: true,
            assignmentState,
            canSeeFeedback: false,
            canSeeRevision: false,
            showWhitespace: true,
            fontSize: 12,
            selectedLanguage: 'Default',
            selectedRevision: this.$route.query.revision || 'student',
            showPreferences: false,
            forceInclude,
        };
    },

    computed: {
        studentMode() {
            return this.$route.query.revision === 'student';
        },

        diffMode() {
            return this.$route.query.revision === 'diff';
        },
    },

    watch: {
        assignment() {
            if (this.submission) {
                let title = this.assignment.name;
                if (this.submission.grade) {
                    title += ` (${formatGrade(this.submission.grade)})`;
                }
                setPageTitle(`${title} ${pageTitleSep} ${this.submission.created_at}`);
            }
        },

        submission(submission) {
            if (submission.id === this.submissionId) {
                this.initalLoad = false;
                return;
            }

            this.submissionId = submission.id;
            if (!this.initialLoad) {
                this.fileTree = null;
                this.currentFile = null;
                this.selectedRevision = 'student';
            }

            if (this.assignment) {
                let title = this.assignment.name;
                if (submission.grade) {
                    title += ` (${formatGrade(submission.grade)})`;
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
                    query: Object.assign(
                        {}, this.$route.query, { revision: this.selectedRevision },
                    ),
                });
            }

            this.initialLoad = false;
        },

        $route(to) {
            const fileId = Number(to.params.fileId);
            if (this.fileTree && fileId !== this.currentFile.id) {
                this.currentFile = this.searchTree(this.fileTree, fileId);
            }
        },

        fileTree(treeTo) {
            if (treeTo == null) {
                return;
            }

            let fileId = Number(this.$route.params.fileId);

            let file;
            if (fileId) {
                file = this.searchTree(treeTo, fileId);
                if (file == null && this.currentFile != null) {
                    file = this.searchTree(treeTo, this.currentFile.revision.id);
                }
            }

            if (file == null) {
                file = this.getFirstFile(treeTo);
            }

            if (file != null) {
                if (this.currentFile == null || this.currentFile.id !== file.id) {
                    this.currentFile = file;
                }
                fileId = file.id || (file.ids && (file.ids[0] || file.ids[1]));
                this.$router.replace({
                    name: 'submission_file',
                    params: { fileId },
                    query: Object.assign(
                        {}, this.$route.query, { revision: this.selectedRevision },
                    ),
                });
            }
        },

        currentFile(file) {
            if (file != null) {
                file.extension = '';
                const nameparts = file.name.split('.');
                if (nameparts.length > 1) {
                    file.extension = nameparts[nameparts.length - 1];
                }
            }
            this.showPreferences = false;
        },
    },

    mounted() {
        this.loading = true;
        Promise.all([
            this.$hasPermission(
                [
                    'can_grade_work',
                    'can_see_grade_before_open',
                    'can_delete_submission',
                    'can_view_own_teacher_files',
                    'can_edit_others_work',
                ],
                this.courseId,
            ),
            this.getAssignment(),
            this.getAllSubmissions(),
            this.getSubmissionData(),
        ]).then(([[canGrade, canSeeGrade, canDeleteSubmission, ownTeacher, editOthersWork]]) => {
            this.editable = canGrade;
            this.canSeeFeedback = canSeeGrade;
            this.canDeleteSubmission = canDeleteSubmission;

            if (this.$store.getters['user/id'] === this.submission.user.id &&
                this.assignment.state === assignmentState.DONE) {
                this.canSeeRevision = ownTeacher;
            } else {
                this.canSeeRevision = editOthersWork;
            }

            this.setPageCSS();
            this.loading = false;
        });

        this.clickHideSettings = (event) => {
            let target = event.target;
            while (target !== document.body) {
                if (target.id === 'codeviewer-settings-content' ||
                    target.id === 'codeviewer-settings-toggle') {
                    return;
                }
                target = target.parentNode;
            }
            this.$root.$emit('hide::popover');
        };
        document.body.addEventListener('click', this.clickHideSettings, true);

        this.keyupHideSettings = (event) => {
            if (event.key === 'Escape') {
                this.$root.$emit('hide::popover');
            }
        };
        document.body.addEventListener('keyup', this.keyupHideSettings);
    },

    destroyed() {
        this.restorePageCSS();
        document.body.removeEventListener('click', this.clickHideSettings);
        document.body.removeEventListener('keyup', this.keyupHideSettings);
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
                `/api/v1/assignments/${this.assignmentId}/submissions/?extended`,
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
                this.getFileTrees(),
                this.getRubric(),
            ]);
        },

        getFileTrees() {
            return Promise.all([
                this.$http.get(`/api/v1/submissions/${this.submissionId}/files/`),
                this.$http.get(`/api/v1/submissions/${this.submissionId}/files/?owner=teacher`)
                    .catch(() => null),
            ]).then(([student, teacher]) => {
                this.studentTree = student.data;
                this.studentTree.isStudent = true;
                if (teacher != null) {
                    this.teacherTree = teacher.data;
                    this.teacherTree.isTeacher = true;
                    this.diffTree = this.matchFiles(this.studentTree, this.teacherTree);
                    this.diffTree.isDiff = true;
                }
                this.selectFileTree();
            });
        },

        matchFiles(tree1, tree2) {
            const diffTree = {
                name: tree1.name,
                entries: [],
                push(ids, name) { this.entries.push({ ids, name }); },
            };

            for (let i = 0; i < tree1.entries.length; i += 1) {
                const child1 = tree1.entries[i];
                let match = false;
                for (let j = 0; j < tree2.entries.length; j += 1) {
                    const child2 = tree2.entries[j];
                    if (child1.name === child2.name) {
                        match = true;
                        if (child1.entries && child2.entries) {
                            diffTree.entries.push(this.matchFiles(child1, child2));
                        } else if (child1.id !== child2.id) {
                            child1.revision = child2;
                            child2.revision = child1;
                            diffTree.push([child1.id, child2.id], child1.name);
                        }
                        break;
                    }
                }
                if (!match) {
                    child1.revision = null;
                    diffTree.push([child1.id, null], child1.name);
                }
            }

            for (let i = 0; i < tree2.entries.length; i += 1) {
                const child2 = tree2.entries[i];
                if (!child2.revision && !child2.entries) {
                    const match = tree1.entries.find(child1 => child1.name === child2.name);
                    diffTree.push([match ? match.id : null, child2.id], child2.name);
                }
            }

            diffTree.entries.sort((a, b) => cmpNoCase(a.name, b.name));

            delete diffTree.push;
            return diffTree;
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

        // Returns the first file in the file tree that is not a folder
        // The file tree is searched with BFS
        getFirstFile(fileTree) {
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

        // Search the tree for the file with the givven id.
        searchTree(tree, id) {
            for (let i = 0; i < tree.entries.length; i += 1) {
                const child = tree.entries[i];
                if ((child.id === id || (child.revision && child.revision.id === id)) ||
                    (child.ids && (child.ids[0] === id || child.ids[1] === id))) {
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
            const filterLatest = parseBool(this.$route.query.latest, true);
            const filterAssignee = parseBool(this.$route.query.mine, true);

            const checkReally = (sub) => {
                if (this.forceInclude.has(sub.id)) {
                    return true;
                }

                if (this.submissionId === sub.id) {
                    this.forceInclude.add(sub.id);
                    this.$router.replace({ query: Object.assign(
                        {},
                        this.$route.query,
                        { forceInclude: JSON.stringify([...this.forceInclude]) },
                    ) });
                    return true;
                }
                return false;
            };

            return filterSubmissions(
                submissions,
                filterLatest,
                filterAssignee,
                userId,
                this.$route.query.search,
                checkReally,
            );
        },

        downloadType(type) {
            this.$http.get(`/api/v1/submissions/${this.submissionId}?type=${type}`).then(({ data }) => {
                const params = new URLSearchParams();
                params.append('not_as_attachment', '');
                window.open(`/api/v1/files/${data.name}/${data.output_name}?${params.toString()}`);
            });
        },

        gradeUpdated(grade) {
            this.$set(this.submission, 'grade', grade);
            if (this.submissions) {
                this.$set(this.submissions, this.submissions.indexOf(this.submission),
                    this.submission);
            }
        },

        whitespaceChanged(val) {
            this.showWhitespace = val;
        },

        languageChanged(val) {
            this.selectedLanguage = val;
        },

        fontSizeChanged(val) {
            this.fontSize = val;
        },

        revisionChanged(val) {
            this.selectedRevision = val;
            this.selectFileTree();
        },

        selectFileTree() {
            switch (this.selectedRevision) {
            case 'teacher':
                this.fileTree = this.teacherTree;
                break;
            case 'diff':
                this.fileTree = this.diffTree;
                break;
            case 'student':
            default:
                this.fileTree = this.studentTree;
                break;
            }
        },

        setPageCSS() {
            this.pageStyleEl = document.head.appendChild(document.createElement('style'));
            this.pageStyleEl.innerHTML = `
                @media (min-width: 768px) {
                    html, body, #app { height: 100% !important; }
                    #app { display: flex !important; flex-direction: column !important; }
                    nav { flex-grow: 0 !important; flex-shrink: 0 !important; }
                    footer { flex-grow: 0 !important; flex-shrink: 0 !important; height: unset; !important }
                }
            `;
        },

        restorePageCSS() {
            document.head.removeChild(this.pageStyleEl);
        },
    },

    components: {
        CodeViewer,
        DiffViewer,
        FileTree,
        GradeViewer,
        ImageViewer,
        Loader,
        PdfViewer,
        PreferenceManager,
        SubmissionNavBar,
        SubmitButton,
        Toggle,
        Icon,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

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
    position: relative;
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.pdf-viewer {
    flex-grow: 1;
    flex-shrink: 1;
    min-height: 0;
}

.image-viewer {
    flex-grow: 0;
    flex-shrink: 1;
    min-height: 0;
}

.code-viewer,
.diff-viewer {
    overflow: auto;
}

.grade-viewer,
.submission-nav-bar {
    flex-grow: 0;
    flex-shrink: 0;
}

.no-file,
.code-viewer,
.diff-viewer,
.pdf-viewer,
.image-viewer,
.grade-viewer,
.file-tree {
    margin-bottom: 1rem;
}

.file-tree-container {
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.submission-button-bar {
    flex-grow: 0;
    flex-shrink: 0;
    padding-bottom: 1rem;
    margin-bottom: -.2rem;

    button {
        margin-bottom: .2rem;

        &:not(:last-child) {
            margin-right: .5rem;
        }
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

.settings-popover {
    z-index: 10;

    .settings-toggle {
        border: 1px solid rgba(0, 0, 0, 0.15);
        background: #f8f8f8;

        &:focus {
            box-shadow: none;
        }

        #app.dark & {
            background: @color-primary-darkest;
            color: @color-secondary-text-lighter;
        }
    }

    @media (min-width: 992px) {
        position: absolute;
        right: 100%;
        top: 4rem;
        margin-right: -1rem;

        .settings-toggle {
            border-right: 0;
            border-top-right-radius: 0;
            border-bottom-right-radius: 0;
        }
    }

    @media (max-width: 992px) {
        margin-bottom: -1px;

        .settings-toggle {
            margin-left: 0.5em;
            border-bottom: 0;
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }
    }
}

#codeviewer-settings-content {
    margin: -.75em -1em;
    padding: .75em 1em;
}
</style>
