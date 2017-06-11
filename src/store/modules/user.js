import axios from 'axios';
import * as error from '@/errors';
import * as types from '../mutation-types';

const getters = {
    loggedIn: state => state.id !== 0,
    id: state => state.id,
    name: state => state.name,
};

const actions = {
    login({ commit }, { email, password }) {
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/login', { email, password }).then((response) => {
                const body = response.data;
                if (body.success) {
                    commit(types.LOGIN, {
                        id: body.id,
                        name: body.name,
                        email,
                    });
                    resolve();
                    return;
                }

                if ('email_error' in body) {
                    reject(error.emailDoesNotExist);
                    return;
                }

                if ('password_error' in body) {
                    reject(error.passwordIsInvalid);
                    return;
                }

                // This should never happen
                reject(error.apiError);
            }).catch(() => {
                reject(error.apiError);
            });
        });
    },
    logout({ commit }) {
        return new Promise((resolve, reject) => {
            axios.post('/api/v1/logout').then((response) => {
                const body = response.data;
                if (body.success) {
                    commit(types.LOGOUT);
                    resolve();
                    return;
                }

                // This should never happen
                reject(error.apiError);
            }).catch(() => {
                reject(error.apiError);
            });
        });
    },
};

const mutations = {
    [types.LOGIN](state, userdata) {
        state.id = userdata.id;
        state.email = userdata.email;
        state.name = userdata.name;
    },
    [types.LOGOUT](state) {
        state.id = 0;
        state.email = '';
        state.name = '';
    },
};

export default {
    namespaced: true,
    state: {
        id: 0,
        email: '',
        name: '',
    },
    getters,
    actions,
    mutations,
};
