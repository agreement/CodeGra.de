<template>
    <div class="snippet-manager">
        <b-form-fieldset>
            <input v-model="filter"
                   class="form-control"
                   placeholder="Type to Search"
                   v-on:keyup.enter="submit"/>
        </b-form-fieldset>
        <b-table striped hover
                 class="snippets-table"
            :items="snippets"
            :fields="fields"
            :current-page="currentPage"
            :filter="filter"
            :response="true">

            <template slot="key" scope="item">
                <b-form-fieldset
                    :state="!item.item.submitted ? '' : validSnippetKey(item.item) ? 'success' : 'danger'"
                    :feedback="item.item.keyError"
                    v-if="item.item.editing">
                    <input type="text"
                           class="form-control"
                           placeholder="Key"
                           v-model="item.item.key"/>
                </b-form-fieldset>
                <span v-else>{{ item.item.key ? item.item.key : '-' }}</span>
            </template>

            <template slot="text" scope="item">
                <b-form-fieldset
                    :state="!item.item.submitted ? '' : validSnippetValue(item.item) ? 'success' : 'danger'"
                    :feedback="item.item.valueError"
                    v-if="item.item.editing">
                    <input type="text"
                           class="form-control"
                           placeholder="Value"
                           v-model="item.item.value"/>
                </b-form-fieldset>
                <span v-else>{{ item.item.value ? item.item.value : '-' }}</span>
            </template>

            <template slot="actions" scope="item">
                <div v-if="item.item.editing" class="button-wrapper">
                    <b-btn size="sm" variant="danger" :disabled="item.item.pending" @click="cancelSnippetEdit(item.item)">
                        <icon name="ban" scale="1"></icon>
                    </b-btn>
                    <b-btn size="sm" variant="success" :disabled="item.item.pending" @click="saveSnippet(item.item)">
                        <loader v-if="item.item.pending" :scale="1" ></loader>
                        <icon name="floppy-o" scale="1" v-else></icon>
                    </b-btn>
                </div>
                <div class="button-wrapper" v-else>
                    <b-btn size="sm" variant="danger" :disabled="item.item.pending" @click="deleteSnippet(item.item)">
                        <icon name="times" scale="1"></icon>
                    </b-btn>
                    <b-btn size="sm" variant="primary" @click="editSnippet(item.item)">
                        <icon name="pencil" scale="1"></icon>
                    </b-btn>
                </div>
            </template>
        </b-table>
        <b-button-group class="global">
            <loader :scale="2" class="" v-if="loading"></loader>
            <b-button variant="primary" @click="newSnippet" v-else>
                <span>Add</span>
            </b-button>
        </b-button-group>
    </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/floppy-o';
import 'vue-awesome/icons/ban';

import Loader from './Loader';

export default {
    name: 'snippet-manager',

    data() {
        return {
            loading: true,
            snippets: [],
            filter: null,
            currentPage: 1,
            fields: {
                key: {
                    label: 'Key',
                    sortable: true,
                },
                text: {
                    label: 'Text',
                    sortable: true,
                },
                actions: {
                    label: 'Actions',
                    sortable: false,
                    class: 'text-center',
                },
            },
        };
    },

    methods: {
        validSnippetKey(snippet) {
            if (snippet.key.match(/\s/)) {
                snippet.keyError = 'No spaces allowed!';
                return false;
            } else if (snippet.key.length === 0) {
                snippet.keyError = 'Snippet key cannot be empty';
                return false;
            } else if (snippet.key !== snippet.origKey &&
                this.snippets.some(snip => snip !== snippet && snip.key === snippet.key)) {
                snippet.keyError = 'Snippet key must be unique';
                return false;
            }
            snippet.keyError = '';
            return true;
        },
        validSnippetValue(snippet) {
            if (snippet.value.length === 0) {
                snippet.valueError = 'Snippet value cannot be empty';
                return false;
            }
            snippet.valueError = '';
            return true;
        },
        newSnippet() {
            this.snippets.push({
                key: '',
                value: '',
                submitted: false,
                editing: true,
                pending: false,
                id: null,
            });
        },
        editSnippet(snippet) {
            snippet.origKey = snippet.key;
            snippet.origValue = snippet.value;
            snippet.editing = true;
        },
        cancelSnippetEdit(snippet) {
            if (snippet.id === null) {
                this.deleteSnippet(snippet);
                return;
            }
            snippet.editing = false;
            snippet.value = snippet.origValue;
            snippet.key = snippet.origKey;
        },
        saveSnippet(snippet) {
            snippet.submitted = true;
            if (!this.validSnippetKey(snippet) || !this.validSnippetValue(snippet)) {
                return;
            }
            if (snippet.id !== null && snippet.key === snippet.origKey &&
                snippet.value === snippet.origValue) {
                snippet.editing = false;
                return;
            }
            this.$set(snippet, 'pending', true);
            if (snippet.id === null) {
                this.$http.put('/api/v1/snippet', {
                    key: snippet.key,
                    value: snippet.value,
                }).then((response) => {
                    snippet.pending = false;
                    snippet.editing = false;
                    snippet.id = response.data.id;
                    this.addSnippetToStore({
                        key: snippet.key,
                        value: { value: snippet.value, id: snippet.id } },
                    );
                });
            } else {
                this.deleteSnippetFromStore(snippet.origKey);
                this.addSnippetToStore({
                    key: snippet.key,
                    value: { value: snippet.value, id: snippet.id } },
                );
                this.$http.patch(`/api/v1/snippets/${snippet.id}`, {
                    key: snippet.key,
                    value: snippet.value,
                }).then(() => {
                    snippet.pending = false;
                    snippet.editing = false;
                });
            }
        },
        deleteSnippet(snippet) {
            if (snippet.id !== null) {
                this.deleteSnippetFromStore(snippet.key);
                this.$http.delete(`/api/v1/snippets/${snippet.id}`).then(() => {
                    this.snippets.splice(this.snippets.indexOf(snippet), 1);
                });
            } else {
                this.snippets.splice(this.snippets.indexOf(snippet), 1);
            }
        },
        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
            addSnippetToStore: 'user/addSnippet',
            deleteSnippetFromStore: 'user/deleteSnippet',
        }),
        ...mapGetters({
            getSnippetsFromStore: 'user/snippets',
        }),
    },

    mounted() {
        this.refreshSnippets().then(() => {
            const snips = this.getSnippetsFromStore();
            this.snippets = Object.keys(snips).map((key) => {
                const dict = {
                    key,
                    value: snips[key].value,
                    editing: false,
                    submitted: true,
                    pending: false,
                    id: snips[key].id,
                };
                return dict;
            });
            this.loading = false;
        });
    },

    components: {
        Icon,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.form-group {
    margin-bottom: 0;
}

.global.btn-group {
    float: right;
}

.button-wrapper {
    width: 5em;
}
</style>

<style lang="less">
table.snippets-table tr th:first-child {
    width: 25%;
}

table.snippets-table tr th:nth-child(2) {
    width: 60%;
}
</style>
