<template>
    <loader v-if="loading"/>
    <div class="pref-manager" v-else>
        <table class="table settings-table"
               style="margin-bottom: 0;">
            <tbody>
                <tr v-if="showWhitespace">
                    <td>
                        Whitespace
                        <loader :scale="1" :center="true" v-if="whiteLoading"/>
                    </td>
                    <td>
                        <toggle v-model="whitespace" label-on="Show" label-off="Hide"/>
                    </td>
                </tr>
                <tr v-if="showLanguage">
                    <td>Language
                        <loader v-if="langLoading" :scale="1" center/>
                    </td>
                    <td>
                        <multiselect v-model="selectedLanguage"
                                     :hide-selected="selectedLanguage === 'Default'"
                                     deselect-label="Reset language"
                                     select-label="Select language"
                                     :options="languages"/>
                    </td>
                </tr>
                <tr v-if="showFontSize">
                    <td>
                        Code font size
                        <loader v-show="fontSizeLoading" :scale="1" center/>
                    </td>
                    <td>
                        <b-input-group append="px">
                            <input v-model="fontSize"
                                   class="form-control"
                                   style="z-index: 0;"
                                   type="number"
                                   step="1"
                                   min="1"/>
                        </b-input-group>
                    </td>
                </tr>
                <tr v-if="showCharColumn">
                    <td>
                        Line at column
                        <loader v-show="charColumnLoading" :scale="1" center/>
                    </td>
                    <td>
                        <b-input-group>
                            <b-input-group-prepend is-text
                                                   class="char-column-checkbox">
                                <b-form-checkbox v-model="charColumnVisible"/>
                            </b-input-group-prepend>
                            <input v-model="charColumnOffset"
                                   class="form-control"
                                   :disabled="!charColumnVisible"
                                   placeholder="Offset"
                                   type="number"
                                   step="1"
                                   min="0"/>
                            <toggle v-model="charColumnWide"
                                    label-on="wide"
                                    label-off="narrow"
                                    :disabled="!charColumnVisible"
                                    class="form-control char-column-toggle"/>
                        </b-input-group>
                    </td>
                </tr>
                <tr v-if="showContextAmount">
                   <td>
                       Amount of context
                       <loader v-show="contextAmountLoading" :scale="1" center/>
                   </td>
                   <td>
                       <b-input-group append="lines">
                           <input v-model="contextAmount"
                                  class="form-control"
                                  style="z-index: 0;"
                                  type="number"
                                  step="1"
                                  min="0"/>
                       </b-input-group>
                   </td>
               </tr>
               <tr v-if="showTheme">
                    <td>Theme</td>
                    <td>
                        <toggle v-model="darkMode" label-on="Dark" label-off="Light"/>
                    </td>
                </tr>
                <tr v-if="showRevision">
                    <td>Revision</td>
                    <td>
                        <b-form-radio-group v-model="selectedRevision"
                                            :options="revisionOptions"/>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
import { listLanguages } from 'highlightjs';
import { mapGetters } from 'vuex';
import Multiselect from 'vue-multiselect';

import { cmpNoCase } from '@/utils';

import Toggle from './Toggle';
import Loader from './Loader';

export default {
    name: 'preference-manager',

    components: {
        Toggle,
        Loader,
        Multiselect,
    },

    computed: {
        ...mapGetters('pref', {
            storeDarkMode: 'darkMode',
            storeFontSize: 'fontSize',
            storeContextAmount: 'contextAmount',
            storeCharColumn: 'charColumn',
            storeCharColumnOffset: 'charColumnOffset',
        }),

        charColumn() {
            const res = {
                visible: this.charColumnVisible,
                offset: Number(this.charColumnOffset),
                wide: this.charColumnWide,
            };
            res.text = Array(res.offset + 1).join('.');
            return res;
        },
    },

    props: {
        showWhitespace: {
            type: Boolean,
            default: true,
        },
        showLanguage: {
            type: Boolean,
            default: true,
        },
        showFontSize: {
            type: Boolean,
            default: true,
        },
        showTheme: {
            type: Boolean,
            default: true,
        },
        showRevision: {
            type: Boolean,
            default: true,
        },
        fileId: {
            type: Number,
            default: null,
        },

        revision: {
            default: null,
        },

        showContextAmount: {
            default: false,
        },

        showLoader: {
            type: Boolean,
            default: true,
        },

        showCharColumn: {
            type: Boolean,
            default: false,
        },
    },

    methods: {
        loadValues() {
            this.loading = true;
            let promise = Promise.resolve();
            if (this.showTheme) this.darkMode = this.storeDarkMode;
            if (this.showFontSize) this.fontSize = this.storeFontSize;
            if (this.showContextAmount) this.contextAmount = this.storeContextAmount;

            if (this.showCharColumn) {
                this.charColumnVisible = this.storeCharColumn.visible;
                this.charColumnOffset = this.storeCharColumn.offset;
                this.charColumnWidth = this.storeCharColumn.width;
            }

            if (this.showWhitespace) {
                promise = promise
                    .then(() =>
                        this.$whitespaceStore.getItem(`${this.fileId}`).then((white) => {
                            this.whitespace = white === null || white;
                        }));
            }

            if (this.showLanguage) {
                promise = promise
                    .then(() =>
                        this.$hlanguageStore.getItem(`${this.fileId}`).then((lang) => {
                            this.selectedLanguage = lang || 'Default';
                        }));
            }

            promise.then(() => {
                this.loading = false;
            });
        },
    },

    data() {
        const languages = listLanguages();
        languages.push('plain');
        languages.sort(cmpNoCase);
        languages.unshift('Default');
        return {
            loading: true,
            darkMode: false,
            languages,
            whitespace: true,
            contextAmount: false,
            contextAmountLoading: false,
            fontSize: false,
            fontSizeLoading: false,
            langLoading: false,
            whiteLoading: false,
            initialFont: true,
            selectedLanguage: -1,
            selectedRevision: this.revision || 'student',
            charColumnVisible: false,
            charColumnOffset: 80,
            charColumnWide: true,
            charColumnLoading: false,
            revisionOptions: [
                {
                    text: 'Student',
                    value: 'student',
                }, {
                    text: 'Teacher',
                    value: 'teacher',
                }, {
                    text: 'Diff',
                    value: 'diff',
                },
            ],
        };
    },

    mounted() {
        this.loadValues();
    },

    watch: {
        revision(newVal) {
            if (this.selectedRevision !== newVal) {
                this.selectedRevision = newVal;
            }
        },

        fileId(newVal, oldVal) {
            if (newVal != null && newVal !== oldVal) {
                this.loadValues();
            }
        },

        darkMode(val) {
            this.$store.dispatch('pref/setDarkMode', val);
        },

        storeContextAmount(val) {
            if (this.contextAmount !== val) {
                this.contextAmount = val;
            }
        },

        contextAmount(val) {
            this.contextAmountLoading = true;
            const amount = Math.max(val, 0);
            const cont = this.$store.dispatch('pref/setContextAmount', amount);
            cont.then(() => {
                this.contextAmountLoading = false;
                this.$emit('context-amount', amount);
            });
        },

        charColumnVisible() {
            this.charColumnLoading = true;
            this.$store.dispatch('pref/setCharColumn', this.charColumn).then(() => {
                this.charColumnLoading = false;
                this.$emit('charcolumn', this.charColumn);
            });
        },

        charColumnOffset() {
            this.charColumnLoading = true;
            this.$store.dispatch('pref/setCharColumn', this.charColumn).then(() => {
                this.charColumnLoading = false;
                this.$emit('charcolumn', this.charColumn);
            });
        },

        charColumnWide() {
            this.charColumnLoading = true;
            this.$store.dispatch('pref/setCharColumn', this.charColumn).then(() => {
                this.charColumnLoading = false;
                this.$emit('charcolumn', this.charColumn);
            });
        },

        storeFontSize(val) {
            if (this.fontSize !== val) {
                this.fontSize = val;
            }
        },

        fontSize(val) {
            this.fontSizeLoading = true;
            const size = Math.max(val, 1);
            const cont = this.$store.dispatch('pref/setFontSize', size);
            const done = () => cont.then(() => {
                this.fontSizeLoading = false;
                this.$emit('font-size', size);
            });


            if (this.showLoader && !this.initialFont) {
                setTimeout(() => {
                    this.$nextTick(done);
                }, 200);
            } else {
                this.initialFont = false;
                done();
            }
        },

        selectedLanguage(lang, old) {
            if (old === -1) return;

            if (lang == null) {
                this.selectedLanguage = 'Default';
            } else {
                this.langLoading = true;
                this.$hlanguageStore.setItem(`${this.fileId}`, lang).then(() => {
                    this.langLoading = false;
                    this.$emit('language', lang);
                });
            }
        },

        whitespace(val) {
            this.whiteLoading = true;

            const cont = this.$whitespaceStore.setItem(`${this.fileId}`, val);

            setTimeout(() => {
                this.$nextTick(() => {
                    cont.then(() => {
                        this.whiteLoading = false;
                        this.$emit('whitespace', val);
                    });
                });
            }, 200);
        },

        selectedRevision(val) {
            this.$emit('revision', val);
        },
    },
};
</script>

<style lang="less">
@import '~mixins.less';

.pref-manager {
    #app.dark ~ .popover & .table {
        .dark-table-colors;
    }

    #app.dark ~ .popover & .table {
        .dark-input-colors;
    }

    #app.dark ~ .popover & .input-group {
        .dark-input-group-colors;
    }

    #app.dark &,
    #app.dark ~ .popover & {
        .dark-selects-colors;
    }

    .table {
        .loader {
            margin-top: 4px;
            float: right;
        }
    }

    .multiselect__option--highlight {
        background: @color-primary;

        &::after {
            background: @color-primary;
        }

        &.multiselect__option--selected {
            background: #d9534f !important;

            &::after {
                background: #d9534f !important;
            }
        }
    }

    .table td {
        vertical-align: middle;
        text-align: left;

        &:first-child {
            width: 10em;
        }
    }

    .char-column-checkbox {
        .input-group-text {
            background-color: transparent;
        }

        .custom-checkbox {
            padding-left: 1rem;
        }
    }

    .char-column-toggle {
        text-align: center;

        &.disabled {
            background-color: #e9ecef;
        }
    }
}
</style>
