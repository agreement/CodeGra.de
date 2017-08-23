<template>
    <div class="userinfo">
        <loader class="col-md-12 text-center" v-if="loading"></loader>
        <div @keyup.enter="submit" @keyup.capture="error = ''" v-else>
            <b-form-fieldset>
                <b-input-group left="Username">
                    <b-form-input type="text" v-model="name"></b-form-input>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Email">
                    <b-form-input type="text" v-model="email"></b-form-input>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Old Password">
                    <b-form-input  :type="oldPwVisible ? 'text' : 'password'" v-model="oldPw"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="oldPwVisible = !oldPwVisible" >
                            <icon v-if="!oldPwVisible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="New Password">
                    <b-form-input :type="newPwVisible ? 'text' : 'password'" v-model="newPw"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="newPwVisible = !newPwVisible" >
                            <icon v-if="!newPwVisible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Confirm Password">
                    <b-form-input :type="confirmPwVisible ? 'text' : 'password'" v-model="confirmPw"></b-form-input>
                    <b-input-group-button slot="right">
                        <b-button @click="confirmPwVisible = !confirmPwVisible" >
                            <icon v-if="!confirmPwVisible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <b-alert variant="danger" :show="true" v-if="error">
                {{ error }}
            </b-alert>

            <b-button-toolbar justify>
                <submit-button @click="submit" ref="submitButton" :showError="false"/>
                <b-button variant="danger" @click="resetAll">Reset</b-button>
            </b-button-toolbar>
        </div>
    </div>
</template>

<script>
import validator from 'email-validator';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import SubmitButton from './SubmitButton';

export default {
    name: 'userinfo',

    data() {
        return {
            name: '',
            email: '',
            oldPw: '',
            newPw: '',
            confirmPw: '',
            loading: false,
            oldPwVisible: false,
            newPwVisible: false,
            confirmPwVisible: false,
            error: '',
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
            this.name = data.name;
            this.email = data.email;
            this.loading = false;
        });
    },

    methods: {
        resetParams() {
            this.name = this.$store.state.user.name;
            this.email = this.$store.state.user.email;
            this.oldPw = '';
            this.newPw = '';
            this.confirmPw = '';
        },

        resetAll() {
            this.resetErrors();
            this.resetParams();
        },

        submit() {
            this.error = '';

            if (!this.oldPw) {
                this.error = 'Please fill in your password.';
                return;
            }
            if (this.newPw !== this.confirmPw) {
                this.error = 'New password doesn\'t match confirm password.';
                return;
            }
            if (!validator.validate(this.email)) {
                this.error = 'Invalid email address.';
                return;
            }

            const req = this.$store.dispatch('user/updateUserInfo', {
                name: this.name,
                email: this.email,
                oldPw: this.oldPw,
                newPw: this.newPw,
            });
            req.then(() => {
                this.resetParams();
            }, (err) => {
                switch (err.response.data.code) {
                case 5:
                    this.error = err.response.data.rest.name || err.response.data.rest.password;
                    break;
                case 12:
                    this.error = err.response.data.message;
                    break;
                default:
                    this.error = 'Unknown error';
                    break;
                }
            });
            this.$refs.submitButton.submit(req);
        },
    },
};
</script>
