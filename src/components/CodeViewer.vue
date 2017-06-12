<template>
    <div class="code-viewer" v-bind:class="{ editable }">
        <ol class="form-control">
            <li v-on:click="addFeedback($event, i)" v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <feedback-area :editing='feedback' :feedback='feedback[i]' v-on:feedbackChange="val => { feedbackChange(i, val); }"></feedback-area>

                <icon name="plus" class="add-feedback" v-if="editable && feedback[i] == null"
                    v-on:click="addFeedback($event, value)"></icon>
            </li>
        </ol>
    </div>
</template>

<script>
import { highlight } from 'highlightjs';
import Vue from 'vue';

import { bButton, bFormInput, bInputGroup, bInputGroupButton }
    from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/plus';

import FeedbackArea from '@/components/FeedbackArea';

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

        feedbackChange(line, feedback) {
            this.feedback[line] = feedback;
        },
        // eslint-disable-next-line
        submitAllFeedback(event) {},

        // Moved to feedbackarea.vue
        // eslint-disable-next-line
        // submitFeedback(event, line) {
        //     this.$http.put(`/api/v1/code/${this.fileId}/comment/${line}`,
        //         {
        //             comment: this.feedback[line],
        //         },
        //         {
        //             headers: { 'Content-Type': 'application/json' },
        //         },
        //     ).then(() => {
        //         console.log('Comment updated or inserted!');
        //     });
        // },
        // cancelFeedback(event, line) {
        //     event.stopPropagation();
        //     Vue.set(this.feedback, line, null);
        // },
    },

    components: {
        bButton,
        bFormInput,
        bInputGroup,
        bInputGroupButton,
        Icon,
        FeedbackArea,
    },
};
</script>

<style lang="less" scoped>
ol {
    position: relative;
    font-family: monospace;
    font-size: small;
    margin: 0;
    padding: 0;
    padding-left: 4rem;
}

li {
    padding-left: 1em;
    padding-right: 1em;

    .editable & {
        cursor: pointer;
    }
}

code {
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
