<template>
    <div class="page user">
        <div class="row">
            <user-info class="col-6"></user-info>
            <snippet-manager class="col-6"></snippet-manager>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { UserInfo, SnippetManager } from '@/components';

export default {
    name: 'user-page',

    components: {
        UserInfo,
        SnippetManager,
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>
