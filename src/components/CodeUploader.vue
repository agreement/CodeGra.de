<template>
    <form ref="form">
        <b-popover placement="top" :triggers="disabled ? ['hover'] : []" content="You can only submit this assignment from within your LMS">
        <b-form-fieldset :feedback="error">
            <b-input-group>
                <b-input-group-button>
                    <submit-button
                        :disabled="!hasFile"
                        @click="submit"
                        ref="submitButton">
                    </submit-button>
                </b-input-group-button>
                <b-form-file
                    name="file"
                    placeholder="click or drop file"
                    v-model="file"
                    @change="change">
                </b-form-file>
            </b-input-group>
        </b-form-fieldset>
        </b-popover>
    </form>
</template>

<script>

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/exclamation-triangle';

import SubmitButton from './SubmitButton';

export default {
    name: 'code-uploader',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    computed: {
        action() {
            return this.assignment ? `/api/v1/assignments/${this.assignment.id}/submission` : null;
        },
    },

    data() {
        return {
            file: null,
            done: false,
            pending: false,
            error: '',
            hasFile: false,
            disabled: this.assignment.is_lti && !window.inLTI,
        };
    },

    methods: {
        change: function change() {
            this.error = '';
            this.hasFile = true;
        },

        submit: function submit() {
            const fdata = new FormData(this.$refs.form);
            const req = this.$http.post(this.action, fdata);
            req.then(({ data }) => {
                this.$router.push({
                    name: 'submission',
                    params: { submissionId: data.id },
                });
            });
            this.$refs.submitButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },
    },

    components: {
        Icon,
        SubmitButton,
    },
};
</script>

<style lang="less">
.custom-file input:disabled {
    cursor: not-allowed !important;
}
</style>
