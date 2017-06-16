<template>
  <loader class="col-md-12 text-center" v-if="loading"></loader>
  <ol class="code-viewer form-control" :class="{ editable }" v-else>
    <li v-on:click="editable && addFeedback($event, i)" v-for="(line, i) in codeLines">
      <code v-html="line"></code>


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

    props: ['editable', 'id'],

    data() {
        return {
            fileId: this.id,
            lang: '',
            codeLines: [],
            loading: true,
            editing: {},
            feedback: {},
            clicks: {},
        };
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
    },

    methods: {
        getCode() {
            this.$http.get(`/api/v1/code/${this.fileId}`).then((data) => {
                this.lang = data.data.lang;
                this.feedback = data.data.feedback;
                this.codeLines = this.highlightCode(this.lang, data.data.code);
            });
        },

        // Highlights the given string and returns an array of highlighted strings
        highlightCode(lang, code) {
            let lines = code.split('\n');
            if (getLanguage(lang) !== undefined) {
                let state = null;
                lines = lines.map((line) => {
                    const { top, value } = highlight(lang, line, true, state);
                    state = top;
                    return value;
                });
            }
            this.loading = false;
            return lines;
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
