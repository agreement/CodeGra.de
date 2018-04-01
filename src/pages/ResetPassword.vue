<template>
<div class="reset-password row justify-content-center">
    <b-form-fieldset class="col-sm-8 text-center"
                        @keyup.native.ctrl.enter="submit">
        <h4>Reset your password</h4>

        <password-input label="New password"
                        v-model="newPw"/>
        <password-input label="Confirm password"
                        v-model="confirmPw"/>

        <submit-button ref="btn" @click="submit" popover-placement="bottom"/>
    </b-form-fieldset>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';
import { mapActions } from 'vuex';

import { SubmitButton, PasswordInput } from '@/components';

export default {
    name: 'reset-password',

    data() {
        return {
            newPw: '',
            confirmPw: '',
        };
    },

    components: {
        Icon,
        SubmitButton,
        PasswordInput,
    },

    methods: {
        ...mapActions('user', [
            'updateAccessToken',
        ]),

        submit() {
            const button = this.$refs.btn;

            if (this.newPw !== this.confirmPw) {
                button.fail('The passwords don\'t match');
                return;
            } else if (this.newPw === '') {
                button.fail('The new password may not be empty');
                return;
            }

            const req = this.$http.patch('/api/v1/login?type=reset_password', {
                user_id: Number(this.$route.query.user),
                token: this.$route.query.token,
                new_password: this.newPw,
            }).then(async ({ data }) => {
                await this.updateAccessToken(data.access_token);
                this.$router.replace({
                    name: 'home',
                    query: { sbloc: 'm' },
                });
            }, (err) => {
                throw err.response.data.message;
            });

            button.submit(req);
        },
    },
};
</script>

<style lang="less" scoped>
.reset-password {
    margin-top: 1rem;
}

h4 {
    margin-bottom: 1rem;
}
</style>
