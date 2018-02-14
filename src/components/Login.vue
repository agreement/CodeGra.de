<template>
    <div class="login">
        <h4 class="text-center">
            {{ showForgot ? 'Reset password' : 'Login' }}
        </h4>

        <small v-if="showForgot">
            We will send you a link to reset your password to your email. You
            can use this link for a limited period of time. Please check you spam
            folder if you not receive the email shortly after requesting it.
        </small>

        <div @keyup.enter="submit">
            <b-form-fieldset>
                <input type="text"
                       class="form-control"
                       placeholder="Username"
                       v-model="username"
                       ref="username"/>
            </b-form-fieldset>

            <b-form-fieldset v-if="!showForgot">
                <input type="password"
                       class="form-control"
                       placeholder="Password"
                       v-model="password"/>
            </b-form-fieldset>
        </div>

        <b-form-fieldset class="text-center">
            <submit-button ref="submit"
                           @click.native="submit"
                           :label="showForgot ? 'Request email' : 'Login'"
                           :show-empty="false"/>
            <div class="login-links">
                <div class="left-box">
                    <router-link class="login"
                                :to="{ hash: showForgot ? 'login' : 'forgot', }"
                                @click="reset">
                        {{ showForgot ? 'Login' : 'Forgot password' }}</router-link>
                </div>
                <div class="right-box">
                    <router-link class="login" to="register">Register</router-link>
                </div>
            </div>
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
            password: '',
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

    watch: {
        showForgot() {
            this.reset();
        },
    },

    mounted() {
        if (this.$refs.username) {
            this.$refs.username.focus();
        }
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
                this.$router.replace({ name: 'assignments' });
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

h4 {
    margin-bottom: 15px;
}

.alert {
    margin-top: 2px;
}

small {
    margin: -10px 0 15px;
    display: block;
    color: #868686;
}

.login-links {
    display: flex;
    margin-top: 15px;

    .left-box, .right-box {
        width: 100%;
    }


    .left-box {
        text-align: right;
        a.login {
            margin-right: @link-margin;
        }
    }

    .right-box {
        text-align: left;
        a.login {
            margin-left: @link-margin;
        }
    }

    a.login {
        text-decoration: underline !important;
    }
}
</style>
