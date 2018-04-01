import * as types from '../mutation-types';

const getters = {
    fontSize: state => state.fontSize,
    darkMode: state => state.darkMode,
    contextAmount: state => state.contextAmount,
};

const actions = {
    setFontSize({ commit }, fontSize) {
        commit(types.UPDATE_FONT_SIZE, fontSize);
    },
    setContextAmount({ commit }, contextAmount) {
        commit(types.UPDATE_CONTEXT_AMOUNT, contextAmount);
    },
    setDarkMode({ commit }, darkMode) {
        commit(types.UPDATE_DARK_MODE, darkMode);
    },
};

const mutations = {
    [types.UPDATE_DARK_MODE](state, darkMode) {
        state.darkMode = darkMode;
    },
    [types.UPDATE_FONT_SIZE](state, fontSize) {
        state.fontSize = fontSize;
    },
    [types.UPDATE_CONTEXT_AMOUNT](state, contextAmount) {
        state.contextAmount = contextAmount;
    },
};

export default {
    namespaced: true,
    state: {
        fontSize: 12,
        darkMode: false,
        contextAmount: 3,
    },
    getters,
    actions,
    mutations,
};
