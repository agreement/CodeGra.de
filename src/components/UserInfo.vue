<template>
    <div id="userinfo">
        <div class="row justify-content-md-center">
            <div class="col col-lg-9">
                <div v-if="edit == false">
                    <div class="alert alert-success" v-show="succes">
                        Your userdata has been updated.
                    </div>
                    Username: {{ username }} <br>
                    Email: {{ email }}
                    <button type="edit" class="btn btn-primary" v-on:click="edit = true">Edit</button>
                </div>

                <div v-else v-on:keyup.enter="submit()">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" class="form-control" v-model="username">
                        <div v-show="submitted && invalid_username_error.length !== 0" class="help alert-danger">
                            {{ invalid_username_error }}
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="text" class="form-control" v-model="email">
                        <div v-show="submitted && !validator.validate(email)" class="help alert-danger">
                            Please enter a valid email
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="password">Old password:</label>
                        <input type="password" class="form-control" v-model="oldPassword">
                        <div v-show="submitted && invalid_credentials" class="help alert-danger">
                            Wrong password
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="password">New password:</label>
                        <input type="password" class="form-control" v-model="newPassword">
                        <div v-show="submitted && invalid_password_error.length !== 0" class="help alert-danger">
                            {{ invalid_password_error }}
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="password">Confirm password:</label>
                        <input type="password" class="form-control" v-model="confirmPassword">
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
            invalid_password_error: '',
            invalid_username_error: '',
            invalid_credentials: false,
            validator,
        };
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
