import axios from 'axios';
import * as error from '@/errors';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    snippets: state => state.snippets,
    name: state => state.name,
};

const actions = {
    login({ commit }, { email, password }) {
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/login', { email, password }).then((response) => {
                commit(types.LOGIN, response.data);
                resolve();
                actions.refreshSnippets({ commit });
            }).catch((err) => {
                reject(err.response.data);
            });
        });
    },
    refreshSnippets({ commit }) {
        axios.get('/api/v1/snippets/').then((response) => {
            commit(types.SNIPPETS, response.data);
        }).catch(() => {
            actions.refreshSnippets({ commit });
        });
    },
    logout({ commit }) {
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/logout').then(() => {
                commit(types.LOGOUT);
                resolve();
            }).catch(() => {
                reject(error.apiError);
            });
        });
    },
    verifyLogin({ commit }) {
        axios.get('/api/v1/login').then((response) => {
            // We are already logged in. Update state to logged in state
            commit(types.LOGIN, response.data);
            actions.refreshSnippets({ commit });
        }).catch(() => {
            commit(types.LOGOUT);
        });
    },
};

const mutations = {
    [types.LOGIN](state, userdata) {
        state.id = userdata.id;
        state.email = userdata.email;
        state.name = userdata.name;
    },
    [types.SNIPPETS](state, snippets) {
        state.snippets = snippets;
    },
    [types.LOGOUT](state) {
        state.id = 0;
        state.email = '';
        state.name = '';
        state.snippets = null;
    },
};

export default {
    namespaced: true,
    state: {
        id: 0,
        email: '',
        name: '',
        snippets: null,
    },
    getters,
    actions,
    mutations,
};
