<template>
    <b-card v-if="(done && !editing)">
    <div v-on:click="changeFeedback()" :style="{'min-height': '1em'}">
        {{ internalFeedback }}
    </div>
    </b-card>
    <b-input-group v-else>
        <b-form-input ref="field" v-model="internalFeedback"></b-form-input>
        <b-input-group-button>
            <b-button variant="default" @click="cancelFeedback()">
                <icon name="refresh" spin v-if="deletingFeedback"></icon>
                <icon name="times" aria-hidden="true" v-else></icon>
            </b-button>
        </b-input-group-button>
        <b-input-group-button>
            <b-button variant="primary" @click="submitFeedback()">
              <icon name="refresh" spin v-if="submittingFeedback"></icon>
              <icon name="check" aria-hidden="true" v-else></icon>
            </b-button>
        </b-input-group-button>
    </b-input-group>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

export default {
    name: 'feedback-area',
    props: ['line', 'editing', 'feedback', 'editable', 'fileId'],
    data() {
        return {
            internalFeedback: this.feedback,
            done: true,
            deletingFeedback: false,
            submittingFeedback: false,
        };
    },
    methods: {
        changeFeedback() {
            this.done = false;
            this.$refs.field.focus();
        },
        submitFeedback() {
            this.submittingFeedback = true;
            this.$http.put(`/api/v1/code/${this.fileId}/comments/${this.line}`,
                {
                    comment: this.internalFeedback,
                },
            ).then(() => {
                this.$emit('feedbackChange', this.internalFeedback);
                this.submittingFeedback = false;
                this.done = true;
            });
        },
        cancelFeedback() {
            this.deletingFeedback = true;
            const done = () => {
                this.deletingFeedback = true;
                this.$emit('cancel', this.line);
            };
            this.$http
                .delete(`/api/v1/code/${this.fileId}/comments/${this.line}`)
                .then(done, done);
        },
    },
    components: {
        Icon,
    },
};
</script>
