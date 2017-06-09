<template>
    <div class="code-viewer" v-bind:class="{ editable }">
        <ol>
            <li v-on:click="addFeedback($event, i)" v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <div class="feedback" v-if="!editable" v-show="feedback[i]">
                    {{ feedback[i] }}
                </div>

                <div class="input-group" v-if="editable" v-show="feedback[i] != null">
                    <input type="text" class="form-control" v-model="feedback[i]"></textarea>

                    <div class="input-group-btn">
                        <button type="button" class="btn btn-default cancel" v-on:click="cancelFeedback($event, i)">
                            <span class="glyphicon glyphicon-remove" aria-hidden="true"></span>
                        </button>
                    </div>
                    <div class="input-group-btn">
                        <button type="button" class="btn btn-primary submit" v-on:click="submitFeedback($event, i)">
                            <span class="glyphicon glyphicon-ok" aria-hidden="true"></span>
                        </button>
                    </div>
                </div>
                <span class="add-feedback" v-if="editable" v-show="feedback[i] == null"
                    v-on:click="addFeedback($event, i)">+</span>
            </li>
        </ol>
        <div class="input-group">
            <button type="button" class="btn btn-primary" v-on:click="submitAllFeedback($event)">Submit All</button>
        </div>
    </div>
</template>

<script>
import { highlight } from 'highlightjs';
import Vue from 'vue';

export default {
    name: 'code-viewer',

    props: ['editable', 'id'],

    data() {
        return {
            fileId: this.id,
            lang: '',
            code: '',
            feedback: [],
        };
    },

    computed: {
        highlighted_code() {
            if (!this.code) {
                return [];
            }
            if (!this.lang) {
                return this.code.split('\n');
            }
            const highlighted = highlight(this.lang, this.code);
            return highlighted.value.split('\n');
        },
    },

    mounted() {
        this.getCode();
    },

    watch: {
        id(to) {
            this.fileId = to;
        },

        fileId() {
            this.getCode();
        },
    },

    methods: {
        getCode() {
            this.$http.get(`/api/v1/code/${this.fileId}`).then((data) => {
                this.lang = data.body.lang;
                this.code = data.body.code;
                this.feedback = data.body.feedback;
            });
        },

        addFeedback(event, line) {
            if (this.feedback[line] == null) {
                Vue.set(this.feedback, line, '');
            }
        },

        // eslint-disable-next-line
        submitAllFeedback(event) {},

        // eslint-disable-next-line
        submitFeedback(event, line) {},

        cancelFeedback(event, line) {
            event.stopPropagation();
            Vue.set(this.feedback, line, null);
        },
    },
};
</script>

<style src="../../node_modules/highlightjs/styles/github.css"></style>

<style lang="less" scoped>
@linenr-width: 40px;

ol {
    font-family: monospace;
    margin: 0;
    padding: 0 0 0 @linenr-width;
}

li {
    position: relative;
    padding-left: 1em;
    padding-bottom: 1px;
}

&.editable li {
    cursor: pointer;
}

code {
    white-space: pre;
}

.feedback {
    font-family: sans-serif;
}

.add-feedback {
    display: none;
    position: absolute;
    top: 0;
    left: -@linenr-width;

    li:hover & {
        display: block;
    }
}

</style>
