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
            this.done = false;
            console.log(this.$refs);
            this.$refs.field.focus();
        },
        submitFeedback() {
            console.log(this.$refs);
            this.$emit('feedbackChange', this.internalFeedback);
            this.$http.put(`/api/v1/codes/${this.fileId}/comments/${this.line}`,
                {
                    comment: this.internalFeedback,
                },
            ).then(() => {
                this.done = true;
                console.log('Comment updated or inserted!');
            });
        },
        cancelFeedback() {
            // TODO: collaps textarea
            this.$http.delete(`/api/v1/codes/${this.fileId}/comments/${this.line}`)
            .then(() => {
                // eslint-disable-next-line
                console.log('Comment removed!');
            }, () => null);
            this.$emit('cancel', this.line);
        },
    },
    components: {
        Icon,
    },
};
</script>
