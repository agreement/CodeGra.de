<template>
    <b-alert variant="danger" show v-if="error">
        <div v-html="error"></div>
    </b-alert>
    <loader class="text-center" v-else-if="loading"></loader>
    <div class="diff-viewer form-control" v-else>
        <ol :class="{ 'show-whitespace': showWhitespace }"
            :style="{
                paddingLeft: `${3 + Math.log10(lines.length) * 2/3}em`,
                fontSize: `${fontSize}px`,
            }">
            <li v-for="(line, i) in lines"
                :key="i"
                :class="line.cls">
                <code v-html="line.txt"/>
            </li>
        </ol>
    </div>
</template>

<script>
import { diffLines } from 'diff';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/cog';
import 'vue-multiselect/dist/vue-multiselect.min.css';

import FeedbackArea from './FeedbackArea';
import LinterFeedbackArea from './LinterFeedbackArea';
import Loader from './Loader';
import Toggle from './Toggle';

import { visualizeWhitespace } from './utils';

const decoder = new TextDecoder('utf-8', { fatal: true });

export default {
    name: 'diff-viewer',

    props: {
        file: {
            type: Object,
            default: null,
        },
        fontSize: {
            type: Number,
            default: 12,
        },
        showWhitespace: {
            type: Boolean,
            default: true,
        },
    },

    data() {
        return {
            code: '',
            lines: [],
            loading: true,
            error: false,
            canUseSnippets: false,
        };
    },

    mounted() {
        this.getCode();
    },

    watch: {
        file(f) {
            if (f) this.getCode();
        },

        tree() {
            this.linkFiles();
        },
    },

    methods: {
        getCode() {
            this.loading = true;
            this.error = '';

            const promises = this.file.ids.map(id => (id ?
                this.$http.get(`/api/v1/code/${id}`, { responseType: 'arraybuffer' }) :
                Promise.resolve('')));

            Promise.all(promises).then(([{ data: orig }, { data: rev }]) => {
                let origCode;
                let revCode;
                try {
                    origCode = decoder.decode(orig);
                    revCode = decoder.decode(rev);
                } catch (e) {
                    this.error = 'This file cannot be displayed';
                    return;
                }

                this.diffCode(origCode, revCode);
            }, ({ response: { data: { message } } }) => {
                this.error = message;
            }).then(() => {
                this.loading = false;
                this.$emit('load');
            });
        },

        diffCode(origCode, revCode) {
            const diff = diffLines(origCode, revCode);
            const lines = [];

            for (let i = 0; i < diff.length; i += 1) {
                let cls = '';
                if (diff[i].added) cls = 'added';
                else if (diff[i].removed) cls = 'removed';

                let partLines = diff[i].value.split('\n');
                if (!partLines[partLines.length - 1]) partLines.pop();
                partLines = partLines.map(txt => ({ txt, cls }));
                lines.push(...partLines);
            }

            lines.forEach((line) => {
                line.txt = this.$htmlEscape(line.txt);
            });

            if (lines.length < 5000) {
                lines.forEach((line) => {
                    line.txt = visualizeWhitespace(line.txt);
                });
            }

            this.lines = lines;
        },
    },

    components: {
        Icon,
        FeedbackArea,
        LinterFeedbackArea,
        Loader,
        Toggle,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.diff-viewer {
    position: relative;
    padding: 0;
    background: #f8f8f8;

    #app.dark & {
        background: @color-primary-darker;
    }
}

ol {
    min-height: 5em;
    overflow-x: visible;
    background: @linum-bg;
    margin: 0;
    padding: 0;
    font-family: monospace;
    font-size: small;

    #app.dark & {
        background: @color-primary-darkest;
        color: @color-secondary-text-lighter;
    }
}

li {
    position: relative;
    padding-left: .75em;
    padding-right: .75em;
    background-color: lighten(@linum-bg, 1%);
    border-left: 1px solid darken(@linum-bg, 5%);

    &.added {
        background-color: @color-diff-added-light !important;

        #app.dark & {
            background-color: @color-diff-added-dark !important;
        }
    }

    &.removed {
        background-color: @color-diff-removed-light !important;

        #app.dark & {
            background-color: @color-diff-removed-dark !important;
        }
    }

    #app.dark & {
        background: @color-primary-darker;
        border-left: 1px solid darken(@color-primary-darkest, 5%);
    }
}

code {
    color: @color-secondary-text;
    background: transparent;
    white-space: pre-wrap;

    #app.dark & {
        color: #839496;
    }

    li.added & {
        color: black !important;
    }

    li.removed & {
        color: black !important;
    }
}

.loader {
    margin-top: 2.5em;
    margin-bottom: 3em;
}
</style>

<style lang="less">
@import '~mixins.less';

.diff-viewer {
    .whitespace {
        opacity: 0;
        #app.dark & {
            color: @color-secondary-text;
        }
    }

    .show-whitespace .whitespace {
        opacity: 1;
    }
}
</style>
