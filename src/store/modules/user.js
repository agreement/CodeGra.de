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
                commit(types.LOGIN, response.data);
                resolve();
            }).catch((err) => {
                reject(err.response.data);
            });
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
