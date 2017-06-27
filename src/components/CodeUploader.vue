<template>
    <form ref="fileInput">
        <b-form-fieldset :feedback="error">
            <b-input-group>
                <b-input-group-button>
                <b-button :disabled="!hasFile" :variant="error ? 'danger' : (done ? 'success' : 'primary')" @click.native="submit" >
                    <icon scale=1 name="exclamation-triangle" v-if="error"></icon>
                    <loader scale=1 v-else-if="pending"></loader>
                    <icon scale=1 name="check" v-else-if="done"></icon>
                    <span v-else>Submit</span>
                </b-button>
                </b-input-group-button>
                <b-form-file name="file" placeholder="click or drop file" v-model="file" @change="change"></b-form-file>
            </b-input-group>
        </b-form-fieldset>
    </form>
</template>

<script>

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/exclamation-triangle';

import Loader from './Loader';

export default {
    name: 'code-uploader',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    computed: {
        action: function action() {
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
        };
    },

    methods: {
        change: function change() {
            this.error = '';
            this.hasFile = true;
        },

        submit: function submit() {
            this.pending = true;
            const formData = new FormData(this.$refs.fileInput);
            this.$http.post(this.action, formData).then((response) => {
                this.done = true;
                this.pending = false;
                this.$router.push({ name: 'submission', params: { submissionId: response.data.id } });

                this.$nextTick(() => setTimeout(() => {
                    this.done = false;
                }, 1000));
            }, () => {
                this.error = 'Something went wrong';
                this.pending = false;
            });
        },
    },

    components: {
        Icon,
        Loader,
    },
};
</script>
