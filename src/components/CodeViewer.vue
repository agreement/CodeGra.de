<template>
    <div class="code-viewer">
        <ol>
            <li v-for="(line, i) in highlighted_code">
                <code v-html="line"></code>
                <div class="feedback" v-if="feedback[i]">
                    {{ feedback[i] }}
                </div>
                <span class="add-comment" v-if="!feedback[i]">+</span>
            </li>
        </ol>
    </div>
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
    margin: 0;
    margin-left: 2em;
    padding: 0;
    background: #f8f8f8;
}

li {
    position: relative;
    margin-left: 4em;
    padding-left: 1em;
    background: white;

    /* Prevent margin collapse. */
    /* TODO: Find better solution. */
    padding-bottom: 1px;
}

code {
    white-space: pre;
    line-height: 1.5;
}

.feedback {
    margin: .5em;
    padding: 1em;
    border: 1px solid #eee;
    border-radius: 8px;
    font-family: sans-serif;
}

/* The '+' button on the left side. */
.add-comment {
    display: none;
    position: absolute;
    top: 0;
    right: 100%;
    width: 1.5em;
    height: 100%;
    margin-right: 4em;
    padding: .2em .5em;
    background: #f8f8f8;
    border: 2px solid #f8f8f8;
    border-right-width: 0;
    border-radius: 35% 0 0 35%;
    font-weight: bold;
    text-align: center;
    cursor: pointer;
}

.add-comment:hover {
        display: block;
        background: transparent;
}

li:hover .add-comment {
    display: block;
}

/* Need this to be able to move the cursor all
 * the way to the left to the '+' button without
 * losing the hover on the li. */
li::before {
    display: block;
    position: absolute;
    top: 0;
    right: 100%;
    width: 4em;
    height: 100%;
    content: '';
}
</style>
