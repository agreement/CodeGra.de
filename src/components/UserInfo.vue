<template>
<div class="userinfo">
    <loader class="col-md-12 text-center" v-if="loading"></loader>
    <div @keyup.enter="submit" @keydown.capture="error = ''" v-else>
        <b-form-fieldset>
            <b-input-group prepend="Username">
                <div v-b-popover.top.hover="'You cannot change your username'"
                     style="flex: 1;">
                    <input type="text"
                           v-model="username"
                           disabled
                           style="border-top-left-radius: 0; border-bottom-left-radius: 0; width: 100%"
                           class="form-control"/>
                </div>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group prepend="Full name">
                <input :disabled="!canEditInfo"
                       class="form-control"
                       type="text"
                       v-model="name"/>
            </b-input-group>
        </b-form-fieldset>

        <b-form-fieldset>
            <b-input-group prepend="Email">
                <input :disabled="!canEditInfo"
                       type="text"
                       class="form-control"
                       v-model="email"/>
            </b-input-group>
        </b-form-fieldset>

        <password-input v-model="oldPw"
                        v-if="canEditPw || canEditInfo">
            <b-input-group-prepend is-text slot="prepend">
                Old Password
                <description-popover hug-text
                                     placement="right"
                                     triggers="click"
                                     title="What is my current password?">
                    <p slot="description"
                       style="text-align: left; margin-bottom: 0;">
                        If your account was created by using your LMS
                        (Canvas, blackboard or another) it can happen
                        that you don't know this password. In this case
                        you should use the
                        <router-link :to="{
                                          name: 'login',
                                          hash: '#forgot'
                                          }">
                            reset password</router-link> page.<br><br>

                        However this does require
                        that your email is correct. If this is not the
                        case you can force CodeGra.de to copy the email
                        that your LMS gives us the next time you use
                        CodeGra.de within your LMS. To do this please
                        press <submit-button
                                  label="here"
                                  id="resetOnLtiButton-fixPopover"
                                  size="sm"
                                  ref="resetOnLtiButton"
                                  @click="resetEmailOnLti"
                                  style="display: inline;"/>
                        <!-- The id for the submit button is needed as vue
                             reuses elements and if that is done here the
                             popover will not show correctly. -->
                    </p>
                </description-popover>
            </b-input-group-prepend>
        </password-input>

        <password-input v-model="newPw" label="New password" v-if="canEditPw"/>
        <password-input v-model="confirmPw" label="Confirm password" v-if="canEditPw"/>

        <b-alert variant="danger" :show="true" v-if="error">
            {{ error }}
        </b-alert>

        <b-button-toolbar justify v-if="canEditInfo || canEditPw">
            <b-button variant="danger" @click="reset">Reset</b-button>
            <submit-button @click="submit" ref="submitButton" :showError="false"/>
        </b-button-toolbar>
    </div>
</div>
</template>

<script>
import validator from 'email-validator';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/info';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import DescriptionPopover from './DescriptionPopover';
import SubmitButton from './SubmitButton';
import PasswordInput from './PasswordInput';

export default {
    name: 'userinfo',

    data() {
        return {
            name: '',
            username: '',
            email: '',
            oldPw: '',
            newPw: '',
            confirmPw: '',
            loading: false,
            canEditInfo: false,
            canEditPw: false,
            error: '',
            validator,
        };
    },

    components: {
        Icon,
        Loader,
        DescriptionPopover,
        SubmitButton,
        PasswordInput,
    },

    mounted() {
        this.loading = true;
        Promise.all([
            this.$http.get('/api/v1/login'),
            this.$hasPermission(['can_edit_own_info', 'can_edit_own_password']),
        ]).then(([{ data }, [canEditInfo, canEditPw]]) => {
            this.canEditInfo = canEditInfo;
            this.canEditPw = canEditPw;

            this.name = data.name;
            this.username = data.username;
            this.email = data.email;
            this.loading = false;
        });
    },

    methods: {
        resetEmailOnLti() {
            const btn = this.$refs.resetOnLtiButton;
            const req = this.$http.patch('/api/v1/login', {}, { params: { type: 'reset_on_lti' } });
            btn.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },
        reset() {
            this.name = this.$store.state.user.name;
            this.email = this.$store.state.user.email;
            this.oldPw = '';
            this.newPw = '';
            this.confirmPw = '';
            this.error = '';
        },

        submit() {
            this.error = '';

            if (this.newPw !== this.confirmPw) {
                this.error = 'New password doesn\'t match confirm password.';
                return;
            }
            if (!validator.validate(this.email)) {
                this.error = 'The given email is not valid.';
                return;
            }

            const req = this.$store.dispatch('user/updateUserInfo', {
                name: this.name,
                email: this.email,
                oldPw: this.oldPw,
                newPw: this.newPw,
            });
            req.then(() => {
                this.reset();
            }, ({ response }) => {
                this.error = response.data.message;
            });
            this.$refs.submitButton.submit(req);
        },
    },
};
</script>
