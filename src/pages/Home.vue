<template>
    <div class="page home"></div>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
    name: 'home-page',

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },

    mounted() {
        this.$router.push({
            name: this.loggedIn ? 'assignments' : 'login',
        });
    },
};
</script>
