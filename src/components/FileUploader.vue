<template>
    <b-form-fieldset class="file-uploader">
        <b-input-group>
            <b-input-group-prepend>
                <submit-button :disabled="this.file === null"
                               class="file-uploader-button"
                               @click.prevent="submit"
                               :show-error="showError"
                               ref="submitButton"/>
            </b-input-group-prepend>
            <b-form-file class="file-uploader-form"
                         ref="formFile"
                         name="file"
                         placeholder="Click here to choose a file..."
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
            const req = this.$http.post(this.url, this.requestData).then((res) => {
                this.$emit('response', res);
            }, ({ response }) => {
                this.$emit('error', response);
                throw response.data.message;
            });
            return this.$refs.submitButton.submit(req);
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

.custom-file-label {
    border-left: 0;
}

.file-uploader-button {
    height: 100%;
    button {
        height: 100%;
    }
}

#app.dark .file-uploader-form .custom-file-control {
    background: @color-primary;
    color: @text-color-dark;
    &::before {
        background: @color-primary-darker;
        color: white;
    }
}
</style>
