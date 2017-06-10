<template>
    <div class="code-viewer" v-bind:class="{ editable }">
        <ol class="form-control">
            <li v-on:click="addFeedback($event, i)" v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <div class="feedback" v-if="!editable" v-show="feedback[i]">
                    {{ feedback[i] }}
                </div>

                <div class="input-group" v-if="editable" v-show="feedback[i] != null">
                    <input type="text" class="form-control" v-model="feedback[i]"></textarea>

                    <div class="input-group-btn">
                        <button type="button" class="btn btn-default cancel"
                            v-on:click="cancelFeedback($event, i)">
                            <icon name="times" aria-hidden="true"></icon>
                        </button>
                    </div>
                    <div class="input-group-btn">
                        <button type="button" class="btn btn-primary submit"
                            v-on:click="submitFeedback($event, i)">
                            <icon name="check" aria-hidden="true"></icon>
                        </button>
                    </div>
                </div>

                <icon name="plus" class="add-feedback" v-if="editable"
                    v-show="feedback[i] == null" v-on:click="addFeedback($event, i)">
                </icon>
            </li>
        </ol>
        <div class="input-group">
            <button type="button" class="btn btn-primary"
                v-on:click="submitAllFeedback($event)">Submit All</button>
        </div>
    </div>
</template>

<script>
import { highlight } from 'highlightjs';
import Vue from 'vue';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/plus';

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

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
@linenr-width: 60px;

ol {
    position: relative;
    font-family: monospace;
    margin: 0;
    padding: 0;
    padding-left: @linenr-width;
}

li {
    padding: 0 1em;

    &:first-child {
        padding-top: .5em;
        border-top-right-radius: inherit;
    }

    &:last-child {
        padding-bottom: .5em;
        border-bottom-right-radius: inherit;
    }

    .editable & {
        cursor: pointer;
    }
}

code {
    padding: 0;
    white-space: pre;
}

.feedback {
    font-family: sans-serif;
}

.add-feedback {
    position: absolute;
    right: 100%;
    transform: translate(-50%, -100%);
    display: none;

    li:hover & {
        display: block;
    }
}

</style>
