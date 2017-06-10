<template>
    <div class="code-viewer" v-bind:class="{ editable }">
        <ol class="form-control">
            <li v-on:click="addFeedback($event, i)" v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>

                <b-card v-if="!editable && feedback[i]">
                    {{ feedback[i] }}
                </b-card>

                <b-input-group v-if="editable && feedback[i] != null">
                    <b-form-input v-model="feedback[i]"></b-form-input>

                    <b-input-group-button>
                        <b-button variant="default" v-on:click="cancelFeedback($event, i)">
                            <icon name="times" aria-hidden="true"></icon>
                        </b-button>
                    </b-input-group-button>
                    <b-input-group-button>
                        <b-button variant="primary" v-on:click="submitFeedback($event, i)">
                            <icon name="check" aria-hidden="true"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>

                <icon name="plus" class="add-feedback" v-if="editable && feedback[i] == null"
                    v-on:click="addFeedback($event, i)"></icon>
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
        bButton,
        bFormInput,
        bInputGroup,
        bInputGroupButton,
        Icon,
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
