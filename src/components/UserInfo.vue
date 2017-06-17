<template>
    <div id="userinfo">
        <div class="row justify-content-md-center">
            <div class="col col-lg-9">
                <div v-if="edit == false">
                    <div class="alert alert-success" v-show="succes">
                        Your userdata has been updated.
                    </div>
                    Username: {{ username }} <br>
                    Email: {{ email }} <br>
                    <b-button type="edit" variant="primary" v-on:click="edit = true">Edit</b-button>
                </div>

                <div v-else v-on:keyup.enter="submit()">
                    <div class="form-group">
                        <b-input-group left="Username">
                            <b-form-input  type="text" v-model="username"></b-form-input>
                        </b-input-group>
                        <div v-show="submitted && invalid_username_error.length !== 0" class="help alert-danger">
                            {{ invalid_username_error }}
                        </div>
                    </div>

                    <div class="form-group">
                        <b-input-group left="Email">
                            <b-form-input  type="text" v-model="email"></b-form-input>
                        </b-input-group>
                        <div v-show="submitted && !validator.validate(email)" class="help alert-danger">
                            Please enter a valid email
                        </div>
                    </div>

                    <div class="form-group">
                        <b-input-group left="Old Password">
                            <b-form-input  v-if="!o_pw_visible" type="password" v-model="oldPassword"></b-form-input>
                            <b-form-input  v-if="o_pw_visible" type="textt" v-model="oldPassword"></b-form-input>
                            <b-input-group-button slot="right">
                                <b-button @click="o_pw_visible = !o_pw_visible" >
                                    <icon v-if="!o_pw_visible" name="eye" aria-hidden="true"></icon>
                                    <icon v-if="o_pw_visible" name="eye-slash" aria-hidden="true"></icon>
                                </b-button>
                            </b-input-group-button>
                        </b-input-group>
                        <div v-show="submitted && invalid_credentials" class="help alert-danger">
                            Wrong password
                        </div>
                    </div>

                    <div class="form-group">
                        <b-input-group left="New Password">
                            <b-form-input  v-if="!n_pw_visible" type="password" v-model="newPassword"></b-form-input>
                            <b-form-input  v-if="n_pw_visible" type="textt" v-model="newPassword"></b-form-input>
                            <b-input-group-button slot="right">
                                <b-button @click="n_pw_visible = !n_pw_visible" >
                                    <icon v-if="!n_pw_visible" name="eye" aria-hidden="true"></icon>
                                    <icon v-if="n_pw_visible" name="eye-slash" aria-hidden="true"></icon>
                                </b-button>
                            </b-input-group-button>
                        </b-input-group>
                        <div v-show="submitted && invalid_password_error.length !== 0" class="help alert-danger">
                            {{ invalid_password_error }}
                        </div>
                    </div>
                    <div class="form-group">
                        <b-input-group left="Confirm Password">
                            <b-form-input  v-if="!c_pw_visible" type="password" v-model="confirmPassword"></b-form-input>
                            <b-form-input  v-if="c_pw_visible" type="textt" v-model="confirmPassword"></b-form-input>
                            <b-input-group-button slot="right">
                                <b-button @click="c_pw_visible = !c_pw_visible" >
                                    <icon v-if="!c_pw_visible" name="eye" aria-hidden="true"></icon>
                                    <icon v-if="c_pw_visible" name="eye-slash" aria-hidden="true"></icon>
                                </b-button>
                            </b-input-group-button>
                        </b-input-group>
                        <div v-show="submitted && (newPassword != confirmPassword)" class="help alert-danger">
                            New password is not equal to the confirmation password
                        </div>
                    </div>

                    <div class="btn-group btn-group-justified">
                        <div class="btn-group">
                            <button type="cancel" class="btn btn-primary" @click="edit = false; resetParams()">Cancel</button>
                        </div>
                        <div class="btn-group">
                            <button type="submit" class="btn btn-primary" @click="submit()">Submit</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';

const validator = require('email-validator');

export default {
    name: 'userinfo',
    data() {
        return {
            username: '',
            email: '',
            oldPassword: '',
            newPassword: '',
            confirmPassword: '',
            edit: false,
            submitted: false,
            succes: false,
            o_pw_visible: false,
            n_pw_visible: false,
            c_pw_visible: false,
            invalid_password_error: '',
            invalid_username_error: '',
            invalid_credentials: false,
            validator,
        };
    },
    components: {
        Icon,
    },
    mounted() {
        this.$http.get('/api/v1/login').then((data) => {
            this.username = data.data.name;
            this.email = data.data.email;
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
            this.succes = false;
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

            this.$http.put('/api/v1/update_user',
                {
                    username: this.username,
                    email: this.email,
                    o_password: this.oldPassword,
                    n_password: this.newPassword,
                },
            ).then(() => {
                this.edit = false;
                this.succes = true;
            }).catch((reason) => {
                if (reason.response.data.code === 5) {
                    this.invalid_password_error = reason.response.data.rest.password;
                    this.invalid_username_error = reason.response.data.rest.username;
                } else if (reason.response.data.code === 11) {
                    this.invalid_credentials = true;
                }
            });
        },
    },
};
</script>
