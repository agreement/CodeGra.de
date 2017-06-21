<template>
    <div id="newCourse">
        <div class="justify-content-md-center">
            <loader class="text-center" v-if="loading"></loader>
            <div v-if="done">
                <b-alert variant="success" show>
                    <center><span>Succesfully created course!</span></center>
                </b-alert>
            </div>

            <div v-else v-on:keyup.enter="submit()">
                <div class="form-group">
                    <b-input-group left="Course Name">
                        <b-form-input  type="text" v-model="name"></b-form-input>
                    </b-input-group>
                    <div v-show="submitted && invalid_username_error.length !== 0" class="help alert-danger">
                        {{ invalid_username_error }}
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
</template>

<script>
import Loader from './Loader';

export default {
    name: 'userinfo',
    data() {
        return {
            name: '',
            done: false,
            loading: true,
        };
    },
    components: {
        Icon,
        Loader,
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
            }).catch((reason) => {
                if (reason.response.data.code === 5) {
                    this.invalid_password_error = reason.response.data.rest.password;
                    this.invalid_username_error = reason.response.data.rest.username;
                } else if (reason.response.data.code === 11) {
                    this.invalid_credentials = true;
                }
            });
            this.loading = false;
        },
    },
};
</script>
