<template>
  <loader class="col-md-12 text-center" v-if="loading"></loader>
  <ol class="code-viewer form-control" :class="{ editable }" v-else>
    <li v-on:click="editable && addFeedback($event, i)" v-for="(line, i) in codeLines">
      <code v-html="line" @click="onFileClick"></code>


      <feedback-area :editing="editing[i] === true"
                     :feedback='feedback[i]'
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

import { bButton, bFormInput, bInputGroup, bInputGroupButton }
    from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';

import FeedbackArea from './FeedbackArea';
import Loader from './Loader';

export default {
    name: 'code-viewer',

    props: {
        editable: {
            type: Boolean,
            default: false,
        },
        id: {
            type: Number,
            default: 0,
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
            files: this.flattenFileTree(this.tree),
            loading: true,
            editing: {},
            feedback: {},
            clicks: {},
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
        assignmentId() { return this.$route.params.assignmentId; },
        submissionId() { return this.$route.params.submissionId; },
        fileId() { return this.$route.params.fileId; },
    },

    mounted() {
        this.getCode();
    },

    watch: {
        id(to) {
            this.fileId = to;
        },

        fileId() {
            this.loading = true;
            this.getCode();
        },

        tree(to) {
            this.files = this.flattenFileTree(to);
        },

        files() {
            this.linkFiles();
        },
    },

    methods: {
        flattenFileTree(tree, prefix = []) {
            const files = {};
            if (!tree || !tree.entries) {
                return files;
            }
            tree.entries.forEach((f) => {
                if (f.entries) {
                    Object.assign(files, this.flattenFileTree(f, prefix.concat(f.name)));
                } else {
                    const path = prefix.concat(f.name).join('/');
                    let sep = 0;
                    do {
                        files[path.substr(sep)] = f.id;
                        sep = path.indexOf('/', sep + 1);
                    } while (sep > -1);
                }
            });
            return files;
        },

        getCode() {
            this.$http.get(`/api/v1/code/${this.fileId}`).then(({ data }) => {
                this.feedback = data.feedback;
                this.code = data.code;
                this.codeLines = data.code.split('\n');
                this.highlightCode(data.lang);
                this.linkFiles();
                this.loading = false;
            });
        },

        // Highlights the given string and returns an array of highlighted strings
        highlightCode(lang) {
            if (getLanguage(lang) === undefined) {
                return;
            }
            let state = null;
            this.codeLines = this.codeLines.map((line) => {
                const { top, value } = highlight(lang, line, true, state);
                state = top;
                return value;
            });
        },

        linkFiles() {
            if (!Object.keys(this.files).length) {
                return;
            }
            this.codeLines = this.codeLines.map(l =>
                Object.keys(this.files).reduce((line, f) =>
                    line.replace(f, `<a href="#" style="text-decoration: underline;" data-file-id="${this.files[f]}">${f}</a>`),
                l),
            );
        },

        onFileClick(event) {
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

        onChildCancel(line, click) {
            if (click !== false) {
                this.clicks[line] = true;
            }
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
        bButton,
        bFormInput,
        bInputGroup,
        bInputGroupButton,
        Icon,
        FeedbackArea,
        Loader,
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
    padding-left: 1em;
    padding-right: 1em;

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

    li:hover & {
        display: block;
    }
}

.loader {
    margin-top: 5em;
}
</style>
