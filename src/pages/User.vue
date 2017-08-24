<template>
    <div class="page user">
        <div class="row">
            <div class="col-6">
                <b-card header="User info">
                    <user-info></user-info>
                </b-card>
            </div>
            <div class="col-6">
                <b-card header="Snippets">
                    <snippet-manager></snippet-manager>
                </b-card>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { UserInfo, SnippetManager } from '@/components';

import { setPageTitle } from './title';

export default {
    name: 'user-page',

    components: {
        UserInfo,
        SnippetManager,
    },

    mounted() {
        setPageTitle('User info');
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>
