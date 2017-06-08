<template>
    <div class="code-viewer">
        <ol>
            <li v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <div class="feedback" v-if="!editable" v-show="feedback[i]">
                    {{ feedback[i] }}
                </div>

                <div class="edit-feedback" v-if="editable" v-show="feedback[i] != null">
                    <textarea name="feedback" v-model="feedback[i]"></textarea>
                    <button v-on:click="submitFeedback($event, i)">Submit</button>
                    <button v-on:click="resetFeedback($event, i)">Reset</button>
                </div>
                <span class="add-feedback" v-if="editable" v-show="feedback[i] == null"
                    v-on:click="addFeedback($event, i)">+</span>
            </li>
        </ol>
    </div>
</template>

<script>
import { highlight } from 'highlightjs';

export default {
    name: 'code-viewer',

    props: ['editable'],

    data() {
        return {
            id: this.$route.params.id,
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
        if (!this.code) {
            this.getCode();
        }
    },

    watch: {
        $route(to) {
            this.id = to.params.id;
            this.getCode();
        },
    },

    methods: {
        getCode() {
            this.$http.get(`/api/code/${this.id}`).then((data) => {
                Object.assign(this, data.body);
            });
        },

        addFeedback(event, line) {
            this.feedback[line] = '';
        },

        submitFeedback(event, line) {
            console.log(event, line);
        },

        resetFeedback(event, line) {
            this.feedback[line] = null;
        },
    },
};
</script>

<style src="../../node_modules/highlightjs/styles/github.css"></style>

<style lang="less">
@linenr-width: 4em;
@linenr-bg: #f8f8f8;
@line-bg: white;

ol {
    font-family: monospace;
    margin: 0;
    padding: 0;
    padding-left: @linenr-width;
    background: @linenr-bg;
}

li {
    position: relative;
    padding-left: 1em;
    background: @line-bg;
    cursor: text;
}

code {
    white-space: pre;
    line-height: 1.5;
}

.feedback {
    font-family: sans-serif;
}

textarea {
    display: block;
}

/* The '+' button on the left side. */
.add-feedback {
    display: none;
    position: absolute;
    top: 0;
    left: -@linenr-width;
    height: 100%;
    cursor: pointer;

    &:hover, li:hover & {
        display: block;
    }
}

/* Need this to be able to move the cursor all
 * the way to the left to the '+' button without
 * losing the hover on the li. */
li::before {
    display: block;
    position: absolute;
    top: 0;
    right: 100%;
    width: @linenr-width;
    height: 100%;
    content: '';
}
</style>
