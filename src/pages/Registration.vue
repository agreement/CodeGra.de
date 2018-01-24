<template>
<div class="row justify-content-center">
    <div class="register-page col-sm-6"
         @keyup.ctrl.enter="submit">
        <h4 class="text-center">Register</h4>
        <b-form-fieldset>
            <b-input-group>
                <input type="text"
                       class="form-control"
                       placeholder="Your username"
                       v-model="username"
                       tabindex="1"
                       ref="username"/>
                <b-input-group-button slot="right">
                    <b-button tabindex="-1"
                              @mouseenter.native="showHelp = true"
                              @mouseleave.native="showHelp = false">
                        <description-popover
                            description="You cannot change this after registration!"
                            :show="showHelp"/>
                    </b-button>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <input type="text"
                   class="form-control"
                   placeholder="Your full name"
                   v-model="name"
                   tabindex="2"
                   ref="name"/>
        </b-form-fieldset>

        <b-form-fieldset>
            <input type="email"
                   class="form-control"
                   placeholder="Your email"
                   v-model="firstEmail"
                   tabindex="2"
                   ref="email"/>
        </b-form-fieldset>

        <b-form-fieldset>
            <input type="email"
                   class="form-control"
                   placeholder="Repeat email"
                   v-model="secondEmail"
                   tabindex="3"
                   ref="email"/>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group>
                <input type="text"
                       v-if="firstPwVisible"
                       class="form-control"
                       placeholder="Password"
                       v-model="firstPw"
                       tabindex="4"
                       ref="firstPw"/>
                <input type="password"
                       v-else
                       class="form-control"
                       placeholder="Password"
                       v-model="firstPw"
                       tabindex="4"
                       ref="firstPw"/>
                <b-input-group-button slot="right">
                    <b-button @click="firstPwVisible = !firstPwVisible" >
                        <icon v-if="!firstPwVisible" name="eye"/>
                        <icon v-else name="eye-slash"/>
                    </b-button>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group>
                <input type="text"
                       v-if="secondPwVisible"
                       class="form-control"
                       placeholder="Repeat password"
                       v-model="secondPw"
                       tabindex="5"
                       ref="secondPw"/>
                <input type="password"
                       v-else
                       class="form-control"
                       placeholder="Repeat password"
                       v-model="secondPw"
                       tabindex="5"
                       ref="secondPw"/>
                <b-input-group-button slot="right">
                    <b-button @click="secondPwVisible = !secondPwVisible" >
                        <icon v-if="!secondPwVisible" name="eye"/>
                        <icon v-else name="eye-slash"/>
                    </b-button>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>

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
import { SubmitButton, DescriptionPopover } from '@/components';

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
            firstPwVisible: false,
            secondPwVisible: false,
            showHelp: false,
            firstPw: '',
            secondPw: '',
        };
    },

    methods: {
        submit() {
            const button = this.$refs.submit;
            let req;

            if (this.firstPw !== this.secondPw) {
                req = Promise.reject('The two passwords do not match!');
            } else if (this.firstEmail !== this.secondEmail) {
                req = Promise.reject('The two emails do not match!');
            } else {
                req = this.$http.post('/api/v1/user', {
                    username: this.username,
                    password: this.firstPw,
                    email: this.firstEmail,
                    name: this.name,
                }).catch((err) => {
                    throw err.response.data.message;
                });
            }

            button.submit(req.then(({ data }) => {
                if (data.access_token) {
                    this.$store.commit(`user/${types.UPDATE_ACCESS_TOKEN}`, data);
                    this.$router.push({
                        name: 'assignments',
                    });
                }
            }));
        },
    },

    components: {
        Icon,
        SubmitButton,
        DescriptionPopover,
    },
};
</script>

<style lang="less" scoped>
h4 {
    margin-bottom: 15px;
}
</style>
