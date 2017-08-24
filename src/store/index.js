import Vue from 'vue';
import Vuex from 'vuex';
import createPersistedState from 'vuex-persistedstate';

import user from './modules/user';
import features from './modules/features';

Vue.use(Vuex);

const debug = process.env.NODE_ENV !== 'production';
const plugins = [
    createPersistedState(),
];

export default new Vuex.Store({
    modules: {
        user,
        features,
    },
    strict: debug,
    plugins,
});
