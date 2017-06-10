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
                            <icon name="times" aria-hidden="true"></icon>
                        </button>
                    </div>
                    <div class="input-group-btn">
                        <button type="button" class="btn btn-primary submit" v-on:click="submitFeedback($event, i)">
                            <icon name="check" aria-hidden="true"></icon>
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

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

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
        submitFeedback(event, line) {
            this.$http.put(`/api/v1/code/${this.fileId}/comment/${line}`,
                {
                    comment: this.feedback[line],
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                // eslint-disable-next-line
                console.log('Comment updated or inserted!');
            });
        },

        cancelFeedback(event, line) {
            event.stopPropagation();
            Vue.set(this.feedback, line, null);
        },
    },

    components: {
        Icon,
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
