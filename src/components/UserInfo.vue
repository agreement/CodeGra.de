<template>
    <div class="userinfo">
        <loader class="col-md-12 text-center" v-if="loading"></loader>
        <div @keyup.enter="submit" v-else>
            <b-form-fieldset>
                <b-input-group left="Username">
                    <b-form-input type="text" v-model="username"></b-form-input>
                </b-input-group>
                <b-alert variant="danger" :show="true" v-if="invalid_username_error.length">
                    {{ invalid_username_error }}
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Email">
                    <b-form-input type="text" v-model="email"></b-form-input>
                </b-input-group>
                <b-alert variant="danger" :show="!validator.validate(email)">
                    Please enter a valid email
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Old Password">
                    <b-form-input  :type="o_pw_visible ? 'text' : 'password'" v-model="oldPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="o_pw_visible = !o_pw_visible" >
                            <icon v-if="!o_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="true" v-if="invalid_credentials_error.length">
                    {{ invalid_credentials_error }}
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="New Password">
                    <b-form-input :type="n_pw_visible ? 'text' : 'password'" v-model="newPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="n_pw_visible = !n_pw_visible" >
                            <icon v-if="!n_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="true" v-if="invalid_password_error.length">
                    {{ invalid_password_error }}
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Confirm Password">
                    <b-form-input :type="c_pw_visible ? 'text' : 'password'" v-model="confirmPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="c_pw_visible = !c_pw_visible" >
                            <icon v-if="!c_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="true" v-if="newPassword != confirmPassword">
                    New password is not equal to the confirmation password
                </b-alert>
            </b-form-fieldset>

            <b-button-toolbar justify>
                <submit-button @click="submit" ref="submitButton" :showError="false"/>
                <b-button variant="danger" @click="resetAll">Reset</b-button>
            </b-button-toolbar>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import SubmitButton from './SubmitButton';

const validator = require('email-validator');

export default {
    name: 'userinfo',

    data() {
        return {
            original: {},
            username: '',
            email: '',
            oldPassword: '',
            newPassword: '',
            confirmPassword: '',
            loading: false,
            o_pw_visible: false,
            n_pw_visible: false,
            c_pw_visible: false,
            invalid_password_error: '',
            invalid_username_error: '',
            invalid_credentials_error: '',
            validator,
        };
    },

    components: {
        Icon,
        Loader,
        SubmitButton,
    },

    mounted() {
        this.loading = true;
        this.$http.get('/api/v1/login').then(({ data }) => {
            this.original = data;
            this.username = data.name;
            this.email = data.email;
            this.loading = false;
        });
    },

    methods: {
        resetErrors() {
            this.invalid_password_error = '';
            this.invalid_username_error = '';
            this.invalid_credentials_error = '';
        },

        resetParams() {
            this.username = this.original.name;
            this.email = this.original.email;
            this.oldPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
            this.o_pw_visible = false;
            this.n_pw_visible = false;
            this.c_pw_visible = false;
        },

        resetAll() {
            this.resetErrors();
            this.resetParams();
        },

        submit() {
            this.resetErrors();

            if (this.newPassword !== this.confirmPassword || !validator.validate(this.email)) {
                return;
            }

            const req = this.$http.patch('/api/v1/login', {
                username: this.username,
                email: this.email,
                o_password: this.oldPassword,
                n_password: this.newPassword,
            });
            req.then(() => {
                this.original.name = this.username;
                this.original.email = this.email;
                this.resetParams();
            }, ({ response }) => {
                if (response.data.code === 5) {
                    this.invalid_password_error = response.data.rest.password;
                    this.invalid_username_error = response.data.rest.username;
                } else if (response.data.code === 12) {
                    this.invalid_credentials_error = response.data.message;
                }
            });
            this.$refs.submitButton.submit(req);
        },
    },
};
</script>
