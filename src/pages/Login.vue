<template>
    <div class="page login row justify-content-center">
        <div class="col-6">
            <login></login>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { Login } from '@/components';

import { setTitle } from './title';

export default {
    name: 'login-page',

    data() {
        return {};
    },

    beforeCreate() {
        if (this.loggedIn) {
            this.$router.replace({ name: 'assignments' });
        }
    },

    mounted() {
        setTitle('Login');
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
