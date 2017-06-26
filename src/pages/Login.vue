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

export default {
    name: 'login-page',

    data() {
        return {};
    },

    mounted() {
        if (this.loggedIn) {
            this.$router.replace({ name: 'assignments' });
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
