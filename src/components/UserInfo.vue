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
                        <div v-show="submitted && validateUsername()" class="help alert-danger">
                            Please enter a valid username
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
                        <label for="password">Password:</label>
                        <input type="text" class="form-control" v-model="password">
                        <div v-show="submitted && validatePassword()" class="help alert-danger">
                            Please enter a valid password
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="password">Confirm password:</label>
                        <input type="text" class="form-control" v-model="c_password">
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
            password: '',
            edit: false,
            submitted: false,
            error: '',
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

        },
        validateUsername() {

        },
        validatePassword() {

        },
    },
};
</script>
