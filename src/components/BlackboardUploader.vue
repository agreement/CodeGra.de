<template>
    <form method="post" enctype="multipart/form-data"
            :action="action"
            v-on:submit.prevent="submit"
            :label-size="1">
        <b-form-fieldset :feedback="error">
            <b-input-group>
                <b-input-group-button>
                    <b-button :disabled="disabled || !hasFile" :variant="error ? 'danger' : (done ? 'success' : 'primary')" type="submit">
                        <icon scale=1 name="exclamation-triangle" v-if="error"></icon>
                        <loader scale=1 v-else-if="pending"></loader>
                        <icon scale=1 name="check" v-else-if="done"></icon>
                        <span v-else>Submit</span>
                    </b-button>
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

import Loader from './Loader';

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
        submit: function submit(event) {
            this.pending = true;
            const formData = new FormData(event.target);
            this.$http.post(this.action, formData).then(() => {
                this.done = true;
                this.pending = false;
                this.$nextTick(() => setTimeout(() => {
                    this.done = false;
                }, 2000));
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

<style lang="less">
input:disabled {
    cursor: not-allowed !important;
}
</style>
