<template>
    <b-card class="feedback-area non-editable" v-if="(done && !editing)">
        <div @click="changeFeedback($event)" :style="{'min-height': '1em'}">
            <div v-html="newlines($htmlEscape(serverFeedback))"></div>
        </div>
    </b-card>
    <div class="feedback-area edit" v-else
         @click="$event.stopPropagation()">
        <b-collapse class="collapsep"
                    v-if="canUseSnippets"
                    ref="snippetDialog"
                    :id="`collapse${line}`"
                    style="margin: 0">
            <div>
                <b-input-group class="input-snippet-group">
                    <input class="input form-control"
                           v-model="snippetKey"
                           @keydown.ctrl.enter="addSnippet"/>
                    <b-input-group-append>
                        <submit-button ref="addSnippetButton"
                                    class="add-snippet-btn"
                                    label=""
                                    @click="addSnippet">
                            <icon :scale="1" name="check"/>
                        </submit-button>
                    </b-input-group-append>
                </b-input-group>
            </div>
        </b-collapse>
        <b-input-group class="editable-area">
            <textarea ref="field"
                      v-model="internalFeedback"
                      class="form-control"
                      style="font-size: 1em;"
                      @keydown.tab="expandSnippet"
                      @keydown.ctrl.enter="submitFeedback"
                      @keydown.esc="revertFeedback"/>
            <div class="minor-buttons btn-group-vertical">
                <b-btn v-b-toggle="`collapse${line}`"
                       class="snippet-btn"
                       variant="secondary"
                       v-if="canUseSnippets"
                       @click="findSnippet">
                    <icon name="plus" aria-hidden="true"></icon>
                </b-btn>
                <submit-button @click="cancelFeedback"
                               ref="deleteFeedbackButton"
                               default="danger"
                               show-inline
                               :label="false">
                    <icon name="times" aria-hidden="true"/>
                </submit-button>
            </div>
            <b-input-group-append class="submit-feedback">
                <submit-button @click="submitFeedback"
                               ref="addFeedbackButton"
                               :label="false">
                    <icon name="check" aria-hidden="true"/>
                </submit-button>
            </b-input-group-append>
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

import SubmitButton from './SubmitButton';

export default {
    name: 'feedback-area',
    props: ['line', 'editing', 'feedback', 'editable', 'fileId', 'canUseSnippets'],

    data() {
        return {
            internalFeedback: this.feedback,
            serverFeedback: this.feedback,
            done: true,
            snippetKey: '',
        };
    },

    mounted() {
        this.$nextTick(() => {
            if (!this.done || this.editing) {
                this.$refs.field.focus();
            }
        });
    },

    methods: {
        changeFeedback(e) {
            if (this.editable) {
                this.done = false;
                this.$nextTick(() => this.$refs.field.focus());
                this.internalFeedback = this.serverFeedback;
                e.stopPropagation();
            }
        },

        focusInput() {
            this.$nextTick(() => {
                if (this.$refs.field) this.$refs.field.focus();
            });
        },

        submitFeedback() {
            if (this.internalFeedback === '' || this.internalFeedback == null) {
                this.cancelFeedback();
                return;
            }

            const submitted = this.internalFeedback;

            const req = this.$http.put(
                `/api/v1/code/${this.fileId}/comments/${this.line}`,
                {
                    comment: submitted,
                },
            ).then(() => {
                this.internalFeedback = submitted;
                this.serverFeedback = submitted;
                this.snippetKey = '';
                this.done = true;
                this.$emit('feedbackChange', submitted);
            }, (err) => {
                throw err.response.data.message;
            });

            this.$refs.addFeedbackButton.submit(req);
        },
        newlines(value) {
            return value.replace(/\n/g, '<br>');
        },
        revertFeedback() {
            if (this.serverFeedback === '') {
                this.cancelFeedback(false);
            } else {
                this.$emit('feedbackChange', this.serverFeedback, true);
                this.done = true;
            }
        },
        cancelFeedback(val) {
            this.snippetKey = '';
            if (this.feedback !== '') {
                const done = () => {
                    this.$emit('cancel', this.line, val);
                };
                const req = this.$http.delete(
                    `/api/v1/code/${this.fileId}/comments/${this.line}`,
                ).then(
                    done,
                    (err) => {
                        // Don't error for a 404 as the comment was deleted.
                        if (err.response.status === 404) {
                            done();
                        } else {
                            throw err.response.data.message;
                        }
                    },
                );

                this.$refs.deleteFeedbackButton.submit(req);
            } else {
                this.$emit('cancel', this.line, val);
            }
        },
        expandSnippet(event) {
            event.preventDefault();

            if (!this.canUseSnippets) {
                return;
            }

            const { selectionStart, selectionEnd } = this.$refs.field;

            if (selectionStart === selectionEnd) {
                const val = this.internalFeedback.slice(0, selectionEnd);
                const start = Math.max(val.lastIndexOf(' '), val.lastIndexOf('\n')) + 1;
                const res = this.snippets()[val.slice(start, selectionEnd)];
                if (res !== undefined) {
                    this.snippetKey = val.slice(start, selectionEnd);
                    this.internalFeedback = val.slice(0, start) + res.value +
                        this.internalFeedback.slice(selectionEnd);
                }
                this.refreshSnippets();
            }
        },
        addSnippet() {
            const val = {
                key: this.snippetKey,
                value: this.internalFeedback,
            };
            if (val.key.match(/\s/)) {
                this.$refs.addSnippetButton.fail('No spaces allowed!');
                return;
            } else if (val.key.length === 0) {
                this.$refs.addSnippetButton.fail('Snippet key cannot be empty');
                return;
            } else if (!val.value) {
                this.$refs.addSnippetButton.fail('Snippet value cannot be empty');
                return;
            }

            const req = this.$http.put('/api/v1/snippet', val).then(({ data }) => {
                val.id = data.id;
                this.addSnippetToStore(val);
            }, (err) => {
                throw err.response.data.message;
            });
            this.$refs.addSnippetButton.submit(req).then((success) => {
                if (success) {
                    this.$root.$emit('collapse::toggle', `collapse${this.line}`);
                }
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
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.feedback-area {
    .default-text-colors;
    &.edit {
        padding-top: @line-spacing;
    }
}

.card-body {
    padding: 0.5rem;
}

.non-editable {
    white-space: pre-wrap;
    word-break: break-word;
}

button {
    border: none;
    box-shadow: none !important;
}

.minor-buttons {
    z-index: 1000;
    &:hover {
        box-shadow: none;
    }
    button, .submit-button {
        flex: 1;
        &:first-child {
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
        }
    }
    min-height: 7em;
}

.collapsep {
    float: right;
    display: flex;
}

textarea {
    #app.dark & {
        border: 0;
    }
    min-height: 7em;
}

#app:not(.dark) .snippet-btn {
    border-top-width: 1px;
    border-top-style: solid;
}

.editable-area {
    #app.dark & {
        border: .5px solid @color-secondary;
    }
    padding: 0;
    border-radius: 0.25rem;
}

.input.snippet {
    margin: 0;
}

.input-snippet-group {
    padding-top: 0;
}
</style>

<style lang="less">
.feedback-area .minor-buttons .submit-button.btn:last-child {
    border-bottom-right-radius: 0px;
    border-bottom-left-radius: 0px;
    border-top-right-radius: 0px;
    border-top-left-radius: 0px;
}
</style>
