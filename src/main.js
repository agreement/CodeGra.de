// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import 'highlightjs/styles/github.css';
import '@/style.less';

import Vue from 'vue';
import Resource from 'vue-resource';
import BootstrapVue from 'bootstrap-vue';
// import VueStash from 'vue-stash';

import App from '@/App';
import router from '@/router';
import store from './store';

Vue.use(Resource);
Vue.use(BootstrapVue);
// Vue.use(VueStash);

Vue.config.productionTip = false;

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    template: '<App/>',
    components: { App },
    data: {
        store: {
            user: {
                loggedIn: false,

                id: '1',
                email: 'testo@gmail.com',
                name: 'testo',
            },
        },
    },
    store,
});
