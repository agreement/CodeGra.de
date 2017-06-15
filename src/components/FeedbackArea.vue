<template>
  <b-card v-if="(done && !editing)">
    <div v-on:click="changeFeedback()" :style="{'min-height': '1em'}">
      <div v-html="newlines(escape(serverFeedback))">
      </div>
    </div>
    </b-card>
    <div v-else>
      <b-collapse class="collapsep flex-container" ref="snippetDialog" :id="`collapse${line}`">
        <b-form-input class="input" v-model="snippetKey" v-on:keydown.native.ctrl.enter="addSnippet">
        </b-form-input>
        <b-popover :placement="'top'" :show="error !== '' && $parent.show" :content="error">
          <b-btn :variant="snippetDone ? 'success' : 'primary'" style="margin-left: 0.2em;" @click="addSnippet">
            <icon name="refresh" scale="1" spin v-if="pending"></icon>
            <icon name="check" aria-hidden="true" v-else></icon>
          </b-btn>
        </b-popover>
      </b-collapse>
      <b-input-group>
        <b-form-input
          :textarea="true"
          ref="field" v-model="internalFeedback"
          :style="{'font-size': '1em'}"
          v-on:keydown.native.tab.capture="expandSnippet"
          v-on:keydown.native.ctrl.enter="submitFeedback"
          v-on:keydown.native.esc="revertFeedback">
        </b-form-input>
        <b-input-group-button class="minor-buttons">
          <b-btn v-b-toggle="`collapse${line}`" variant="secondary" v-on:click="findSnippet">
            <icon name="plus" aria-hidden="true"></icon>
          </b-btn>
          <b-button variant="danger" @click="cancelFeedback">
            <icon name="refresh" spin v-if="deletingFeedback"></icon>
            <icon name="times" aria-hidden="true" v-else></icon>
          </b-button>
        </b-input-group-button>
        <b-input-group-button class="submit-feedback">
          <b-button variant="primary" @click="submitFeedback">
            <icon name="refresh" spin v-if="submittingFeedback"></icon>
            <icon name="check" aria-hidden="true" v-else></icon>
          </b-button>
        </b-input-group-button>
      </b-input-group>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/plus';

import { mapActions, mapGetters } from 'vuex';

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
            serverFeedback: this.feedback,
            done: true,
            error: '',
            snippetKey: '',
            pending: false,
            snippetDone: false,
            deletingFeedback: false,
            submittingFeedback: false,
        };
    },
    mounted() {
        this.$nextTick(() => this.$refs.field.focus());
    },
    methods: {
        changeFeedback() {
            if (this.editable) {
                this.done = false;
                this.$nextTick(() => this.$refs.field.focus());
                this.internalFeedback = this.serverFeedback;
            }
        },
        submitFeedback() {
            if (this.internalFeedback === '') {
                this.cancelFeedback();
                return;
            }
            const submitted = this.internalFeedback;
            this.submittingFeedback = true;
            this.$http.put(`/api/v1/code/${this.fileId}/comments/${this.line}`,
                {
                    comment: submitted,
                },
            ).then(() => {
                this.$emit('feedbackChange', this.internalFeedback);
                this.serverFeedback = submitted;
                this.snippetKey = '';
                this.$emit('feedbackChange', this.internalFeedback);
                this.submittingFeedback = false;
                this.done = true;
            });
        },
        newlines(value) {
            return value.replace(/\n/g, '<br>');
        },
        escape(text) {
            return String(text).replace(entityRE, entity => entityMap[entity]);
        },
        revertFeedback() {
            if (this.serverFeedback === '') {
                this.cancelFeedback();
                return;
            }
            this.$emit('feedbackChange', this.serverFeedback);
            this.done = true;
        },
        cancelFeedback() {
            this.snippetKey = '';
            if (this.feedback !== '') {
                this.deletingFeedback = true;
                const done = () => {
                    this.deletingFeedback = true;
                    this.$emit('cancel', this.line);
                };
                this.$http
                    .delete(`/api/v1/code/${this.fileId}/comments/${this.line}`)
                    .then(done, done);
            } else {
                this.$emit('cancel', this.line);
            }
        },
        expandSnippet(event) {
            const field = this.$refs.field;
            const end = field.$el.selectionEnd;
            if (field.$el.selectionStart === end) {
                event.preventDefault();
                const val = this.internalFeedback.slice(0, end);
                const start = Math.max(val.lastIndexOf(' '), val.lastIndexOf('\n')) + 1;
                const res = this.snippets()[val.slice(start, end)];
                if (res !== undefined) {
                    this.snippetKey = val.slice(start, end);
                    this.internalFeedback = val.slice(0, start) + res.value +
                        this.internalFeedback.slice(end);
                }
                if (Math.random() < 0.25) {
                    this.refreshSnippets();
                }
            }
        },
        addSnippet() {
            const val = {
                key: this.snippetKey,
                value: { value: this.internalFeedback },
            };
            if (val.key.indexOf(' ') > -1 || val.key.indexOf('\n') > -1) {
                this.error = 'No spaces allowed!';
                return;
            } else if (val.key.length === 0) {
                this.error = 'Snippet key cannot be empty';
                return;
            } else if (val.value.value.length === 0) {
                this.error = 'Snippet value cannot be empty';
                return;
            }
            this.error = '';
            this.pending = true;
            this.addSnippetToStore(val);
            this.$http.put('/api/v1/snippet', {
                key: val.key,
                value: val.value.value,
            }).then(() => {
                this.pending = false;
                this.snippetDone = true;
                // Add a small timeout such that the green sign is visible
                this.$nextTick(() => setTimeout(() => {
                    this.snippetDone = false;
                    this.$root.$emit('collapse::toggle', `collapse${this.line}`);
                }, 1000));
            });
        },
        findSnippet() {
            if (this.snippetKey !== '' || this.$refs.snippetDialog.show) {
                return;
            }

            const snips = this.snippets();
            const keys = Object.keys(snips);

            for (let i = 0, len = keys.length; i < len; i += 1) {
                if (this.internalFeedback === snips[keys[i]].value) {
                    this.snippetKey = keys[i];
                    return;
                }
            }
        },
        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
            addSnippetToStore: 'user/addSnippet',
        }),
        ...mapGetters({
            snippets: 'user/snippets',
        }),
    },
    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
button.btn {
    cursor: pointer;
}

.minor-buttons:hover {
    z-index: 0;
}

.collapsep .input {
    width: 80% !important;
    flex: 1;
}

.collapsep {
    width: 30%;
    float: right;
    display: flex;
}
.flex-container {
    flex-wrap: wrap;
}
.flex-container::after {
    content: '';
    width: 100%;
}
.flex-item:last-child { /* or `:nth-child(n + 4)` */
    order: 1;
}
.help {
    width: 80%;
    float: left;
}
</style>
