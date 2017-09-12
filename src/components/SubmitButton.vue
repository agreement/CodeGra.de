<template>
    <b-popover class="submission-popover"
               :show="showError && state == 'failure' && (Boolean(err) || showEmpty)"
               :placement="popoverPlacement"
               :content="showError ? err : ''">
        <b-button :disabled="pending || disabled"
                  :variant="variants[state]"
                  :size="size"
                  @click="$emit('click', $event)">
            <loader :scale="1" v-if="pending"/>
            <span v-else-if="label">{{ label }}</span>
            <slot v-else/>
        </b-button>
    </b-popover>
</template>

<script>
import Loader from './Loader';

export default {
    name: 'submit-button',

    data() {
        return {
            err: '',
            pending: false,
            state: 'default',
            variants: {
                default: this.default,
                success: this.success,
                failure: this.failure,
            },
            timeout: null,
        };
    },

    props: {
        popoverPlacement: {
            type: String,
            default: 'top',
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        label: {
            type: String,
            default: 'Submit',
        },
        size: {
            type: String,
            default: 'md',
        },
        delay: {
            type: Number,
            default: 1000,
        },
        default: {
            type: String,
            default: 'primary',
        },
        success: {
            type: String,
            default: 'success',
        },
        failure: {
            type: String,
            default: 'danger',
        },
        showEmpty: {
            type: Boolean,
            default: true,
        },
        showError: {
            type: Boolean,
            default: true,
        },
    },

    methods: {
        submit(promise) {
            this.pending = true;
            return Promise.resolve(promise).then((res) => {
                this.pending = false;
                return this.succeed(res);
            }, (err) => {
                this.pending = false;
                return this.fail(err);
            });
        },

        cancelFail(resolve = null) {
            this.timeout = null;
            this.state = 'default';
            this.$nextTick(() => {
                this.err = '';
            });

            if (resolve) resolve();
        },

        succeed(res) {
            return this.update('success')
                .then(() => res);
        },

        fail(err) {
            this.err = err;
            return this.update('failure', 3)
                .then(() => { throw err; });
        },

        update(state, mult = 1) {
            this.state = state;
            return new Promise((resolve) => {
                if (this.timeout != null) {
                    clearTimeout(this.timeout);
                }
                this.timeout = setTimeout(() => {
                    this.cancelFail(resolve);
                }, this.delay * mult);
            });
        },
    },

    components: {
        Loader,
    },
};
</script>

<style lang="less">
.input-group-btn > .submission-popover {
    height: 100%;

    > span > button {
        height: 100%;
    }
}
</style>

<docs>
Submit button component to be used when
an action involves submitting
data to the server.

Props:

label
    Text in the button. The label must explicitly be set to an empty
    string in order to use the button's inner html. Default: 'Submit'.
size
    Bootstrap size such as 'sm' or 'md'. Default: bootstrap-vue default.
delay
    Number of milliseconds the button will stay in its success/failure
    state before going back to the default state. Default: 1000.
default
    Default bootstrap button variant for the button. Default: 'primary'.
success
    Bootstrap button variant to be used when the promise resolved.
    Default: 'success'.
failure
    Bootstrap button variant to be used when the promise rejected.
    Default: 'danger'.

Methods:

submit(promise)
    Disable the button and show a spinning loader icon until `promise`
    resolves. Then put the button in the success state if the promise
    resolved or the failure state if the promise rejected, for `delay`
    milliseconds.
    Returns a promise that resolves (rejects) when the button goes
    from its success/failure state back to the default state and that
    has the same resolution as the promise passed in.

succeed()
    Put the button in the success state for `delay` milliseconds.
    Returns a promise that resolves when the button goes from the
    success/failure state back to the default state.

fail()
    Put the button in the failure state for `delay` milliseconds.
    Returns a promise that rejects when the button goes from the
    success/failure state back to the default state.

Example:

    <template>
        <submit-button
            ref="submitButton"
            @click="doSubmit"
        />
    </template>

    <script>
    /* eslint-disable */
    export const MyComp = {
        methods: {
            doSubmit() {
                this.$refs.submitButton.submit(
                    this.$http.post(route, data),
                ).then((res) => {
                    // handle response
                }, (err) => {
                    // handle error
                });
            },
        },
    };
    </script>
</docs>
