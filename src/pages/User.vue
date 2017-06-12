<template>
    <div class="page home">
        <user-info></user-info>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { UserInfo } from '@/components';

export default {
    name: 'user-page',

    components: {
        UserInfo,
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>
