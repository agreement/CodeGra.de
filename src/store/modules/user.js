import Vue from 'vue';
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
            Vue.http.post('/api/v1/login', { email, password }).then((response) => {
                const body = response.data;
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
