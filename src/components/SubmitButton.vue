<template>
    <b-button @click="update"
        :variant="success ? 'success' : failure ? 'danger' : 'primary'">
        <loader :scale="1" v-if="submitted"></loader>
        <span v-else>{{ label }}</span>
    </b-button>
</template>

<script>
import { bButton } from 'bootstrap-vue/lib/components';
import Loader from './Loader';

export default {
    name: 'submit-button',

    data() {
        return {
            submitted: false,
            success: false,
            failure: false,
        };
    },

    props: {
        label: {
            type: String,
            default: 'Submit',
        },
        update: {
            type: Function,
            default: () => {},
        },
    },

    methods: {
        submit(promise) {
            this.submitted = true;
            return Promise.resolve(promise).then(() => {
                this.success = true;
                this.$nextTick(() =>
                    setTimeout(() => {
                        this.success = false;
                    }, 1000));
            }, () => {
                this.failure = true;
                this.$nextTick(() =>
                    setTimeout(() => {
                        this.failure = false;
                    }, 1000));
            }).then(() => {
                this.submitted = false;
            });
        },
    },

    components: {
        Loader,
        bButton,
    },
};
</script>
