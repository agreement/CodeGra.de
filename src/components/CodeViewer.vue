<template>
    <div class="code-viewer">
        <ol>
            <li v-on:click="addFeedback($event, i)" v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <div class="feedback" v-if="!editable" v-show="feedback[i]">
                    {{ feedback[i] }}
                </div>

                <div class="edit-feedback input-group" v-if="editable" v-show="feedback[i] != null">
                    <input type="text" class="form-control feedback" v-model="feedback[i]"></textarea>

                    <!-- submint & cancel knoppen -->
                    <div class="input-group-btn feedback-buttons" role="group">
                        <button type="button" class="btn btn-default" v-on:click="cancelFeedback($event, i)"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></button>
                        <button type="button" class="btn btn-primary" v-on:click="submitFeedback($event, i)"><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></button>
                    </div>
                </div>
                <span class="add-feedback" v-if="editable" v-show="feedback[i] == null"
                    v-on:click="addFeedback($event, i)">+</span>
            </li>
        </ol>
        <div class="submit-all-feedback">
            <button type="button" class="btn btn-primary" v-on:click="submitAllFeedback($event)">Submit All</button>
        </div>
    </div>
</template>

<script>
import { highlight } from 'highlightjs';
import Vue from 'vue';

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
            if (this.feedback[line] == null) {
                Vue.set(this.feedback, line, '');
            }
        },

        submitAllFeedback(event) {
            console.log(event);
        },

        submitFeedback(event, line) {
            console.log(event, line);
        },

        cancelFeedback(event, line) {
            event.stopPropagation();
            Vue.set(this.feedback, line, null);
        },
    },
};
</script>

<style src="../../node_modules/highlightjs/styles/github.css"></style>

<style lang="less">
@linenr-width: 50px;
@linenr-bg: #f8f8f8;
@line-bg: white;

* {
    box-sizing: border-box;
}

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
    padding-bottom: 1px;
    background: @line-bg;
    cursor: pointer;
}

code {
    white-space: pre;
    line-height: 1.5;
    background-color: white;
}

.feedback {
    font-family: sans-serif;
}

textarea {
    width: 80%;
    margin: 5px 5px 0 5px;
    display: block;
    border-radius: 3px;
    border: 1px solid #bdc3c7;
    background-color: #e5e5e5;
}

.feedback-buttons {

}

textarea:focus{

    border-color: #3aabf0;
    outline: 0;
    box-shadow: inset 0 1px 1px rgba(0,0,0,0,0.75),0 0 8px rgba(58, 171, 240,0.6);

}

/* The '+' button on the left side. */
.add-feedback {
    display: none;
    position: absolute;
    top: -5px;
    left: -@linenr-width + 5px;
    height: 100%;
    cursor: pointer;
    font-size: 20px;

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

.edit-feedback, .submit-all-feedback {
    margin: 10px;
}
</style>
