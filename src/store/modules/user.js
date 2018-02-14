import Vue from 'vue';
import axios from 'axios';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    snippets: state => state.snippets,
    name: state => state.name,
    canSeeHidden: state => state.canSeeHidden,
};

const actions = {
    login({ commit, state }, { username, password }) {
        state.jwtToken = null;
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/login', { username, password }).then((response) => {
                commit(types.LOGIN, response.data);
                resolve();
                actions.refreshSnippets({ commit });
            }).catch((err) => {
                if (err.response) {
                    reject(err.response.data);
                } else {
                    reject(new Error('Login failed for a unknown reason!'));
                }
            });
        });
    },
    addSnippet({ commit }, val) {
        commit(types.NEW_SNIPPET, val);
    },
    deleteSnippet({ commit }, key) {
        commit(types.REMOVE_SNIPPET, key);
    },
    refreshSnippets({ commit }) {
        return new Promise((resolve) => {
            axios.get('/api/v1/snippets/').then(({ data }) => {
                const snips = {};
                for (let i = 0, len = data.length; i < len; i += 1) {
                    snips[data[i].key] = data[i];
                }
                commit(types.SNIPPETS, snips);
                resolve();
            });
        });
    },
    logout({ commit }) {
        return new Promise((resolve) => {
            commit(types.LOGOUT);
            resolve();
        });
    },
    verifyLogin({ commit, state }) {
        return new Promise((resolve, reject) => {
            axios.get('/api/v1/login?type=extended').then((response) => {
                // We are already logged in. Update state to logged in state
                commit(types.LOGIN, {
                    access_token: state.jwtToken,
                    user: response.data,
                });
                resolve();
            }).catch(() => {
                commit(types.LOGOUT);
                reject();
            });
        });
    },
    updateUserInfo({ commit }, {
        name, email, oldPw, newPw,
    }) {
        return axios.patch('/api/v1/login', {
            name,
            email,
            old_password: oldPw,
            new_password: newPw,
        }).then(() => {
            commit(types.UPDATE_USER_INFO, { name, email });
        });
    },
};

const mutations = {
    [types.LOGIN](state, data) {
        state.jwtToken = data.access_token;

        const userdata = data.user;
        state.id = userdata.id;
        state.email = userdata.email;
        state.name = userdata.name;
        state.canSeeHidden = userdata.hidden;
        state.username = userdata.username;
    },
    [types.SNIPPETS](state, snippets) {
        state.snippets = snippets;
    },
    [types.LOGOUT](state) {
        state.id = 0;
        state.name = '';
        state.email = '';
        state.snippets = null;
        state.canSeeHidden = false;
        state.jwtToken = null;
        state.username = null;
        Vue.prototype.$clearPermissions();
    },
    [types.NEW_SNIPPET](state, { key, value }) {
        state.snippets[key] = { value };
    },
    [types.REMOVE_SNIPPET](state, key) {
        delete state.snippets[key];
    },
    [types.UPDATE_USER_INFO](state, { name, email }) {
        state.name = name;
        state.email = email;
    },
    [types.UPDATE_ACCESS_TOKEN](state, data) {
        mutations[types.LOGOUT](state);
        state.jwtToken = data.access_token;
    },
    [types.CLEAR_CACHE](state) {
        state.snippets = {};
    },
};

export default {
    namespaced: true,
    state: {
        jwtToken: null,
        id: 0,
        email: '',
        name: '',
        snippets: {},
        canSeeHidden: false,
        username: '',
    },
    getters,
    actions,
    mutations,
};
