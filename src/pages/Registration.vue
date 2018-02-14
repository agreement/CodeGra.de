<template>
<div class="row justify-content-center">
    <div class="register-page col-sm-6"
         @keyup.ctrl.enter="submit">
        <h4 class="text-center">Register</h4>
        <b-form-fieldset>
            <b-input-group prepend="Your username">
                <input type="text"
                       class="form-control"
                       v-model="username"
                       tabindex="1"
                       ref="username"/>
                <b-input-group-append is-text>
                    <description-popover
                        description="You cannot change this after registration!"
                        :show="showHelp"/>
                </b-input-group-append>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group prepend="Your full name">
            <input type="text"
                   class="form-control"
                   v-model="name"
                   tabindex="2"
                   ref="name"/>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group prepend="Your email">
            <input type="email"
                   class="form-control"
                   v-model="firstEmail"
                   tabindex="2"
                   ref="email"/>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group prepend="Repeat email">
                <input type="email"
                    class="form-control"
                    v-model="secondEmail"
                    tabindex="3"
                    ref="email"/>
            </b-input-group>
        </b-form-fieldset>

        <password-input v-model="firstPw"
                        label="Password"
                        tabindex="4"/>
        <password-input v-model="secondPw"
                        label="Repeat password"
                        tabindex="5"/>

        <div class="text-center">
            <submit-button label="Register"
                           @click="submit"
                           :delay="1500"
                           tabindex="6"
                           ref="submit"/>
        </div>
    </div>
</div>
</template>

<script>
import { SubmitButton, DescriptionPopover, PasswordInput } from '@/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';

import * as types from '../store/mutation-types';

export default {
    data() {
        return {
            username: '',
            firstEmail: '',
            secondEmail: '',
            name: '',
            showHelp: false,
            firstPw: '',
            secondPw: '',
        };
    },

    methods: {
        submit() {
            const button = this.$refs.submit;

            if (this.firstPw !== this.secondPw) {
                button.fail('The two passwords do not match!');
                return;
            } else if (this.firstEmail !== this.secondEmail) {
                button.fail('The two emails do not match!');
                return;
            }

            const req = this.$http.post('/api/v1/user', {
                username: this.username,
                password: this.firstPw,
                email: this.firstEmail,
                name: this.name,
            }).then(({ data }) => {
                if (data.access_token) {
                    this.$store.commit(`user/${types.UPDATE_ACCESS_TOKEN}`, data);
                    this.$router.push({
                        name: 'assignments',
                    });
                }
            }, ({ response }) => {
                throw response.data.message;
            });
            button.submit(req);
        },
    },

    components: {
        Icon,
        SubmitButton,
        DescriptionPopover,
        PasswordInput,
    },
};
</script>

<style lang="less" scoped>
h4 {
    margin-bottom: 15px;
}
</style>
