<template>
    <ol class="code-viewer">
        <li v-for="(line, i) in highlighted_code">
            <code v-html="line"></code>
            <div class="feedback" v-if="feedback[i]">
                {{ feedback[i] }}
            </div>
        </li>
    </ol>
</template>

<script>
import { highlight } from 'highlightjs';

export default {
    name: 'code-viewer',

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
            if (!this.lang || !this.code) {
                return [];
            }
            const highlighted = highlight(this.lang, this.code);
            return highlighted.value.split('\n');
        },
    },

    mounted() {
        this.getCode();
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
                this.lang = data.body.lang;
                this.code = data.body.code;
                this.feedback = data.body.feedback;
            });
        },
    },
};
</script>

<style src="../../node_modules/highlightjs/styles/github.css"></style>

<style>
ol {
    font-family: monospace;
}

code {
    white-space: pre;
    line-height: 1.5;
}

.feedback {
    font-family: sans-serif;
}
</style>
