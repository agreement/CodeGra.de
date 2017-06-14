<template>
    <b-card v-if="(done && !editing)">
    <div v-on:click="changeFeedback()" :style="{'min-height': '1em'}">
      <div v-html="newlines(escape(internalFeedback))">
      </div>
    </div>
    </b-card>
    <b-input-group v-else>
      <b-form-input
        :textarea="true"
        ref="field" v-model="internalFeedback"
        :style="{'font-size': '1em'}"
        v-on:keydown.native.tab.capture="expandSnippet">
      </b-form-input>
        <b-input-group-button>
            <b-button variant="primary" @click="submitFeedback">
                <icon name="check" aria-hidden="true"></icon>
            </b-button>
            <b-button variant="default" @click="cancelFeedback">
                <icon name="times" aria-hidden="true"></icon>
            </b-button>
        </b-input-group-button>
    </b-input-group>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import { mapActions } from 'vuex';

const entityRE = /[&<>]/g;
const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
};

export default {
    name: 'feedback-area',
    props: ['line', 'editing', 'feedback', 'editable', 'fileId'],
    data() {
        return {
            internalFeedback: this.feedback,
            done: true,
        };
    },
    methods: {
        changeFeedback() {
            this.done = false;
            this.$refs.field.focus();
        },
        submitFeedback() {
            this.$emit('feedbackChange', this.internalFeedback);
            this.$http.put(`/api/v1/code/${this.fileId}/comments/${this.line}`,
                {
                    comment: this.internalFeedback,
                },
            ).then(() => {
                this.done = true;
            });
        },
        newlines(value) {
            return value.replace(/\n/g, '<br>');
        },
        escape(text) {
            return String(text).replace(entityRE, entity => entityMap[entity]);
        },
        cancelFeedback() {
            // TODO: collaps textarea
            this.$http.delete(`/api/v1/code/${this.fileId}/comments/${this.line}`)
            .then(() => {
            }, () => null);
            this.$emit('cancel', this.line);
        },
        expandSnippet(event) {
            const field = this.$refs.field;
            const end = field.$el.selectionEnd;
            if (field.$el.selectionStart === end) {
                event.preventDefault();
                const val = field.value.slice(0, end);
                const start = Math.max(val.lastIndexOf(' '), val.lastIndexOf('\n')) + 1;
                const res = this.$store.getters['user/snippets'][val.slice(start, end)];
                if (res !== undefined) {
                    this.internalFeedback = val.slice(0, start) + res.value +
                        field.value.slice(end);
                }
                if (Math.random() < 0.25) {
                    this.refreshSnippets();
                }
            }
        },
        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
        }),
    },
    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
.input-group-btn button:first-child {
    border-top-right-radius: 0.25rem !important;
}
.input-group-btn button:last-child {
    border-top-right-radius: 0px !important;
    border-bottom-right-radius: 0.25rem !important;
}

.input-group-btn button {
    cursor: pointer;
}
</style>
