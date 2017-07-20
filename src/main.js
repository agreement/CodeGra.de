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

Vue.prototype.$http = axios;

axios.interceptors.response.use(response => response, (() => {
    let toastVisible = false;
    return (error) => {
        if (!error.response && error.request && !toastVisible) {
            toastVisible = true;
            Vue.toasted.error('There was an error connecting to the server... Please try again later', {
                position: 'bottom-center',
                duration: 3000,
                onComplete: () => {
                    toastVisible = false;
                },
            });
        }
        throw error;
    };
})());

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
