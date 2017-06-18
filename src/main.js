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

let toastVisible = false;
axios.interceptors.response.use(response => response, (error) => {
    if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        return Promise.reject(error);
    }

    if (error.request) {
        // The request was made but no response was received
        // `error.request` is an instance of XMLHttpRequest in the browser and an instance of
        // http.ClientRequest in node.js
        if (!toastVisible) {
            toastVisible = true;
            Vue.toasted.error('There was an error connecting to the server... Please try again later', {
                position: 'bottom-center',
                duration: 3000,
                onComplete: () => {
                    toastVisible = false;
                },
            });
        }
        return Promise.reject(error);
    }
    // Something happened in setting up the request that triggered an Error

    // eslint-disable-next-line
    console.error('Error while setting up request', error);
    return Promise.reject(error);
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
