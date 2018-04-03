<template>
<div class="login">
    <div @keyup.enter="submit">
        <b-form-fieldset>
            <input type="text"
                   class="form-control"
                   placeholder="Username"
                   v-model="username"
                   ref="username"/>
        </b-form-fieldset>

        <b-form-fieldset v-if="!showForgot">
            <password-input v-model="password"
                            placeholder="Password"/>
        </b-form-fieldset>
    </div>

    <p v-if="showForgot">
        We will send you a link to reset your password to your email. You
        can use this link for a limited period of time. Please check you spam
        folder if you not receive the email shortly after requesting it.
    </p>

    <b-form-fieldset class="text-center">
        <submit-button ref="submit"
                       @click.native="submit"
                       :label="showForgot ? 'Request email' : 'Login'"
                       :show-empty="false"/>
        <div class="login-links">
            <a class="login"
               :href="showForgot ? '#login' : '#forgot'"
               @click="reset">
                {{ showForgot ? 'Login' : 'Forgot password' }}
            </a>
        </div>
    </b-form-fieldset>
</div>
</template>

<script>
import { mapActions } from 'vuex';

import PasswordInput from './PasswordInput';
import SubmitButton from './SubmitButton';

export default {
    name: 'login',
    data() {
        return {
            username: '',
            password: '',
        };
    },

    components: {
        PasswordInput,
        SubmitButton,
    },

    computed: {
        showForgot() {
            return this.$route.hash === '#forgot';
        },
    },

    watch: {
        showForgot() {
            this.reset();
        },
    },

    mounted() {
        this.$nextTick(() => {
            if (this.$refs.username) {
                this.$refs.username.focus();
            }
        });
    },

    methods: {
        reset() {
            this.username = '';
            this.password = '';
            this.$nextTick(() => this.$refs.username.focus());

            if (this.$refs.submit) {
                this.$refs.submit.reset();
            }
        },

        submit(event) {
            if (this.showForgot) {
                this.submitReset(event);
            } else {
                this.login(event);
            }
        },

        submitReset(event) {
            event.preventDefault();
            if (!this.username) {
                this.$refs.submit.fail('Please enter a username.');
                return;
            }

            this.$refs.submit.submit(this.$http.patch('/api/v1/login?type=reset_email', {
                username: this.username,
            }).catch((err) => {
                throw err.response.data.message;
            }));
        },

        login(event) {
            event.preventDefault();
            if (!this.password || !this.username) {
                this.$refs.submit.fail('Please enter a username and password.');
                return;
            }

            this.$refs.submit.submit(this.tryLogin({
                username: this.username,
                password: this.password,
            }).then(() => {
                this.$router.replace({ name: 'home' });
                this.$emit('login');
            }, (reason) => {
                throw reason ? reason.message : '';
            }));
        },
        ...mapActions({
            tryLogin: 'user/login',
        }),
    },
};
</script>

<style lang="less" scoped>
@link-margin: 2em;
.login-links {
    margin-top: 15px;
    text-align: center;

    a.login {
        text-decoration: underline !important;
    }
}
</style>
