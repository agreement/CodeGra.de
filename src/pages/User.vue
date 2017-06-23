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
import { bCard } from 'bootstrap-vue/lib/components';
import { UserInfo, SnippetManager } from '@/components';

export default {
    name: 'user-page',

    components: {
        UserInfo,
        SnippetManager,
        bCard,
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>
