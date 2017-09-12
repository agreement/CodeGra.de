<template>
    <div>
        <div class="forgot" v-if="showForgot" @keyup.enter="submitReset">
            <h4 class="text-center">Reset password</h4>
            <small>
                We will send you a link to reset your password to your email. You
                can use this link for a limited period of time. Please check you spam
                folder if you not receive the email shortly after requesting it.
            </small>
            <b-form-fieldset @click="submitReset">
                <input type="text"
                       class="form-control"
                       ref="username"
                       placeholder="username"
                       v-model="resetUsername"/>
                <b-alert variant="danger" :show="resetSubmitted && !resetUsername">
                    Please enter a non empty username
                </b-alert>
            </b-form-fieldset>
        </div>

        <div class="login" @keyup.enter="login" v-else>
            <h4 class="text-center">Login</h4>
            <b-form-fieldset>
                <input type="text"
                       class="form-control"
                       placeholder="username"
                       v-model="username"
                       ref="username"/>
                <b-alert variant="danger" :show="submitted && !username">
                    Please enter a non empty username
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <input type="password"
                       class="form-control"
                       placeholder="Password"
                       v-model="password"/>
                <b-alert variant="danger" :show="submitted && password && password.length === 0">
                    Please enter a non empty password
                </b-alert>
            </b-form-fieldset>

            <b-alert :show="error.length" variant="danger">
                {{ error }}
            </b-alert>
        </div>

        <b-form-fieldset class="text-center">
            <submit-button ref="submit"
                           @click="showForgot ? login($event) : submitReset($event)"
                           :label="showForgot ? 'Request email' : 'Login'"
                           :show-empty="false"
                           :show-error="showForgot"/>
            <a class="login" @click="toggleForgot(!showForgot)">
                {{ showForgot ? 'Login' : 'Forgot password' }}
            </a>
        </b-form-fieldset>
    </div>
</template>

<script>
import { mapActions } from 'vuex';

import SubmitButton from './SubmitButton';

export default {
    name: 'login',
    data() {
        return {
            username: '',
            resetUsername: '',
            password: '',
            error: '',
            submitted: false,
            resetSubmitted: false,
        };
    },

    components: {
        SubmitButton,
    },

    computed: {
        showForgot() {
            return this.$route.hash === '#forgot';
        },
    },

    mounted() {
        if (this.$refs.username) this.$refs.username.focus();
    },

    methods: {
        toggleForgot(on) {
            this.username = '';
            this.resetUsername = '';
            this.password = '';
            this.error = '';
            this.submitted = false;
            this.resetSubmitted = false;
            this.$router.push({ hash: on ? 'forgot' : '' });
            this.$nextTick(() => this.$refs.username.focus());
            this.$refs.submit.cancelFail();
        },

        submitReset(event) {
            event.preventDefault();
            this.resetSubmitted = true;
            if (this.resetUsername === '') {
                this.$refs.resetSubmit.submit(Promise.reject(null));
                return;
            }
            const req = this.$http.patch('/api/v1/login?type=reset_email', {
                username: this.resetUsername,
            }).then(() => {
            });
            this.$refs.submit.submit(req.catch((err) => { throw err.response.data.message; }));
        },

        login(event) {
            event.preventDefault();
            this.error = '';
            this.submitted = true;
            if (this.password.length === 0 || this.username.length === 0) {
                this.$refs.submit.submit(Promise.reject(null));
                return;
            }

            this.$refs.submit.submit(
                this.tryLogin({ username: this.username, password: this.password }).then(() => {
                    this.$nextTick(() => {
                        this.$router.replace({ name: 'assignments' });
                    });
                }).catch((reason) => {
                    if (reason) {
                        this.error = reason.message;
                    }
                    // eslint-disable-next-line
                    throw '';
                }),
            );
        },
        ...mapActions({
            tryLogin: 'user/login',
        }),
    },
};
</script>

<style scoped>
h4 {
    margin-bottom: 15px;
}

small {
    margin-top: -10px;
    margin-bottom: 15px;
    text-align: center;
    display: block;
    color: #868686;
}

a.forgot, a.login {
    text-decoration: underline !important;
    margin-top: 15px;
    cursor: pointer;
    display: block;
}
</style>
