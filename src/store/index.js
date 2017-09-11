import Vue from 'vue';
import Vuex from 'vuex';
import createPersistedState from 'vuex-persistedstate';

import user from './modules/user';
import pref from './modules/preference';

Vue.use(Vuex);

const debug = process.env.NODE_ENV !== 'production';
const plugins = [
    createPersistedState(),
];

export default new Vuex.Store({
    modules: {
        user,
        pref,
    },
    strict: debug,
    plugins,
});
