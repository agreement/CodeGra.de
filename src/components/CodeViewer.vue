<template>
    <b-alert class="error" variant="danger" show v-if="error">
        <div v-html="error"></div>
    </b-alert>
    <loader class="text-center" v-else-if="loading"></loader>
    <div class="code-viewer form-control" v-else>
        <b-popover triggers="click"
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
                    <preference-manager :fileId="file.id"
                                        @whitespace="(value) => { showWhitespace = value; }"
                                        @language="highlightCode"
                                        @font-size="(val) => { fontSize = val; }"/>
                </div>
            </div>
        </b-popover>
        <div class="scroller" ref="scroller">
            <ol :class="{ editable, 'lint-whitespace': assignment.whitespace_linter, 'show-whitespace': showWhitespace }"
                :style="{
                    paddingLeft: `${3 + Math.log10(codeLines.length) * 2/3}em`,
                    fontSize: `${fontSize}px`,
                }"
                class="hljs"
                @click="onClick">
                <li v-on:click="editable && addFeedback($event, i)" v-for="(line, i) in codeLines"
                    :class="{ 'linter-feedback-outer': linterFeedback[i] }" v-bind:key="i">

                    <linter-feedback-area :feedback="linterFeedback[i]"
                                          v-if="linterFeedback[i] != null"/>

                    <code v-html="line"/>

                    <feedback-area :editing="editing[i] === true"
                                   :feedback="feedback[i].msg"
                                   :editable="editable"
                                   :line="i"
                                   :fileId="file.id"
                                   :can-use-snippets="canUseSnippets"
                                   v-on:feedbackChange="val => { feedbackChange(i, val); }"
                                   v-on:cancel='onChildCancel'
                                   v-if="feedback[i] !== undefined && feedback[i] !== null"/>
                </li>
            </ol>
        </div>
    </div>
</template>

<script>
import { getLanguage, highlight, listLanguages } from 'highlightjs';
import Vue from 'vue';
import { mapActions } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/cog';
import 'vue-multiselect/dist/vue-multiselect.min.css';

import FeedbackArea from './FeedbackArea';
import LinterFeedbackArea from './LinterFeedbackArea';
import Loader from './Loader';
import Toggle from './Toggle';
import PreferenceManager from './PreferenceManager';

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
    },

    computed: {
        extension() {
            const fileParts = this.file.name.split('.');
            return fileParts.length > 1 ? fileParts[fileParts.length - 1] : null;
        },
    },

    data() {
        const languages = listLanguages();
        languages.push('plain');
        languages.sort((a, b) =>
            a.toLowerCase().localeCompare(b.toLowerCase()));
        languages.unshift('Default');
        return {
            selectedLanguage: 'Default',
            code: '',
            rawCodeLines: [],
            codeLines: [],
            loading: true,
            editing: {},
            feedback: {},
            linterFeedback: {},
            clicks: {},
            error: false,
            showWhitespace: true,
            darkMode: true,
            fontSize: 12,
            languages,
            canUseSnippets: false,
        };
    },

    mounted() {
        Promise.all([
            this.loadCodeWithSettings(false),
            this.hasPermission({ name: 'can_use_snippets' }),
        ]).then(([, snips]) => {
            this.canUseSnippets = snips;
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
        document.body.removeEventListener('click', this.clickHideSettings);
        document.body.removeEventListener('keyup', this.keyupHideSettings);
    },

    watch: {
        file(f) {
            if (f) this.loadCodeWithSettings();
        },

        tree() {
            this.linkFiles();
        },
    },

    methods: {
        loadCodeWithSettings(setLoading = true) {
            return this.$hlanguageStore.getItem(`${this.file.id}`).then((val) => {
                if (val !== null) {
                    this.selectedLanguage = val;
                }
                return Promise.all([
                    this.getCode(setLoading),
                    this.$whitespaceStore.getItem(`${this.file.id}`).then((white) => {
                        this.showWhitespace = white === null || white;
                    }),
                ]);
            });
        },

        getCode(setLoading = true) {
            if (setLoading) this.loading = true;
            this.error = '';

            const addError = (err) => {
                let errVal = this.$htmlEscape(err);

                if (this.error) {
                    errVal = `<br>${errVal}`;
                }

                this.error += errVal;
            };

            // Split in two promises so that highlighting can begin before we
            // have feedback as this is not needed anyway.
            return Promise.all([
                this.$http.get(`/api/v1/code/${this.file.id}`, {
                    responseType: 'arraybuffer',
                }).then((code) => {
                    try {
                        this.code = decoder.decode(code.data);
                    } catch (e) {
                        addError('This file cannot be displayed');
                        return;
                    }
                    this.rawCodeLines = this.code.split('\n');

                    this.highlightCode(this.selectedLanguage);
                    this.linkFiles();
                }, ({ response: { data: { message } } }) => {
                    addError(message);
                }),

                Promise.all([
                    this.$http.get(`/api/v1/code/${this.file.id}?type=feedback`),
                    this.$http.get(`/api/v1/code/${this.file.id}?type=linter-feedback`),
                ]).then(([feedback, linterFeedback]) => {
                    this.linterFeedback = linterFeedback.data;
                    this.feedback = feedback.data;
                }, ({ response: { data: { message } } }) => {
                    addError(message);
                }),
            ]).then(() => {
                if (setLoading) {
                    this.loading = false;
                }
            });
        },

        // Highlight this.codeLines.
        highlightCode(language) {
            const lang = language === 'Default' ? this.extension : language;
            if (getLanguage(lang) === undefined) {
                this.codeLines = this.rawCodeLines
                    .map(this.$htmlEscape)
                    .map(this.visualizeWhitespace);
                return;
            }

            let state = null;
            this.codeLines = this.rawCodeLines.map((line) => {
                const { top, value } = highlight(lang, line, true, state);

                state = top;
                return this.visualizeWhitespace(value);
            });
        },

        visualizeWhitespace(line) {
            const newLine = [];
            for (let i = 0; i < line.length;) {
                const start = i;
                if (line[i] === '<') {
                    while (line[i] !== '>' && i < line.length) i += 1;
                    newLine.push(line.slice(start, i + 1));
                    i += 1;
                } else if (line[i] === ' ') {
                    while (line[i] === ' ' && i < line.length) i += 1;
                    newLine.push(`<span class="whitespace space">${Array((i - start) + 1).join('&middot;')}</span><wbr>`);
                } else if (line[i] === '\t') {
                    while (line[i] === '\t' && i < line.length) i += 1;
                    newLine.push(`<span class="whitespace tab">${Array((i - start) + 1).join('&#10230;   ')}</span><wbr>`);
                } else {
                    while (line[i] !== '<' && line[i] !== ' ' && line[i] !== '\t' && i < line.length) i += 1;
                    newLine.push(line.slice(start, i));
                }
            }
            return newLine.join('');
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
                        courseId: this.assignment.course.id,
                        assignmentId: this.assignment.id,
                        submissionId: this.submission.id,
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

        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    components: {
        PreferenceManager,
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

        .settings-toggle,
        ol {
            background: @color-primary-darkest;
            color: @color-secondary-text-lighter;
        }

        code {
            color: #839496;
        }
    }
}

.settings-toggle {
    position: absolute;
    top: -1px;
    right: 0;
    z-index: 10;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: 0;

}

#codeviewer-settings-content {
    margin: -.75em -1em;
    padding: .75em 1em;
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
            text-decoration: underline;
        }
    }
}

code {
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

.settings-popover {
    .settings-toggle {
        border: 1px solid rgba(0, 0, 0, 0.15);
        background: #f8f8f8;

        &:focus {
            box-shadow: none;
        }
    }

    @media-large {
        position: fixed;

        .settings-toggle {
            margin-right: 0px !important;
            border-right: 0 !important;
            margin-top: 0.5em;
        }
    }

    @media-no-large {
        position: relative;

        .settings-toggle {
            position: absolute;
            left: 0;

            margin-top: -2.4rem;
            height: 2.4rem;
            margin-left: 0.5em;

            top: 0;
            border-bottom: 0;
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }
    }
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
