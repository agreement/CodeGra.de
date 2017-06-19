<template>
    <b-card header="Snippets">
    <div class="justify-content-centermy-1 row">
      <b-form-fieldset horizontal label="" class="col-12" :label-size="1">
        <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
      </b-form-fieldset>
    </div>
    <b-table striped hover
      :items="snippets"
      :fields="fields"
      :current-page="currentPage"
      :filter="filter"
      :response="true">
        <template slot="key" scope="item">
            <b-form-fieldset :state="validSnippetKey(item.item)?'success':'danger'" :feedback="item.item.keyError" v-if="item.item.editing">
                <b-form-input type="text" placeholder="Key" v-model="item.item.key"></b-form-input>
            </b-form-fieldset>
            <span v-else>{{item.item.key ? item.item.key : '-'}}</span>
        </template>
        <template slot="text" scope="item">
            <b-form-fieldset :state="validSnippetValue(item.item)?'success':'danger'" :feedback="item.item.valueError" v-if="item.item.editing">
                <b-form-input type="text" placeholder="Value" v-model="item.item.value"></b-form-input>
            </b-form-fieldset>
            <span v-else>{{item.item.value ? item.item.value : '-'}}</span>
        </template>
        <template slot="actions" scope="item">
            <b-btn size="sm" variant="info" :disabled="item.item.pending" @click="saveSnippet(item.item)" v-if="item.item.editing">
                <loader v-if="item.item.pending" :scale="1" ></loader>
                <icon name="floppy-o" scale="1" v-else></icon>
            </b-btn>
            <b-btn size="sm" variant="warning" @click="editSnippet(item.item)" v-else>
                <icon name="pencil" scale="1"></icon>
            </b-btn>
            <b-btn size="sm" variant="warning" v-if="item.item.editing" :disabled="item.item.pending" @click="cancelSnippetEdit(item.item)">
                <icon name="ban" scale="1"></icon>
            </b-btn>
            <b-btn size="sm" variant="danger" :disabled="item.item.pending" @click="deleteSnippet(item.item)" v-else   >
                <icon name="times" scale="1"></icon>
            </b-btn>
        </template>
    </b-table>
    <div class="row">
        <div class="col">
            <b-button-group>
                <loader :scale="2" class="" v-if="loading"></loader>
                <b-button size="sm" variant="success" @click="newSnippet" v-else>
                    <icon name="plus" scale="1"></icon>
                </b-button>
            </b-button-group>
        </div>
    </div>
    </b-card>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/floppy-o';
import 'vue-awesome/icons/ban';
import 'vue-awesome/icons/plus';


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
                },
            },
        };
    },

    methods: {
        validSnippetKey(snippet) {
            if (snippet.key.indexOf(' ') > -1 || snippet.key.indexOf('\n') > -1) {
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
            if (!this.validSnippetKey(snippet) || !this.validSnippetValue(snippet)) {
                return;
            }
            if (snippet.id !== null && snippet.key === snippet.origKey &&
                snippet.value === snippet.origValue) {
                snippet.editing = false;
                return;
            }
            snippet.pending = true;
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