// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import 'highlightjs/styles/tomorrow.css';
import '@/style.less';

import Vue from 'vue';
import { mapActions } from 'vuex';
import BootstrapVue from 'bootstrap-vue';
import axios from 'axios';
import Toasted from 'vue-toasted';

import App from '@/App';
import router from '@/router';
import store from './store';

Vue.use(BootstrapVue);
Vue.use(Toasted);

Vue.config.productionTip = false;

// console.dir is just much more useful
// eslint-disable-next-line
if (console.dir) console.log = console.dir;

// Execute additional setup code
require('./setup.js');

axios.defaults.transformRequest.push((data, headers) => {
    if (store.state.user.jwtToken) {
        headers.Authorization = `Bearer ${store.state.user.jwtToken}`;
    }
    return data;
});


Vue.prototype.$http = axios;

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    template: '<App/>',
    components: { App },
    store,
    created() {
        this.verifyLogin();
    },
    methods: {
        ...mapActions('user', [
            'verifyLogin',
        ]),
    },
});
