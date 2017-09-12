<template>
    <div class="page reset-password row justify-content-center">
        <b-form-fieldset class="col-sm-8 text-center"
                         @keyup.native.ctrl.enter="submit">
            <h4>Reset your password</h4>
            <b-input-group left="New password">
                <b-form-input  :type="newPwVisible ? 'text' : 'password'"
                               tabindex="1"
                               v-model="newPw"/>
                <b-input-group-button slot="right">
                    <b-button @click="newPwVisible = !newPwVisible" >
                        <icon v-if="!newPwVisible" name="eye"/>
                        <icon v-else name="eye-slash"/>
                    </b-button>
                </b-input-group-button>
            </b-input-group>
            <b-input-group left="Confirm password">
                <b-form-input  :type="confirmPwVisible ? 'text' : 'password'"
                               tabindex="2"
                               v-model="confirmPw"/>
                <b-input-group-button slot="right">
                    <b-button @click="confirmPwVisible = !confirmPwVisible" >
                        <icon v-if="!confirmPwVisible" name="eye"/>
                        <icon v-else name="eye-slash"/>
                    </b-button>
                </b-input-group-button>
            </b-input-group>

            <submit-button ref="btn" @click="submit" popover-placement="bottom"/>
        </b-form-fieldset>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';

import { SubmitButton } from '@/components';

import * as types from '../store/mutation-types';

export default {
    name: 'reset-password',

    data() {
        return {
            newPw: '',
            confirmPw: '',
            newPwVisible: false,
            confirmPwVisible: false,
        };
    },

    components: {
        Icon,
        SubmitButton,
    },

    methods: {
        submit() {
            let req;
            if (this.newPw !== this.confirmPw) {
                req = Promise.reject('The passwords don\'t match');
            } else if (this.newPw === '') {
                req = Promise.reject('The new password may not be empty');
            } else {
                req = this.$http.patch('/api/v1/login?type=reset_password', {
                    user_id: Number(this.$route.query.user),
                    token: this.$route.query.token,
                    new_password: this.newPw,
                }).then(({ data }) => {
                    this.$store.commit(`user/${types.UPDATE_ACCESS_TOKEN}`, data);
                    this.$router.replace({
                        name: 'me',
                    });
                }, (err) => {
                    throw err.response.data.message;
                });
            }
            this.$refs.btn.submit(req);
        },
    },
};
</script>

<style lang="less" scoped>
.input-group:not(:last-child) {
    margin-bottom: 15px;
}

h4 {
    margin-bottom: 15px;
}
</style>
