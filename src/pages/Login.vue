<template>
    <div class="page login">
        <login></login>
    </div>
</template>

<script>
import { Login } from '@/components';

export default {
    name: 'login-page',

    data() {
        return {};
    },

    mounted() {
        if (this.user.loggedIn) {
            this.$router.replace('/');
        }
    },

    components: {
        Login,
    },

    store: {
        user: 'user',
    },
};
</script>
