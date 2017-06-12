<template>
    <b-card v-if="!editing">
        {{ internalFeedback }}
    </b-card>
    <b-input-group v-else>
        <b-form-input v-model="internalFeedback"></b-form-input>

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

export default {
    name: 'feedback-area',
    props: ['line', 'editing', 'feedback'],
    data() {
        return {
            internalFeedback: this.feedback,
        };
    },
    methods: {
        submitFeedback() {
            this.$emit('feedbackChange', this.internalFeedback);
            this.$http.put(`/api/v1/code/${this.fileId}/comment/${this.line}`,
                {
                    comment: this.feedback[this.line],
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                console.log('Comment updated or inserted!');
            });
        },
        cancelFeedback() {
            // TODO: Decide what to do
        },
    },
    components: {
        Icon,
    },
};
</script>
