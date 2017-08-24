<template>
    <div class="login" @keyup.enter="login">
        <b-form-fieldset>
            <b-form-input type="text" placeholder="username" v-model="username"></b-form-input>
            <b-alert variant="danger" :show="submitted && !username">
                Please enter a non empty username
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

export default {
    name: 'login',
    data() {
        return {
            username: '',
            password: '',
            error: '',
            submitted: false,
        };
    },

    methods: {
        login(event) {
            event.preventDefault();
            this.error = '';
            this.submitted = true;
            if (this.password.length === 0 || this.username.length === 0) {
                return;
            }

            this.tryLogin({ username: this.username, password: this.password }).then(() => {
                this.$router.replace({ name: 'assignments' });
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
