<template>
    <b-form-fieldset>
        <b-input-group>
            <b-input-group-button>
                <submit-button :disabled="this.file === null"
                               @click.prevent="submit"
                               :show-error="showError"
                               ref="submitButton"/>
            </b-input-group-button>
            <b-form-file id="fileUploader"
                         class="fileUploader"
                         ref="formFile"
                         name="file"
                         v-model="file"
                         :disabled="disabled"/>
        </b-input-group>
    </b-form-fieldset>
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
        showError: {
            type: Boolean,
            default: true,
        },
    },

    data() {
        return {
            file: null,
        };
    },

    computed: {
        requestData() {
            const fdata = new FormData();
            fdata.append('file', this.file);
            return fdata;
        },
    },

    methods: {
        submit() {
            return this.$refs.submitButton.submit(
                this.$http.post(this.url, this.requestData).then((res) => {
                    this.$emit('response', res);
                }, ({ response }) => {
                    this.$emit('error', response);
                    throw response.data.message;
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
@import '~mixins.less';

input:disabled {
    cursor: not-allowed !important;
}
</style>

<style lang="less">
@import '~mixins.less';

.custom-file-control{
    &::before {
        border: 0 !important;
    }
}

#app.dark .fileUploader .custom-file-control {
    background: @color-primary;
    color: @text-color-dark;
    &::before {
        background: @color-primary-darker;
        color: white;
    }
}
</style>
