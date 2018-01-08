<template>
    <div class="userinfo">
        <loader class="col-md-12 text-center" v-if="loading"></loader>
        <div @keyup.enter="submit" @keydown.capture="error = ''" v-else>
            <b-form-fieldset>
                <b-input-group left="Username">
                    <b-popover placement="top" triggers="hover" content="You cannot change your username" style="width: 100%;">
                      <input type="text"
                             v-model="username"
                             :disabled="true"
                             style="border-top-left-radius: 0; border-bottom-left-radius: 0; width: 100%"
                             class="form-control"/>
                    </b-popover>
                </b-input-group>
            </b-form-fieldset>
            <b-form-fieldset>
                <b-input-group left="Full name">
                    <input :disabled="!canEditInfo"
                           class="form-control"
                           type="text"
                           v-model="name"/>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Email">
                    <input :disabled="!canEditInfo"
                           type="text"
                           class="form-control"
                           v-model="email"/>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset v-if="canEditPw || canEditInfo">
                <b-input-group left="Old Password">
                    <input v-if="oldPwVisible"
                           type="text"
                           v-model="oldPw"
                           class="form-control"/>
                    <input v-else
                           type="password"
                           v-model="oldPw"
                           class="form-control"/>
                    <b-input-group-button slot="right">
                        <b-button @click="oldPwVisible = !oldPwVisible" >
                            <icon v-if="!oldPwVisible" name="eye"/>
                            <icon v-else name="eye-slash"/>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset v-if="canEditPw">
                <b-input-group left="New Password">
                  <input v-if="newPwVisible"
                         type="text"
                         v-model="newPw"
                         class="form-control"/>
                  <input v-else
                         type="password"
                         v-model="newPw"
                         class="form-control"/>
                    <b-input-group-button slot="right">
                        <b-button @click="newPwVisible = !newPwVisible" >
                            <icon v-if="!newPwVisible" name="eye"></icon>
                            <icon v-else name="eye-slash"></icon>
                        </b-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset v-if="canEditPw">
                <b-input-group left="Confirm Password">
                  <input v-if="confirmPwVisible"
                         type="text"
                         v-model="confirmPw"
                         class="form-control"/>
                  <input v-else
                         type="password"
                         v-model="confirmPw"
                         class="form-control"/>
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
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import SubmitButton from './SubmitButton';

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
