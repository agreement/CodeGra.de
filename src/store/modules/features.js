import axios from 'axios';
import * as types from '../mutation-types';

// FIXME: Remove these useless getters.
const getters = {
    features: state => state.features,
    version: state => state.version,
};

const actions = {
    refreshFeatures({ commit }) {
        return axios.get('/api/v1/about?type=features').then(({ data }) => {
            commit(types.UPDATE_FEATURES, data);
        });
    },
};

const mutations = {
    [types.UPDATE_FEATURES](state, data) {
        state.version = data.version;
        state.features = data.features;
    },
};

export default {
    namespaced: true,
    state: {
        version: 0,
        featues: {},
    },
    getters,
    actions,
    mutations,
};
