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
      :filter="filter">
        <template slot="key" scope="item">
            <b-form-input type="text" v-model="item.item.key" v-if="item.item.editing"></b-form-input>
            <span v-else>{{item.item.key ? item.item.key : '-'}}</span>
        </template>
        <template slot="text" scope="item">
            <b-form-input type="text" v-model="item.item.value" v-if="item.item.editing"></b-form-input>
            <span v-else>{{item.item.value ? item.item.value : '-'}}</span>
        </template>
        <template slot="actions" scope="item">
            <b-btn size="sm" variant="info" :disabled="item.item.pending" @click="saveSnippet(item.item)" v-if="item.item.editing">
                <icon name="refresh" scale="1" spin v-if="item.item.pending"></icon>
                <icon name="floppy-o" scale="1" v-else></icon>
            </b-btn>
            <b-btn size="sm" variant="warning" @click="editSnippet(item.item)" v-else>
                <icon name="pencil" scale="1"></icon>
            </b-btn>
            <b-btn size="sm" variant="warning" v-if="item.item.editing" :disabled="item.item.pending" @click="editSnippet(item.item)">
                <icon name="ban" scale="1"></icon>
            </b-btn>
            <b-btn size="sm" variant="danger" :disabled="item.item.pending" @click="deleteSnippet(item.item)" v-else   >
                <icon name="times" scale="1"></icon>
            </b-btn>
        </template>
    </b-table>
    <b-button size="sm" variant="success" @click="newSnippet">
        <icon name="plus" scale="1"></icon>
    </b-button>
    </b-card>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/floppy-o';
import 'vue-awesome/icons/refresh';
import 'vue-awesome/icons/ban';
import 'vue-awesome/icons/plus';

export default {
    name: 'snippet-manager',

    data() {
        return {
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
        newSnippet() {
            this.snippets.push({ key: '', value: '', editing: true, pending: false, id: null });
            this.$forceUpdate();
        },
        editSnippet(snippet) {
            snippet.editing = !snippet.editing;
            this.$forceUpdate();
        },
        saveSnippet(snippet) {
            const val = {
                key: snippet.key,
                value: { value: snippet.value },
            };
            if (val.key.indexOf(' ') > -1 || val.key.indexOf('\n') > -1) {
                snippet.error = 'No spaces allowed!';
                return;
            } else if (val.key.length === 0) {
                snippet.error = 'Snippet key cannot be empty';
                return;
            } else if (val.value.value.length === 0) {
                snippet.error = 'Snippet value cannot be empty';
                return;
            }
            snippet.error = '';
            snippet.pending = true;
            this.$forceUpdate();
            this.addSnippetToStore(val);
            if (snippet.id == null) {
                this.$http.put('/api/v1/snippet', {
                    key: val.key,
                    value: val.value.value,
                }).then((response) => {
                    snippet.pending = false;
                    snippet.editing = false;
                    snippet.id = response.data.id;
                    this.$forceUpdate();
                });
            } else {
                this.$http.patch(`/api/v1/snippets/${snippet.id}`, {
                    key: val.key,
                    value: val.value.value,
                }).then(() => {
                    snippet.pending = false;
                    snippet.editing = false;
                    this.$forceUpdate();
                });
            }
        },
        deleteSnippet(snippet) {
            if (snippet.id !== null) {
                this.$http.delete(`/api/v1/snippets/${snippet.id}`).then(() => {
                    this.snippets.splice(this.snippets.indexOf(snippet), 1);
                    this.$forceUpdate();
                });
            else {
                this.snippets.splice(this.snippets.indexOf(snippet), 1);
                this.$forceUpdate();
            }
        },
        ...mapActions({
            refreshSnippets: 'user/refreshSnippets',
            addSnippetToStore: 'user/addSnippet',
        }),
        ...mapGetters({
            getSnippetsFromStore: 'user/snippets',
        }),
    },

    mounted() {
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
    },

    components: {
        Icon,
    },
};
</script>
