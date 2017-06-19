import axios from 'axios';
import * as error from '@/errors';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    snippets: state => state.snippets,
    name: state => state.name,
    permissions: state => state.permissions,
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
    addSnippet({ commit }, val) {
        commit(types.NEW_SNIPPET, val);
    },
    refreshSnippets({ commit }) {
        axios.get('/api/v1/snippets/').then((response) => {
            commit(types.SNIPPETS, response.data);
        }).catch(() => {
            setTimeout(() => actions.refreshSnippets({ commit }), 1000 * 15);
        });
    },
    hasPermission({ commit, state }, perm) {
        return new Promise((resolve) => {
            const getPermission = () => {
                if (state.permissions === null) {
                    return {};
                } else if (perm.course_id === null) {
                    return state.permissions;
                }
                return state.permissions[`course_${perm.course_id}`];
            };

            const checkPermission = () => getPermission()[perm.name] === true;

            if (getPermission() === undefined || getPermission()[perm.name] === undefined) {
                axios.get('/api/v1/permissions/', {
                    params: perm.course_id ? { course_id: perm.course_id } : {},
                }).then((response) => {
                    commit(types.PERMISSIONS, { response: response.data, perm });
                    resolve(checkPermission());
                }, () => resolve(false));
            } else {
                if (Math.random() < 0.005) {
                    axios.get('/api/v1/permissions/').then((response) => {
                        commit(types.PERMISSIONS, { response: response.data, perm });
                    });
                }
                resolve(checkPermission());
            }
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
    [types.PERMISSIONS](state, { response, perm }) {
        if (perm.course_id !== undefined) {
            if (!state.permissions) {
                state.permissions = {};
            }
            state.permissions[`course_${perm.course_id}`] = response;
        } else {
            state.permissions = response;
        }
    },
    [types.LOGOUT](state) {
        state.id = 0;
        state.email = '';
        state.name = '';
        state.snippets = null;
        state.permissions = null;
    },
    [types.NEW_SNIPPET](state, { key, value }) {
        state.snippets[key] = value;
    },
};

export default {
    namespaced: true,
    state: {
        id: 0,
        email: '',
        name: '',
        snippets: null,
        permissions: null,
    },
    getters,
    actions,
    mutations,
};
