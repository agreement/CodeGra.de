import Vue from 'vue';
import * as error from '@/errors';
import * as types from '../mutation-types';

const getters = {
    loggedIn: (state) => {
        if (!state.id) {
            state.id = localStorage.getItem('user_id', false);
        }
        return state.id || false;
    },
    id: state => state.id || false,
    name: (state) => {
        if (!state.name) {
            state.name = localStorage.getItem('user_name', false);
        }
        return state.name || false;
    },
};

const actions = {
    login({ commit }, { email, password }) {
        return new Promise((resolve, reject) => {
            Vue.http.post('/api/v1/login', { email, password }).then((response) => {
                const body = response.data;
                localStorage.setItem('user_id', body.id);
                localStorage.setItem('user_name', body.name);
                commit(types.LOGIN, {
                    id: body.id,
                    name: body.name,
                    email,
                });
                resolve();
            }, (response) => {
                reject(response.body);
            });
        });
    },
    logout({ commit }) {
        return new Promise((resolve, reject) => {
            Vue.http.post('/api/v1/logout').then(() => {
                localStorage.removeItem('user_id');
                localStorage.removeItem('user_name');
                commit(types.LOGOUT);
                resolve();
            }, () => {
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
        state.id = false;
        state.email = '';
        state.name = false;
    },
};

export default {
    namespaced: true,
    state: {
        id: false,
        email: '',
        name: false,
    },
    getters,
    actions,
    mutations,
};
