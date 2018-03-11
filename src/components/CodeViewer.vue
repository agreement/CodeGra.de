<template>
    <b-alert class="error" variant="danger" show v-if="error">
        <div v-html="error"></div>
    </b-alert>
    <loader class="text-center" v-else-if="loading"></loader>
    <div class="code-viewer form-control" v-else>
        <div class="scroller" ref="scroller">
            <ol :class="{ editable, 'lint-whitespace': assignment.whitespace_linter, 'show-whitespace': showWhitespace }"
                :style="{
                    paddingLeft: `${3 + Math.log10(codeLines.length) * 2/3}em`,
                    fontSize: `${fontSize}px`,
                }"
                class="hljs"
                @click="onClick">
                <li @click="editable && addFeedback($event, i)"
                    v-for="(line, i) in codeLines"
                    :class="{ 'linter-feedback-outer': UserConfig.features.linters &&
                                                       linterFeedback[i] &&
                                                       !diffMode }"
                    :key="i">

                    <linter-feedback-area :feedback="linterFeedback[i]"
                                          v-if="UserConfig.features.linters &&
                                                linterFeedback[i] != null &&
                                                !diffMode"/>

                    <code v-html="line"/>

                    <feedback-area :editing="editing[i] === true"
                                   :feedback="feedback[i].msg"
                                   :editable="editable"
                                   :line="i"
                                   :fileId="file.id"
                                   :can-use-snippets="canUseSnippets"
                                   v-on:feedbackChange="val => { feedbackChange(i, val); }"
                                   v-on:cancel='onChildCancel'
                                   v-if="feedback[i] != null && !diffMode"/>
                </li>
            </ol>
        </div>
    </div>
</template>

<script>
import { getLanguage, highlight, listLanguages } from 'highlightjs';
import Vue from 'vue';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/cog';
import 'vue-multiselect/dist/vue-multiselect.min.css';

import { cmpNoCase } from '@/utils';

import FeedbackArea from './FeedbackArea';
import LinterFeedbackArea from './LinterFeedbackArea';
import Loader from './Loader';
import Toggle from './Toggle';

import { visualizeWhitespace } from './utils';

const decoder = new TextDecoder('utf-8', { fatal: true });

export default {
    name: 'code-viewer',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
        submission: {
            type: Object,
            default: null,
        },
        file: {
            type: Object,
            default: null,
        },
        editable: {
            type: Boolean,
            default: false,
        },
        tree: {
            type: Object,
            default: {},
        },
        language: {
            type: String,
            default: 'Default',
        },
        fontSize: {
            type: Number,
            default: 12,
        },
        showWhitespace: {
            type: Boolean,
            default: true,
        },
    },

    computed: {
        extension() {
            const fileParts = this.file.name.split('.');
            return fileParts.length > 1 ? fileParts[fileParts.length - 1] : null;
        },

        diffMode() {
            return this.$route.query.revision === 'diff';
        },

        isLargeFile() {
            return this.rawCodeLines && this.rawCodeLines.length > 5000;
        },
    },

    data() {
        const languages = listLanguages();
        languages.push('plain');
        languages.sort(cmpNoCase);
        languages.unshift('Default');
        return {
            UserConfig,
            code: '',
            rawCodeLines: [],
            codeLines: [],
            loading: true,
            editing: {},
            feedback: {},
            linterFeedback: {},
            clicks: {},
            error: false,
            darkMode: true,
            selectedLanguage: 'Default',
            languages,
            canUseSnippets: false,
        };
    },

    mounted() {
        Promise.all([
            this.loadCodeWithSettings(false),
            this.$hasPermission('can_use_snippets'),
        ]).then(([, snips]) => {
            this.canUseSnippets = snips;
            this.loading = false;
        });
    },

    watch: {
        file(f) {
            if (f) this.loadCodeWithSettings();
        },

        tree() {
            if (!this.isLargeFile && !this.diffMode) {
                this.linkFiles();
            }
        },

        language(lang) {
            if (this.selectedLanguage === lang) {
                return;
            }
            this.selectedLanguage = lang;
            if (!this.isLargeFile) {
                this.highlightCode(lang);
            }
        },
    },

    methods: {
        loadCodeWithSettings(setLoading = true) {
            return this.$hlanguageStore.getItem(`${this.file.id}`).then((val) => {
                if (val !== null) {
                    this.$emit('new-lang', val);
                    this.selectedLanguage = val;
                } else {
                    this.selectedLanguage = 'Default';
                }
                return this.getCode(setLoading);
            });
        },

        getCode(setLoading = true) {
            if (setLoading) this.loading = true;
            const error = [];
            this.error = '';

            const fileId = this.file.id || this.file.ids[0] || this.file.ids[1];

            // Split in two promises so that highlighting can begin before we
            // have feedback as this is not needed anyway.
            return Promise.all([
                this.$http.get(`/api/v1/code/${fileId}`, {
                    responseType: 'arraybuffer',
                }).then((code) => {
                    try {
                        this.code = decoder.decode(code.data);
                    } catch (e) {
                        error.push('This file cannot be displayed');
                        return;
                    }
                    this.rawCodeLines = this.code.split('\n');

                    this.highlightCode(this.selectedLanguage);
                    if (!this.isLargeFile && !this.diffMode) {
                        this.linkFiles();
                    }
                }, ({ response: { data: { message } } }) => {
                    error.push(message);
                }),

                Promise.all([
                    this.$http.get(`/api/v1/code/${fileId}?type=feedback`),
                    (UserConfig.features.linters ?
                        this.$http.get(`/api/v1/code/${fileId}?type=linter-feedback`) :
                        Promise.resolve({ data: {} })),
                ]).then(([feedback, linterFeedback]) => {
                    this.linterFeedback = linterFeedback.data;
                    this.feedback = feedback.data;
                }, ({ response: { data: { message } } }) => {
                    error.push(message);
                }),
            ]).then(() => {
                this.error = error.join('<br>');
                if (setLoading) {
                    this.loading = false;
                }
                this.$emit('load');
            });
        },

        // Highlight this.codeLines.
        highlightCode(language) {
            if (this.isLargeFile) {
                this.codeLines = this.rawCodeLines.map(this.$htmlEscape);
                return;
            }

            const lang = language === 'Default' ? this.extension : language;
            if (getLanguage(lang) === undefined || this.diffMode) {
                this.codeLines = this.rawCodeLines
                    .map(this.$htmlEscape)
                    .map(visualizeWhitespace);
                return;
            }

            let state = null;
            this.codeLines = this.rawCodeLines.map((line) => {
                const { top, value } = highlight(lang, line, true, state);

                state = top;
                return visualizeWhitespace(value);
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
                        fileIds[path.substr(i)] = f.id || f.ids[0] || f.ids[1];
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
                }));
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
                        courseId: this.assignment.course.id,
                        assignmentId: this.assignment.id,
                        submissionId: this.submission.id,
                        fileId,
                    },
                    query: this.$route.query,
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
            } else {
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
    },

    components: {
        Icon,
        FeedbackArea,
        LinterFeedbackArea,
        Loader,
        Toggle,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.code-viewer {
    position: relative;
    padding: 0;
    background: #f8f8f8;

    @media-no-large {
        margin-top: 2.3rem;
        overflow: visible !important;
    }

    ol {
        min-height: 5em;
        overflow-x: visible;
        background: @linum-bg;
    }

    li {
        background-color: lighten(@linum-bg, 1%);
        border-left: 1px solid darken(@linum-bg, 5%);
    }

    #app.dark & {
        background: @color-primary-darker;

        li {
            background: @color-primary-darker;
            border-left: 1px solid darken(@color-primary-darkest, 5%);
        }

        ol {
            background: @color-primary-darkest;
            color: @color-secondary-text-lighter;
        }

        code {
            color: #839496;
        }
    }
}

.scroller {
    width: 100%;
    height: 100%;
    overflow-x: auto;
    overflow-y: auto;
}

ol {
    font-family: monospace;
    font-size: small;
    margin: 0;
    padding: 0;
}

li {
    position: relative;
    padding-left: .75em;
    padding-right: .75em;

    .editable &:hover {
        cursor: pointer;

        code {
            border-radius: 0;
            border-bottom: 1px solid currentColor;
        }
    }
}

code {
    color: @color-secondary-text;
    white-space: pre-wrap;
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
    margin-top: 2.5em;
    margin-bottom: 3em;
}
</style>

<style lang="less">
@import '~mixins.less';

.code-viewer {
    .whitespace {
        opacity: 0;
        #app.dark & {
            color: @color-secondary-text;
        }
    }

    .show-whitespace .whitespace {
        opacity: 1;
    }
}

#app.dark .code-viewer ol
.btn:not(.btn-success):not(.btn-danger):not(.btn-warning) {
    background: @color-secondary;
    &.btn-secondary {
        background-color: @color-primary-darker;
        &:hover {
            background: @color-primary-darker;
        }
    }
    &:hover {
        background: darken(@color-secondary, 10%);
    }
}
</style>
