<template>
    <b-alert variant="danger" show v-if="error">
        <center><span>Cannot display file!</span></center>
    </b-alert>
    <loader class="text-center" v-else-if="loading"></loader>
    <ol class="code-viewer form-control" v-else :class="{ editable: editable }"
        @click="onClick">
        <li v-on:click="editable && addFeedback($event, i)" v-for="(line, i) in codeLines"
            :class="{ 'linter-feedback-outer': linterFeedback[i] }">

            <linter-feedback-area :feedback="linterFeedback[i]"></linter-feedback-area>

            <code  v-html="line"></code>


            <feedback-area :editing="editing[i] === true"
                            :feedback='feedback[i].msg'
                            :editable='editable'
                            :line='i'
                            :fileId='fileId'
                            v-on:feedbackChange="val => { feedbackChange(i, val); }"
                            v-on:cancel='onChildCancel'
                            v-if="feedback[i] != null">
            </feedback-area>

            <icon name="plus" class="add-feedback" v-if="editable && feedback[i] == null"
                    v-on:click="addFeedback($event, value)"></icon>
        </li>
    </ol>
</template>

<script>
import { getLanguage, highlight } from 'highlightjs';
import Vue from 'vue';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';

import FeedbackArea from './FeedbackArea';
import LinterFeedbackArea from './LinterFeedbackArea';
import Loader from './Loader';

const entityRE = /[&<>]/g;
const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
};
const escape = text => String(text).replace(entityRE, entity => entityMap[entity]);

export default {
    name: 'code-viewer',

    props: {
        editable: {
            type: Boolean,
            default: false,
        },
        tree: {
            type: Object,
            default: {},
        },
    },

    data() {
        return {
            code: '',
            codeLines: [],
            loading: true,
            editing: {},
            feedback: {},
            linterFeedback: {},
            clicks: {},
            error: false,
        };
    },

    computed: {
        courseId() { return Number(this.$route.params.courseId); },
        assignmentId() { return Number(this.$route.params.assignmentId); },
        submissionId() { return Number(this.$route.params.submissionId); },
        fileId() { return Number(this.$route.params.fileId); },
    },

    mounted() {
        this.getCode();
    },

    watch: {
        fileId() {
            this.loading = true;
            this.getCode();
        },

        tree() {
            this.linkFiles();
        },
    },

    methods: {
        getCode() {
            this.error = false;

            let done = 0;
            const addDone = () => {
                if (this.error) {
                    return;
                }
                done += 1;
                if (done === 2) {
                    this.linkFiles();
                    this.loading = false;
                    this.error = false;
                }
            };

            // Split in two promises so that highlighting can begin before we
            // have feedback as this is not needed anyway.
            Promise.all([
                this.$http.get(`/api/v1/code/${this.fileId}`),
                this.$http.get(`/api/v1/code/${this.fileId}?type=metadata`),
            ]).then(([file, metadata]) => {
                this.code = file.data;
                this.codeLines = this.code.split('\n');
                this.highlightCode(metadata.data.extension);
                addDone();
            }).catch(() => { this.error = true; });

            Promise.all([
                this.$http.get(`/api/v1/code/${this.fileId}?type=feedback`),
                this.$http.get(`/api/v1/code/${this.fileId}?type=linter-feedback`),
            ]).then(([feedback, linterFeedback]) => {
                this.linterFeedback = linterFeedback.data;
                this.feedback = feedback.data;
                addDone();
            }).catch(() => { this.error = true; });
        },

        // Highlight this.codeLines.
        highlightCode(lang) {
            if (getLanguage(lang) === undefined) {
                this.codeLines = this.codeLines.map(escape);
                return;
            }
            let state = null;
            this.codeLines = this.codeLines.map((line) => {
                const { top, value } = highlight(lang, line, true, state);
                state = top;
                return value;
            });
        },

        // Given a file-tree object as returned by the API, generate an
        // object with file-paths as keys and file-ids as values and an
        // array of file-paths. All // possible paths to a file will be
        // included. E.g. if file `a/b/c` has id 3, the object shall
        // contain the following keys: { 'a/b/c': 3, 'b/c': 3, 'c': 3 }.
        // Longer paths to the same file shall come before shorter paths
        // in the array, so the matching will prefer longer paths.
        flattenFileTree(tree, prefix = []) {
            const fileIds = {};
            const filePaths = [];
            if (!tree || !tree.entries) {
                return [fileIds, filePaths];
            }
            tree.entries.forEach((f) => {
                if (f.entries) {
                    const [dirIds, dirPaths] = this.flattenFileTree(f, prefix.concat(f.name));
                    Object.assign(fileIds, dirIds);
                    filePaths.push(...dirPaths);
                } else {
                    const path = prefix.concat(f.name).join('/');
                    let i = 0;
                    do {
                        const spath = path.substr(i);
                        filePaths.push(spath);
                        fileIds[path.substr(i)] = f.id;
                        i = path.indexOf('/', i + 1) + 1;
                    } while (i > 0);
                }
            });
            return [fileIds, filePaths];
        },

        // Search for each file in this.files on each line, and
        // replace each occurrence with a link to the file.
        linkFiles() {
            const [fileIds, filePaths] = this.flattenFileTree(this.tree);
            if (!filePaths.length) {
                return;
            }
            // Use a regex to match each file at most once.
            const filesRegex = new RegExp(`\\b(${filePaths.join('|')})\\b`, 'g');
            this.codeLines = this.codeLines.map(line =>
                line.replace(filesRegex, (fileName) => {
                    const fileId = fileIds[fileName];
                    return `<a href="${fileId}" data-file-id="${fileId}" style="text-decoration: underline;">${fileName}</a>`;
                }),
            );
        },

        onClick(event) {
            // Check if the click was on a link to a file.
            const fileId = event.target.getAttribute('data-file-id');
            if (fileId) {
                event.stopImmediatePropagation();
                event.preventDefault();
                this.$router.push({
                    name: 'submission_file',
                    params: {
                        courseId: this.courseId,
                        assignmentId: this.assignmentId,
                        submissionId: this.submissionId,
                        fileId,
                    },
                });
            }
        },

        onChildCancel(line) {
            this.clicks[line] = true;
            Vue.set(this.editing, line, false);
            Vue.set(this.feedback, line, null);
        },

        addFeedback(event, line) {
            if (this.clicks[line] === true) {
                delete this.clicks[line];
            } else if (this.feedback[line] == null) {
                Vue.set(this.editing, line, true);
                Vue.set(this.feedback, line, '');
            }
        },

        feedbackChange(line, feedback) {
            if (this.editable) {
                this.editing[line] = false;
                this.feedback[line] = feedback;
            }
        },
        // eslint-disable-next-line
        submitAllFeedback(event) {},
    },

    components: {
        Icon,
        FeedbackArea,
        Loader,
        LinterFeedbackArea,
    },
};
</script>

<style lang="less" scoped>
ol {
    font-family: monospace;
    font-size: small;
    margin: 0;
    padding: 0;
    padding-left: 4rem;
}

li {
    position: relative;
    padding-left: .75em;
    padding-right: .75em;

    .editable & {
        cursor: pointer;
    }
}

code {
    white-space: pre-wrap;
}

.feedback {
    font-family: sans-serif;
}

.add-feedback {
    position: absolute;
    top: 0;
    right: .5em;
    display: none;
    color: black;

    li:hover & {
        display: block;
    }
}

.loader {
    margin-top: 5em;
}
</style>
