<template>
    <div class="page home">
        <login v-if="!user.loggedIn"></login>
    </div>
</template>

<script>
import { Login } from '@/components';

export default {
    name: 'home-page',

    components: {
        Login,
    },

    store: {
        user: 'user',
    },
};
</script>
