<template>
    <div id="userinfo">
        <div class="row justify-content-md-center">
            <div class="col col-lg-9">
                <div v-if="edit == false">
                    Username: {{ username }} <br>
                    Email: {{ email }}
                    <button type="edit" class="btn btn-primary" v-on:click="edit = true">Edit</button>
                </div>

                <div v-else>
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" class="form-control" v-model="username">
                        <div v-show="submitted && invalid_input['username'] != ''" class="help alert-danger">
                            {{ invalid_input['username'] }}
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
                        <input type="text" class="form-control" v-model="oldPassword">
                        <div v-show="submitted" class="help alert-danger">
                            pw_err
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="password">New password:</label>
                        <input type="text" class="form-control" v-model="newPassword">
                        <div v-show="submitted && invalid_input['password'] != ''" class="help alert-danger">
                            {{ invalid_input['password'] }}
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="password">Confirm password:</label>
                        <input type="text" class="form-control" v-model="confirmPassword">
                        <div v-show="submitted && newPassword != confirmPassword" class="help alert-danger">
                            New password is not equal to the confirmation password
                        </div>
                    </div>

                    <div class="btn-group btn-group-justified">
                        <div class="btn-group">
                            <button type="cancel" class="btn btn-primary" @click="edit = false">Cancel</button>
                        </div>
                        <div class="btn-group">
                            <button type="submit" class="btn btn-primary" @click="saveChanges()">Submit</button>
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
    name: 'hello',
    data() {
        return {
            username: '',
            email: '',
            oldPassword: '',
            newPassword: '',
            confirmPassword: '',
            edit: false,
            submitted: false,
            error: '',
            invalid_input = {},
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
        saveChanges() {
            this.error = '';
            this.submitted = true;

            if (this.newPassword !== this.confirmPassword) {
                return;
            }
            if (!validator.validate(this.email)) {
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
                console.log('Stuff send');
            }).catch((reason) => {
                this.error = reason.error;
                this.invalid_input = reason.rest;
            });
        },
    },
};
</script>
