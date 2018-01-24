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
                        <toggle v-model="whitespace" label-on="show" label-off="hide"/>
                    </td>
                </tr>
                <tr v-if="showLanguage">
                    <td>Language
                        <loader :scale="1" :center="true" v-if="langLoading"/>
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
                    <td>Code font size</td>
                    <td>
                        <b-input-group right="px">
                            <input v-model="fontSize"
                                   class="form-control fontsize-select"
                                   style="z-index: 0;"
                                   type="number"
                                   min="1"/>
                        </b-input-group>
                    </td>
                </tr>
                <tr v-if="showTheme">
                    <td>Theme</td>
                    <td>
                        <toggle v-model="darkMode" label-on="dark" label-off="light"/>
                    </td>
                </tr>
                <tr v-if="showRevision">
                    <td>Revision</td>
                    <td>
                        <b-input-group>
                            <b-form-radio v-model="selectedRevision"
                                          :options="revisionOptions"/>
                        </b-input-group>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
import { listLanguages } from 'highlightjs';
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
    },

    methods: {
        loadValues() {
            this.loading = true;
            let promise = Promise.resolve();
            if (this.showTheme) this.darkMode = this.$store.getters['pref/darkMode'];
            if (this.showFontSize) this.fontSize = this.$store.getters['pref/fontSize'];
            if (this.showWhitespace) {
                promise = promise
                    .then(() =>
                          this.$whitespaceStore.getItem(`${this.fileId}`).then((white) => {
                              this.whitespace = white === null || white;
                          }));
            }
            if (this.showLanguage) {
                promise = promise
                    .then(() => this.$hlanguageStore.getItem(`${this.fileId}`).then((lang) => {
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
            fontSize: false,
            langLoading: false,
            whiteLoading: false,
            initial: true,
            selectedLanguage: -1,
            selectedRevision: this.$route.query.revision || 'student',
            revisionOptions: [
                {
                    text: 'Student',
                    value: 'student',
                },
                {
                    text: 'Teacher',
                    value: 'teacher',
                },
                {
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
        fileId() {
            if (this.initial) {
                this.initial = false;
                return;
            }
            this.loadValues();
        },

        darkMode(val) {
            this.$store.dispatch('pref/setDarkMode', val);
        },

        fontSize(val) {
            const size = Math.max(val, 1);
            this.$store.dispatch('pref/setFontSize', size);
            this.$emit('font-size', size);
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
            // Use a timeout to prevent very short loaders.
            let load = true;
            setTimeout(() => {
                this.whiteLoading = load;
            }, 100);

            this.$whitespaceStore.setItem(`${this.fileId}`, val).then(() => {
                load = false;
                this.whiteLoading = false;
                this.$emit('whitespace', val);
            });
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
    }
    .toggle-container {
        margin-bottom: -2px;
        border-radius: 0;
    }
}
</style>
