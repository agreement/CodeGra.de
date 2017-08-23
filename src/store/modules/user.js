import axios from 'axios';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    snippets: state => state.snippets,
    name: state => state.name,
    permissions: state => state.permissions,
    canSeeHidden: state => state.canSeeHidden,
};

const actions = {
    login({ commit, state }, { email, password }) {
        state.jwtToken = null;
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/login', { email, password }).then((response) => {
                commit(types.LOGIN, response.data);
                resolve();
                actions.refreshSnippets({ commit });
            }).catch((err) => {
                if (err.response) {
                    reject(err.response.data);
                } else {
                    reject(null);
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
            }).catch(() => {
                setTimeout(() => actions.refreshSnippets({ commit }).then(resolve), 1000 * 15);
            });
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

            const getPermissionvalues = () => {
                if (typeof perm.name === 'string') {
                    return [getPermission()[perm.name]];
                }
                return perm.name.map(val => getPermission()[val]);
            };

            const checkPermission = () => {
                const res = getPermissionvalues().map(val => val === true);
                if (typeof perm.name === 'string') {
                    return res[0];
                }
                return res;
            };

            if (getPermission() === undefined ||
                getPermissionvalues().some(val => val === undefined)) {
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
        return new Promise((resolve) => {
            commit(types.LOGOUT);
            resolve();
        });
    },
    verifyLogin({ commit, state }) {
        return new Promise((resolve, reject) => {
            axios.get('/api/v1/login').then((response) => {
                // We are already logged in. Update state to logged in state
                commit(types.LOGIN, {
                    access_token: state.jwtToken,
                    user: response.data,
                });
                actions.refreshSnippets({ commit });
                resolve();
            }).catch(() => {
                commit(types.LOGOUT);
                reject();
            });
        });
    },
    updateUserInfo({ commit }, { name, email, oldPw, newPw }) {
        return axios.patch('/api/v1/login', {
            name,
            email,
            o_password: oldPw,
            n_password: newPw,
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
            if (!state.permissions) {
                state.permissions = {};
            }
            Object.keys(response).forEach((key) => {
                state.permissions[key] = response[key];
            });
        }
    },
    [types.LOGOUT](state) {
        state.id = 0;
        state.name = '';
        state.email = '';
        state.snippets = null;
        state.permissions = null;
        state.canSeeHidden = false;
        state.jwtToken = null;
    },
    [types.NEW_SNIPPET](state, { key, value }) {
        state.snippets[key] = value;
    },
    [types.REMOVE_SNIPPET](state, key) {
        delete state.snippets[key];
    },
    [types.UPDATE_USER_INFO](state, { name, email }) {
        state.name = name;
        state.email = email;
    },
    [types.UPDATE_ACCESS_TOKEN](state, data) {
        state.jwtToken = data.access_token;
    },
};

export default {
    namespaced: true,
    state: {
        jwtToken: null,
        id: 0,
        email: '',
        name: '',
        snippets: null,
        permissions: null,
        canSeeHidden: false,
    },
    getters,
    actions,
    mutations,
};
