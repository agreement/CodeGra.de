<template>
    <b-card header="Snippets">
         <div class="justify-content-centermy-1 row">
            <b-form-fieldset horizontal label="" class="col-10" :label-size="1">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
            </b-form-fieldset>
        </div>
    <b-table striped hover
         v-on:row-clicked='expandSnippet'
         :items="snippets"
         :fields="fields"
         :current-page="currentPage"
         :filter="filter">
      <template slot="key" scope="item">
        {{item.key}}
      </template>
      <template slot="text" scope="item">
        {{item.value}}
      </template>
    </b-table>
    </b-card>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

export default {
    name: 'snippet-manager',

    data() {
        return {
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
            },
        };
    },

    computed: {
        snippets: this.getSnippets,
    },

    methods() {
    },

    ...mapActions({
        refreshSnippets: 'user/refreshSnippets',
        addSnippetToStore: 'user/addSnippet',
    }),
    ...mapGetters({
        getSnippets: 'user/snippets',
    }),
};
</script>
