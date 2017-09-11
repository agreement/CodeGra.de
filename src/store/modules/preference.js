import * as types from '../mutation-types';

const getters = {
    fontSize: state => state.fontSize,
};

const actions = {
    setFontSize({ commit }, fontSize) {
        commit(types.UPDATE_FONT_SIZE, fontSize);
    },
};

const mutations = {
    [types.UPDATE_FONT_SIZE](state, fontSize) {
        state.fontSize = fontSize;
    },
};

export default {
    namespaced: true,
    state: {
        fontSize: 12,
    },
    getters,
    actions,
    mutations,
};
