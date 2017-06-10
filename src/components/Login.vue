<template>
    <div class="row justify-content-center">
        <div class="col-6">
            <form>
                <div class="form-group">
                    <b-popover placement="right" :content="emailError" :show="emailError.length > 0">
                        <input type="text" class="form-control" placeholder="Email" v-model="email" @keydown="clearErrors()">
                    </b-popover>
                </div>
                <div class="form-group">
                    <b-popover placement="right" :content="passwordError" :show="passwordError.length > 0">
                        <input type="password" class="form-control" placeholder="Password" v-model="password" @keydown="clearErrors()">
                    </b-popover>
                </div>
                <div class="form-group">
                    <input type="submit" value="Submit" @click="login()">
                </div>
            </form>
        </div>
    </div>
</template>

<script>

import { mapActions } from 'vuex';
import { bPopover } from 'bootstrap-vue/lib/components';

import * as error from '@/errors';

export default {
    name: 'login',
    data() {
        return {
            email: '',
            emailError: '',
            password: '',
            passwordError: '',
        };
    },
    methods: {
        login() {
            if (this.email.length === 0) {
                this.emailError = 'Don\'t forget to enter your email';
                return;
            }
            if (this.password.length === 0) {
                this.passwordError = 'You forgot your password';
                return;
            }

            this.tryLogin({ email: this.email, password: this.password }).then(() => {
                this.$router.replace('/');
            }).catch((reason) => {
                if (reason === error.emailDoesNotExist) {
                    this.emailError = 'Email does not exist';
                    return;
                }

                if (reason === error.passwordIsInvalid) {
                    this.passwordError = 'Password is invalid';
                    return;
                }

                // TODO: toast the error
                // eslint-disable-next-line
                console.log(reason);
            });
        },
        clearErrors() {
            this.emailError = '';
            this.passwordError = '';
        },
        ...mapActions({
            tryLogin: 'login',
        }),
    },
    components: {
        bPopover,
    },
};
</script>
