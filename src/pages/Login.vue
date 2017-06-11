<template>
    <div class="page login">
        <login></login>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { Login } from '@/components';

export default {
    name: 'login-page',

    data() {
        return {};
    },

    mounted() {
        if (this.loggedIn) {
            this.$router.replace('/');
        }
    },

    components: {
        Login,
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>
