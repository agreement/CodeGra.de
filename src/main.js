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
import * as mutationTypes from './store/mutation-types';

Vue.use(BootstrapVue);
Vue.use(Toasted);

Vue.config.productionTip = false;

// console.dir is just much more useful
// eslint-disable-next-line
if (console.dir) console.log = console.dir;

axios.defaults.transformRequest.push((data, headers) => {
    if (store.state.user.jwtToken) {
        headers.Authorization = `Bearer ${store.state.user.jwtToken}`;
    }
    return data;
});

Vue.prototype.$http = axios;

// Fix axios automatically parsing all responses as JSON... WTF!!!
axios.defaults.transformResponse = [
    function defaultTransformResponse(data, headers) {
        switch (headers['content-type']) {
        case 'application/json':
            return JSON.parse(data);
        default:
            return data;
        }
    },
];

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
const app = new Vue({
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

// Clear some items in vuex store on CTRL-F5
document.addEventListener('keydown', (event) => {
    if (event.code === 'F5' && event.ctrlKey) {
        app.$store.commit(`user/${mutationTypes.CLEAR_CACHE}`);
    }
}, true);
