<template>
<multiselect :value="value"
             @input="onInput"
             :hide-selected="false"
             :options="students"
             :multiple="false"
             :searchable="true"
             :select-label="selectLabel"
             @search-change="asyncFind"
             :internal-search="true"
             :custom-label="o => `${o.name} (${o.username})`"
             :loading="loadingStudents"
             class="user-selector"
             style="flex: 1;"
             :placeholder="placeholder"
             :disabled="disabled"
             label="name"
             track-by="username"
             v-if="canSearchUsers">
    <span slot="noResult" v-if="searchQuery && searchQuery.length < 3">
        Please give a larger search string.
    </span>
    <span slot="noResult" v-else>
        No results were found. You can search on name and username.
    </span>
</multiselect>
<input :value="value ? value.username : ''"
       @input="onInput({ username: $event.target.value })"
       class="form-control user-selector"
       :placeholder="placeholder"
       :disabled="disabled"
       v-else/>
</template>

<script>
import Multiselect from 'vue-multiselect';

export default {
    name: 'user-selector',

    props: {
        disabled: {
            type: Boolean,
            default: false,
        },
        placeholder: {
            type: String,
            required: true,
        },

        filterStudents: {
            type: Function,
            default: () => true,
        },

        selectLabel: {
            type: String,
            default: 'Press enter to select',
        },

        value: {
            required: true,
        },
    },

    data() {
        return {
            students: [],
            username: '',
            canSearchUsers: false,
            loadingStudents: false,
            stopLoadingStudents: () => {},
            searchQuery: null,
        };
    },

    mounted() {
        this.$hasPermission('can_search_users').then((val) => {
            this.canSearchUsers = val;
        });
    },

    methods: {
        onInput(newValue) {
            this.$emit('input', newValue);
        },

        queryMatches() {
            if (this.searchQuery == null || this.value == null) {
                return false;
            }

            if (this.searchQuery.length === 0) {
                return true;
            }

            const username = this.value.username.toLocaleLowerCase();
            const name = this.value.name ? this.value.name.toLocaleLowerCase() : ';';

            return this.searchQuery.split(' ').every((queryWord) => {
                const word = queryWord.toLocaleLowerCase();
                return username.indexOf(word) >= 0 || name.indexOf(word) >= 0;
            });
        },

        asyncFind(query) {
            this.stopLoadingStudents();
            this.searchQuery = query;

            if (query.length < 3 && this.value && this.queryMatches()) {
                this.students = [this.value];
                this.loadingStudents = false;
            } else if (query.length < 3) {
                this.students = [];
                this.loadingStudents = false;
            } else {
                this.loadingStudents = true;
                let stop = false;
                let id;
                id = setTimeout(() => {
                    this.$http.get('/api/v1/users/', { params: { q: query } }).then(({ data }) => {
                        if (stop) {
                            return;
                        }

                        this.loadingStudentsCallback = null;
                        this.students = data.filter(this.filterStudents);
                        this.loadingStudents = false;
                    }, (err) => {
                        if (stop) {
                            return;
                        }

                        if (err.response.data.code === 'RATE_LIMIT_EXCEEDED') {
                            id = setTimeout(() => this.asyncFind(query), 1000);
                        } else {
                            throw err;
                        }
                    });
                }, 250);

                this.stopLoadingStudents = () => {
                    clearTimeout(id);
                    stop = true;
                };
            }
        },
    },

    components: {
        Multiselect,
    },
};
</script>

<style lang="less">
@import '~mixins.less';

#app.dark .user-selector {
    .dark-selects-colors;
}

.user-selector.multiselect {
    .multiselect__tags {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }

    .multiselect__option {
        white-space: normal;
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
}
</style>
