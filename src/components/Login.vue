<template>
    <div class="login">
        <div class="form-group">
            <input type="text" class="form-control" placeholder="Email" v-model="email">
            <b-alert variant="danger" :show="submitted && !validator.validate(email)" class="help">
                Please enter a valid email
            </b-alert>
        </div>

        <div class="form-group">
            <input type="password" class="form-control" placeholder="Password" v-model="password">
            <b-alert variant="danger" v-show="submitted && password.length === 0" class="help">
                Please enter a non empty password
            </b-alert>
        </div>

        <b-alert :show="error !== ''" variant="danger">
            {{ error }}
        </b-alert>

        <div class="form-group">
            <input type="submit" class="form-control" value="Submit" @click="login">
        </div>
    </div>
</template>

<script>

import { mapActions } from 'vuex';
import { bAlert, bPopover } from 'bootstrap-vue/lib/components';

const validator = require('email-validator');

export default {
    name: 'login',
    data() {
        return {
            email: '',
            password: '',
            error: '',
            validator,
            submitted: false,
        };
    },
    methods: {
        login(event) {
            event.preventDefault();
            this.error = '';
            this.submitted = true;
            if (!validator.validate(this.email)) {
                return;
            }
            if (this.password.length === 0) {
                return;
            }

            this.tryLogin({ email: this.email, password: this.password }).then(() => {
                this.$router.replace({ name: 'home' });
            }).catch((reason) => {
                if (reason) {
                    this.error = reason.message;
                }
            });
        },
        ...mapActions({
            tryLogin: 'user/login',
        }),
    },
    components: {
        bAlert,
        bPopover,
    },
};
</script>

<style lang="less">
.help {
    position: relative;
    margin-top: -4px;
    z-index: -1;
}
</style>
