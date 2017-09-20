import * as types from '../mutation-types';

const getters = {
    fontSize: state => state.fontSize,
    darkMode: state => state.darkMode,
};

const actions = {
    setFontSize({ commit }, fontSize) {
        commit(types.UPDATE_FONT_SIZE, fontSize);
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
};

export default {
    namespaced: true,
    state: {
        fontSize: 12,
        darkMode: false,
    },
    getters,
    actions,
    mutations,
};
