<template>
<b-alert class="error" variant="danger" show v-if="error">
    <div v-html="error"></div>
</b-alert>
<loader class="text-center" v-else-if="loading"/>
<div class="overview-mode form-control" v-else>
    <b-tabs no-fade
            nav-wrapper-class="tab-wrapper"
            v-model="tabIndex">
        <b-tab title="Line feedback"
               class="code">
            <b-card v-if="fileIds.length === 0" class="file-card">
                This submission has no line comments.
            </b-card>
            <div class="scroller" v-else>
                <b-card v-for="id in fileIds"
                        :key="id"
                        class="file-card">
                    <h4 slot="header"
                        class="file-card-header">
                        <router-link :to="getFileLink(id)">
                            {{ flattenedFileTree[id] }}
                        </router-link>
                    </h4>
                    <div v-for="(part, i) in getParts(id)"
                         :key="`file-${id}-line-${part[0]}`">
                        <hr v-if="i !== 0">
                        <ol :class="{
                                'lint-whitespace': assignment.whitespace_linter,
                                'show-whitespace': showWhitespace,
                                'show-char-column': charColumn,
                            }"
                            :start="part[0] + 1"
                            :style="{
                                paddingLeft: `${3 + Math.log10(part[1]) * 2/3}em`,
                                fontSize: `${fontSize}px`,
                            }"
                            class="hljs code-part"
                            :data-char-column="charColumn">
                            <li v-for="line in range(part[0], part[1])"
                                :key="line"
                                class="line"
                                :class="{
                                    'linter-feedback-outer': UserConfig.features.linters &&
                                    feedback.linter[id] &&
                                    feedback.linter[id][line] != null,
                                    'feedback-outer': feedback.user[id][line]
                                }">
                                <linter-feedback-area :feedback="feedback.linter[id][line]"
                                                      v-if="UserConfig.features.linters &&
                                                            feedback.linter[id] &&
                                                            feedback.linter[id][line] != null"/>

                                <code v-html="codeLines[id][line]"/>

                                <feedback-area :feedback="feedback.user[id][line]"
                                               :editable="false"
                                               :line="line"
                                               :fileId="id"
                                               :can-use-snippets="false"
                                               v-if="feedback.user[id][line] != null"/>
                            </li>
                        </ol>
                    </div>
                </b-card>
            </div>
        </b-tab>
        <b-tab title="Changed files" class="code">
            <b-card v-if="changedFiles.length === 0" class="file-card">
                <span>
                    No files were changed
                </span>
            </b-card>
            <b-card v-for="f in changedFiles"
                    :key="`file-${f.ids[0]}-${f.ids[1]}`"
                    class="file-card">
                <h4 slot="header"
                    class="file-card-header">
                    <router-link :to="getFileLink(f.ids[0], 'diff')">
                        {{ f.fullName }}
                    </router-link>
                </h4>
                <diff-viewer :file="f"
                             :font-size="fontSize"
                             :char-column="charColumn"
                             :show-whitespace="showWhitespace"
                             diff-only
                             :context="context"/>
            </b-card>
        </b-tab>
        <b-tab title="Added or deleted files">
            <b-card v-if="newFiles.length + deletedFiles.length === 0" class="file-card">
                No files were added or deleted.
            </b-card>
            <div v-else>
                <b-card class="added-deleted-files file-card">
                    <h4 slot="header">
                        Added files
                    </h4>
                    <span v-if="newFiles.length === 0">
                        No files were added
                    </span>
                    <ul v-else>
                        <li v-for="f in newFiles"  :key="`file-added-${f.ids[1]}`">
                            <router-link :to="getFileLink(f.ids[1], 'teacher')">
                                <code>{{ f.fullName }}</code>
                            </router-link>
                        </li>
                    </ul>
                </b-card>
                <b-card class="added-deleted-files file-card">
                    <h4 slot="header">
                        Deleted files
                    </h4>
                    <span v-if="deletedFiles.length === 0">
                        No files were deleted
                    </span>
                    <ul v-else>
                        <li  v-for="f in deletedFiles"  :key="`file-deleted-${f.ids[1]}`">
                            <router-link :to="getFileLink(f.ids[0], 'student')">
                                <code>{{ f.fullName }}</code>
                            </router-link>
                        </li>
                    </ul>
                </b-card>
            </div>
        </b-tab>
    </b-tabs>
</div>
</template>

<script>
import { getLanguage, highlight } from 'highlightjs';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/cog';
import 'vue-multiselect/dist/vue-multiselect.min.css';

import { visualizeWhitespace, last, getExtension, range } from '@/utils';

import FeedbackArea from './FeedbackArea';
import LinterFeedbackArea from './LinterFeedbackArea';
import Loader from './Loader';
import Toggle from './Toggle';
import DiffViewer from './DiffViewer';

const decoder = new TextDecoder('utf-8', { fatal: true });

export default {
    name: 'overview-mode',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
        context: {
            type: Number,
            default: 3,
        },
        submission: {
            type: Object,
            default: null,
        },
        file: {
            type: Object,
            default: null,
        },
        tree: {
            type: Object,
            default: {},
        },
        teacherTree: {
            type: Object,
            default: null,
        },
        fontSize: {
            type: Number,
            default: 12,
        },
        charColumn: {
            type: String,
            default: null,
        },
        showWhitespace: {
            type: Boolean,
            default: true,
        },
    },

    watch: {
        urlTabIndex() {
            this.tabIndex = this.urlTabIndex;
        },

        tabIndex(newVal, oldVal) {
            if (newVal === oldVal || oldVal == null) {
                return;
            }

            const newQuery = Object.assign(
                {},
                this.$route.query,
                { overviewTab: newVal },
            );
            if (newVal === 0) {
                delete newQuery.overviewTab;
            }
        },
    },

    data() {
        return {
            UserConfig,
            codeLines: {},
            loading: true,
            feedback: {},
            fileIds: [],
            error: '',
            range,
            tabIndex: null,
        };
    },

    async mounted() {
        this.tabIndex = this.urlTabIndex;
        await this.$nextTick();

        this.error = '';
        this.feedback = (await this.$http.get(`/api/v1/submissions/${this.submission.id}/feedbacks/`)).data;

        this.fileIds = Object.keys(this.feedback.user);
        const codeLines = await Promise.all(this.fileIds.map(this.loadCodeWithSettings));

        for (let i = 0, len = this.fileIds.length; i < len; ++i) {
            this.codeLines[this.fileIds[i]] = codeLines[i];
        }
        this.loading = false;
    },

    methods: {
        getFileLink(fileId, revision) {
            const newQuery = Object.assign({}, this.$route.query, {
                overview: false,
                revision,
            });
            delete newQuery.overviewTab;

            return {
                name: 'submission_file',
                params: {
                    courseId: this.assignment.course.id,
                    assignmentId: this.assignment.id,
                    submissionId: this.submission.id,
                    fileId,
                },
                query: newQuery,
            };
        },

        getParts(fileId) {
            const lines = this.codeLines[fileId];
            const feedback = this.feedback.user[fileId];

            return Object.keys(feedback).reduce((res, lineStr) => {
                const line = Number(lineStr);
                const startLine = Math.max(line - this.context, 0);
                const endLine = Math.min(line + this.context + 1, lines.length);

                if (res.length === 0 || last(last(res)) <= startLine - 2) {
                    res.push([startLine, endLine]);
                } else {
                    last(res)[1] = endLine;
                }

                return res;
            }, []);
        },

        async loadCodeWithSettings(fileId) {
            const val = await this.$hlanguageStore.getItem(`${fileId}`);
            let selectedLanguage;

            if (val !== null) {
                selectedLanguage = val;
            } else {
                selectedLanguage = 'Default';
            }
            const code = await this.getCode(fileId, selectedLanguage);
            return code;
        },

        getCode(fileId, selectedLanguage) {
            return this.$http.get(`/api/v1/code/${fileId}`, {
                responseType: 'arraybuffer',
            }).then((rawCode) => {
                let code;
                try {
                    code = decoder.decode(rawCode.data);
                } catch (e) {
                    return [];
                }
                return this.highlightCode(code.split('\n'), selectedLanguage, this.flattenedFileTree[fileId]);
            }, ({ response: { data: { message } } }) => {
                this.error = message;
            });
        },

        // Highlight this.codeLines.
        highlightCode(codeLines, language, filePath) {
            if (codeLines.length > 1000) {
                return codeLines.map(this.$htmlEscape);
            }

            const lang = language === 'Default' ? getExtension(filePath) : language;
            if (getLanguage(lang) === undefined) {
                return codeLines
                    .map(this.$htmlEscape)
                    .map(visualizeWhitespace);
            }

            let state = null;
            return codeLines.map((line) => {
                const { top, value } = highlight(lang, line, true, state);

                state = top;
                return visualizeWhitespace(value);
            });
        },

        flattenFileTree(tree, prefix = []) {
            const filePaths = {};
            if (!tree || !tree.entries) {
                return {};
            }
            tree.entries.forEach((f) => {
                if (f.entries) {
                    const dirPaths = this.flattenFileTree(f, prefix.concat(f.name));
                    Object.assign(filePaths, dirPaths);
                } else {
                    if (f.id != null) {
                        filePaths[f.id] = prefix.concat(f.name).join('/');
                    }
                    if (f.ids && f.ids[0] != null) {
                        filePaths[f.ids[0]] = prefix.concat(f.name).join('/');
                    }
                    if (f.ids && f.ids[1] != null) {
                        filePaths[f.ids[1]] = prefix.concat(f.name).join('/');
                    }
                }
            });
            return filePaths;
        },

        getChangedFiles(tree, prefix = []) {
            const changed = [];
            const added = [];
            const deleted = [];

            if (!tree || !tree.entries) {
                return { changed, added, deleted };
            }
            tree.entries.forEach((f) => {
                if (f.entries) {
                    const res = this.getChangedFiles(f, prefix.concat(f.name));
                    changed.push(...res.changed);
                    added.push(...res.added);
                    deleted.push(...res.deleted);
                } else if (f.ids && f.ids[0] !== f.ids[1] && !(f.ids[0] === f.ids[1] === null)) {
                    let toChange = changed;
                    if (f.ids[0] == null) {
                        toChange = added;
                    } else if (f.ids[1] == null) {
                        toChange = deleted;
                    }

                    toChange.push(Object.assign({}, f, {
                        fullName: prefix.concat(f.name).join('/'),
                    }));
                }
            });
            return { changed, added, deleted };
        },
    },

    computed: {
        urlTabIndex() {
            return Number(this.$route.query.overviewTab) || 0;
        },
        allModifiedFiles() {
            return this.getChangedFiles(this.tree);
        },
        changedFiles() {
            return this.allModifiedFiles.changed;
        },
        flattenedFileTree() {
            return this.flattenFileTree(this.tree);
        },
        newFiles() {
            return this.allModifiedFiles.added;
        },
        deletedFiles() {
            return this.allModifiedFiles.deleted;
        },
    },

    components: {
        Icon,
        FeedbackArea,
        LinterFeedbackArea,
        Loader,
        Toggle,
        DiffViewer,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.file-card.card {
    &:first-child, &:last-child:not(:nth-child(2)) {
        border: 0;
    }
    &:last-child {
        border-bottom: 0;
    }
    border-left: 0;
    border-right: 0;
    border-radius: 0;
}

.overview-mode {
    position: relative;
    padding: 0;
    border: 0;
    padding-left: 4px;
    margin-left: -4px;
    display: flex;

    .diff-viewer {
        background: white;
        border: 0;
    }

    .code .card {
        margin-top: 0;
    }
}

.scroller {
    width: 100%;
    height: 100%;
    overflow-x: auto;
    overflow-y: auto;
}

.code ol {
    position: relative;
    min-height: 5em;
    margin: 0;
    padding: 0;
    overflow-x: visible;
    background: @linum-bg;
    font-family: monospace;
    font-size: small;

    #app.dark & {
        background: @color-primary-darkest;
        color: @color-secondary-text-lighter;
    }

    &.show-char-column {
        .code-viewer-char-column;
    }
}

.code li {
    position: relative;
    padding-left: .75em;
    padding-right: .75em;

    background-color: lighten(@linum-bg, 1%);
    border-left: 1px solid darken(@linum-bg, 5%);

    #app.dark & {
        background: @color-primary-darker;
        border-left: 1px solid darken(@color-primary-darkest, 5%);
    }

    &:hover {
        cursor: text;
    }
}

.code code {
    border-bottom: 1px solid transparent;
    font-size: 100%;
    color: @color-secondary-text;
    white-space: pre-wrap;

    word-wrap: break-word;
    word-break: break-word;
    -ms-word-break: break-all;

    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    -ms-hyphens: auto;
    hyphens: auto;

    #app.dark & {
        color: #839496;
    }
}

.loader {
    margin-top: 2.5em;
    margin-bottom: 3em;
}

.code-part {
    border: 1px solid rgba(0, 0, 0, 0.1);
    padding-right: .25rem;
    border-radius: .25rem;
    li:first-child {
        border-top-right-radius: .25rem;
    }
    li:last-child {
        border-bottom-right-radius: .25rem;
    }
}

.card-header {
    border-radius: 0;
    .file-card-header {
        margin: 0;
        a {
            .default-text-colors;
        }
    }
}

.added-deleted-files ul {
    margin-bottom: 0;
    padding-left: 1.25rem;
}

.added-deleted-files a {
    .default-text-colors;
}

.feedback-area {
    position: relative;
    z-index: 20;
}
</style>

<style lang="less">
@import '~mixins.less';

.overview-mode {
    .tabs {
        overflow-y: hidden;
        display: flex;
        flex-direction: column;
        max-height: 100%;
        flex-grow: 1;
        flex-shrink: 1;
        position: relative;
    }

    .nav-tabs {
        border-color: @color-border-gray-lighter;
        .default-background;
    }

    .tab-wrapper {
        flex: 1 0 auto;
        border-color: @color-border-gray-lighter;
        border-color: transparent;

        .nav-link {
            &:hover {
                color: inherit !important;
            }

            &:not(.active):not(:hover) {
                border-color: transparent !important;
            }

            &.active {
                border-color: @color-border-gray-lighter;
                background-color: rgb(247, 247, 247);
                border-bottom-color: rgb(247, 247, 247);
            }
        }
    }

    .tab-content {
        border: 1px solid @color-border-gray-lighter;
        #app.dark & {
            border-color: @color-primary-darker;
        }

        border-top: 0;
        overflow: auto;

        border-radius: .25rem;
        border-top-right-radius: 0;
        border-top-left-radius: 0;

        margin-bottom: 2px;

        .tab-pane {
            will-change: transform;
            height: 100%;
        }
    }
}

#app.dark .overview-mode ol .btn:not(.btn-success):not(.btn-danger):not(.btn-warning) {
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
