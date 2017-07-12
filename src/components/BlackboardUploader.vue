<template>
    <form :label-size="1" ref="fileInput">
        <b-form-fieldset :feedback="error">
            <b-input-group>
                <b-input-group-button>
                    <submit-button @click="submit" ref="submitButton" :showError="false"/>
                </b-input-group-button>
                <b-form-file name="file" v-model="file" @change="change" :disabled="disabled"/>
            </b-input-group>
        </b-form-fieldset>
    </form>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/exclamation-triangle';

import SubmitButton from './SubmitButton';

export default {
    name: 'blackboard-uploader',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
        disabled: {
            type: Boolean,
            default: false,
        },
    },

    computed: {
        action: function action() {
            return this.assignment ? `/api/v1/assignments/${this.assignment.id}/submissions/` : null;
        },
    },

    data() {
        return {
            file: null,
            error: '',
            hasFile: false,
        };
    },

    methods: {
        change() {
            this.error = '';
            this.hasFile = true;
        },

        submit() {
            const formData = new FormData(this.$refs.fileInput);
            const req = this.$http.post(this.action, formData);
            req.catch(({ response }) => {
                this.error = response.data.description;
            });
            this.$refs.submitButton.submit(req);
        },
    },

    components: {
        Icon,
        SubmitButton,
    },
};
</script>

<style lang="less">
input:disabled {
    cursor: not-allowed !important;
}
</style>
