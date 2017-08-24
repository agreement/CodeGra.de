<template>
    <form class="file-uploader" ref="form" method="POST" enctype="multipart/form-data">
        <b-form-fieldset>
            <b-input-group>
                <b-input-group-button>
                    <submit-button
                        :disabled="this.file === null"
                        @click.prevent="submit"
                        ref="submitButton"/>
                </b-input-group-button>
                <b-form-file
                    name="file"
                    v-model="file"
                    :disabled="disabled"/>
            </b-input-group>
        </b-form-fieldset>
    </form>
</template>

<script>
import SubmitButton from './SubmitButton';

export default {
    name: 'file-uploader',

    props: {
        url: {
            type: String,
            default: '',
        },
        disabled: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            file: null,
        };
    },

    methods: {
        submit() {
            const fdata = new FormData(this.$refs.form);
            return this.$refs.submitButton.submit(
                this.$http.post(this.url, fdata).then((res) => {
                    this.$emit('response', res);
                }, ({ response: { data: { message } } }) => {
                    this.$emit('error', message);
                    throw message;
                }),
            );
        },
    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
input:disabled {
    cursor: not-allowed !important;
}
</style>
