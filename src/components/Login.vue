<template>
    <div class="login" @keyup.enter="login">
        <b-form-fieldset>
            <b-form-input type="text" placeholder="Email" v-model="email"></b-form-input>
            <b-alert variant="danger" :show="submitted && !validator.validate(email)">
                Please enter a valid email
            </b-alert>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-form-input type="password" placeholder="Password" v-model="password"></b-form-input>
            <b-alert variant="danger" :show="submitted && password && password.length === 0">
                Please enter a non empty password
            </b-alert>
        </b-form-fieldset>

        <b-alert :show="error.length" variant="danger">
            {{ error }}
        </b-alert>

        <b-form-fieldset>
            <b-form-input type="submit" @click.native="login"></b-form-input>
        </b-form-fieldset>
    </div>
</template>

<script>
import { mapActions } from 'vuex';

const validator = require('email-validator');

export default {
    name: 'login',
    data() {
        return {
            email: '',
            password: '',
            error: '',
            validator,
            submitted: false,
        };
    },

    methods: {
        login(event) {
            event.preventDefault();
            this.error = '';
            this.submitted = true;
            if (!validator.validate(this.email)) {
                return;
            }
            if (this.password.length === 0) {
                return;
            }

            this.tryLogin({ email: this.email, password: this.password }).then(() => {
                this.$router.replace({ name: 'home' });
            }).catch((reason) => {
                if (reason) {
                    this.error = reason.message;
                }
            });
        },
        ...mapActions({
            tryLogin: 'user/login',
        }),
    },
};
</script>
