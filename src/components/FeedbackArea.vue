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
            this.$http.put(`/api/v1/code/${this.fileId}/comment/${this.line}`,
                {
                    comment: this.internalFeedback,
                },
            ).then(() => {
                this.done = true;
                console.log('Comment updated or inserted!');
            });
        },
        cancelFeedback() {
            this.internalFeedback = null;
            // lelijke 'fix' die lege string naar database stuurt.
            this.submitFeedback();
            console.log('TODO:remove comment from database');
            // TODO:remove comment from database
        },
    },
    components: {
        Icon,
    },
};
</script>
