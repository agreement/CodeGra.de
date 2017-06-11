<template>
  <div class="container">
    <div class="row justify-content-md-center">
      <div class="col col-lg-9">
        <form>
          <div class="form-group">
            <input type="text" class="form-control" placeholder="Email" v-model="email">
            <div v-show="submitted && !validator.validate(email)" class="help alert-danger">
              Please enter a valid email
            </div>
          </div>

          <div class="form-group">
            <input type="password" class="form-control" placeholder="Password" v-model="password">
            <div v-show="submitted && password.length === 0" class="help alert-danger">
              Please enter a non empty password
            </div>
          </div>

          <b-alert :show="error !== ''" variant="danger">
            {{ error }}
          </b-alert>

          <div class="form-group">
            <input type="submit" class="form-control" value="Submit" @click="login()">
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue';

import { mapActions } from 'vuex';
import { bPopover } from 'bootstrap-vue/lib/components';

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
        login() {
            Vue.http.get('/api/v1/login').then((res) => {
                console.log(res);
            });
            this.error = '';
            this.submitted = true;
            if (!validator.validate(this.email)) {
                return;
            }
            if (this.password.length === 0) {
                return;
            }

            this.tryLogin({ email: this.email, password: this.password }).then(() => {
                Vue.http.get('/api/v1/login').then((res) => {
                    console.log(res);
                });
                this.$router.replace('/');
            }).catch((reason) => {
                this.error = reason.message;

                // TODO: toast the error
                // eslint-disable-next-line
                console.log(reason);
            });
        },
        clearErrors() {
            // this.error = '';
        },
        ...mapActions({
            tryLogin: 'user/login',
        }),
    },
    components: {
        bPopover,
    },
};
</script>

<style lang="less">
.help {
   margin-top: -4px;
   padding: 1%;
   z-index: -1;
}
.form-control {
    position: relative;
}
</style>
