// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import 'highlightjs/styles/solarized-dark.css';
import '@/style.less';

import Vue from 'vue';
import { mapActions } from 'vuex';
import BootstrapVue from 'bootstrap-vue';
import axios from 'axios';
import Toasted from 'vue-toasted';
import localforage from 'localforage';
import memoryStorageDriver from 'localforage-memoryStorageDriver';

import '@/polyfills';
import App from '@/App';
import router from '@/router';
import store from './store';
import * as mutationTypes from './store/mutation-types';
import PermissionStore from './permissions';

Vue.use(BootstrapVue);
Vue.use(Toasted);

Vue.config.productionTip = false;

axios.defaults.transformRequest.push((data, headers) => {
    if (store.state.user.jwtToken) {
        headers.Authorization = `Bearer ${store.state.user.jwtToken}`;
    }
    return data;
});

Vue.prototype.$http = axios;

const DRIVERS = [
    localforage.INDEXEDDB,
    localforage.WEBSQL,
    localforage.LOCALSTORAGE,
    'memoryStorageDriver',
];

let inLTI = false;
Object.defineProperty(Vue.prototype, '$inLTI', {
    get() {
        return inLTI;
    },
    set(val) {
        if (val === true) {
            inLTI = val;
        } else {
            throw new TypeError('You can only set this to true');
        }
    },
});

let LTIAssignmentId = null;
Object.defineProperty(Vue.prototype, '$LTIAssignmentId', {
    get() {
        return LTIAssignmentId;
    },
    set(val) {
        if (val == null) {
            throw new TypeError('You cannot set this to null or undefined');
        }
        if (LTIAssignmentId == null || val === LTIAssignmentId) {
            LTIAssignmentId = val;
        } else {
            throw new TypeError('You cannot change this property once it is set');
        }
    },
});

// eslint-disable-next-line
localforage.defineDriver(memoryStorageDriver).then(() => {
    Vue.prototype.$hlanguageStore = localforage.createInstance({
        name: 'highlightLanguageStore',
        driver: DRIVERS,
    });
    Vue.prototype.$whitespaceStore = localforage.createInstance({
        name: 'showWhitespaceStore',
        driver: DRIVERS,
    });

    const reUnescapedHtml = /[&<>"'`]/g;
    const reHasUnescapedHtml = RegExp(reUnescapedHtml.source);
    /** Used to map characters to HTML entities. */
    const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '`': '&#96;',
    };
    Vue.prototype.$htmlEscape = (inputString) => {
        const string = `${inputString}`;
        if (string && reHasUnescapedHtml.test(string)) {
            return string.replace(reUnescapedHtml, ent => htmlEscapes[ent]);
        }
        return string;
    };

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

    const permissionStore = new PermissionStore(axios, { driver: DRIVERS });

    Vue.prototype.$clearPermissions = (...args) => permissionStore.clearCache(...args);
    Vue.prototype.$hasPermission = (...args) => permissionStore.hasPermission(...args);

    /* eslint-disable no-new */
    const app = new Vue({
        el: '#app',
        router,
        template: '<App/>',
        components: { App },
        store,

        data() {
            return {
                screenWidth: window.innerWidth,
            };
        },

        created() {
            this.verifyLogin();

            window.addEventListener('resize', () => {
                this.screenWidth = window.innerWidth;
            });
        },

        computed: {
            $isSmallWindow() {
                return this.screenWidth <= 628;
            },

            $isMediumWindow() {
                return this.screenWidth >= 768;
            },

            $isLargeWindow() {
                return this.screenWidth >= 992;
            },
        },

        methods: {
            ...mapActions('user', [
                'verifyLogin',
            ]),
        },
    });

    // Clear some items in vuex store on CTRL-F5
    document.addEventListener('keydown', async (event) => {
        let isF5;
        if (event.key !== undefined) {
            isF5 = event.key === 'F5';
        } else if (event.keyIdentifier !== undefined) {
            isF5 = event.keyIdentifier === 'F5';
        } else if (event.keyCode !== undefined) {
            isF5 = event.keyCode === 116;
        }

        if (isF5 && (event.ctrlKey || event.shiftKey)) {
            event.preventDefault();
            await permissionStore.clearCache();
            await app.$store.commit(`user/${mutationTypes.CLEAR_CACHE}`);
            window.location.reload(true);
        }
    }, true);
});
