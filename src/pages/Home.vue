<template>
    <div class="page home">
        <login v-if="!loggedIn"></login>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { Login } from '@/components';

export default {
    name: 'home-page',

    components: {
        Login,
    },

    computed: {
        ...mapGetters([
            'loggedIn',
        ]),
    },
};
</script>
