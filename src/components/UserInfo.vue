<template>
    <div class="userinfo">
        <loader class="col-md-10 text-center" v-if="loading"></loader>

        <div v-else @keyup.enter="submit()">
            <b-alert variant="success" :show="success">
                Your userdata has been updated.
            </b-alert>

            <b-form-fieldset>
                <b-input-group left="Username">
                    <b-form-input type="text" v-model="username" v-if="edit"></b-form-input>
                    <p class="form-control" v-else>{{ username }}</p>
                </b-input-group>
                <b-alert variant="danger" :show="submitted && invalid_username_error.length">
                    {{ invalid_username_error }}
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Email">
                    <b-form-input type="text" v-model="email" v-if="edit"></b-form-input>
                    <p class="form-control" v-else>{{ email }}</p>
                </b-input-group>
                <b-alert variant="danger" :show="submitted && !validator.validate(email)">
                    Please enter a valid email
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset v-if="edit">
                <b-input-group left="Old Password">
                    <b-form-input  :type="o_pw_visible ? 'text' : 'password'" v-model="oldPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="o_pw_visible = !o_pw_visible" >
                            <icon v-if="!o_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="submitted && invalid_credentials">
                    Wrong password
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset v-if="edit">
                <b-input-group left="New Password">
                    <b-form-input :type="n_pw_visible ? 'text' : 'password'" v-model="newPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="n_pw_visible = !n_pw_visible" >
                            <icon v-if="!n_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="submitted && invalid_password_error.length">
                    {{ invalid_password_error }}
                </b-alert>
            </b-form-fieldset>

            <b-form-fieldset v-if="edit">
                <b-input-group left="Confirm Password">
                    <b-form-input :type="c_pw_visible ? 'text' : 'password'" v-model="confirmPassword"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="c_pw_visible = !c_pw_visible" >
                            <icon v-if="!c_pw_visible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
                <b-alert variant="danger" :show="newPassword != confirmPassword">
                    New password is not equal to the confirmation password
                </b-alert>
            </b-form-fieldset>

            <b-button-group justify>
                <b-button variant="primary" @click="edit = true" v-if="!edit">Edit</b-button>
                <b-button variant="primary" @click="submit()" v-if="edit">Submit</b-button>
                <b-button variant="danger" @click="edit = false; resetParams()" v-if="edit">Cancel</b-button>
            </b-button-group>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';

import { bAlert, bButtonGroup, bButton, bFormFieldset, bFormInput, bInputGroup }
    from 'bootstrap-vue/lib/components';

import Loader from './Loader';

const validator = require('email-validator');

export default {
    name: 'userinfo',

    props: {
        edit: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            username: '',
            email: '',
            oldPassword: '',
            newPassword: '',
            confirmPassword: '',
            submitted: false,
            success: false,
            o_pw_visible: false,
            n_pw_visible: false,
            c_pw_visible: false,
            invalid_password_error: '',
            invalid_username_error: '',
            invalid_credentials: false,
            validator,
            loading: true,
        };
    },

    components: {
        Icon,
        Loader,
        bAlert,
        bButtonGroup,
        bButton,
        bFormFieldset,
        bFormInput,
        bInputGroup,
    },

    mounted() {
        this.$http.get('/api/v1/login').then((data) => {
            this.username = data.data.name;
            this.email = data.data.email;
            this.loading = false;
        });
    },

    methods: {
        resetErrors() {
            this.invalid_password_error = '';
            this.invalid_username_error = '';
            this.invalid_credentials = false;
        },

        resetParams() {
            this.oldPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
            this.submitted = false;
            this.o_pw_visible = false;
            this.n_pw_visible = false;
            this.c_pw_visible = false;
            this.resetErrors();
        },

        submit() {
            this.submitted = true;
            this.resetErrors();

            if (this.newPassword !== this.confirmPassword || !validator.validate(this.email)) {
                return;
            }

            this.loading = true;
            this.$http.patch('/api/v1/login',
                {
                    username: this.username,
                    email: this.email,
                    o_password: this.oldPassword,
                    n_password: this.newPassword,
                },
            ).then(() => {
                this.edit = false;
                this.succes = true;
                this.resetParams();
            }).catch(({ response }) => {
                if (response.data.code === 5) {
                    this.invalid_password_error = response.data.rest.password;
                    this.invalid_username_error = response.data.rest.username;
                } else if (response.data.code === 12) {
                    this.invalid_credentials = true;
                }
            }).then(() => {
                this.loading = false;
            });
        },
    },
};
</script>

<style lang="less" scoped>
.form-group .alert {
    margin-bottom: 0;
}
</style>
