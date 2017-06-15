import axios from 'axios';
import * as error from '@/errors';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    name: state => state.name,
    permissions: state => state.permissions,
};

const actions = {
    login({ commit }, { email, password }) {
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/login', { email, password }).then((response) => {
                commit(types.LOGIN, response.data);
                resolve();
            }).catch((err) => {
                reject(err.response.data);
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

            const checkPermission = () => getPermission()[perm.name] === true;

            if (getPermission() === undefined || getPermission()[perm.name] === undefined) {
                axios.get('/api/v1/permissions/', {
                    params: perm.course_id ? { course_id: perm.course_id } : {},
                }).then((response) => {
                    commit(types.PERMSSIONS, { response: response.data, perm });
                    resolve(checkPermission());
                }, () => resolve(false));
            } else {
                if (Math.random() < 0.005) {
                    axios.get('/api/v1/permissions/').then((response) => {
                        commit(types.PERMSSIONS, { response: response.data, perm });
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
    [types.PERMSSIONS](state, { response, perm }) {
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
        state.permissions = null;
    },
};

export default {
    namespaced: true,
    state: {
        id: 0,
        email: '',
        name: '',
        permissions: null,
    },
    getters,
    actions,
    mutations,
};
