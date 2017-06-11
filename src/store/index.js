import Vue from 'vue';
import Vuex from 'vuex';

import user from './modules/user';

Vue.use(Vuex);

const debug = process.env.NODE_ENV !== 'production';
const plugins = [];

export default new Vuex.Store({
    modules: {
        user,
    },
    strict: debug,
    plugins,
});
