<template>
    <b-card v-if="(done && !editing)">
      <div v-on:click="changeFeedback" :style="{'min-height': '1em'}">
        {{ internalFeedback }}
      </div>
    </b-card>
    <b-input-group v-else>
        <b-form-input ref="field" v-model="internalFeedback"></b-form-input>
        <b-input-group-button>
            <b-button variant="default" @click="cancelFeedback()">
                <icon name="times" aria-hidden="true"></icon>
            </b-button>
        </b-input-group-button>
        <b-input-group-button>
            <b-button variant="primary" @click="submitFeedback()">
                <icon name="check" aria-hidden="true"></icon>
            </b-button>
        </b-input-group-button>
    </b-input-group>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

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
            if (this.editable) {
                this.done = false;
                this.$refs.field.focus();
            }
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
        cancelFeedback() {
            // TODO: collaps textarea
            this.$http.delete(`/api/v1/code/${this.fileId}/comments/${this.line}`)
            .then(() => {
            }, () => null);
            this.$emit('cancel', this.line);
        },
    },
    components: {
        Icon,
    },
};
</script>
