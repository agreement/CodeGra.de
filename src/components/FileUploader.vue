<template>
<b-form-fieldset class="file-uploader" :class="{ disabled }">
    <b-input-group>
        <b-input-group-prepend>
            <submit-button :disabled="this.file === null"
                           :id="buttonId"
                           class="file-uploader-button"
                           @click.prevent="submit"
                           :show-error="showError"
                           ref="submitButton"/>
        </b-input-group-prepend>
        <b-input-group-prepend v-if="$slots.default">
            <slot/>
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
import SubmitButton, { SubmitButtonCancelled } from './SubmitButton';

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
        beforeUpload: {
            type: Function,
            default: () => false,
        },
        buttonId: {
            default: undefined,
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
            let stopped = false;
            if (this.disabled) {
                return this.$refs.submitButton.fail('This uploader is disabled');
            }

            const req = Promise.resolve(this.beforeUpload()).then((stop) => {
                if (stop) {
                    stopped = true;
                    this.$refs.submitButton.reset();
                    return null;
                }
                return this.$http.post(this.url, this.requestData).then((res) => {
                    this.$emit('response', res);
                }, ({ response }) => {
                    this.$emit('error', response);
                    throw response.data.message;
                });
            });

            return this.$refs.submitButton.submit(req).then(() => {
                if (!stopped) {
                    this.$emit('clear');
                    if (this.$refs.formFile) {
                        this.$refs.formFile.reset();
                    }
                }
            }, (err) => {
                if (err !== SubmitButtonCancelled) {
                    throw err;
                }
            });
        },
    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.form-group {
    margin-bottom: 0;
}

.disabled, :disabled {
    cursor: not-allowed !important;
}

.file-uploader-button {
    height: 100%;

    button {
        height: 100%;
    }
}
</style>

<style lang="less">
@import '~mixins.less';

.custom-file-label {
    border-left: 0;
}

#app.dark .file-uploader-form {
    .custom-file-label {
        background: @color-primary;
        color: @color-secondary-text-lighter;

        &::after {
            background: @color-primary-darker;
            color: white;
        }
    }
}
</style>
