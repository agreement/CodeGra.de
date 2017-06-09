<template>
    <div class="row">
        <div class="col-md-6 col-md-offset-3">
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
                    <input type="submit" class="form-control" value="Submit" @click="login()">
                </div>
            </form>
        </div>
    </div>
</template>

<script>

import { bPopover, bBtn } from 'bootstrap-vue/lib/components';

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

            this.$http.post('/api/login', { email: this.email, password: this.password }).then((data) => {
                // eslint-disable-next-line
                console.log('Login response:', data);
            });
        },
        clearErrors() {
            this.emailError = '';
            this.passwordError = '';
        },
    },
    components: {
        bPopover,
        bBtn,
    },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
