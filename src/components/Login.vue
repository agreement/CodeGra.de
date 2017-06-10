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

import { bPopover } from 'bootstrap-vue/lib/components';

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

            this.$http.post('/api/v1/login', { email: this.email, password: this.password }).then((data) => {
                if (data.body.success) {
                    // eslint-disable-next-line
                    console.log('Log in successful');
                    this.user.loggedIn = true;
                    this.user.email = this.email;

                    this.user.id = data.body.id;
                    this.user.name = data.body.name;

                    // Clear password for security
                    this.password = '';

                    // Redirect to homepage
                    this.$router.replace('/');
                    return;
                }

                // eslint-disable-next-line
                console.log('Unsucessful login:', data.body);
            }).catch((error) => {
                // eslint-disable-next-line
                console.log('There was an error while logging in:', error);
            });
        },
        clearErrors() {
            this.emailError = '';
            this.passwordError = '';
        },
    },
    store: {
        user: 'user',
    },
    components: {
        bPopover,
    },
};
</script>
