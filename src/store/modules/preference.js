import * as types from '../mutation-types';

const getters = {
    fontSize: state => state.fontSize,
    darkMode: state => state.darkMode,
    contextAmount: state => state.contextAmount,
    charColumn: state => state.charColumn,
    charColumnOffset: state => state.charColumnOffset,
};

const actions = {
    setFontSize({ commit }, fontSize) {
        commit(types.UPDATE_FONT_SIZE, fontSize);
    },
    setDarkMode({ commit }, darkMode) {
        commit(types.UPDATE_DARK_MODE, darkMode);
    },
    setContextAmount({ commit }, contextAmount) {
        commit(types.UPDATE_CONTEXT_AMOUNT, contextAmount);
    },
    setCharColumn({ commit }, charColumn) {
        commit(types.UPDATE_CHAR_COLUMN, charColumn);
    },
    setCharColumnOffset({ commit }, charColumnOffset) {
        commit(types.UPDATE_CHAR_COLUMN_OFFSET, charColumnOffset);
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
    [types.UPDATE_CHAR_COLUMN](state, charColumn) {
        state.charColumn = charColumn;
    },
    [types.UPDATE_CHAR_COLUMN_OFFSET](state, charColumnOffset) {
        state.charColumnOffset = charColumnOffset;
    },
};

export default {
    namespaced: true,
    state: {
        fontSize: 12,
        darkMode: false,
        contextAmount: 3,
        charColumn: false,
        charColumnOffset: 80,
    },
    getters,
    actions,
    mutations,
};
