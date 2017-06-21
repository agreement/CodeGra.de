<template>
    <div class="page home row">
        <user-info class="col-5"></user-info>
        <snippet-manager class="col-5"></snippet-manager>
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
